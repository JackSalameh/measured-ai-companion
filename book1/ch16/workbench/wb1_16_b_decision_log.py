#!/usr/bin/env python3
"""WB1.16-b  Decision log checker.

A decision log records each important choice so that someone else can check it later (PR-14).
Columns: id, date, decision, options, evidence, owner, review_by, status, supersedes.
Rules: ids D-nnn, unique; real dates (YYYY-MM-DD); a decision; at least two options considered
(separated by ';'); some evidence (a run, a source-log id, a commit); an owner; a review date
after the decision date; status one of proposed, accepted, rejected, superseded; 'supersedes'
names an existing earlier decision, and a superseded decision is superseded by a later one.

Run:  python wb1_16_b_decision_log.py                 (the example log, with planted problems)
      python wb1_16_b_decision_log.py my_log.csv
"""
import csv
import datetime as dt
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
STATUS = {"proposed", "accepted", "rejected", "superseded"}


def day(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def check(rows):
    probs, ids = [], {}
    for n, r in enumerate(rows, start=2):
        rid = r["id"]
        if not re.fullmatch(r"D-\d{3}", rid):
            probs.append((n, rid, "id must look like D-001"))
        if rid in ids:
            probs.append((n, rid, "duplicate id"))
        ids.setdefault(rid, r)
        d, rv = day(r["date"]), day(r["review_by"])
        if not d:
            probs.append((n, rid, f"date '{r['date']}' is not a real date"))
        if not r["decision"].strip():
            probs.append((n, rid, "no decision stated"))
        if len([o for o in r["options"].split(";") if o.strip()]) < 2:
            probs.append((n, rid, "fewer than two options considered"))
        if not r["evidence"].strip():
            probs.append((n, rid, "no evidence"))
        if not r["owner"].strip():
            probs.append((n, rid, "no owner"))
        if not rv:
            probs.append((n, rid, "review date missing or not real"))
        elif d and rv <= d:
            probs.append((n, rid, "review date is not after the decision"))
        if r["status"] not in STATUS:
            probs.append((n, rid, f"status '{r['status']}' is not one of {', '.join(sorted(STATUS))}"))
    for n, r in enumerate(rows, start=2):
        sup = r["supersedes"].strip()
        if sup and sup not in ids:
            probs.append((n, r["id"], f"supersedes {sup}, which is not in the log"))
        if r["status"] == "superseded" and not any(x["supersedes"].strip() == r["id"] for x in rows):
            probs.append((n, r["id"], "marked superseded, but no decision supersedes it"))
    return sorted(probs)


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "decision_log_example.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    probs = check(rows)
    print(f"WB1.16-b  decision log checker: {len(rows)} decisions")
    for n, rid, msg in probs:
        print(f"  line {n}  {rid}  {msg}")
    print(f"{len(probs)} problems" if probs else "no problems")


if __name__ == "__main__":
    main()
