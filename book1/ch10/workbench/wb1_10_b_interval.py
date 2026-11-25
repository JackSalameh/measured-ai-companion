"""WB1.10-b  Interval of doubt.

How much should a pass rate measured on n cases be trusted, and is one prompt (or model) really
better than another? Standard library only.

  wilson(k, n)        Wilson score interval for a proportion (Wilson 1927)
  wald(k, n)          the textbook p +/- z*SE interval, for comparison
  mcnemar(b, c)       exact two-sided test on the discordant pairs of a paired comparison
  cluster_se(...)     standard error when cases come in groups of near-copies
  n_for(p, h)         cases needed for a 95% interval of half-width h around p

  python wb1_10_b_interval.py                  demo
  python wb1_10_b_interval.py recorded         the recorded run of the chapter, analysed
  python wb1_10_b_interval.py results.jsonl    the same analysis for your own WB1.10-a run
"""
import json
import math
import pathlib
import sys
from collections import defaultdict

Z = 1.959963984540054          # 97.5th percentile of the standard normal: 95% two-sided


def wilson(k, n, z=Z):
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z / (1 + z * z / n) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return centre - half, centre + half


def wald(k, n, z=Z):
    p = k / n
    se = math.sqrt(p * (1 - p) / n)
    return p - z * se, p + z * se


def binom_cdf(x, n):
    """P(X <= x) for X ~ Binomial(n, 1/2), exact with integers."""
    return sum(math.comb(n, i) for i in range(x + 1)) / 2 ** n


