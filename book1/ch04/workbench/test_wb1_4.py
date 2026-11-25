"""Tests for the chapter 4 Workbench apps."""
import pathlib
import subprocess
import sys

import wb1_4_a_baserate as br
import wb1_4_b_averages as av

HERE = pathlib.Path(__file__).parent


def run(script, *args):
    return subprocess.run([sys.executable, str(HERE / script), *args], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_three_methods_agree_on_defaults_and_extremes():
    for base, sens, fpr in ((0.02, 0.90, 0.05), (0.01, 0.80, 0.096), (0.5, 0.7, 0.3), (0.001, 0.99, 0.01)):
        exact = br.bayes(base, sens, fpr)
        t = br.table(base, sens, fpr, n=1_000_000)
        assert abs(t["tp"] / (t["tp"] + t["fp"]) - exact) < 1e-3
        mc, se, _ = br.monte_carlo(base, sens, fpr)
        assert abs(mc - exact) <= 3 * se


def test_bayes_by_hand():
    # 2% base rate, 90% sensitivity, 5% false alarms: 180 / (180 + 490)
    assert abs(br.bayes(0.02, 0.90, 0.05) - 180 / 670) < 1e-12


def test_quartet_summaries_match_anscombe():
    for x, y in av.QUARTET.values():
        s = av.summary(x, y)
        assert s["mx"] == 9 and abs(s["vx"] - 11) < 1e-12
        assert abs(s["my"] - 7.50) < 0.005 and abs(s["vy"] - 4.125) < 0.004
        assert abs(s["r"] - 0.816) < 0.0015 and abs(s["a"] - 3.00) < 0.005 and abs(s["b"] - 0.500) < 0.0005


def test_expected_output():
    assert run("wb1_4_a_baserate.py") == (HERE / "expected" / "wb1_4_a.txt").read_text(encoding="utf-8")
    assert run("wb1_4_b_averages.py") == (HERE / "expected" / "wb1_4_b.txt").read_text(encoding="utf-8")
