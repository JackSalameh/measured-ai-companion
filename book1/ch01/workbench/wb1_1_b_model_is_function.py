"""WB1.1-b  A model is a function

A model here is the function f(x) = a*x + b with two parameters (a, b).
Training = choosing (a, b) from data. Inference = using the fixed (a, b).

Two ways to train, which must agree:
  1. closed form (the least-squares formulas),
  2. gradient descent (many small parameter updates, the idea behind the training of deep networks).
Only the standard library is used. Run:  python wb1_1_b_model_is_function.py
Options (try one at a time):  --noise 0   --points 5   --x 100
"""
import math
import random

TRUE_A, TRUE_B, NOISE_SD, SEED = 2.5, 1.0, 0.8, 2026
XS = [0.5 * i for i in range(20)]  # 0.0, 0.5, ..., 9.5


def noisy_data(sd=NOISE_SD):
    rng = random.Random(SEED)  # random() is stable across Python versions

    def normal():  # Box-Muller, built from random() only
        u1, u2 = 1.0 - rng.random(), rng.random()
        return math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)

    return [TRUE_A * x + TRUE_B + sd * normal() for x in XS]


def model(x, a, b):
    return a * x + b


def mse(xs, ys, a, b):
    return sum((model(x, a, b) - y) ** 2 for x, y in zip(xs, ys)) / len(xs)


def fit_closed_form(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    a = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)
    return a, my - a * mx


def fit_gradient_descent(xs, ys, lr=0.01, steps=20000):
    a = b = 0.0
    n = len(xs)
    for _ in range(steps):
        ga = 2.0 / n * sum((model(x, a, b) - y) * x for x, y in zip(xs, ys))
        gb = 2.0 / n * sum((model(x, a, b) - y) for x, y in zip(xs, ys))
        a, b = a - lr * ga, b - lr * gb
    return a, b


def main(argv=()):
    import argparse
    ap = argparse.ArgumentParser(description="WB1.1-b  A model is a function")
    ap.add_argument("--noise", type=float, default=NOISE_SD, help="noise standard deviation (default 0.8)")
    ap.add_argument("--points", type=int, default=len(XS), help="use only the first N points (default 20)")
    ap.add_argument("--x", type=float, default=12.0, help="second input for inference (default 12)")
    o = ap.parse_args(argv)
    xs = XS[:o.points]
    ys = noisy_data(o.noise)[:o.points]
    a1, b1 = fit_closed_form(xs, ys)
    a2, b2 = fit_gradient_descent(xs, ys)
    print("WB1.1-b  A model is a function")
    print(f"data: {len(xs)} points, seed {SEED}, true a={TRUE_A}, b={TRUE_B}, noise sd={o.noise}")
    print(f"before training (a=0, b=0): MSE = {mse(xs, ys, 0.0, 0.0):.4f}")
    print(f"closed form      : a = {a1:.4f}, b = {b1:.4f}, MSE = {mse(xs, ys, a1, b1):.4f}")
    print(f"gradient descent : a = {a2:.4f}, b = {b2:.4f}, MSE = {mse(xs, ys, a2, b2):.4f}")
    print(f"the two methods agree to 1e-9: {max(abs(a1 - a2), abs(b1 - b2)) < 1e-9}")
    print("inference with the fixed parameters:")
    for x in (3.0, o.x):
        note = "inside the training range" if x <= max(xs) else "outside the training range (extrapolation)"
        print(f"  f({x:>4}) = {model(x, a1, b1):.4f}   [{note}]")


if __name__ == "__main__":
    import sys
    main(sys.argv[1:])
