"""Tests for the chapter 6 Workbench apps."""
import pathlib
import subprocess
import sys

import wb1_6_a_tiny_network as tn
import wb1_6_b_detector_duel as dd

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_backprop_matches_finite_differences_at_several_points():
    for seed in (1, 2, 3, 6101):
        p = tn.init(seed)
        assert max(abs(a - b) for a, b in zip(tn.backprop(p), tn.numerical(p))) < 1e-8


def test_single_neuron_cannot_fit_xor_but_network_can():
    # a single sigmoid neuron trained the same way stays near 0.5 on at least one case
    import math
    w = [0.0, 0.0, 0.0]
    for _ in range(5000):
        g = [0.0, 0.0, 0.0]
        for x, t in tn.XOR:
            d = tn.sigmoid(w[0] * x[0] + w[1] * x[1] + w[2]) - t
            g = [g[0] + d * x[0], g[1] + d * x[1], g[2] + d]
        w = [a - 1.0 * b / 4 for a, b in zip(w, g)]
    wrong = sum(int(tn.sigmoid(w[0] * x[0] + w[1] * x[1] + w[2]) > 0.5) != t for x, t in tn.XOR)
    assert wrong >= 1
    p, _ = tn.train(tn.init(tn.SEED))
    assert all(int(tn.forward(p, x)[2] > 0.5) == t for x, t in tn.XOR)


def test_duel_splits_are_balanced():
    train, val, test = dd.dataset()
    assert [len(train), len(val), len(test)] == list(dd.SPLIT)
    for part in (train, val, test):
        assert sum(r[1] for r in part) * 2 == len(part)


def test_expected_output():
    assert run("wb1_6_a_tiny_network.py") == (HERE / "expected" / "wb1_6_a.txt").read_text(encoding="utf-8")
    assert run("wb1_6_b_detector_duel.py") == (HERE / "expected" / "wb1_6_b.txt").read_text(encoding="utf-8")
