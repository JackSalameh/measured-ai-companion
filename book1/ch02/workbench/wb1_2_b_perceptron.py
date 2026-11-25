"""WB1.2-b  A perceptron in under 40 lines

The perceptron error-correction rule (the form analyzed by Novikoff, 1962) on two inputs: output 1 if w1*x1 + w2*x2 + b > 0, else 0.
After each wrong answer: w <- w + rate * (target - output) * x, and b likewise.
It learns AND and OR, then fails on XOR, and prints why no weights can exist for XOR.
Run:  python wb1_2_b_perceptron.py
"""
INPUTS = [(0, 0), (0, 1), (1, 0), (1, 1)]
TASKS = {"AND": [0, 0, 0, 1], "OR": [0, 1, 1, 1], "XOR": [0, 1, 1, 0]}


def output(w, b, x):
    return 1 if w[0] * x[0] + w[1] * x[1] + b > 0 else 0


def train(targets, rate=1.0, max_epochs=100):
    w, b = [0.0, 0.0], 0.0
    for epoch in range(1, max_epochs + 1):
        errors = 0
        for x, t in zip(INPUTS, targets):
            e = t - output(w, b, x)
            if e:
                errors += 1
                w = [w[0] + rate * e * x[0], w[1] + rate * e * x[1]]
                b += rate * e
        if errors == 0:
            return w, b, epoch, True
    return w, b, max_epochs, False


def main():
    print("WB1.2-b  A perceptron in under 40 lines")
    for name, targets in TASKS.items():
        w, b, epochs, ok = train(targets)
        correct = sum(output(w, b, x) == t for x, t in zip(INPUTS, targets))
        state = f"learned in {epochs} passes" if ok else f"not learned after {epochs} passes"
        print(f"{name:<4} {state:<28} w = ({w[0]:g}, {w[1]:g}), b = {b:g}, correct {correct}/4")
    print("\nWhy XOR fails: the weights would have to satisfy all four conditions")
    print("  (0,0) -> 0 :  b <= 0")
    print("  (0,1) -> 1 :  w2 + b > 0")
    print("  (1,0) -> 1 :  w1 + b > 0")
    print("  (1,1) -> 0 :  w1 + w2 + b <= 0")
    print("Adding the middle two gives w1 + w2 + 2b > 0, so w1 + w2 + b > -b >= 0,")
    print("which contradicts the last line. No straight line separates the 1s from the 0s.")


if __name__ == "__main__":
    main()
