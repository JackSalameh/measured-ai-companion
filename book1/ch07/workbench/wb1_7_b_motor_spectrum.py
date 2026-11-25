"""WB1.7-b  Spectrum of a motor.

A synthetic motor vibration with a known shaft frequency and one harmonic, plus noise:
    x(t) = 1.0 sin(2 pi 25 t) + 0.3 sin(2 pi 50 t + 1.0) + noise (SD 0.2)
sampled at 1,000 Hz for 1 s. The spectrum should show peaks at 25 Hz and 50 Hz with amplitudes
close to 1.0 and 0.3. Both frequencies fall exactly on frequency bins (resolution fs / N = 1 Hz).
A second run moves the shaft to 25.5 Hz, between two bins, to show spectral leakage.
Run:  python wb1_7_b_motor_spectrum.py      (--export writes motor_signal.csv for the MATLAB check)
"""
import math
import pathlib
import statistics
import sys

from dft import dft_magnitude

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"))
from rng import Rng  # noqa: E402

FS, N, SEED = 1000, 1000, 7201
PLANTED = ((25.0, 1.0, 0.0), (50.0, 0.3, 1.0))         # frequency (Hz), amplitude, phase
NOISE = 0.2


def signal(shaft=25.0, seed=SEED):
    g = Rng(seed)
    comps = ((shaft, 1.0, 0.0), (2 * shaft, 0.3, 1.0))
    return [sum(a * math.sin(2 * math.pi * f * t / FS + ph) for f, a, ph in comps) + NOISE * g.normal() for t in range(N)]


def peaks(mag, k=2):
    """Indices of the k largest local maxima (bins 1 .. N/2 - 1)."""
    loc = [i for i in range(1, len(mag) - 1) if mag[i] >= mag[i - 1] and mag[i] >= mag[i + 1]]
    return sorted(sorted(loc, key=lambda i: -mag[i])[:k])


def main(argv=()):
    x = signal()
    mag = dft_magnitude(x)
    res = FS / N
    print("WB1.7-b  Spectrum of a motor")
    print(f"  fs = {FS} Hz, N = {N} samples, frequency resolution fs/N = {res:g} Hz, noise SD {NOISE}")
    ok = True
    for (f, a, _), k in zip(PLANTED, peaks(mag)):
        print(f"  planted {f:5.1f} Hz amplitude {a:.2f}  ->  peak at bin {k} = {k * res:5.1f} Hz, amplitude {mag[k]:.3f}")
        ok = ok and abs(k * res - f) <= res
    pk = peaks(mag)
    floor = statistics.median(m for i, m in enumerate(mag) if 0 < i < len(mag) - 1 and i not in pk)
    print(f"  median amplitude of all other bins (noise floor): {floor:.4f}")
    print(f"  peaks within one bin of the planted frequencies: {'yes' if ok else 'NO'}")
    m2 = dft_magnitude(signal(shaft=25.5))
    print("Leakage: shaft at 25.5 Hz, between bins 25 and 26")
    for k in (23, 24, 25, 26, 27, 28):
        print(f"  bin {k:2d} ({k * res:4.0f} Hz): amplitude {m2[k]:.3f}")
    if "--export" in argv:
        with open(HERE / "motor_signal.csv", "w") as f:
            f.write("\n".join(repr(v) for v in x) + "\n")
        print("wrote motor_signal.csv")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
