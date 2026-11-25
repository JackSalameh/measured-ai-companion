"""WB1.4-b  Averages lie.

Part 1: Anscombe's quartet (Anscombe 1973). Four small datasets with the same summary
        numbers and very different shapes. The program prints the numbers; the book's
        figure shows the shapes.
Part 2: the series ledger. Mean and median of the transaction amounts, then the same
        after one typing error (a decimal point slipped two places).

Run:  python wb1_4_b_averages.py
"""
import csv
import pathlib
import statistics as st

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"

# Anscombe, F. J. (1973). Graphs in statistical analysis. The American Statistician 27(1), 17-21.
X123 = [10, 8, 13, 9, 11, 14, 6, 4, 12, 7, 5]
QUARTET = {
    "I":   (X123, [8.04, 6.95, 7.58, 8.81, 8.33, 9.96, 7.24, 4.26, 10.84, 4.82, 5.68]),
    "II":  (X123, [9.14, 8.14, 8.74, 8.77, 9.26, 8.10, 6.13, 3.10, 9.13, 7.26, 4.74]),
    "III": (X123, [7.46, 6.77, 12.74, 7.11, 7.81, 8.84, 6.08, 5.39, 8.15, 6.42, 5.73]),
    "IV":  ([8, 8, 8, 8, 8, 8, 8, 19, 8, 8, 8], [6.58, 5.76, 7.71, 8.84, 8.47, 7.04, 5.25, 12.50, 5.56, 7.91, 6.89]),
}


def summary(x, y):
    """Means, sample variances, correlation and least-squares line y = a + b x."""
    mx, my = st.mean(x), st.mean(y)
    sxy = sum((u - mx) * (v - my) for u, v in zip(x, y))
    sxx = sum((u - mx) ** 2 for u in x)
    syy = sum((v - my) ** 2 for v in y)
    b = sxy / sxx
    return {"mx": mx, "my": my, "vx": sxx / (len(x) - 1), "vy": syy / (len(y) - 1),
            "r": sxy / (sxx * syy) ** 0.5, "a": my - b * mx, "b": b}


def ledger_amounts():
    with open(DATA / "out" / "ledger.csv", encoding="utf-8") as f:
        return [float(r["debit"]) for r in csv.DictReader(f) if float(r["debit"]) > 0]


def main():
    print("WB1.4-b  Averages lie")
    print("Part 1: Anscombe's quartet, 11 points each")
    print("  set   mean x  var x  mean y  var y     r     line")
    for name, (x, y) in QUARTET.items():
        s = summary(x, y)
        print(f"  {name:<4} {s['mx']:6.2f} {s['vx']:6.2f} {s['my']:7.2f} {s['vy']:6.2f} {s['r']:6.3f}   "
              f"y = {s['a']:.2f} + {s['b']:.3f} x")
    d = ledger_amounts()
    print(f"Part 2: ledger transaction amounts (EUR), {len(d)} transactions")
    print(f"  as recorded       : mean {st.mean(d):10,.2f}   median {st.median(d):10,.2f}")
    k = max(range(len(d)), key=lambda i: d[i] if d[i] < 3000 else -1)   # one ordinary amount below 3,000
    bad = d[:]
    bad[k] = d[k] * 100                                                  # decimal point slipped two places
    print(f"  one typing error  : mean {st.mean(bad):10,.2f}   median {st.median(bad):10,.2f}"
          f"   ({d[k]:,.2f} entered as {bad[k]:,.2f})")


if __name__ == "__main__":
    main()
