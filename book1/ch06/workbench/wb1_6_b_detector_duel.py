"""WB1.6-b  Detector duel: a threshold against a small learned detector.

Synthetic motor vibration in short windows (0.1 s at 12,000 samples per second). Half the
windows contain an early-stage fault: short decaying bursts at a resonance, with a strength
that varies from barely visible to clear. Each window is summarized by four features
(RMS, peak, crest factor, kurtosis; chapter 3).
  Detector A: one feature and one threshold, both chosen on the training windows.
  Detector C: a single sigmoid neuron (logistic regression) on the same four features,
              trained and stopped the same way: it separates "more features" from "hidden layer".
  Detector B: a network with one hidden layer of 6 sigmoid neurons on all four standardized
              features, trained by gradient descent; the number of epochs is chosen on the
              validation windows.
Both are scored once on the test windows. The setting is synthetic: the result says which
detector wins here, not in general. Only the standard library is used.
Run:  python wb1_6_b_detector_duel.py            (writes duel_features.csv and duel_init.csv
                                                    for the MATLAB cross-check)
"""
import csv
import math
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
DATA = next(p for p in HERE.resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data"
sys.path.insert(0, str(DATA))
from rng import Rng  # noqa: E402
import gen_signals as gs  # noqa: E402

SEED = 6201
FS, WIN = 12000, 1200                       # 0.1 s windows
NOISE = 0.35                                # standard deviation of the broadband noise, m/s^2
FAULT_MIN, FAULT_MAX = 0.2, 1.2             # burst amplitude range, m/s^2
SPLIT = (300, 150, 300)                     # training, validation, test windows
HIDDEN, LR, MAX_EPOCHS = 6, 0.5, 3000
FEATS = ("rms", "peak", "crest", "kurtosis")


def window(g, faulty):
    amp = 1.0 + 0.1 * g.normal()
    phase = g.uniform(0, 2 * math.pi)
    a_f = g.uniform(FAULT_MIN, FAULT_MAX) if faulty else 0.0
    start = g.uniform(0, 1 / gs.FAULT_RATE)
    x = []
    for n in range(WIN):
        t = n / FS
        v = amp * math.sin(2 * math.pi * gs.FR * t + phase) + 0.3 * amp * math.sin(2 * math.pi * 2 * gs.FR * t + 2 * phase)
        v += NOISE * g.normal()
        if faulty:
            tau = ((t + start) * gs.FAULT_RATE) % 1.0 / gs.FAULT_RATE
            v += a_f * math.exp(-gs.DECAY * tau) * math.sin(2 * math.pi * gs.RESONANCE * tau)
        x.append(v)
    return x, a_f


def dataset():
    g = Rng(SEED)
    rows = []
    for i in range(sum(SPLIT)):
        faulty = i % 2 == 1
        x, a_f = window(g, faulty)
        f = gs.features(x)
        rows.append(([f[k] for k in FEATS], int(faulty), a_f))
    a, b = SPLIT[0], SPLIT[0] + SPLIT[1]
    return rows[:a], rows[a:b], rows[b:]


# ---- Detector A: best single feature and threshold on the training windows
def fit_threshold(train):
    best = None
    for j, name in enumerate(FEATS):
        vals = sorted(set(r[0][j] for r in train))
        for lo, hi in zip(vals, vals[1:]):
            t = (lo + hi) / 2
            acc = sum((r[0][j] > t) == bool(r[1]) for r in train) / len(train)
            if best is None or acc > best[0]:
                best = (acc, j, t)
    return best


# ---- Detector B: 4-HIDDEN-1 network, sigmoid units, mean cross-entropy, full-batch gradient descent
def sig(z):
    return 1 / (1 + math.exp(-max(-50.0, min(50.0, z))))


def standardizer(train):
    cols = list(zip(*[r[0] for r in train]))
    mu = [sum(c) / len(c) for c in cols]
    sd = [math.sqrt(sum((v - m) ** 2 for v in c) / (len(c) - 1)) for c, m in zip(cols, mu)]
    return lambda x: [(v - m) / s for v, m, s in zip(x, mu, sd)]


def init_net(seed=SEED + 1):
    g = Rng(seed)
    W = [[g.uniform(-0.5, 0.5) for _ in FEATS] for _ in range(HIDDEN)]
    b = [0.0] * HIDDEN
    v = [g.uniform(-0.5, 0.5) for _ in range(HIDDEN)]
    return W, b, v, 0.0


def predict(net, x):
    W, b, v, c = net
    h = [sig(sum(w * xi for w, xi in zip(Wj, x)) + bj) for Wj, bj in zip(W, b)]
    return sig(sum(vj * hj for vj, hj in zip(v, h)) + c), h


def step(net, data, lr):
    W, b, v, c = net
    gW = [[0.0] * len(FEATS) for _ in range(HIDDEN)]
    gb, gv, gc = [0.0] * HIDDEN, [0.0] * HIDDEN, 0.0
    for x, t in data:
        y, h = predict(net, x)
        d = y - t
        gc += d
        for j in range(HIDDEN):
            gv[j] += d * h[j]
            dj = d * v[j] * h[j] * (1 - h[j])
            gb[j] += dj
            for i in range(len(FEATS)):
                gW[j][i] += dj * x[i]
    n = len(data)
    W = [[w - lr * gw / n for w, gw in zip(Wj, gWj)] for Wj, gWj in zip(W, gW)]
    return W, [bj - lr * g / n for bj, g in zip(b, gb)], [vj - lr * g / n for vj, g in zip(v, gv)], c - lr * gc / n


def train_neuron(tr, va):
    """Single sigmoid neuron on the standardized features; epochs chosen on validation."""
    w, c = [0.0] * len(FEATS), 0.0
    acc = lambda w, c, d: sum((sig(sum(a * b for a, b in zip(w, x)) + c) > 0.5) == bool(t) for x, t in d) / len(d)
    best = (acc(w, c, va), 0, w, c)
    for e in range(1, MAX_EPOCHS + 1):
        gw, gc = [0.0] * len(FEATS), 0.0
        for x, t in tr:
            d = sig(sum(a * b for a, b in zip(w, x)) + c) - t
            gw = [g + d * xi for g, xi in zip(gw, x)]
            gc += d
        w = [a - LR * g / len(tr) for a, g in zip(w, gw)]
        c -= LR * gc / len(tr)
        if e % 100 == 0 and acc(w, c, va) > best[0]:
            best = (acc(w, c, va), e, w, c)
    return best


def accuracy_net(net, data):
    return sum((predict(net, x)[0] > 0.5) == bool(t) for x, t in data) / len(data)


def run():
    train, val, test = dataset()
    thr_acc, j, t = fit_threshold(train)
    z = standardizer(train)
    tr = [(z(r[0]), r[1]) for r in train]
    va = [(z(r[0]), r[1]) for r in val]
    te = [(z(r[0]), r[1]) for r in test]
    net = init_net()
    best = (accuracy_net(net, va), 0, net)
    curve = []
    for e in range(1, MAX_EPOCHS + 1):
        net = step(net, tr, LR)
        if e % 100 == 0:
            a = accuracy_net(net, va)
            curve.append((e, accuracy_net(net, tr), a))
            if a > best[0]:
                best = (a, e, net)
    res = {"train": train, "val": val, "test": test, "thr": (thr_acc, j, t), "best_epoch": best[1], "val_acc": best[0],
           "net": best[2], "curve": curve, "z": z}
    res["thr_test"] = [int(r[0][j] > t) for r in test]
    lv, le, lw, lc = train_neuron(tr, va)
    res["log"] = (lv, le, lw, lc)
    res["log_test"] = [int(sig(sum(a * b for a, b in zip(lw, x)) + lc) > 0.5) for x, _ in te]
    res["net_test"] = [int(predict(best[2], z(r[0]))[0] > 0.5) for r in test]
    return res


def by_strength(test, pred, edges=(0.2, 0.533, 0.867, 1.2)):
    out = []
    for lo, hi in zip(edges, edges[1:]):
        idx = [i for i, r in enumerate(test) if r[1] == 1 and lo <= r[2] < hi + (1e-9 if hi == edges[-1] else 0)]
        out.append((lo, hi, sum(pred[i] for i in idx), len(idx)))
    return out


def export(res):
    with open(HERE / "duel_features.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["split"] + list(FEATS) + ["fault", "strength"])
        for name in ("train", "val", "test"):
            for x, lab, a in res[name]:
                w.writerow([name] + [repr(v) for v in x] + [lab, repr(a)])
    W, b, v, c = init_net()
    with open(HERE / "duel_init.csv", "w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        for Wj, bj, vj in zip(W, b, v):
            w.writerow([repr(x) for x in Wj] + [repr(bj), repr(vj)])
        w.writerow([repr(c)])


def main(argv=()):
    res = run()
    test = res["test"]
    thr_acc, j, t = res["thr"]
    print("WB1.6-b  Detector duel")
    print(f"  windows: {SPLIT[0]} training, {SPLIT[1]} validation, {SPLIT[2]} test (half faulty);"
          f" noise SD {NOISE}, fault amplitude {FAULT_MIN} to {FAULT_MAX}, seed {SEED}")
    print(f"Detector A: {FEATS[j]} > {t:.4f}   (training accuracy {thr_acc:.3f})")
    print(f"Detector C: single neuron on 4 features, best validation accuracy {res['log'][0]:.3f} at epoch {res['log'][1]}")
    print(f"Detector B: 4-{HIDDEN}-1 network, rate {LR}, best validation accuracy {res['val_acc']:.3f} at epoch {res['best_epoch']}")
    for name, pred in (("A threshold", res["thr_test"]), ("C neuron   ", res["log_test"]), ("B network  ", res["net_test"])):
        hits = sum(p == r[1] for p, r in zip(pred, test))
        tp = sum(p and r[1] for p, r in zip(pred, test))
        fp = sum(p and not r[1] for p, r in zip(pred, test))
        nf = sum(r[1] for r in test)
        print(f"  {name} test accuracy {hits}/{len(test)} = {hits / len(test):.3f}   faults caught {tp}/{nf}   false alarms {fp}/{len(test) - nf}")
    print("Faults caught by fault strength (test windows)")
    for (lo, hi, a, n), (_, _, c, _), (_, _, b, _) in zip(by_strength(test, res["thr_test"]), by_strength(test, res["log_test"]), by_strength(test, res["net_test"])):
        print(f"  amplitude {lo:.2f} to {hi:.2f}: threshold {a}/{n}   neuron {c}/{n}   network {b}/{n}")
    if "--export" in argv:
        export(res)
        print("wrote duel_features.csv and duel_init.csv")


if __name__ == "__main__":
    main(sys.argv[1:])
