"""WB1.6-a  Tiny network from scratch.

A 2-2-1 network (two inputs, two hidden neurons, one output neuron, sigmoid activations)
learns XOR, which no single neuron can compute. Backpropagation is written out by hand,
checked against finite differences, then used for gradient descent on the cross-entropy loss.
Only the standard library is used. Run:  python wb1_6_a_tiny_network.py
"""
import math
import pathlib
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402

XOR = [((0, 0), 0), ((0, 1), 1), ((1, 0), 1), ((1, 1), 0)]
SEED = 6101
NAMES = ["w11", "w12", "w21", "w22", "b1", "b2", "v1", "v2", "c"]   # hidden weights w_ji, biases, output weights, bias


def sigmoid(z):
    return 1 / (1 + math.exp(-z))


def init(seed):
    g = Rng(seed)
    return [g.uniform(-1, 1) for _ in NAMES]


def forward(p, x):
    """Return hidden activations h1, h2 and output y for input x = (x1, x2)."""
    w11, w12, w21, w22, b1, b2, v1, v2, c = p
    h1 = sigmoid(w11 * x[0] + w12 * x[1] + b1)
    h2 = sigmoid(w21 * x[0] + w22 * x[1] + b2)
    y = sigmoid(v1 * h1 + v2 * h2 + c)
    return h1, h2, y


def loss(p):
    """Mean cross-entropy over the four XOR cases."""
    total = 0.0
    for x, t in XOR:
        y = forward(p, x)[2]
        total -= t * math.log(y) + (1 - t) * math.log(1 - y)
    return total / len(XOR)


def backprop(p):
    """Gradient of the mean cross-entropy by the chain rule, one case at a time."""
    w11, w12, w21, w22, b1, b2, v1, v2, c = p
    g = [0.0] * len(p)
    for x, t in XOR:
        h1, h2, y = forward(p, x)
        d_out = y - t                         # dL/dz_out for sigmoid + cross-entropy
        d1 = d_out * v1 * h1 * (1 - h1)       # dL/dz_1: back through v1 and the sigmoid's slope
        d2 = d_out * v2 * h2 * (1 - h2)
        grads = [d1 * x[0], d1 * x[1], d2 * x[0], d2 * x[1], d1, d2, d_out * h1, d_out * h2, d_out]
        g = [a + b for a, b in zip(g, grads)]
    return [v / len(XOR) for v in g]


def numerical(p, h=1e-6):
    out = []
    for i in range(len(p)):
        up, dn = p[:], p[:]
        up[i] += h
        dn[i] -= h
        out.append((loss(up) - loss(dn)) / (2 * h))
    return out


def train(p, lr=1.0, epochs=5000):
    history = []
    for e in range(epochs + 1):
        if e % 1000 == 0:
            history.append((e, loss(p)))
        if e < epochs:
            p = [a - lr * b for a, b in zip(p, backprop(p))]
    return p, history


def main():
    p0 = init(SEED)
    print("WB1.6-a  Tiny network from scratch: a 2-2-1 network learns XOR")
    a, n = backprop(p0), numerical(p0)
    worst = max(abs(x - y) for x, y in zip(a, n))
    print(f"Gradient check at the starting weights (seed {SEED}): largest difference {worst:.1e}")
    for name, x, y in zip(NAMES, a, n):
        print(f"  {name:<4} backprop {x:+.6f}   finite difference {y:+.6f}")
    p, hist = train(p0)
    print("Training: gradient descent, learning rate 1.0")
    for e, l in hist:
        print(f"  epoch {e:5d}   loss {l:.4f}")
    print("Result")
    for x, t in XOR:
        y = forward(p, x)[2]
        print(f"  input {x}   target {t}   output {y:.3f}   -> {int(y > 0.5)}")
    ok = all(int(forward(p, x)[2] > 0.5) == t for x, t in XOR)
    solved = sum(all(int(forward(train(init(s))[0], x)[2] > 0.5) == t for x, t in XOR) for s in range(SEED, SEED + 20))
    print(f"Same training from 20 different random starts (seeds {SEED} to {SEED + 19}): {solved} of 20 solve XOR")
    return ok and worst < 1e-6


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
