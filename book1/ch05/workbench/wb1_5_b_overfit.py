"""WB1.5-b  Overfit a polynomial.

Twenty-four noisy points from a smooth curve, y = sin(2 pi x) + noise, x between 0 and 1.
Twelve train the model; twelve others validate it. Polynomials of degree 0 to 9 are fitted
by least squares to the training points only. The training error keeps falling as the
degree rises; the validation error falls, then rises again: overfitting.
Only the standard library is used (least squares by QR decomposition).
Run:  python wb1_5_b_overfit.py
"""
import math
import pathlib
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402

SEED = 5207
NOISE = 0.25


def make_points(n=24, seed=SEED):
    g = Rng(seed)
    pts = []
    for _ in range(n):
        x = g.uniform(0.0, 1.0)
        pts.append((x, math.sin(2 * math.pi * x) + g.normal(0.0, NOISE)))
    return pts[: n // 2], pts[n // 2:]


def lstsq(A, b):
    """Least squares by modified Gram-Schmidt QR: minimize |A c - b|."""
    m, n = len(A), len(A[0])
    Q = [[A[i][j] for i in range(m)] for j in range(n)]          # columns
    R = [[0.0] * n for _ in range(n)]
    for j in range(n):
        for k in range(j):
            R[k][j] = sum(Q[k][i] * Q[j][i] for i in range(m))
            Q[j] = [Q[j][i] - R[k][j] * Q[k][i] for i in range(m)]
        R[j][j] = math.sqrt(sum(v * v for v in Q[j]))
        Q[j] = [v / R[j][j] for v in Q[j]]
    qtb = [sum(Q[j][i] * b[i] for i in range(m)) for j in range(n)]
    c = [0.0] * n
    for j in reversed(range(n)):
        c[j] = (qtb[j] - sum(R[j][k] * c[k] for k in range(j + 1, n))) / R[j][j]
    return c


def z(x):
    return 2 * x - 1                                    # map [0, 1] to [-1, 1] for stable numbers


def fit(points, degree):
    A = [[z(x) ** p for p in range(degree + 1)] for x, _ in points]
    return lstsq(A, [y for _, y in points])


def predict(c, x):
    return sum(ci * z(x) ** p for p, ci in enumerate(c))


def mse(c, points):
    return sum((predict(c, x) - y) ** 2 for x, y in points) / len(points)


def curves(max_degree=9):
    train, val = make_points()
    rows = []
    for d in range(max_degree + 1):
        c = fit(train, d)
        rows.append((d, mse(c, train), mse(c, val)))
    return rows


def main():
    rows = curves()
    print("WB1.5-b  Overfit a polynomial")
    print(f"12 training and 12 validation points, y = sin(2 pi x) + noise (SD {NOISE})")
    print("  degree   training MSE   validation MSE")
    best = min(rows, key=lambda r: r[2])
    for d, tr, va in rows:
        mark = "   <- lowest validation error" if d == best[0] else ""
        print(f"  {d:6d}   {tr:12.4f}   {va:14.4f}{mark}")
    print(f"Noise variance alone: {NOISE ** 2:.4f} (no model can do better on average)")


if __name__ == "__main__":
    main()
