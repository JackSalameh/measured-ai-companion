"""WB1.10-a  Prompt tester.

Runs every (prompt version, back end) pair over a golden test set of labelled tickets, turns each
answer into a queue label, and prints a confusion matrix per pair. Answers that are not exactly
one of the four queue names count as "invalid" and as wrong.

Back ends come from the chapter 9 adapter (WB1.9-b):
  replay    answers recorded earlier (JSONL), no network
  remote    any chat-completions service; key read from an environment variable
  program   a Python function that ignores the prompt: a stand-in, NOT a language model,
            used to show the measurement on real counts before you have recorded any model

  python wb1_10_a_prompt_tester.py                 demo: two stand-in programs on the P1 test set
  python wb1_10_a_prompt_tester.py recorded        replay of a recorded run (Claude, 23 Nov 2026)
  python wb1_10_a_prompt_tester.py run my.json     live run, writes results_<date>.jsonl

Every result line records the SHA-256 hash of the prompt file, so a later reader knows exactly
which wording produced which score (versioning returns in chapter 13).
"""
import datetime as dt
import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BOOK = HERE.parents[1]
sys.path.insert(0, str(BOOK / "ch09" / "workbench"))
sys.path.insert(0, str(BOOK / "ch05" / "workbench"))
import wb1_9_b_adapter as ad  # noqa: E402

LABELS = ("billing", "login", "shipping", "other")
COLS = LABELS + ("invalid",)


def golden_set():
    """The P1 test split of chapters 3 and 5: 98 labelled tickets, never used for tuning."""
    import p1_first_classifier as p1
    _, _, test, _, best_k, _, models = p1.run()
    return test, models, best_k


def prompt_version(path):
    text = pathlib.Path(path).read_text(encoding="utf-8")
    return text, hashlib.sha256(text.encode()).hexdigest()          # full hash; screens show 8 digits


def parse_label(answer):
    """Strict parser: the whole answer, trimmed of spaces, a final full stop and case, must be a queue name."""
    a = answer.strip().rstrip(".").strip().lower()
    return a if a in LABELS else "invalid"


class Program:
    """Stand-in back end: a function from ticket text to label. Not a language model."""

    def __init__(self, label, fn):
        self.label, self.fn = label, fn

    def complete(self, prompt, settings, task_id):
        return ad.Result(self.fn(task_id), self.label, None, None, 0.0, self.label)


def run_pairs(prompts, backends, cases, settings=None):
    """prompts: {name: path}; backends: list of objects with .label and .complete(prompt, settings, task_id).
    Returns one record per (prompt, back end, case)."""
    rows = []
    for pname, ppath in prompts.items():
        template, version = prompt_version(ppath)
        for b in backends:
            for c in cases:
                # replay files are keyed "prompt:ticket", so answers to two wordings never collide
                key = c["text"] if isinstance(b, Program) else f"{pname}:{c['ticket_id']}"
                r = b.complete(template.replace("{ticket}", c["text"]), settings or {}, key)
                rows.append({"prompt": pname, "prompt_sha": version, "backend": b.label, "model": r.model,
                             "ticket_id": c["ticket_id"], "truth": c["queue"], "answer": r.text,
                             "label": parse_label(r.text)})
    return rows


def confusion(rows):
    m = {(t, p): 0 for t in LABELS for p in COLS}
    for r in rows:
        m[(r["truth"], r["label"])] += 1
    return m


def show(title, rows):
    m = confusion(rows)
    n = len(rows)
    hits = sum(m[(c, c)] for c in LABELS)
    bad = sum(m[(t, "invalid")] for t in LABELS)
    print(f"{title}: correct {hits}/{n}, invalid answers {bad}")
    print("  true \\ answer" + "".join(f"{c:>9}" for c in COLS))
    for t in LABELS:
        print(f"  {t:<13}" + "".join(f"{m[(t, p)]:9d}" for p in COLS))
    return hits


def paired_table(rows_a, rows_b):
    """Counts on the same cases: both right, only A right, only B right, both wrong."""
    a = {r["ticket_id"]: r["label"] == r["truth"] for r in rows_a}
    b = {r["ticket_id"]: r["label"] == r["truth"] for r in rows_b}
    assert a.keys() == b.keys(), "a paired comparison needs the same cases"
    both = sum(a[k] and b[k] for k in a)
    only_a = sum(a[k] and not b[k] for k in a)
    only_b = sum(b[k] and not a[k] for k in a)
    return both, only_a, only_b, len(a) - both - only_a - only_b


