"""Tests for the chapter 15 Workbench apps."""
import pathlib
import subprocess
import sys

import wb1_15_a_scanner as sc
import wb1_15_b_selection as sel

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_15_a_scanner", "wb1_15_b_selection"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_luhn_and_patterns():
    assert sc.luhn_ok("4242 4242 4242 4242") and not sc.luhn_ok("4242 4242 4242 4243")
    kinds = [k for k, *_ in sc.scan("mail a.b@c.org, card 4242424242424242, call +44 20 7946 0123")]
    assert kinds == ["EMAIL", "CARD", "PHONE"]
    assert sc.scan("order 1234567812345678") == []          # 16 digits failing Luhn: not a card


def test_iban_check_digits_00_never_valid():
    # check digits = 98 - (n mod 97) lie in 2..98, so the demo account number cannot exist
    assert min(98 - m for m in range(97)) == 2


def test_least_squares_recovers_known_weights():
    rows = [{"skill": s, "break": b, "past": 3 + 2 * s - 5 * b} for s in range(10) for b in (0.0, 1.0)]
    w = sel.fit(rows, ["skill", "break"])
    assert all(abs(a - b) < 1e-9 for a, b in zip(w, [3, 2, -5]))
