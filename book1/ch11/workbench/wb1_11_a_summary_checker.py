"""WB1.11-a  Ledger summary checker.

Recomputes facts from the ledger (the ground truth) and checks every claim of a summary against them.
Each claim names the fact it states and the value it gives; a claim that names no fact cannot be
checked from the ledger and is listed for a person to check against its source.

  python wb1_11_a_summary_checker.py                  the bundled summary (constructed, with planted errors)
  python wb1_11_a_summary_checker.py my_claims.csv    your own claims file (same columns)
"""
import collections
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = next(p for p in HERE.resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data" / "out" / "ledger.csv"
QUARTERS = {f"q{i}": [f"{m:02d}" for m in range(3 * i - 2, 3 * i + 1)] for i in (1, 2, 3, 4)}


def load(path=LEDGER):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def total(rows, account, side, months=None):
    return round(sum(float(r[side]) for r in rows
                     if r["account"] == account and (months is None or r["date"][5:7] in months)), 2)


def issues(rows):
    """Data-quality problems a faithful summary should not hide."""
    entries = collections.OrderedDict()
    for r in rows:
        entries.setdefault(r["entry_id"], []).append(r)
    sig = [tuple((r["date"], r["account"], r["debit"], r["credit"], r["description"]) for r in e)
           for e in entries.values()]
    ids = list(entries)
    dup = [ids[i] for i in range(1, len(sig)) if sig[i] == sig[i - 1]]
    blank = sorted({r["entry_id"] for r in rows if not r["description"].strip()})
    bad = []
    for eid, e in entries.items():
        y, m, d = (int(x) for x in e[0]["date"].split("-"))
        if d > [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31][m - 1]:
            bad.append(eid)
    return {"duplicate": dup, "no description": blank, "impossible date": bad}


def facts(rows):
    f = {"sales.year": total(rows, "4000", "credit"),
         "purchases.year": total(rows, "5000", "debit"),
         "rent.year": total(rows, "6100", "debit"),
         "travel.h1": total(rows, "6400", "debit", [f"{m:02d}" for m in range(1, 7)]),
         "travel.h2": total(rows, "6400", "debit", [f"{m:02d}" for m in range(7, 13)])}
    for q, months in QUARTERS.items():
        f[f"sales.{q}"] = total(rows, "4000", "credit", months)
    qs = [f[f"sales.q{i}"] for i in (1, 2, 3, 4)]
    f["sales.grew.every.quarter"] = "yes" if all(b > a for a, b in zip(qs, qs[1:])) else "no"
    f["sales.best.quarter"] = "q" + str(1 + qs.index(max(qs)))
    best = max((float(r["credit"]), r["date"]) for r in rows if r["account"] == "4000")
    f["sale.largest"], f["sale.largest.date"] = round(best[0], 2), best[1]
    f["travel.change.pct"] = round(100 * (f["travel.h2"] - f["travel.h1"]) / f["travel.h1"], 1)
    f["issues.count"] = sum(len(v) for v in issues(rows).values())
    return f


def same(stated, true):
    try:
        return abs(float(stated) - float(true)) < 0.005
    except ValueError:
        return stated.strip().lower() == str(true).lower()


def check(claims, f):
    out = []
    for c in claims:
        if not c["fact"]:
            out.append((c["id"], "SOURCE", "no ground truth in the ledger: check by hand"))
        elif same(c["value"], f[c["fact"]]):
            out.append((c["id"], "OK", f"{c['fact']} = {f[c['fact']]}"))
        else:
            out.append((c["id"], "WRONG", f"{c['fact']}: stated {c['value']}, ledger {f[c['fact']]}"))
    return out


def main(path):
    rows = load()
    f = facts(rows)
    claims = list(csv.DictReader(open(path, encoding="utf-8")))
    print(f"WB1.11-a  summary checker: {len(claims)} claims, ledger {len(rows)} lines")
    res = check(claims, f)
    for cid, verdict, note in res:
        print(f"  {cid:<4}{verdict:<8}{note}")
    n = collections.Counter(v for _, v, _ in res)
    print(f"ok {n['OK']}, wrong {n['WRONG']}, to check by hand {n['SOURCE']}")
    print("issues in the ledger:")
    for kind, ids in issues(rows).items():
        print(f"  {kind:<16}{', '.join(ids)}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else HERE / "summary_claims.csv")
