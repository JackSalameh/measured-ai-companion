"""WB1.5-a  Gradient-descent explorer.

Fits a straight line through five points by gradient descent and checks every
result against the exact (analytic) answer.
  Part 1: one parameter, y = w x. Three learning rates: too small, good, too large.
  Part 2: the gradient formula checked against a numerical slope.
  Part 3: two parameters, y = w x + b, compared with the exact least-squares line.
Only the standard library is used. Run:  python wb1_5_a_gradient.py
"""
import sys

X = [1.0, 2.0, 3.0, 4.0, 5.0]
Y = [2.1, 3.9, 6.2, 7.8, 10.1]
N = len(X)


def loss1(w):
    """Mean squared error of y = w x."""
    return sum((w * x - y) ** 2 for x, y in zip(X, Y)) / N


def grad1(w):
    """dL/dw = (2/N) sum x (w x - y)."""
    return 2 * sum(x * (w * x - y) for x, y in zip(X, Y)) / N


def exact1():
    return sum(x * y for x, y in zip(X, Y)) / sum(x * x for x in X)


def descend1(lr, steps, w=0.0):
    path = [w]
    for _ in range(steps):
        w = w - lr * grad1(w)
        path.append(w)
    return path


def loss2(w, b):
    return sum((w * x + b - y) ** 2 for x, y in zip(X, Y)) / N


def grad2(w, b):
    r = [w * x + b - y for x, y in zip(X, Y)]
    return 2 * sum(x * e for x, e in zip(X, r)) / N, 2 * sum(r) / N


def exact2():
    mx, my = sum(X) / N, sum(Y) / N
    w = sum((x - mx) * (y - my) for x, y in zip(X, Y)) / sum((x - mx) ** 2 for x in X)
    return w, my - w * mx


def descend2(lr, steps, w=0.0, b=0.0):
    for _ in range(steps):
        gw, gb = grad2(w, b)
        w, b = w - lr * gw, b - lr * gb
    return w, b


def main():
    print("WB1.5-a  Gradient-descent explorer")
    ws = exact1()
    print(f"Part 1: y = w x, exact minimum w* = {ws:.4f}, loss {loss1(ws):.4f}")
    limit = 2 / (2 * sum(x * x for x in X) / N)
    print(f"  learning rates above {limit:.4f} make the steps grow instead of shrink")
    for lr in (0.005, 0.04, 0.095):
        p = descend1(lr, 20)
        print(f"  rate {lr:<6} after  1 step w = {p[1]:9.4f}   after 20 steps w = {p[20]:12.4f}   loss {loss1(p[20]):14.4f}")
    print("Part 2: gradient formula against a numerical slope (h = 0.0001)")
    for w in (0.0, 1.0, 2.0):
        h = 1e-4
        num = (loss1(w + h) - loss1(w - h)) / (2 * h)
        print(f"  w = {w:.1f}: formula {grad1(w):10.4f}   numerical {num:10.4f}")
    we, be = exact2()
    wg, bg = descend2(0.04, 2000)
    print("Part 3: y = w x + b, rate 0.04, 2,000 steps from (0, 0)")
    print(f"  gradient descent: w = {wg:.4f}  b = {bg:.4f}  loss {loss2(wg, bg):.4f}")
    print(f"  exact          : w = {we:.4f}  b = {be:.4f}  loss {loss2(we, be):.4f}")
    ok = abs(wg - we) < 1e-4 and abs(bg - be) < 1e-4
    print(f"  agree to 4 decimals: {'yes' if ok else 'NO'}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
