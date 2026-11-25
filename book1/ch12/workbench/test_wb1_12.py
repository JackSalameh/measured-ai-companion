"""Tests for the chapter 12 Workbench apps."""
import datetime as dt
import pathlib
import subprocess
import sys

import wb1_12_a_citation_checker as cc
import wb1_12_b_source_log as sl

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_12_a_citation_checker", "wb1_12_b_source_log"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_identifier_syntax():
    assert cc.doi_ok("10.1145/1273445.1273458") and not cc.doi_ok("10.11/x") and not cc.doi_ok("doi:10.1145/1")
    assert cc.arxiv_ok("1706.03762") and cc.arxiv_ok("0704.0001v2") and cc.arxiv_ok("2310.01798v2")
    assert not cc.arxiv_ok("2313.01798") and not cc.arxiv_ok("1501.0001") and not cc.arxiv_ok("1412.12345")
    assert cc.isbn13_ok("978-0-262-03561-3") and not cc.isbn13_ok("9780262035614")


def test_every_isbn_in_library_valid():
    import csv
    for w in csv.DictReader(open(HERE / "library.csv", encoding="utf-8")):
        if w["isbn"]:
            assert cc.isbn13_ok(w["isbn"])


def test_source_log_rules():
    rows = [{"id": "S-001", "claim": "c", "source": "", "checked": "2026-01-01", "status": "V", "used_in": ""}]
    assert any("no source" in m for _, _, m in sl.problems(rows, dt.date(2026, 2, 1)))
    rows[0].update(source="s", checked="2026-03-01")
    assert any("future" in m for _, _, m in sl.problems(rows, dt.date(2026, 2, 1)))
