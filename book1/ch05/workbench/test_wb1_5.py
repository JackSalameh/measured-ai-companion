"""Tests for the chapter 5 Workbench apps and the P1 milestone program."""
import pathlib
import subprocess
import sys

import p1_first_classifier as p1
import wb1_5_a_gradient as gd
import wb1_5_b_overfit as of

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_gradient_matches_numerical_and_exact():
    for w in (-1.0, 0.5, 3.0):
        h = 1e-5
        assert abs(gd.grad1(w) - (gd.loss1(w + h) - gd.loss1(w - h)) / (2 * h)) < 1e-6
    assert abs(gd.descend1(0.04, 200)[-1] - gd.exact1()) < 1e-9
    w, b = gd.descend2(0.04, 2000)
    we, be = gd.exact2()
    assert abs(w - we) < 1e-4 and abs(b - be) < 1e-4
    assert abs(gd.descend1(0.095, 100)[-1]) > 1000         # above the limit it diverges


def test_least_squares_recovers_a_known_polynomial():
    pts = [(x / 10, 1 - 2 * (2 * x / 10 - 1) + 0.5 * (2 * x / 10 - 1) ** 3) for x in range(11)]
    c = of.fit(pts, 3)
    for got, want in zip(c, (1, -2, 0, 0.5)):
        assert abs(got - want) < 1e-9


def test_training_error_never_rises_with_degree():
    rows = of.curves()
    assert all(rows[i + 1][1] <= rows[i][1] + 1e-12 for i in range(len(rows) - 1))


def test_p1_split_is_clean_and_test_used_once():
    train, val, test, val_acc, best_k, _, _ = p1.run()
    texts = lambda rs: {r["text"] for r in rs}
    assert not (texts(train) & texts(val)) and not (texts(train) & texts(test)) and not (texts(val) & texts(test))
    assert len(train) + len(val) + len(test) == 618 and best_k in p1.KS


def test_expected_output():
    for script, name in (("wb1_5_a_gradient.py", "wb1_5_a"), ("wb1_5_b_overfit.py", "wb1_5_b"), ("p1_first_classifier.py", "p1")):
        assert run(script) == (HERE / "expected" / f"{name}.txt").read_text(encoding="utf-8")
