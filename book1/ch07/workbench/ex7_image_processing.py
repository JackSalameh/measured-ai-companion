#!/usr/bin/env python3
"""Chapter 7 example: processing an image with small filters, and shrinking it safely.

Part (a) filters the 8 x 8 "7" of Figure 7.1 with two 3 x 3 filters:
    a blur (average of the 9 pixels under the window) and
    an edge detector (|left-right difference| + |up-down difference|, the filter of chapter 6 and its rotation).
Part (b) halves an image of fine stripes (period 2.5 pixels) by keeping every other column,
    first directly, then after a 5-tap smoothing filter [1 4 6 4 1]/16 along the rows.

Run: python ex7_image_processing.py
Pure Python, no packages needed. Windows only where the filter fits ("valid" positions): an
8 x 8 image gives a 6 x 6 result.
"""
import math

IMAGE = [
    [255, 255, 255, 255, 255, 255, 255, 255],
    [255, 40, 30, 30, 30, 30, 60, 255],
    [255, 255, 255, 255, 255, 50, 200, 255],
    [255, 255, 255, 255, 70, 180, 255, 255],
    [255, 255, 255, 90, 160, 255, 255, 255],
    [255, 255, 110, 140, 255, 255, 255, 255],
    [255, 255, 60, 255, 255, 255, 255, 255],
    [255, 255, 255, 255, 255, 255, 255, 255],
]

BLUR = [[1 / 9] * 3 for _ in range(3)]
EDGE_X = [[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]]   # brightness rising left to right (chapter 6)
EDGE_Y = [[-1, -1, -1], [0, 0, 0], [1, 1, 1]]   # brightness rising top to bottom

# part (b)
WIDTH, HEIGHT = 84, 20   # 84 columns: after smoothing, 80 remain, a whole number of cycles of both waves
FINE = 0.4      # cycles per pixel: period 2.5 pixels, below the Nyquist limit of 0.5
COARSE = 0.05   # cycles per pixel: period 20 pixels
SMOOTH = [1 / 16, 4 / 16, 6 / 16, 4 / 16, 1 / 16]


def filter2d(img, k):
    """Slide the 3 x 3 filter k over img (no flipping, as deep-learning libraries do); valid positions only."""
    n, m = len(img), len(img[0])
    return [[sum(k[a][b] * img[r + a][c + b] for a in range(3) for b in range(3))
             for c in range(m - 2)] for r in range(n - 2)]


def edges(img):
    gx, gy = filter2d(img, EDGE_X), filter2d(img, EDGE_Y)
    return [[abs(x) + abs(y) for x, y in zip(rx, ry)] for rx, ry in zip(gx, gy)]


def stripes():
    """Gray image whose brightness varies along each row: a slow wave plus fine stripes."""
    row = [128 + 50 * math.cos(2 * math.pi * COARSE * x) + 50 * math.cos(2 * math.pi * FINE * x)
           for x in range(WIDTH)]
    return [row[:] for _ in range(HEIGHT)]


def smooth_rows(img):
    """Apply the 5-tap smoothing filter along each row; valid positions only (4 columns are lost)."""
    return [[sum(w * row[c + i] for i, w in enumerate(SMOOTH)) for c in range(len(row) - 4)] for row in img]


def halve(img):
    """Keep every other column: the new image samples the scene half as often."""
    return [row[::2] for row in img]


def shrink(img):
    """Return one row of each half-size image: halved directly, and smoothed then halved.
    Both use the same 80 central columns (2 to 81), the positions where the smoothing filter fits."""
    naive = halve([row[2:WIDTH - 2] for row in img])[0]
    safe = halve(smooth_rows(img))[0]
    return naive, safe


def wave_amplitude(row, f):
    """Amplitude of the cosine of frequency f (cycles per pixel) in a row, by projecting on cos and sin."""
    n = len(row)
    mean = sum(row) / n
    c = sum((v - mean) * math.cos(2 * math.pi * f * i) for i, v in enumerate(row)) * 2 / n
    s = sum((v - mean) * math.sin(2 * math.pi * f * i) for i, v in enumerate(row)) * 2 / n
    return math.hypot(c, s)


def report():
    blur, edge = filter2d(IMAGE, BLUR), edges(IMAGE)
    print("(a) blur, 6 x 6 (rounded):")
    for row in blur:
        print("   ", " ".join(f"{v:4.0f}" for v in row))
    print("    edge strength, 6 x 6:")
    for row in edge:
        print("   ", " ".join(f"{v:4.0f}" for v in row))
    img = stripes()
    naive, safe = shrink(img)
    # after halving, frequencies are counted per NEW pixel: 0.4 -> 0.8, which folds to 0.2
    print("(b) fine stripes 0.4 cycles/pixel, amplitude", round(wave_amplitude(img[0][2:WIDTH - 2], FINE), 1))
    print("    halved directly: false stripes at 0.2 cycles/new pixel, amplitude",
          round(wave_amplitude(naive, 0.2), 1))
    print("    smoothed then halved: amplitude at 0.2 cycles/new pixel", round(wave_amplitude(safe, 0.2), 2),
          "; slow wave kept at", round(wave_amplitude(safe, 0.1), 1))


if __name__ == "__main__":
    report()
