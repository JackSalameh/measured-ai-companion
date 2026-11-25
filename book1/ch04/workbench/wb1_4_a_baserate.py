"""WB1.4-a  Base-rate calculator.

Answers one question three ways and checks that the answers agree:
"An alarm went off. What is the chance that the condition is really there?"
  1. by a table of natural frequencies (counts in an imagined population),
  2. by Bayes' rule,
  3. by Monte Carlo simulation (simulated cases with a fixed seed).

Run:  python wb1_4_a_baserate.py
      python wb1_4_a_baserate.py --base 0.02 --sens 0.90 --fpr 0.05
"""
import argparse
import math
import pathlib
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402

SEED = 4101


def table(base, sens, fpr, n=10_000):
    """Natural frequencies for a population of n (rounded to whole cases)."""
    sick = round(n * base)
    healthy = n - sick
    tp = round(sick * sens)
    fp = round(healthy * fpr)
    return {"n": n, "with": sick, "without": healthy, "tp": tp, "fn": sick - tp, "fp": fp, "tn": healthy - fp}


def bayes(base, sens, fpr):
    """P(condition | alarm) = P(alarm | condition) P(condition) / P(alarm)."""
    p_alarm = sens * base + fpr * (1 - base)
    return sens * base / p_alarm


def monte_carlo(base, sens, fpr, cases=200_000, seed=SEED):
    g = Rng(seed)
    alarms = true_alarms = 0
    for _ in range(cases):
        cond = g.chance(base)
        alarm = g.chance(sens) if cond else g.chance(fpr)
        if alarm:
            alarms += 1
            true_alarms += cond
    p = true_alarms / alarms
    se = math.sqrt(p * (1 - p) / alarms)          # standard error of the estimate
    return p, se, alarms


def main(argv=()):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=float, default=0.02, help="share of cases that have the condition")
    ap.add_argument("--sens", type=float, default=0.90, help="P(alarm | condition), the sensitivity")
    ap.add_argument("--fpr", type=float, default=0.05, help="P(alarm | no condition), the false-alarm rate")
    a = ap.parse_args(argv)
    t = table(a.base, a.sens, a.fpr)
    exact = bayes(a.base, a.sens, a.fpr)
    mc, se, n_al = monte_carlo(a.base, a.sens, a.fpr)
    print("WB1.4-a  Base-rate calculator")
    print(f"  base rate {a.base:.2%}, sensitivity {a.sens:.2%}, false-alarm rate {a.fpr:.2%}")
    print(f"1. Natural frequencies, out of {t['n']:,} cases")
    print(f"                    alarm   no alarm    total")
    print(f"  condition       {t['tp']:7,} {t['fn']:10,} {t['with']:8,}")
    print(f"  no condition    {t['fp']:7,} {t['tn']:10,} {t['without']:8,}")
    print(f"  total           {t['tp'] + t['fp']:7,} {t['fn'] + t['tn']:10,} {t['n']:8,}")
    print(f"  P(condition | alarm) = {t['tp']:,} / {t['tp'] + t['fp']:,} = {t['tp'] / (t['tp'] + t['fp']):.4f}")
    print(f"2. Bayes' rule         = {exact:.4f}")
    print(f"3. Monte Carlo         = {mc:.4f}  (standard error {se:.4f}, {n_al:,} alarms in 200,000 simulated cases)")
    ok = abs(mc - exact) <= 3 * se
    print(f"  agreement: |Monte Carlo - Bayes| = {abs(mc - exact):.4f} {'<=' if ok else '>'} 3 standard errors ({3 * se:.4f}): {'yes' if ok else 'NO'}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
