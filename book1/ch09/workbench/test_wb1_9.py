"""Tests for the chapter 9 Workbench apps and example."""
import http.server
import importlib.util
import json
import pathlib
import subprocess
import sys
import threading

import pytest

import wb1_9_a_cost as cost
import wb1_9_b_adapter as ad

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_9_a_cost", "wb1_9_b_adapter"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_cost_formula_by_hand():
    task = {"input_tokens": "900", "cacheable_input_tokens": "700", "output_tokens": "10"}
    price = {"input_per_m": "2", "cached_input_per_m": "0.1", "output_per_m": "10"}
    assert abs(cost.call_cost(task, price) - (900 * 2 + 10 * 10) / 1e6) < 1e-15
    assert abs(cost.call_cost(task, price, cached=True) - (200 * 2 + 700 * 0.1 + 10 * 10) / 1e6) < 1e-15
    price["cached_input_per_m"] = ""                       # no cached price: full input price
    assert cost.call_cost(task, price, cached=True) == cost.call_cost(task, price)


def test_cost_scales_linearly():
    tasks = cost.read(cost.USAGE)
    p = cost.read(cost.PRICES)[0]
    double = [dict(t, calls_per_month=str(2 * int(t["calls_per_month"]))) for t in tasks]
    assert abs(cost.monthly(double, p)[1] - 2 * cost.monthly(tasks, p)[1]) < 1e-9
    assert 0 < cost.output_share(tasks, p) < 1


def test_checks():
    tasks = {t["id"]: t for t in json.loads((HERE / "panel_tasks.json").read_text(encoding="utf-8"))["tasks"]}
    assert ad.check(tasks["T2-classify"], "Billing.") == "pass"
    assert ad.check(tasks["T2-classify"], "billing or delivery") == "fail"
    assert ad.check(tasks["T3-arithmetic"], "The VAT is 209.88 EUR") == "pass"
    assert ad.check(tasks["T3-arithmetic"], "209.87") == "fail"
    assert ad.check(tasks["T1-extract"], '{"number":"INV-2041","date":"2026-03-14","total":1500}') == "pass"
    assert ad.check(tasks["T1-extract"], '{"number":"INV-2041","date":"2026-03-14","total":"1,500.00"}') == "fail"
    assert ad.check(tasks["T1-extract"], "no json here") == "fail"
    assert ad.check(tasks["T5-summarize"], "word " * 26) == "fail"
    assert ad.check(tasks["T5-summarize"], "short summary") == "human"
    assert ad.check(tasks["T4-translate"], "anything") == "human"


class FakeService(http.server.BaseHTTPRequestHandler):
    """Answers like a chat-completions service; the first request gets HTTP 429."""
    seen = []

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        FakeService.seen.append((self.path, self.headers.get("Authorization"), body))
        if len(FakeService.seen) == 1:
            self.send_response(429)
            self.send_header("Retry-After", "0")
            self.end_headers()
            return
        out = json.dumps({"model": body["model"] + "-2026-11-01",
                          "choices": [{"message": {"role": "assistant", "content": "billing"}}],
                          "usage": {"prompt_tokens": 71, "completion_tokens": 1}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def log_message(self, *a):
        pass


def test_chat_completions_backend_against_fake_service(monkeypatch):
    srv = http.server.HTTPServer(("127.0.0.1", 0), FakeService)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        monkeypatch.setenv("FAKE_KEY", "k-123")
        b = ad.ChatCompletions("fake", f"http://127.0.0.1:{srv.server_port}/v1/", "toy-model", "FAKE_KEY")
        r = b.complete("Classify this.", {"temperature": 0, "max_tokens": 5})
    finally:
        srv.shutdown()
    assert len(FakeService.seen) == 2                          # one 429, one retry
    path, auth, body = FakeService.seen[-1]
    assert path == "/v1/chat/completions" and auth == "Bearer k-123"
    assert body == {"model": "toy-model", "messages": [{"role": "user", "content": "Classify this."}],
                    "temperature": 0, "max_tokens": 5}
    assert (r.text, r.model, r.input_tokens, r.output_tokens) == ("billing", "toy-model-2026-11-01", 71, 1)


def test_missing_key_is_reported(monkeypatch):
    monkeypatch.delenv("NO_SUCH_KEY", raising=False)
    with pytest.raises(RuntimeError, match="NO_SUCH_KEY"):
        ad.ChatCompletions("x", "http://127.0.0.1:9", "m", "NO_SUCH_KEY").request("p", {})


@pytest.mark.skipif(importlib.util.find_spec("mistral_common") is None, reason="needs mistral-common")
def test_token_counts_match_expected():
    assert run("ex9_tokens.py") == (HERE / "expected" / "ex9_tokens.txt").read_text(encoding="utf-8")


def test_recorded_panel_matches_expected_and_is_labelled():
    out = subprocess.run([sys.executable, str(HERE / "wb1_9_b_adapter.py"), "recorded"],
                         capture_output=True, text=True, check=True, cwd=HERE).stdout
    assert out == (HERE / "expected" / "wb1_9_b_recorded.txt").read_text(encoding="utf-8")
    for line in (HERE / "replay_claude_2026-11-23.jsonl").read_text(encoding="utf-8").splitlines():
        assert "RECORDED 2026-11-23" in json.loads(line)["note"]


def test_retry_after_accepts_seconds_and_dates():
    import wb1_9_b_adapter as ad
    assert ad.retry_after("3", 9) == 3.0
    assert ad.retry_after(None, 9) == 9
    assert ad.retry_after("Wed, 21 Oct 2015 07:28:00 GMT", 9) == 0.0     # a past date: no wait
    assert ad.retry_after("soon", 9) == 9


def test_refused_call_is_recorded_as_error(tmp_path):
    import wb1_9_b_adapter as ad
    cfg = tmp_path / "c.json"
    cfg.write_text(json.dumps({"backends": [{"type": "remote", "label": "x", "base_url": "http://127.0.0.1:9",
                                             "model": "m", "key_env": "NO_SUCH_KEY_VARIABLE_XYZ"}]}), encoding="utf-8")
    rows = ad.run_panel(cfg, quiet=True)
    assert len(rows) == 5 and all(r["check"] == "error" for r in rows)
