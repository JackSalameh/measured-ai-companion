"""Tests for the chapter 11 Workbench apps."""
import pathlib
import subprocess
import sys

import wb1_11_a_summary_checker as sc
import wb1_11_b_consistency as cp

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_11_a_summary_checker", "wb1_11_b_consistency"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_facts_recomputed_independently():
    rows = sc.load()
    sales = sum(float(r["credit"]) for r in rows if r["account"] == "4000")
    assert abs(sc.facts(rows)["sales.year"] - sales) < 0.005
    qs = [sc.facts(rows)[f"sales.q{i}"] for i in (1, 2, 3, 4)]
    assert abs(sum(qs) - sales) < 0.01          # the quarters add up to the year


def test_planted_issues_found():
    i = sc.issues(sc.load())
    assert "J0101" in i["duplicate"] and i["no description"] == ["J0041", "J0181", "J0301"]
    assert i["impossible date"] == ["J0223"]


def test_checker_verdicts():
    f = {"x": 10.0, "y": "no"}
    claims = [{"id": "a", "fact": "x", "value": "10.00"}, {"id": "b", "fact": "x", "value": "1.0"},
              {"id": "c", "fact": "y", "value": "No"}, {"id": "d", "fact": "", "value": ""}]
    assert [v for _, v, _ in sc.check(claims, f)] == ["OK", "WRONG", "OK", "SOURCE"]


def test_agreement():
    assert cp.agreement(["a", "a", "b", "a"]) == ("a", 0.75)
