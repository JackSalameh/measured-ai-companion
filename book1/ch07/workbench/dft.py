"""A plain discrete Fourier transform, written out so it can be read. Standard library only."""
import cmath
import math


def dft_magnitude(x):
    """Single-sided amplitude spectrum: for bins 0 .. N/2, the amplitude of the cosine at that bin.
    Bin k is the frequency k * fs / N. A sinusoid of amplitude A exactly on a bin (not 0 or N/2) gives A."""
    n = len(x)
    out = []
    for k in range(n // 2 + 1):
        s = sum(x[t] * cmath.exp(-2j * math.pi * k * t / n) for t in range(n))
        a = abs(s) / n
        out.append(a if k in (0, n // 2) else 2 * a)
    return out
