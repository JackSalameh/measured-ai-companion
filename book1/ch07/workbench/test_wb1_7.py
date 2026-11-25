"""Tests for the chapter 7 Workbench apps."""
import math
import pathlib
import subprocess
import sys

import wb1_7_a_aliasing as al
import wb1_7_b_motor_spectrum as ms
from dft import dft_magnitude

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_dft_recovers_amplitude_on_a_bin():
    x = [0.7 * math.cos(2 * math.pi * 5 * t / 64) for t in range(64)]
    m = dft_magnitude(x)
    assert abs(m[5] - 0.7) < 1e-12 and max(m[k] for k in range(len(m)) if k != 5) < 1e-12


def test_aliasing_prediction_for_many_tones_and_rates():
    for f in (37, 120, 330, 499):
        for fs in (100, 150, 240, 1000):
            if 2 * f == fs:
                continue
            meas, _ = al.measure(f, fs)
            assert abs(meas - al.apparent(f, fs)) < 1e-9


def test_motor_peaks_on_the_planted_bins():
    mag = dft_magnitude(ms.signal())
    assert ms.peaks(mag) == [25, 50]
    assert abs(mag[25] - 1.0) < 0.05 and abs(mag[50] - 0.3) < 0.05


def test_expected_output():
    assert run("wb1_7_a_aliasing.py") == (HERE / "expected" / "wb1_7_a.txt").read_text(encoding="utf-8")
    assert run("wb1_7_b_motor_spectrum.py") == (HERE / "expected" / "wb1_7_b.txt").read_text(encoding="utf-8")


def test_image_example_matches_hand_and_theory():
    import ex7_image_processing as e
    blur = e.filter2d(e.IMAGE, e.BLUR)
    assert abs(blur[0][0] - (255 * 6 + 40 + 30 + 255) / 9) < 1e-9   # the window worked by hand
    edge = e.edges(e.IMAGE)
    assert len(edge) == 6 and len(edge[0]) == 6
    naive, safe = e.shrink(e.stripes())
    assert abs(e.wave_amplitude(naive, 0.2) - 50) < 1e-9           # fine stripes fold to false wide ones
    gain = math.cos(math.pi * 0.4) ** 4                             # response of [1 4 6 4 1]/16 at 0.4
    assert abs(e.wave_amplitude(safe, 0.2) - 50 * gain) < 1e-9
    assert abs(e.wave_amplitude(safe, 0.1) - 50 * math.cos(math.pi * 0.05) ** 4) < 1e-9
    assert run("ex7_image_processing.py") == (HERE / "expected" / "ex7_image_processing.txt").read_text()
