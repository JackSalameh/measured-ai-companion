"""Tests for the chapter 13 Workbench apps."""
import pathlib
import shutil
import subprocess
import sys

import pytest

import spec_parse_amount as spec
import wb1_13_b_test_first as tf
import wb1_13_c_edit_test_loop as el

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


@pytest.mark.skipif(shutil.which("git") is None, reason="Git not installed")
def test_git_sandbox_is_reproducible():
    assert run("wb1_13_a_git_sandbox.py") == (HERE / "expected" / "wb1_13_a_git_sandbox.txt").read_text(encoding="utf-8")


def test_outputs_match_expected():
    for f in ("wb1_13_b_test_first", "wb1_13_c_edit_test_loop"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text(encoding="utf-8")


def test_spec_has_eight_tests_and_b_passes_all():
    assert len(spec.TESTS) == 8
    assert all(ok for _, ok, _ in tf.run(tf.candidate_b))
    assert [n for n, ok, _ in tf.run(tf.candidate_a) if not ok] == ["test_brackets_negative", "test_currency_code"]


def test_loop_stops_when_tests_pass_and_respects_budget():
    assert el.loop(el.ReplaySteps(), 5, lambda c: "no") == 3
    assert el.loop(el.ReplaySteps(), 2, lambda c: "no") is None


def test_unlisted_command_is_never_auto_allowed():
    assert "pip install price-parser" not in el.ALLOWED
