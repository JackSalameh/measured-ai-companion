"""WB1.7-a  Aliasing lab.

A 120 Hz tone is sampled at several rates for one second. For each rate the program predicts the
frequency the samples appear to have, then measures it as the largest peak of the spectrum.
Prediction: fold the true frequency into the range 0 .. fs/2,
    f_apparent = | f - fs * round(f / fs) |
Run:  python wb1_7_a_aliasing.py            (or: python wb1_7_a_aliasing.py --tone 330)
"""
import argparse
import math
import sys

from dft import dft_magnitude

RATES = (1000, 300, 240, 200, 150, 100)


def apparent(f, fs):
    return abs(f - fs * round(f / fs))


def measure(f, fs, seconds=1):
    n = int(fs * seconds)
    x = [math.sin(2 * math.pi * f * t / fs + 0.3) for t in range(n)]     # small phase so samples are not all zero
    mag = dft_magnitude(x)
    k = max(range(len(mag)), key=lambda i: mag[i])
    return k * fs / n, mag[k]


def main(argv=()):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tone", type=float, default=120.0)
    a = ap.parse_args(argv)
    print(f"WB1.7-a  Aliasing lab: a {a.tone:g} Hz tone sampled for 1 s")
    print("  sampling rate   Nyquist frequency   predicted   measured peak   amplitude")
    ok = True
    for fs in RATES:
        pred = apparent(a.tone, fs)
        meas, amp = measure(a.tone, fs)
        flag = "" if fs > 2 * a.tone else ("   <- aliased" if pred != a.tone else "   <- exactly 2x the tone: amplitude depends on phase")
        print(f"  {fs:8d} Hz      {fs / 2:9.1f} Hz      {pred:6.1f} Hz     {meas:6.1f} Hz      {amp:6.3f}{flag}")
        ok = ok and abs(pred - meas) < 1e-9
    print(f"  predictions match measurements: {'yes' if ok else 'NO'}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
