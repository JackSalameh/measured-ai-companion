import csv
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).parent


def rows(name):
    return list(csv.DictReader(open(HERE / "out" / name, encoding="utf-8")))


def test_validate_reproduces_files():
    assert subprocess.run([sys.executable, str(HERE / "validate.py")], cwd=HERE).returncode == 0


def test_ledger_balances_and_planted_defects():
    L = rows("ledger.csv")
    assert abs(sum(float(r["debit"]) for r in L) - sum(float(r["credit"]) for r in L)) < 1e-6
    assert sum(1 for r in L if r["description"] == "") == 6          # 3 transactions x 2 lines
    assert sum(1 for r in L if r["date"] == "2026-02-30") == 2


def test_signal_planted_units_and_missing():
    S = rows("signal_features.csv")
    assert [r["record_id"] for r in S if r["unit"] == "g"] == ["R018", "R059", "R102"]
    assert sum(1 for r in S if r["temp_c"] == "") == 2


def test_tickets_counts():
    T = rows("tickets.csv")
    assert len(T) == 618 and sum(1 for r in T if r["channel"] == "") > 0
