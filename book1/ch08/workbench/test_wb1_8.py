"""Tests for the chapter 8 Workbench apps and example."""
import math
import pathlib
import subprocess
import sys

import ex8_bigram as bg
import wb1_8_a_temperature as tp
import wb1_8_b_attention as at

HERE = pathlib.Path(__file__).parent


def run(script):
    return subprocess.run([sys.executable, str(HERE / script)], capture_output=True, text=True, check=True, cwd=HERE).stdout


def test_outputs_match_expected():
    for f in ("wb1_8_a_temperature", "wb1_8_b_attention", "ex8_bigram"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text()


def test_softmax_properties():
    for t in (0.25, 0.5, 1.0, 2.0, 10.0):
        p = tp.softmax(tp.LOGITS, t)
        assert abs(sum(p) - 1) < 1e-12 and all(x > 0 for x in p)
        assert p == sorted(p, reverse=True)                      # order of the logits is kept at every T
    # ratio of two probabilities is exp((z1 - z2)/T)
    p = tp.softmax(tp.LOGITS, 0.5)
    assert abs(p[0] / p[1] - math.exp((2.0 - 1.5) / 0.5)) < 1e-12
    # high temperature approaches uniform, low temperature approaches greedy
    assert max(tp.softmax(tp.LOGITS, 1000)) < 0.21 and tp.softmax(tp.LOGITS, 0.01)[0] > 0.999


def test_top_p_is_smallest_set():
    p = tp.softmax(tp.LOGITS, 1.0)
    keep, renorm = tp.top_p(p, 0.9)
    assert sum(p[i] for i in keep) >= 0.9 > sum(p[i] for i in keep[:-1])
    assert abs(sum(renorm.values()) - 1) < 1e-12


def test_attention_rows_and_checks():
    _, w, out = at.attention(at.Q, at.K, at.V)
    assert all(abs(sum(r) - 1) < 1e-12 for r in w)
    chk = at.attention_check(at.Q, at.K, at.V)
    assert max(abs(a - b) for r1, r2 in zip(out, chk) for a, b in zip(r1, r2)) < 1e-12


def test_bigram_probabilities_sum_to_one():
    counts = bg.train(bg.texts())
    for word in counts:
        assert abs(sum(bg.next_probs(counts, word).values()) - 1) < 1e-12


def test_bpe_tokens_rebuild_the_word():
    import ex8_tokens as tk
    merges = tk.learn(tk.word_counts())
    for w in ("password", "declined", "arrived", "bank", "xylophone"):
        toks = tk.tokenize(w, merges)
        assert "".join(toks) == w + tk.END                     # nothing lost, nothing added
    assert len(tk.tokenize("password", merges)) == 1           # a frequent ticket word is one token


def test_cosine_basics():
    import ex8_embeddings as em
    v = em.vectors(em.sentences())
    assert abs(em.cosine(v["order"], v["order"]) - 1) < 1e-12
    assert all(0 <= em.cosine(v[a], v[b]) <= 1 + 1e-12 for a, b in em.PAIRS)


def test_new_outputs_match_expected():
    for f in ("ex8_tokens", "ex8_embeddings"):
        assert run(f + ".py") == (HERE / "expected" / (f + ".txt")).read_text()
