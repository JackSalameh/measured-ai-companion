"""WB1.3-a  Dataset inspector

Profiles any CSV file: the type of each column, missing values, distinct values, ranges,
impossible dates, mixed units and duplicate rows (ignoring the first column, the record ID).
Run:  python wb1_3_a_inspector.py FILE.csv
      python wb1_3_a_inspector.py            (inspects the three series datasets)
"""
import csv
import datetime as dt
import pathlib
import re
import sys

DATA = next(p for p in pathlib.Path(__file__).resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data" / "out"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def kind(values):
    vals = [v for v in values if v != ""]
    if not vals:
        return "empty"
    if all(re.fullmatch(r"-?\d+", v) for v in vals):
        return "integer"
    if all(re.fullmatch(r"-?\d+(\.\d+)?", v) for v in vals):
        return "decimal"
    if all(DATE.match(v) for v in vals):
        return "date"
    return "category" if len(set(vals)) <= 20 else "text"


def valid_date(v):
    try:
        dt.date.fromisoformat(v)
        return True
    except ValueError:
        return False


def inspect(path):
    rows = list(csv.reader(open(path, encoding="utf-8")))
    head, body = rows[0], rows[1:]
    print(f"== {pathlib.Path(path).name}: {len(body)} rows, {len(head)} columns")
    for j, name in enumerate(head):
        col = [r[j] for r in body]
        k = kind(col)
        missing = sum(1 for v in col if v == "")
        vals = [v for v in col if v != ""]
        line = f"  {name:<14} {k:<9} missing {missing:>3}   distinct {len(set(vals)):>4}"
        if k in ("integer", "decimal"):
            nums = [float(v) for v in vals]
            line += f"   min {min(nums):g}   max {max(nums):g}"
        if k == "date":
            bad = sorted(set(v for v in vals if not valid_date(v)))
            ok = [v for v in vals if valid_date(v)]
            line += f"   {min(ok)} to {max(ok)}" + (f"   IMPOSSIBLE: {', '.join(bad)}" if bad else "")
        if k == "category" and len(set(vals)) <= 6:
            line += "   values " + ", ".join(sorted(set(vals)))
        print(line)
    if "unit" in head:
        units = sorted(set(r[head.index("unit")] for r in body))
        if len(units) > 1:
            print(f"  WARNING mixed units in one column: {', '.join(units)}")
    seen, dups = {}, 0
    for r in body:
        key = tuple(r[1:])
        dups += key in seen
        seen[key] = True
    print(f"  duplicate rows (all columns except {head[0]}): {dups}")


if __name__ == "__main__":
    files = sys.argv[1:] or [DATA / "tickets.csv", DATA / "ledger.csv", DATA / "signal_features.csv"]
    print("WB1.3-a  Dataset inspector")
    for f in files:
        inspect(f)
