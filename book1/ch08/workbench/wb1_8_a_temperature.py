"""WB1.8-a  Temperature playground.

A language model ends each step with one score (logit) per candidate token. Softmax turns the
scores into probabilities; dividing the scores by a temperature T first makes the distribution
sharper (T < 1) or flatter (T > 1). Top-p (nucleus) sampling keeps the smallest set of most
likely tokens whose probabilities add up to at least p, and renormalizes.
The program prints the probabilities at several temperatures, the top-p set, and the share of
each token in 10,000 seeded draws, so you can see that sampling follows the probabilities.
Only the standard library is used. Run:  python wb1_8_a_temperature.py
"""
import math
import pathlib
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402

CONTEXT = "The parcel arrived"
TOKENS = ["today", "damaged", "late", "safely", "purple"]
LOGITS = [2.0, 1.5, 1.0, 0.5, -2.0]
TEMPS = [0.5, 1.0, 2.0]
TOP_P = 0.9
DRAWS, SEED = 10_000, 8101


def softmax(z, t=1.0):
    """Probabilities from scores z at temperature t. Subtracting the maximum avoids overflow."""
    s = [x / t for x in z]
    m = max(s)
    e = [math.exp(x - m) for x in s]
    tot = sum(e)
    return [x / tot for x in e]


def top_p(p, threshold):
    """Indices of the smallest set of most likely tokens whose probabilities add up to >= threshold,
    and the renormalized probabilities over that set."""
    order = sorted(range(len(p)), key=lambda i: -p[i])
    keep, acc = [], 0.0
    for i in order:
        keep.append(i)
        acc += p[i]
        if acc >= threshold:
            break
    tot = sum(p[i] for i in keep)
    return keep, {i: p[i] / tot for i in keep}


def sample(p, g):
    x, acc = g.uniform(), 0.0
    for i, pi in enumerate(p):
        acc += pi
        if x < acc:
            return i
    return len(p) - 1


def frequencies(p, n=DRAWS, seed=SEED):
    g, counts = Rng(seed), [0] * len(p)
    for _ in range(n):
        counts[sample(p, g)] += 1
    return [c / n for c in counts]


def report():
    print(f'WB1.8-a  Temperature playground: next token after "{CONTEXT}"')
    print("  token      logit " + "".join(f"   p(T={t:g})" for t in TEMPS) + f"   drawn at T=1 ({DRAWS:,} draws)")
    probs = {t: softmax(LOGITS, t) for t in TEMPS}
    freq = frequencies(probs[1.0])
    for i, tok in enumerate(TOKENS):
        print(f"  {tok:<9}{LOGITS[i]:6.1f}" + "".join(f"   {probs[t][i]:8.3f}" for t in TEMPS) + f"   {freq[i]:8.3f}")
    keep, renorm = top_p(probs[1.0], TOP_P)
    print(f"  top-p with p = {TOP_P} at T=1 keeps: " + ", ".join(f"{TOKENS[i]} {renorm[i]:.3f}" for i in keep))
    print(f"  greedy choice (T -> 0): {TOKENS[max(range(len(LOGITS)), key=lambda i: LOGITS[i])]}")


if __name__ == "__main__":
    report()
