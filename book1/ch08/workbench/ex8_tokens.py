"""Chapter 8 example: a byte pair encoding (BPE) tokenizer learned from the P1 ticket texts.

BPE, adapted to word segmentation by Sennrich, Haddow and Birch (2016): start with every word
split into characters plus an end-of-word mark, then repeatedly merge the most frequent
adjacent pair of symbols into one new symbol. Frequent words end up as single tokens; rare
or unseen words are split into pieces. The program learns a fixed number of merges and then
tokenizes a few sentences, so you can compare word counts with token counts.
Only the standard library is used. Run:  python ex8_tokens.py
"""
import collections
import csv
import pathlib

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
END = "_"            # end-of-word mark (Sennrich et al. use a similar marker)
MERGES = 300
EXAMPLES = ["The password reset email never arrives",
            "My parcel arrived damaged",
            "The refund was declined by my bank"]


def word_counts():
    with open(DATA / "out" / "tickets.csv", encoding="utf-8") as f:
        texts = [r["text"] for r in csv.DictReader(f)]
    c = collections.Counter()
    for t in texts:
        for w in t.lower().replace("?", " ").replace(",", " ").split():
            if not w.isdigit():
                c[w] += 1
    return c


def learn(counts, n_merges=MERGES):
    vocab = {tuple(w) + (END,): n for w, n in counts.items()}
    merges = []
    for _ in range(n_merges):
        pairs = collections.Counter()
        for sym, n in vocab.items():
            for a, b in zip(sym, sym[1:]):
                pairs[(a, b)] += n
        if not pairs:
            break
        best = max(pairs.items(), key=lambda kv: (kv[1], kv[0]))[0]   # ties broken by the pair itself
        merges.append(best)
        new = {}
        for sym, n in vocab.items():
            out, i = [], 0
            while i < len(sym):
                if i + 1 < len(sym) and (sym[i], sym[i + 1]) == best:
                    out.append(sym[i] + sym[i + 1])
                    i += 2
                else:
                    out.append(sym[i])
                    i += 1
            new[tuple(out)] = new.get(tuple(out), 0) + n
        vocab = new
    return merges


def tokenize(word, merges):
    sym = list(word.lower()) + [END]
    for a, b in merges:
        i, out = 0, []
        while i < len(sym):
            if i + 1 < len(sym) and sym[i] == a and sym[i + 1] == b:
                out.append(a + b)
                i += 2
            else:
                out.append(sym[i])
                i += 1
        sym = out
    return sym


def report():
    counts = word_counts()
    merges = learn(counts)
    print(f"BPE learned from {sum(counts.values()):,} words of ticket text ({len(counts)} distinct); {len(merges)} merges")
    print("  first five merges:", ", ".join(f"{a}+{b}" for a, b in merges[:5]))
    for s in EXAMPLES:
        toks = [t for w in s.split() for t in tokenize(w, merges)]
        print(f"  {s}")
        print(f"    {len(s.split())} words -> {len(toks)} tokens: " + " | ".join(toks))


if __name__ == "__main__":
    report()
