"""Tests for the chapter 3 Workbench apps."""
import pathlib
import subprocess
import sys

import wb1_3_b_leakage as lk

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_inspector_finds_planted_defects():
    out = run("wb1_3_a_inspector.py")
    assert "IMPOSSIBLE: 2026-02-30" in out
    assert "WARNING mixed units in one column: g, m/s^2" in out
    assert "description    category  missing   6" in out


def test_group_split_has_no_shared_text():
    import csv
    rows = list(csv.DictReader(open(lk.DATA / "out" / "tickets.csv", encoding="utf-8")))
    texts = sorted(set(r["text"] for r in rows))
    assert len(texts) < len(rows)   # duplicates exist, so the trap is real


def test_random_split_is_optimistic():
    (h1, n1), (h2, n2), overlap, _ = lk.part1()
    assert overlap > 0 and h1 / n1 > h2 / n2
    m_rnd, m_time, _, _ = lk.part2()
    assert m_time > m_rnd


def test_outputs_match_expected():
    for script, name in (("wb1_3_a_inspector.py", "wb1_3_a.txt"), ("wb1_3_b_leakage.py", "wb1_3_b.txt")):
        assert run(script) == (HERE / "expected" / name).read_text()


def test_save_split_matches_part1(tmp_path):
    import csv
    lk.save_split(tmp_path)
    train = list(csv.DictReader(open(tmp_path / "train.csv", encoding="utf-8")))
    test = list(csv.DictReader(open(tmp_path / "test.csv", encoding="utf-8")))
    (_, _), (_, n2), _, _ = lk.part1()
    assert len(test) == n2 and len(train) + len(test) == 618
    assert not set(r["text"] for r in train) & set(r["text"] for r in test)
