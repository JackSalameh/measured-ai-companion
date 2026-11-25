#!/usr/bin/env python3
"""WB1.15-b  Selection-rate check, and how a proxy feature carries bias.

Synthetic hiring data, seed 1501: 400 applicants in two groups, A and B, with the same
distribution of skill.  A career break is more common in group B (40% against 10%).
Past hiring decisions, the "labels", penalized career breaks.  A model is fitted to those
past decisions by least squares from two features, skill and career break; the group is
NOT a feature.  The top 30% by model score are selected.  The app reports selection rates
by group and their ratio, then refits without the career-break feature.

All data are invented for teaching; they describe no real employer or applicant.
Run:  python wb1_15_b_selection.py
"""
import pathlib
import sys

sys.path.insert(0, str(next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"))
from rng import Rng  # noqa: E402

SEED, N, SELECT = 1501, 400, 0.30


def make():
    g = Rng(SEED)
    rows = []
    for _ in range(N):
        group = "B" if g.uniform() < 0.5 else "A"
        skill = g.normal(50, 10)
        brk = 1.0 if g.uniform() < (0.40 if group == "B" else 0.10) else 0.0
        past = skill - 12.0 * brk + g.normal(0, 5)          # past decisions penalized breaks
        rows.append({"group": group, "skill": skill, "break": brk, "past": past})
    return rows


def fit(rows, feats):
    """Least squares with an intercept, solved by the normal equations (Gaussian elimination)."""
    X = [[1.0] + [r[f] for f in feats] for r in rows]
    y = [r["past"] for r in rows]
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) for j in range(k)] + [sum(x[i] * t for x, t in zip(X, y))] for i in range(k)]
    for c in range(k):
        p = max(range(c, k), key=lambda r: abs(A[r][c]))
        A[c], A[p] = A[p], A[c]
        for r in range(k):
            if r != c:
                f = A[r][c] / A[c][c]
                A[r] = [a - f * b for a, b in zip(A[r], A[c])]
    return [A[i][k] / A[i][i] for i in range(k)]


def select(rows, feats, w):
    scores = [w[0] + sum(wi * r[f] for wi, f in zip(w[1:], feats)) for r in rows]
    cut = sorted(scores, reverse=True)[int(SELECT * len(rows)) - 1]
    return [s >= cut for s in scores]


def rates(rows, chosen):
    out = {}
    for grp in ("A", "B"):
        idx = [i for i, r in enumerate(rows) if r["group"] == grp]
        out[grp] = (sum(chosen[i] for i in idx), len(idx))
    return out


def report(label, rows, feats):
    w = fit(rows, feats)
    r = rates(rows, select(rows, feats, w))
    ra, rb = r["A"][0] / r["A"][1], r["B"][0] / r["B"][1]
    weights = ", ".join(f"{f} {x:+.2f}" for f, x in zip(feats, w[1:]))
    print(f"{label}: weights {weights}")
    print(f"  selected A {r['A'][0]}/{r['A'][1]} = {ra:.3f}, B {r['B'][0]}/{r['B'][1]} = {rb:.3f}, "
          f"ratio B/A {rb / ra:.3f}")
    return ra, rb


def main():
    rows = make()
    na = sum(r["group"] == "A" for r in rows)
    mean = {grp: sum(r["skill"] for r in rows if r["group"] == grp) / sum(r["group"] == grp for r in rows) for grp in "AB"}
    brk = {grp: sum(r["break"] for r in rows if r["group"] == grp) / sum(r["group"] == grp for r in rows) for grp in "AB"}
    print(f"WB1.15-b  selection rates: {N} applicants (A {na}, B {N - na}), top {SELECT:.0%} chosen")
    print(f"  mean skill A {mean['A']:.1f}, B {mean['B']:.1f}; career break A {brk['A']:.1%}, B {brk['B']:.1%}")
    report("model 1, skill and career break", rows, ["skill", "break"])
    report("model 2, skill only", rows, ["skill"])


if __name__ == "__main__":
    main()
