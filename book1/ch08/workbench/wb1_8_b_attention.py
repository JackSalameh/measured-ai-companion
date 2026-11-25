"""WB1.8-b  Attention by hand.

Scaled dot-product attention, as defined by Vaswani et al. (2017):
    Attention(Q, K, V) = softmax(Q K^T / sqrt(d_k)) V
Three tokens, vectors of dimension 2. Each token has a query (what it looks for), a key (what it
offers to be found by) and a value (what it passes on). For each token the program computes the
scores against every key, the softmax weights (each row adds up to 1), and the weighted sum of
the values. A second, independent implementation (column by column, no shared code) checks it.
Only the standard library is used. Run:  python wb1_8_b_attention.py
"""
import math

TOKENS = ["parcel", "arrived", "damaged"]
Q = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
K = [[1.0, 0.0], [0.0, 1.0], [1.0, 1.0]]
V = [[1.0, 0.0], [0.0, 1.0], [0.5, 0.5]]


def softmax(row):
    m = max(row)
    e = [math.exp(x - m) for x in row]
    s = sum(e)
    return [x / s for x in e]


def attention(q, k, v):
    d = len(k[0])
    scores = [[sum(a * b for a, b in zip(qi, kj)) / math.sqrt(d) for kj in k] for qi in q]
    weights = [softmax(r) for r in scores]
    out = [[sum(w * vj[c] for w, vj in zip(wr, v)) for c in range(len(v[0]))] for wr in weights]
    return scores, weights, out


def attention_check(q, k, v):
    """Independent version: build the score matrix by columns, exponentiate without the max shift."""
    n, d = len(q), len(k[0])
    sc = [[0.0] * n for _ in range(n)]
    for j in range(n):
        for i in range(n):
            sc[i][j] = (q[i][0] * k[j][0] + q[i][1] * k[j][1]) / d ** 0.5
    out = []
    for i in range(n):
        e = [math.e ** sc[i][j] for j in range(n)]
        z = sum(e)
        out.append([sum(e[j] / z * v[j][c] for j in range(n)) for c in range(2)])
    return out


def report():
    scores, weights, out = attention(Q, K, V)
    print("WB1.8-b  Attention by hand: 3 tokens, d_k = 2")
    print("  scores q.k / sqrt(2)                 weights (each row sums to 1)         output")
    for i, t in enumerate(TOKENS):
        print(f"  {t:<8}" + " ".join(f"{x:6.3f}" for x in scores[i]) + "      "
              + " ".join(f"{x:6.3f}" for x in weights[i]) + f"   (sum {sum(weights[i]):.3f})"
              + "    " + " ".join(f"{x:6.3f}" for x in out[i]))
    chk = attention_check(Q, K, V)
    diff = max(abs(a - b) for r1, r2 in zip(out, chk) for a, b in zip(r1, r2))
    print(f"  independent implementation agrees: {'yes' if diff < 1e-12 else 'NO'} (largest difference {diff:.1e})")


if __name__ == "__main__":
    report()
