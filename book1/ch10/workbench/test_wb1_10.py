"""Tests for the chapter 10 Workbench apps."""
import json
import math
import pathlib
import subprocess
import sys

import wb1_10_a_prompt_tester as pt
import wb1_10_b_interval as iv

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_10_a_prompt_tester", "wb1_10_b_interval"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_recorded_run_matches_expected():
    out = subprocess.run([sys.executable, str(HERE / "wb1_10_a_prompt_tester.py"), "recorded"],
                         capture_output=True, text=True, check=True, cwd=HERE).stdout
    assert out == (HERE / "expected" / "wb1_10_a_recorded.txt").read_text(encoding="utf-8")


def test_recording_is_labelled():
    for line in (HERE / "replay_claude_2026-11-23.jsonl").read_text(encoding="utf-8").splitlines():
        assert "RECORDED 2026-11-23" in json.loads(line)["note"]


def test_wilson_known_values_and_bounds():
    lo, hi = iv.wilson(0, 10)                         # never below 0 or above 1, unlike Wald
    assert lo == 0 or abs(lo) < 1e-12
    assert 0 < hi < 1
    for k in range(11):
        lo, hi = iv.wilson(k, 10)
        assert -1e-12 <= lo <= k / 10 + 1e-12 and k / 10 - 1e-12 <= hi <= 1 + 1e-12
    lo, hi = iv.wilson(50, 100)                       # symmetric around 0.5
    assert abs((lo + hi) / 2 - 0.5) < 1e-12


def test_wilson_matches_score_test_inversion():
    # the Wilson interval is the set of p whose score statistic |k/n - p| / sqrt(p(1-p)/n) <= z
    k, n = 80, 98
    lo, hi = iv.wilson(k, n)
    for p in (lo, hi):
        assert abs(abs(k / n - p) / math.sqrt(p * (1 - p) / n) - iv.Z) < 1e-9


def test_mcnemar_exact():
    assert iv.mcnemar(0, 0) == 1.0
    assert iv.mcnemar(5, 5) == 1.0
    # b + c = 6, all on one side: p = 2 * (1/2)^6
    assert abs(iv.mcnemar(6, 0) - 2 / 64) < 1e-15
    assert abs(iv.mcnemar(18, 7) - 2 * sum(math.comb(25, i) for i in range(8)) / 2 ** 25) < 1e-15


def test_cluster_se_equals_plain_se_for_singletons():
    ys = [1, 1, 0, 1, 0, 1, 1, 1]
    out = [(i, y) for i, y in enumerate(ys)]          # each case its own group
    p = sum(ys) / len(ys)
    se, groups = iv.cluster_se(out)
    assert groups == len(ys)
    assert abs(se - math.sqrt(p * (1 - p) / len(ys))) < 1e-12


def test_parser_is_strict():
    assert pt.parse_label("Login.") == "login"
    assert pt.parse_label("login, I think") == "invalid"
    assert pt.parse_label("") == "invalid"


def test_replay_keys_separate_prompt_versions(tmp_path):
    cases = [{"ticket_id": "T1", "text": "x", "queue": "login"}, {"ticket_id": "T2", "text": "y", "queue": "other"}]
    rec = tmp_path / "rec.jsonl"
    lines = []
    for p, answers in (("v1", ("Login problem", "other")), ("v2", ("login", "other"))):
        for c, a in zip(cases, answers):
            lines.append(json.dumps({"backend": "m", "task": f"{p}:{c['ticket_id']}", "text": a, "model": "m",
                                     "input_tokens": 1, "output_tokens": 1, "latency_s": 0}))
    rec.write_text("\n".join(lines), encoding="utf-8")
    prompts = {p: HERE / "prompts" / f"triage_{p}.txt" for p in ("v1", "v2")}
    rows = pt.run_pairs(prompts, [pt.ad.Replay(rec, "m")], cases)
    score = {p: sum(r["label"] == r["truth"] for r in rows if r["prompt"] == p) for p in prompts}
    assert score == {"v1": 1, "v2": 2}


def test_no_example_leaks_into_golden_set():
    cases, _, _ = pt.golden_set()
    assert pt.leaked_examples(HERE / "prompts" / "triage_v2.txt", cases) == ([], [])


def test_leak_check_finds_near_copies(tmp_path):
    cases = [{"ticket_id": "T1", "text": "Please refund order 1234", "queue": "billing"},
             {"ticket_id": "T2", "text": "Where is parcel 77?", "queue": "shipping"}]
    p = tmp_path / "p.txt"
    p.write_text("Examples:\nTicket: Please refund order 9999\nQueue: billing\nTicket: {ticket}\n", encoding="utf-8")
    assert pt.leaked_examples(p, cases) == ([], ["T1"])
