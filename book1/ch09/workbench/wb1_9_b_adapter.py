"""WB1.9-b  Provider adapter and Provider Panel runner.

Your own code calls one function, complete(prompt), and gets back one Result. Behind it sit
interchangeable back ends:

  Replay  reads answers recorded earlier from a JSONL file. No network, no key, no cost.
          Used for tests and for re-running an analysis on yesterday's answers.
  Remote  sends the prompt over HTTPS to any service that accepts the widely copied
          "chat completions" request shape (POST {base}/chat/completions).
  Local   the same request shape, sent to a model running on your own computer
          (for example a local runtime listening on http://localhost:11434/v1).

Changing provider means changing one line of configuration, not your program. That is the
adapter pattern: convert the interface of each service into the one interface your code expects.

Panel mode runs every task in panel_tasks.json on every back end listed in a config file and
writes one JSON line per answer: date and time, back end, model identifier returned by the
service, settings, the answer, token counts, latency, and the automatic check.

  python wb1_9_b_adapter.py                  replay demo on the bundled synthetic recording
  python wb1_9_b_adapter.py recorded         a recorded run of one real model (23 Nov 2026)
  python wb1_9_b_adapter.py panel my.json    live run; keys are read from environment variables

Only the standard library is used. A live run sends your prompts to the services you list:
read their data terms first (chapter 9, section on privacy).
"""
import dataclasses
import datetime as dt
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).parent


@dataclasses.dataclass
class Result:
    text: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    latency_s: float
    backend: str


class Replay:
    """Answers from a recording: one JSON object per line with keys backend, task, text, model,
    input_tokens, output_tokens, latency_s."""

    def __init__(self, path, label):
        self.label = label
        self.rows = {}
        for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                r = json.loads(line)
                self.rows[(r["backend"], r["task"])] = r

    def complete(self, prompt, settings, task_id):
        r = self.rows[(self.label, task_id)]
        return Result(r["text"], r["model"], r["input_tokens"], r["output_tokens"], r["latency_s"], self.label)


def retry_after(value, default):
    """Seconds to wait from a Retry-After header, which RFC 9110 allows as a number of seconds
    or as an HTTP date; anything unreadable falls back to the default."""
    if not value:
        return default
    try:
        return max(0.0, float(value))
    except ValueError:
        pass
    try:
        from email.utils import parsedate_to_datetime
        when = parsedate_to_datetime(value)
        return max(0.0, (when - dt.datetime.now(dt.timezone.utc)).total_seconds())
    except (TypeError, ValueError):
        return default


class ChatCompletions:
    """Remote or local service that accepts POST {base_url}/chat/completions."""

    def __init__(self, label, base_url, model, key_env=None, timeout=120):
        self.label, self.base, self.model, self.key_env, self.timeout = label, base_url.rstrip("/"), model, key_env, timeout

    def request(self, prompt, settings):
        body = {"model": self.model, "messages": [{"role": "user", "content": prompt}]}
        body.update(settings)
        headers = {"Content-Type": "application/json"}
        if self.key_env:
            key = os.environ.get(self.key_env)
            if not key:
                raise RuntimeError(f"environment variable {self.key_env} is not set")
            headers["Authorization"] = "Bearer " + key
        return urllib.request.Request(self.base + "/chat/completions", json.dumps(body).encode(), headers)

    def complete(self, prompt, settings, task_id=None):
        req = self.request(prompt, settings)
        for attempt in range(4):                     # rate limits: HTTP 429, wait and retry
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data = json.load(resp)
                break
            except urllib.error.HTTPError as e:
                if e.code != 429 or attempt == 3:
                    raise
                time.sleep(retry_after(e.headers.get("Retry-After"), 2 ** (attempt + 1)))
        latency = time.perf_counter() - t0
        usage = data.get("usage") or {}
        return Result(data["choices"][0]["message"]["content"], data.get("model", self.model),
                      usage.get("prompt_tokens"), usage.get("completion_tokens"), latency, self.label)


