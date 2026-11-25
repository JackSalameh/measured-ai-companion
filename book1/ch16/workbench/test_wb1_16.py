"""Tests for the chapter 16 Workbench apps."""
import csv
import pathlib
import subprocess
import sys

import wb1_16_b_decision_log as dl

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, cwd=HERE).stdout


def test_decision_log_output_matches_expected():
    assert run("wb1_16_b_decision_log.py") == (HERE / "expected" / "wb1_16_b_decision_log.txt").read_text(encoding="utf-8")


def test_clean_log_has_no_problems():
    rows = list(csv.DictReader((HERE / "decision_log_example.csv").open(encoding="utf-8")))[:2]
    rows[0]["status"] = "accepted"                  # D-001 is no longer superseded once D-004 is gone
    assert dl.check(rows) == []


def test_portfolio_runner_reports_every_chapter_and_no_failures():
    out = run("wb1_16_a_portfolio_runner.py")
    assert "15 chapters" in out and out.rstrip().endswith("all chapters reproduce")
