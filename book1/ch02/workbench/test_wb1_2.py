"""Tests for the chapter 2 Workbench apps (run with pytest)."""
import hashlib
import pathlib
import subprocess
import sys

import wb1_2_a_timeline as ta
import wb1_2_b_perceptron as tp

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_every_row_has_a_source_and_order():
    rows = ta.load(HERE / "milestones.csv")
    assert all(r["ledger"].startswith("L-") for r in rows)
    assert [int(r["year"]) for r in rows] == sorted(int(r["year"]) for r in rows)


def test_missing_source_is_refused(tmp_path):
    p = tmp_path / "m.csv"
    p.write_text("date,year,milestone,idea,ledger\n1950,1950,x,y,\n", encoding="utf-8")
    try:
        ta.load(p)
    except SystemExit as e:
        assert "without a source" in str(e)
    else:
        raise AssertionError("a row without a source ID was accepted")


def test_and_or_learned_xor_not():
    for name, ok in (("AND", True), ("OR", True), ("XOR", False)):
        w, b, _, learned = tp.train(tp.TASKS[name])
        assert learned is ok
        if ok:
            assert all(tp.output(w, b, x) == t for x, t in zip(tp.INPUTS, tp.TASKS[name]))


def test_xor_has_no_solution_on_a_grid():
    # brute force over a grid of weights: no line computes XOR
    vals = [i / 2 for i in range(-8, 9)]
    for w1 in vals:
        for w2 in vals:
            for b in vals:
                assert [tp.output((w1, w2), b, x) for x in tp.INPUTS] != tp.TASKS["XOR"]


def test_outputs_match_expected():
    for script, name in (("wb1_2_a_timeline.py", "wb1_2_a.txt"), ("wb1_2_b_perceptron.py", "wb1_2_b.txt")):
        assert run(script) == (HERE / "expected" / name).read_text()
