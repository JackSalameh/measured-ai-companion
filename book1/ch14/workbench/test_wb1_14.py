"""Tests for the chapter 14 Workbench apps."""
import csv
import pathlib
import subprocess
import sys

import make_invoices as mk
import wb1_14_a_extract_eval as ev
import wb1_14_b_reconcile as rc

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_14_a_extract_eval", "wb1_14_b_reconcile"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_truth_file_and_documents_are_what_the_generator_writes():
    rows = list(csv.DictReader((HERE / "invoices_truth.csv").open(encoding="utf-8")))
    assert rows == [{k: str(v) for k, v in r.items()} for r in mk.truth()]
    for r in rows:
        assert abs(float(r["net"]) + float(r["vat"]) - float(r["total"])) < 0.005
    assert len(list((HERE / "invoices").glob("*.txt"))) == 14


def test_validation_rules():
    good = {"invoice_no": "BW-2601", "date": "2026-01-02", "supplier": "x", "net": "100.00", "vat": "20.00", "total": "120.00"}
    assert ev.validate(good) == []
    assert any("not total" in p for p in ev.validate(dict(good, total="100.00")))
    assert any("register" in p for p in ev.validate(dict(good, po_number="PO-999")))
    assert any("outside" in p for p in ev.validate(dict(good, date="2026-03-02")))


def test_swapped_digits():
    assert rc.swapped_digits(2175.37, 2157.37) and not rc.swapped_digits(2175.37, 2175.37)
    assert not rc.swapped_digits(2175.37, 2185.37) and (2175.37 - 2157.37) % 9 < 1e-9
