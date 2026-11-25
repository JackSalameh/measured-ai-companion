"""WB1.11-b  Consistency probe.

Asks the same question k times and measures agreement: the share of answers equal to the most
common answer. Low agreement is a warning sign; high agreement is NOT proof of correctness.

  python wb1_11_b_consistency.py               demo: a stand-in answerer (weighted dice, NOT a model)
  python wb1_11_b_consistency.py run my.json   live: the chapter 9 adapter, k answers per question
"""
import collections
import datetime as dt
import json
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
BOOK = HERE.parents[1]
sys.path.insert(0, str(BOOK / "ch09" / "workbench"))

# question, true answer, and the stand-in's answer probabilities (invented to show the three cases)
DEMO = [("In which quarter were sales highest?", "q3", {"q3": 0.95, "q2": 0.05}),
        ("How many ledger entries lack a description?", "3", {"3": 0.4, "2": 0.3, "4": 0.3}),
        ("Did sales grow in every quarter?", "no", {"yes": 0.9, "no": 0.1})]


def agreement(answers):
    top, n = collections.Counter(answers).most_common(1)[0]
    return top, n / len(answers)


def norm(text):
    return text.strip().strip(".").lower()


def report(rows, k):
    print(f"{'question':<46}{'top answer':>11}{'agreement':>11}  correct")
    for q, truth, answers in rows:
        top, a = agreement(answers)
        print(f"{q:<46}{top:>11}{a:>11.2f}  {'yes' if top == truth else 'NO'}")


def demo(k=10, seed=1102):
    rng = random.Random(seed)
    rows = []
    for q, truth, p in DEMO:
        opts, w = zip(*p.items())
        rows.append((q, truth, rng.choices(opts, w, k=k)))
    print(f"WB1.11-b  consistency probe, stand-in answerer (not a model), k = {k}, seed {seed}")
    report(rows, k)


def live(config_path):
    import wb1_9_b_adapter as ad
    cfg = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    b = ad.make_backend(cfg["backend"])
    k, rows = cfg.get("k", 10), []
    for item in cfg["questions"]:
        answers = [norm(b.complete(item["prompt"], cfg.get("settings", {})).text) for _ in range(k)]
        rows.append((item["prompt"][:44], item["answer"], answers))
    print(f"consistency probe on {b.label}, k = {k}, {dt.date.today()}")
    report(rows, k)


if __name__ == "__main__":
    live(sys.argv[2]) if len(sys.argv) >= 3 and sys.argv[1] == "run" else demo()