def make_backend(cfg):
    if cfg["type"] == "replay":
        return Replay(HERE / cfg["file"], cfg["label"])
    return ChatCompletions(cfg["label"], cfg["base_url"], cfg["model"], cfg.get("key_env"))


def number_in(text):
    m = re.search(r"-?\d[\d,]*\.?\d*", text)
    return float(m.group().replace(",", "")) if m else None


def check(task, text):
    """Automatic check. Returns 'pass', 'fail' or 'human' (needs a person, rubric in the task)."""
    c = task["check"]
    if c["type"] == "one_of":
        return "pass" if text.strip().strip(".").lower() == c["expected"] else "fail"
    if c["type"] == "number":
        x = number_in(text)
        return "pass" if x is not None and abs(x - c["expected"]) <= c["tolerance"] else "fail"
    if c["type"] == "json_fields":
        m = re.search(r"\{.*\}", text, flags=re.S)
        try:
            got = json.loads(m.group()) if m else {}
        except json.JSONDecodeError:
            return "fail"
        def same(v, g):
            if isinstance(v, float):              # numbers must be numbers, not "1,500.00 EUR"
                return isinstance(g, (int, float)) and float(g) == v
            return g == v
        ok = isinstance(got, dict) and all(same(v, got.get(k)) for k, v in c["expected"].items())
        return "pass" if ok else "fail"
    if c["type"] == "max_words":
        return "human" if len(text.split()) <= c["limit"] else "fail"
    return "human"


def run_panel(config_path, out_path=None, quiet=False):
    cfg = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    tasks = json.loads((HERE / "panel_tasks.json").read_text(encoding="utf-8"))
    rows = []
    for b in cfg["backends"]:
        backend = make_backend(b)
        # services differ in the settings they accept: a back end may override or drop
        # (value null) a setting, and the record keeps what was actually sent
        settings = {k: v for k, v in {**tasks["settings"], **b.get("settings", {})}.items() if v is not None}
        for t in tasks["tasks"]:
            try:
                r = backend.complete(t["prompt"], settings, t["id"])
                verdict = check(t, r.text)
            except Exception as e:                   # a refused call is a result, not a crash
                r = Result(f"{type(e).__name__}: {e}", b.get("model", "?"), None, None, None, b["label"])
                verdict = "error"
            rows.append({"run_at": cfg.get("run_at") or dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                         "backend": r.backend, "model": r.model, "task": t["id"], "settings": settings,
                         "input_tokens": r.input_tokens, "output_tokens": r.output_tokens,
                         "latency_s": None if r.latency_s is None else round(r.latency_s, 2), "check": verdict, "text": r.text})
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
    if not quiet:
        report(rows)
    return rows


def report(rows):
    print(f"{'backend':<10}{'model':<20}{'task':<15}{'in':>5}{'out':>5}{'s':>6}  check")
    for r in rows:
        tin = "-" if r["input_tokens"] is None else r["input_tokens"]
        tout = "-" if r["output_tokens"] is None else r["output_tokens"]
        lat = "-" if r["latency_s"] is None else f"{r['latency_s']:.2f}"
        print(f"{r['backend']:<10}{r['model']:<20}{r['task']:<15}{tin:>5}{tout:>5}{lat:>6}  {r['check']}")


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "recorded":
        print("WB1.9-b  recorded run: claude-opus-5-5, 23 Nov 2026")
        print("         (agent session, not the API; see note in the file)")
        run_panel(HERE / "panel_config_claude.json")
    elif len(sys.argv) >= 3 and sys.argv[1] == "panel":
        stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
        run_panel(sys.argv[2], HERE / f"panel_results_{stamp}.jsonl")
    else:
        print("WB1.9-b  replay demo (synthetic recording, not real provider answers)")
        run_panel(HERE / "panel_config_replay.json")
