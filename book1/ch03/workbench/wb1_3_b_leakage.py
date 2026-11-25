"""WB1.3-b  Split and leakage trap

Part 1. A 1-nearest-neighbor router for the series tickets (word overlap, chapter 5 explains the method)
is scored twice: with a random split, where identical ticket texts can sit on both sides, and with a
split that keeps all copies of a text on the same side. The difference is what the duplicates leak.
Part 2. A drifting process is fitted with a straight line and scored with a random split and with a
time-ordered split. The random split tests on points from the same period as the training data.
Run:  python wb1_3_b_leakage.py
      python wb1_3_b_leakage.py --save-split FOLDER   (also writes the split-by-text tickets to
                                                        FOLDER/train.csv and FOLDER/test.csv)
"""
import csv
import math
import pathlib
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402

SEED = 3401


def words(t):
    return set(w.strip("?.,!").lower() for w in t.split())


def nn_accuracy(train, test):
    tw = [(words(t), q) for t, q in train]
    hits = 0
    for t, q in test:
        w = words(t)
        best = max(tw, key=lambda p: len(w & p[0]) / len(w | p[0]))   # most similar training ticket (ties: first)
        hits += best[1] == q
    return hits, len(test)


def shuffled(items, g):
    items = list(items)
    for i in range(len(items) - 1, 0, -1):   # Fisher-Yates with the portable generator
        j = g.index(i + 1)
        items[i], items[j] = items[j], items[i]
    return items


def part1():
    rows = [(r["text"], r["queue"]) for r in csv.DictReader(open(DATA / "out" / "tickets.csv", encoding="utf-8"))]
    g = Rng(SEED)
    order = shuffled(range(len(rows)), g)
    cut = int(0.8 * len(rows))
    rnd = nn_accuracy([rows[i] for i in order[:cut]], [rows[i] for i in order[cut:]])
    texts = shuffled(sorted(set(t for t, _ in rows)), g)
    test_texts = set(texts[:int(0.2 * len(texts))])
    grp = nn_accuracy([r for r in rows if r[0] not in test_texts], [r for r in rows if r[0] in test_texts])
    seen_train = set(rows[i][0] for i in order[:cut])
    overlap = sum(1 for i in order[cut:] if rows[i][0] in seen_train)
    return rnd, grp, overlap, len(rows) - cut


def fit(pts):
    n = len(pts)
    mx = sum(x for x, _ in pts) / n
    my = sum(y for _, y in pts) / n
    a = sum((x - mx) * (y - my) for x, y in pts) / sum((x - mx) ** 2 for x, _ in pts)
    return a, my - a * mx


def mse(pts, a, b):
    return sum((y - (a * x + b)) ** 2 for x, y in pts) / len(pts)


def part2():
    g = Rng(SEED + 1)
    pts = []
    for t in range(200):                      # the slope drifts from 1.0 to 2.0 over 200 time steps
        x = g.uniform(0, 10)
        pts.append((t, x, (1.0 + t / 200) * x + g.normal(0, 0.5)))
    order = shuffled(range(200), g)
    rnd_train = [(x, y) for t, x, y in (pts[i] for i in order[:150])]
    rnd_test = [(x, y) for t, x, y in (pts[i] for i in order[150:])]
    a1, b1 = fit(rnd_train)
    tim_train = [(x, y) for t, x, y in pts[:150]]
    tim_test = [(x, y) for t, x, y in pts[150:]]
    a2, b2 = fit(tim_train)
    return mse(rnd_test, a1, b1), mse(tim_test, a2, b2), a1, a2


def split_rows():
    """The split by distinct text of part 1 (same seed, same test texts): (train rows, test rows)."""
    with open(DATA / "out" / "tickets.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    g = Rng(SEED)
    shuffled(range(len(rows)), g)                       # same draws as part1, so the same test texts
    texts = shuffled(sorted(set(r["text"] for r in rows)), g)
    test_texts = set(texts[:int(0.2 * len(texts))])
    return [r for r in rows if r["text"] not in test_texts], [r for r in rows if r["text"] in test_texts]


def save_split(folder):
    """Write the split-by-distinct-text tickets of part 1 to FOLDER/train.csv and FOLDER/test.csv."""
    train, test = split_rows()
    out = pathlib.Path(folder)
    out.mkdir(parents=True, exist_ok=True)
    for name, part in (("train.csv", train), ("test.csv", test)):
        with open(out / name, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(train[0]))
            w.writeheader()
            w.writerows(part)
    print(f"wrote {out / 'train.csv'} ({len(train)} tickets) and {out / 'test.csv'} ({len(test)} tickets)")


def main(argv=()):
    print("WB1.3-b  Split and leakage trap")
    (h1, n1), (h2, n2), overlap, ntest = part1()
    print("Part 1: 1-nearest-neighbor ticket router, 80/20 split")
    print(f"  random split            : {h1}/{n1} = {h1 / n1:.3f}   ({overlap} of {ntest} test tickets have an identical text in training)")
    print(f"  split by distinct text  : {h2}/{n2} = {h2 / n2:.3f}   (no test text appears in training)")
    m1, m2, a1, a2 = part2()
    print("Part 2: straight-line fit to a drifting process, 150 training and 50 test points")
    print(f"  random split            : test MSE = {m1:.3f}   (fitted slope {a1:.3f})")
    print(f"  time-ordered split      : test MSE = {m2:.3f}   (fitted slope {a2:.3f})")
    if len(argv) == 2 and argv[0] == "--save-split":
        save_split(argv[1])


if __name__ == "__main__":
    main(sys.argv[1:])
