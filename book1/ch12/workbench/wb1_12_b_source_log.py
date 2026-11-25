"""WB1.12-b  Source log checker.

A source log has one row per claim you rely on: id, claim, source, checked (date), status, used_in.
Status codes, as in this book's own ledger: V verified at the source; V-sec seen only in secondary
sources; P pending; X found wrong. The checker enforces the rules that keep a log trustworthy.

  python wb1_12_b_source_log.py               bundled example (with planted problems)
  python wb1_12_b_source_log.py my_log.csv    your own log; dates may not be later than today
"""
import csv
import datetime as dt
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
STATUS = {"V", "V-sec", "P", "X"}
COLUMNS = ["id", "claim", "source", "checked", "status", "used_in"]


def problems(rows, today):
    out, seen = [], set()
    for n, r in enumerate(rows, start=2):                      # line 1 is the header
        rid = r["id"]
        if not re.fullmatch(r"S-\d{3}", rid):
            out.append((n, rid, "id must look like S-001"))
        if rid in seen:
            out.append((n, rid, "duplicate id"))
        seen.add(rid)
        if r["status"] not in STATUS:
            out.append((n, rid, f"status '{r['status']}' is not one of V, V-sec, P, X"))
        if r["status"] in ("V", "V-sec") and not r["source"].strip():
            out.append((n, rid, "marked verified but no source given"))
        try:
            d = dt.date.fromisoformat(r["checked"])
            if d > today:
                out.append((n, rid, f"checked date {d} is in the future"))
        except ValueError:
            out.append((n, rid, f"checked date '{r['checked']}' is not a real date (YYYY-MM-DD)"))
        if r["status"] == "X" and r["used_in"].strip():
            out.append((n, rid, f"found wrong (X) but still used in {r['used_in']}"))
    return out


def main(path, today):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    missing = [c for c in COLUMNS if c not in (rows[0].keys() if rows else [])]
    print(f"WB1.12-b  source log checker: {len(rows)} rows, checked against {today}")
    if missing:
        print("missing columns:", ", ".join(missing))
        return
    found = problems(rows, today)
    for line, rid, msg in found:
        print(f"  line {line:<3}{rid:<7}{msg}")
    print(f"{len(found)} problems" if found else "no problems")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1], dt.date.today())
    else:
        main(HERE / "source_log_example.csv", dt.date(2026, 11, 25))   # fixed date: the output never changes