def leaked_examples(prompt_path, cases):
    """Few-shot examples found in the test set inflate the score: copied verbatim (exact), or the
    same wording once numbers are masked and case ignored (near-copies, as in chapter 3).
    Returns the two lists of test tickets affected."""
    from p1_first_classifier import template
    text = pathlib.Path(prompt_path).read_text(encoding="utf-8")
    shown = {line[len("Ticket: "):].strip() for line in text.splitlines() if line.startswith("Ticket: ") and "{" not in line}
    exact = sorted(c["ticket_id"] for c in cases if c["text"] in shown)
    near = sorted(c["ticket_id"] for c in cases if template(c["text"]) in {template(x) for x in shown})
    return exact, near


def demo():
    cases, models, best_k = golden_set()
    print("WB1.10-a  prompt tester: demo with two stand-in programs")
    print("         (programs, not language models)")
    print(f"golden set: {len(cases)} tickets from the P1 test split")
    for p in ("triage_v1.txt", "triage_v2.txt"):
        _, sha = prompt_version(HERE / "prompts" / p)
        exact, near = leaked_examples(HERE / "prompts" / p, cases)
        print(f"{p}: sha256 {sha[:8]}, examples in golden set:")
        print(f"  exact copies {len(exact)}, near-copies {len(near)}")
    backends = [Program("rules-v2", models["rules v2"]), Program(f"{best_k}-NN", models[f"{best_k}-NN"])]
    rows = run_pairs({"v2": HERE / "prompts" / "triage_v2.txt"}, backends, cases)
    by = {b.label: [r for r in rows if r["backend"] == b.label] for b in backends}
    for name, rs in by.items():
        show(name, rs)
    both, only_a, only_b, neither = paired_table(by["rules-v2"], by[f"{best_k}-NN"])
    print(f"paired, same {len(cases)} tickets: both right {both}, both wrong {neither},")
    print(f"  only rules-v2 right {only_a}, only {best_k}-NN right {only_b}")
    print("parser check on five answers:")
    for a in ("billing", "Billing.", " shipping\n", "The queue is billing.", "billing or shipping"):
        print(f"  {a!r:<26} -> {parse_label(a)}")


RECORDING = "replay_claude_2026-11-23.jsonl"


def recorded():
    """Both prompt versions, answered by one real model and saved; see the note in every line."""
    cases, _, _ = golden_set()
    prompts = {"v1": HERE / "prompts" / "triage_v1.txt", "v2": HERE / "prompts" / "triage_v2.txt"}
    rows = run_pairs(prompts, [ad.Replay(HERE / RECORDING, "claude")], cases)
    print("WB1.10-a  recorded run: claude-opus-5-5, 23 Nov 2026")
    print("         (agent session, not the API; see note in the file)")
    for p in prompts:
        show(f"prompt {p}", [r for r in rows if r["prompt"] == p])
    v1 = [r for r in rows if r["prompt"] == "v1"]
    names = sorted({r["answer"].split("**")[1].rstrip(".") for r in v1 if r["answer"].startswith("**")})
    print(f"v1 answers use {len(names)} department names, for example:")
    for nm in names[:3]:
        print(f"  {nm}")
    words = sorted(len(r["answer"].split()) for r in v1)
    print(f"v1 answer length: {words[0]} to {words[-1]} words")


def live(config_path):
    cfg = json.loads(pathlib.Path(config_path).read_text(encoding="utf-8"))
    cases, _, _ = golden_set()
    prompts = {name: HERE / path for name, path in cfg["prompts"].items()}
    backends = [ad.make_backend(b) for b in cfg["backends"]]
    rows = run_pairs(prompts, backends, cases, cfg.get("settings"))
    stamp = dt.datetime.now(dt.timezone.utc)
    out = HERE / f"results_{stamp:%Y%m%d-%H%M}.jsonl"
    with open(out, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps({"run_at": stamp.isoformat(timespec="seconds"), **r}, ensure_ascii=False) + "\n")
    for p in prompts:
        for b in backends:
            show(f"{p} on {b.label}", [r for r in rows if r["prompt"] == p and r["backend"] == b.label])
    print(f"saved {len(rows)} answers to {out.name}; WB1.10-b reads this file for intervals")


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "run":
        live(sys.argv[2])
    elif len(sys.argv) == 2 and sys.argv[1] == "recorded":
        recorded()
    else:
        demo()
