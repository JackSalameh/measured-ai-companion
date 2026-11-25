"""P1 milestone: the first learned ticket classifier, measured once on the held-out test set.

Steps, in the order the chapter requires:
  1. Take the chapter 3 split (test texts never seen in training).
  2. Split the training part again, by text, into training and validation.
  3. Choose k for a k-nearest-neighbor classifier on the validation set only.
  4. Refit on training + validation and score the chosen model on the test set, once.
  5. Compare with two references on the same test set: the majority-class baseline and the
     chapter 1 keyword rules (v2), which were written without seeing these tickets.
Run:  python p1_first_classifier.py
"""
import pathlib
import re
import sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
BOOK = HERE.parents[1]
sys.path.insert(0, str(BOOK / "ch03" / "workbench"))
sys.path.insert(0, str(BOOK / "ch01" / "workbench"))
import wb1_1_a_rules_or_learning as rules  # noqa: E402
import wb1_3_b_leakage as lk  # noqa: E402
from rng import Rng  # noqa: E402  (made importable by wb1_3_b_leakage)

SEED = 5301
KS = (1, 3, 5, 9)
LABELS = ("billing", "login", "shipping", "other")


def split_by_text(rows, share, seed):
    texts = lk.shuffled(sorted(set(r["text"] for r in rows)), Rng(seed))
    held = set(texts[:int(share * len(texts))])
    return [r for r in rows if r["text"] not in held], [r for r in rows if r["text"] in held]


def knn(train, k):
    memory = [(lk.words(r["text"]), r["queue"]) for r in train]

    def predict(text):
        w = lk.words(text)
        sims = sorted(((len(w & m) / len(w | m), -i, q) for i, (m, q) in enumerate(memory)), reverse=True)[:k]
        votes = Counter(q for _, _, q in sims)
        top = max(votes.values())
        for _, _, q in sims:                    # ties go to the label of the nearest neighbor
            if votes[q] == top:
                return q
    return predict


def confusion(predict, rows):
    m = {(t, p): 0 for t in LABELS for p in LABELS}
    for r in rows:
        m[(r["queue"], predict(r["text"]))] += 1
    return m


def scores(m):
    n = sum(m.values())
    acc = sum(m[(c, c)] for c in LABELS) / n
    per = {}
    for c in LABELS:
        tp = m[(c, c)]
        pred = sum(m[(t, c)] for t in LABELS)
        true = sum(m[(c, p)] for p in LABELS)
        prec = tp / pred if pred else float("nan")
        rec = tp / true if true else float("nan")
        f1 = 2 * prec * rec / (prec + rec) if pred and true and (prec + rec) else 0.0
        per[c] = (tp, pred, true, prec, rec, f1)
    return acc, per


def template(text):
    return re.sub(r"\d+", "#", text.lower())


def run():
    train_all, test = lk.split_rows()
    train, val = split_by_text(train_all, 0.2, SEED)
    val_acc = {k: sum(knn(train, k)(r["text"]) == r["queue"] for r in val) / len(val) for k in KS}
    best_k = max(KS, key=lambda k: (val_acc[k], -k))     # ties go to the smaller k (simpler)
    final = knn(train_all, best_k)
    majority = Counter(r["queue"] for r in train_all).most_common(1)[0][0]
    models = {f"{best_k}-NN": final, "majority": lambda t: majority, "rules v2": lambda t: rules.route(t, rules.RULES_V2)}
    return train, val, test, val_acc, best_k, majority, models


def main():
    train, val, test, val_acc, best_k, majority, models = run()
    print("P1 milestone: first learned classifier")
    print(f"  training {len(train)}, validation {len(val)}, test {len(test)} tickets (split by text)")
    print("  validation accuracy by k: " + ", ".join(f"k={k}: {a:.3f}" for k, a in val_acc.items()))
    print(f"  chosen k = {best_k} (refit on training + validation)")
    print("Test set, used once:")
    for name, f in models.items():
        m = confusion(f, test)
        acc, _ = scores(m)
        hits = sum(m[(c, c)] for c in LABELS)
        print(f"  {name:<9} accuracy {hits}/{len(test)} = {acc:.3f}")
    m = confusion(models[f"{best_k}-NN"], test)
    print(f"Confusion matrix of {best_k}-NN (rows = true queue, columns = predicted)")
    print("            " + "".join(f"{c:>9}" for c in LABELS))
    for t in LABELS:
        print(f"  {t:<10}" + "".join(f"{m[(t, p)]:9d}" for p in LABELS))
    _, per = scores(m)
    print("  queue      precision   recall      F1")
    for c, (tp, pred, true, prec, rec, f1) in per.items():
        print(f"  {c:<10} {tp:2d}/{pred:<3d}={prec:.2f} {tp:2d}/{true:<3d}={rec:.2f}  {f1:.2f}")
    seen = {template(r["text"]) for r in train + val}
    for name in (f"{best_k}-NN", "rules v2"):
        f = models[name]
        a = [r for r in test if template(r["text"]) in seen]
        b = [r for r in test if template(r["text"]) not in seen]
        print(f"Diagnosis, {name}: same template as a training ticket {sum(f(r['text']) == r['queue'] for r in a)}/{len(a)}, "
              f"new template {sum(f(r['text']) == r['queue'] for r in b)}/{len(b)}")


if __name__ == "__main__":
    main()