def mcnemar(b, c):
    """Exact two-sided p-value: under 'no real difference' each discordant case is equally likely
    to favour either side, so min(b, c) follows Binomial(b + c, 1/2)."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * binom_cdf(min(b, c), n))


def unpaired_se(k1, k2, n):
    """SE of a difference of two proportions as if measured on different cases."""
    p1, p2 = k1 / n, k2 / n
    return math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)


def paired_se(b, c, n):
    """SE of the same difference when both were measured on the same n cases (b, c discordant)."""
    d = (b - c) / n
    return math.sqrt(((b + c) / n - d * d) / n)


def cluster_se(outcomes):
    """outcomes: list of (group, 0/1). SE of the mean when cases within a group are not independent
    (sum of squared group residuals, the usual cluster-robust formula without small-sample factor)."""
    n = len(outcomes)
    p = sum(y for _, y in outcomes) / n
    groups = defaultdict(float)
    for g, y in outcomes:
        groups[g] += y - p
    return math.sqrt(sum(r * r for r in groups.values())) / n, len(groups)


def n_for(p, h, z=Z):
    return math.ceil(z * z * p * (1 - p) / (h * h))


def fmt(iv):
    return f"[{iv[0]:.3f}, {iv[1]:.3f}]"


def demo():
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import wb1_10_a_prompt_tester as pt
    from p1_first_classifier import template

    print("WB1.10-b  interval of doubt (95%)")
    print("1. Two prompts on 10 cases")
    for k in (8, 7):
        print(f"   {k}/10   Wilson {fmt(wilson(k, 10))}   Wald {fmt(wald(k, 10))}")
    print(f"   10/10  Wilson {fmt(wilson(10, 10))}   Wald {fmt(wald(10, 10))}")
    print(f"   8 vs 7 on 10 cases each: difference 0.100, SE {unpaired_se(8, 7, 10):.3f}")

    cases, models, best_k = pt.golden_set()
    nn = f"{best_k}-NN"
    rows = pt.run_pairs({"v2": pt.HERE / "prompts" / "triage_v2.txt"},
                        [pt.Program("rules-v2", models["rules v2"]), pt.Program(nn, models[nn])], cases)
    ra = [r for r in rows if r["backend"] == "rules-v2"]
    rb = [r for r in rows if r["backend"] == nn]
    ka = sum(r["label"] == r["truth"] for r in ra)
    kb = sum(r["label"] == r["truth"] for r in rb)
    n = len(cases)
    print(f"2. Two stand-in programs on the same {n} P1 test tickets")
    print(f"   rules-v2 {ka}/{n} = {ka / n:.3f}   Wilson {fmt(wilson(ka, n))}")
    print(f"   {nn:<8} {kb}/{n} = {kb / n:.3f}   Wilson {fmt(wilson(kb, n))}")
    both, b, c, neither = pt.paired_table(ra, rb)
    d = (b - c) / n
    print(f"   discordant: only rules-v2 {b}, only {nn} {c}; difference {d:.3f}")
    print(f"   SE unpaired {unpaired_se(ka, kb, n):.4f}   SE paired {paired_se(b, c, n):.4f}")
    print(f"   McNemar exact p = {mcnemar(b, c):.4f}")
    text = {cc["ticket_id"]: cc["text"] for cc in cases}
    ok_a = {r["ticket_id"]: r["label"] == r["truth"] for r in ra}
    ok_b = {r["ticket_id"]: r["label"] == r["truth"] for r in rb}
    disc = [template(text[i]) for i in ok_a if ok_a[i] != ok_b[i]]
    top = max(set(disc), key=disc.count)
    print(f"   the {len(disc)} discordant tickets have {len(set(disc))} wordings;")
    print(f"   {disc.count(top)} read {top!r}")
    print(f"3. Near-copies: the {n} tickets have {len({template(t) for t in text.values()})} wordings")
    for name, rs in (("rules-v2", ra), (nn, rb)):
        out = [(template(text[r["ticket_id"]]), int(r["label"] == r["truth"])) for r in rs]
        p = sum(y for _, y in out) / n
        se_c, groups = cluster_se(out)
        print(f"   {name:<8} SE as if independent {math.sqrt(p * (1 - p) / n):.4f}, "
              f"by wording {se_c:.4f}")
    print("4. Cases needed for a 95% interval of +/- h")
    for p, h in ((0.9, 0.05), (0.9, 0.03), (0.5, 0.05)):
        print(f"   p = {p:.2f}, h = {h:.2f}: n = {n_for(p, h)}")


def compare(rows, prompt_a, prompt_b, text_of):
    """Everything chapter 10 teaches for one back end: k/n with Wilson, the same counted by
    wording (near-copies grouped), the paired table and McNemar's exact test."""
    from p1_first_classifier import template
    ra = {r["ticket_id"]: r["label"] == r["truth"] for r in rows if r["prompt"] == prompt_a}
    rb = {r["ticket_id"]: r["label"] == r["truth"] for r in rows if r["prompt"] == prompt_b}
    n = len(ra)
    for name, ok in ((prompt_a, ra), (prompt_b, rb)):
        k = sum(ok.values())
        words = {}
        for t, good in ok.items():                 # a wording counts as right if all its tickets are
            w = template(text_of[t])
            words[w] = words.get(w, True) and good
        kw, nw = sum(words.values()), len(words)
        print(f"   {name}: {k}/{n} {fmt(wilson(k, n))}; "
              f"by wording {kw}/{nw} {fmt(wilson(kw, nw))}")
    b = sum(ra[t] and not rb[t] for t in ra)
    c = sum(rb[t] and not ra[t] for t in ra)
    both = sum(ra[t] and rb[t] for t in ra)
    print(f"   paired: both right {both}, only {prompt_a} {b}, only {prompt_b} {c}, "
          f"both wrong {n - both - b - c}")
    print(f"   McNemar exact p = {mcnemar(b, c):.2g}")


def from_results(path, prompt_a="v1", prompt_b="v2"):
    """Analyse a results file written by WB1.10-a (live run): one block per back end."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import wb1_10_a_prompt_tester as pt
    cases, _, _ = pt.golden_set()
    text_of = {c["ticket_id"]: c["text"] for c in cases}
    rows = [json.loads(line) for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    for backend in sorted({r["backend"] for r in rows}):
        print(f"{backend}:")
        compare([r for r in rows if r["backend"] == backend], prompt_a, prompt_b, text_of)


def recorded():
    """The recorded run of chapter 10, analysed as a reader's own run would be."""
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import wb1_10_a_prompt_tester as pt
    cases, _, _ = pt.golden_set()
    prompts = {"v1": pt.HERE / "prompts" / "triage_v1.txt", "v2": pt.HERE / "prompts" / "triage_v2.txt"}
    rows = pt.run_pairs(prompts, [pt.ad.Replay(pt.HERE / pt.RECORDING, "claude")], cases)
    print("WB1.10-b  recorded run analysed (95% Wilson intervals)")
    compare(rows, "v1", "v2", {c["ticket_id"]: c["text"] for c in cases})


if __name__ == "__main__":
    if len(sys.argv) == 2 and sys.argv[1] == "recorded":
        recorded()
    elif len(sys.argv) == 2:
        from_results(sys.argv[1])
    else:
        demo()
