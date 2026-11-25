"""Chapter 8 example: a bigram language model trained on the P1 support tickets.

A bigram model predicts the next word from the current word only, using counts from the
training text. It is the smallest possible language model: no network, no embeddings, just
P(next | current) = count(current, next) / count(current). The program trains it on the ticket
texts of the series data, generates sentences by sampling, and checks every generated sentence
against the training texts (ignoring punctuation): fluent sentences that no customer ever wrote are the point.
Only the standard library is used. Run:  python ex8_bigram.py
"""
import collections
import csv
import pathlib
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402

START, END = "<s>", "</s>"
SEED, N_SENT = 8201, 8


def texts():
    with open(DATA / "out" / "tickets.csv", encoding="utf-8") as f:
        return [r["text"] for r in csv.DictReader(f)]


NUM = "<n>"   # every number becomes one placeholder token, so "order 4458" and "order 9528" count together


def words(text):
    ws = text.replace("?", " ?").split()
    return [START] + [NUM if w.isdigit() else w for w in ws] + [END]


def train(corpus):
    counts = collections.defaultdict(collections.Counter)
    for t in corpus:
        w = words(t)
        for a, b in zip(w, w[1:]):
            counts[a][b] += 1
    return counts


def next_probs(counts, word):
    c = counts[word]
    tot = sum(c.values())
    return {w: n / tot for w, n in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))}


def generate(counts, g, max_len=20):
    w, out = START, []
    for _ in range(max_len):
        probs = next_probs(counts, w)
        x, acc = g.uniform(), 0.0
        for cand, p in probs.items():
            acc += p
            if x < acc:
                w = cand
                break
        else:
            w = cand
        if w == END:
            break
        out.append(w)
    return " ".join(out).replace(" ?", "?")


def norm(sentence):
    """Compare sentences without punctuation, so a lone '?' does not make a sentence new."""
    return " ".join(sentence.replace("?", " ").split())


def report():
    corpus = texts()
    counts = train(corpus)
    seen = {norm(" ".join(words(t)[1:-1])) for t in corpus}
    print(f"Bigram model trained on {len(corpus)} ticket texts; vocabulary {len(counts) - 1} words")
    print('  P(next | "my"):', ", ".join(f"{w} {p:.2f}" for w, p in list(next_probs(counts, "my").items())[:5]))
    g = Rng(SEED)
    new = 0
    for _ in range(N_SENT):
        s = generate(counts, g)
        status = "in the tickets" if norm(s) in seen else "NEW sentence"
        new += status == "NEW sentence"
        print(f"  {s:<62} {status}")
    print(f"  {new} of {N_SENT} generated sentences appear in no ticket")


if __name__ == "__main__":
    report()
