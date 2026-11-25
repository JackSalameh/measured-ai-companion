"""P2 Motor Health Monitor: seeded synthetic vibration and motor-current signals.
A record is one second sampled at FS samples per second. Healthy vibration: shaft rotation at FR Hz and its
second harmonic plus noise. Faulty vibration adds short decaying bursts at a resonance, repeating at FAULT_RATE
times per second. Current: supply frequency F_SUPPLY; faulty records add small sidebands at F_SUPPLY +/- FR.
These are teaching signals, not models of a real machine; chapter 7 and Book 2 explain the physics.
Output: out/signal_features.csv (one row per record). Raw signals are regenerated on demand by record().
Planted for chapter 3: three records logged in g instead of m/s^2, two missing temperature readings."""
import csv
import math
import pathlib

from rng import Rng

SEED, FS, N_REC = 3201, 12000, 120
FR, F_SUPPLY, FAULT_RATE, RESONANCE, DECAY = 25.0, 50.0, 87.5, 3000.0, 400.0
G = 9.80665  # standard gravity, m/s^2 per g


def record(k, faulty):
    """Vibration (m/s^2) and current (A) for record k; deterministic from SEED and k."""
    g = Rng(SEED * 1000 + k)
    amp = 1.0 + 0.1 * g.normal()
    vib, cur = [], []
    for n in range(FS):
        t = n / FS
        v = amp * math.sin(2 * math.pi * FR * t) + 0.3 * amp * math.sin(2 * math.pi * 2 * FR * t) + 0.2 * g.normal()
        c = 10.0 * math.sin(2 * math.pi * F_SUPPLY * t) + 0.05 * g.normal()
        if faulty:
            tau = (t * FAULT_RATE) % 1.0 / FAULT_RATE          # time since the last burst
            v += 2.0 * math.exp(-DECAY * tau) * math.sin(2 * math.pi * RESONANCE * tau)
            c += 0.3 * (math.sin(2 * math.pi * (F_SUPPLY - FR) * t) + math.sin(2 * math.pi * (F_SUPPLY + FR) * t))
        vib.append(v)
        cur.append(c)
    return vib, cur


def features(x):
    n = len(x)
    mean = sum(x) / n
    rms = math.sqrt(sum(v * v for v in x) / n)
    m2 = sum((v - mean) ** 2 for v in x) / n
    m4 = sum((v - mean) ** 4 for v in x) / n
    peak = max(abs(v) for v in x)
    return {"rms": rms, "peak": peak, "crest": peak / rms, "kurtosis": m4 / (m2 * m2)}


def make():
    g = Rng(SEED)
    rows = []
    for k in range(N_REC):
        faulty = k % 4 == 3                                  # one record in four is faulty
        vib, cur = record(k, faulty)
        fv, fc = features(vib), features(cur)
        temp = round(40 + 8 * g.uniform() + (6 if faulty else 0), 1)
        rows.append({"record_id": f"R{k + 1:03d}", "minute": k, "vib_rms": fv["rms"], "vib_peak": fv["peak"], "vib_crest": fv["crest"],
                     "vib_kurtosis": fv["kurtosis"], "cur_rms": fc["rms"], "temp_c": temp, "unit": "m/s^2", "label": "fault" if faulty else "healthy"})
    for k in (17, 58, 101):                                  # planted: logged in g instead of m/s^2
        for key in ("vib_rms", "vib_peak"):
            rows[k][key] /= G
        rows[k]["unit"] = "g"
    for k in (33, 90):                                       # planted: missing temperature
        rows[k]["temp_c"] = ""
    return rows


def write(path):
    rows = make()
    cols = ["record_id", "minute", "vib_rms", "vib_peak", "vib_crest", "vib_kurtosis", "cur_rms", "temp_c", "unit", "label"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for r in rows:
            w.writerow([f"{r[c]:.4f}" if isinstance(r[c], float) and c != "temp_c" else r[c] for c in cols])
    return len(rows)


if __name__ == "__main__":
    print(write(pathlib.Path(__file__).parent / "out" / "signal_features.csv"), "signal records")
