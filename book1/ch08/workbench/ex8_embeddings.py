"""Chapter 8 example: word vectors from the neighbors of each word in the P1 ticket texts.

The distributional idea: words used in similar company get similar vectors. Here each word's
vector counts its immediate neighbors (one word to the left, one to the right; numbers count
as <n>). Cosine similarity, from 1 (same direction) down to 0 (no neighbor in common), compares
two words. Real embeddings are learned by a network and are dense; these are counted, have one
dimension per neighbor, and show the same principle on data you can inspect.
Only the standard library is used. Run:  python ex8_embeddings.py
"""
import collections
import csv
import math
import pathlib

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
PAIRS = [("january", "february"), ("canada", "japan"), ("invoice", "order"), ("password", "parcel"), ("parcel", "package")]


def sentences():
    with open(DATA / "out" / "tickets.csv", encoding="utf-8") as f:
        texts = [r["text"] for r in csv.DictReader(f)]
    return [["<s>"] + ["<n>" if w.isdigit() else w for w in t.lower().replace("?", " ?").split()] + ["</s>"] for t in texts]


def vectors(sents):
    """For each word, count the word just before it (marked L) and just after it (marked R)."""
    v = collections.defaultdict(collections.Counter)
    for ws in sents:
        for i in range(1, len(ws) - 1):
            v[ws[i]]["L:" + ws[i - 1]] += 1
            v[ws[i]]["R:" + ws[i + 1]] += 1
    return v


def cosine(u, w):
    dot = sum(u[k] * w.get(k, 0) for k in u)
    return dot / math.sqrt(sum(x * x for x in u.values()) * sum(x * x for x in w.values()))


def nearest(v, word, n=3):
    return sorted(((cosine(v[word], v[x]), x) for x in v if x != word), key=lambda t: (-t[0], t[1]))[:n]


def report():
    v = vectors(sentences())
    print(f"Neighbor-count vectors for {len(v)} words of the ticket texts")
    for a, b in PAIRS:
        print(f"  cos({a}, {b}) = {cosine(v[a], v[b]):.2f}")
    for w in ("invoice", "january"):
        print(f"  nearest to {w}: " + ", ".join(f"{x} {c:.2f}" for c, x in nearest(v, w)))
    print("  'invoice' neighbors:", ", ".join(f"{k} {n}" for k, n in v["invoice"].most_common(4)))
    print("  'order' neighbors:  ", ", ".join(f"{k} {n}" for k, n in v["order"].most_common(4)))


if __name__ == "__main__":
    report()
