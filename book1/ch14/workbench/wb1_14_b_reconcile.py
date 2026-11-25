#!/usr/bin/env python3
"""WB1.14-b  Reconcile invoices with the ledger.

Compares the invoice totals for January and February 2026 with the purchases booked in the P3
ledger (account 5000).  A pair matches when the amounts are equal and the booking date is 0 to 5
days after the invoice date.  Everything else is reported: amounts that match but dates that do
not, amounts that differ by a multiple of 9 (the mark of two swapped digits), invoices with no
booking, and bookings with no invoice.

Run:  python wb1_14_b_reconcile.py           reconcile the true invoice values, then the model's
"""
import csv
import datetime as dt
import json
import pathlib

HERE = pathlib.Path(__file__).parent
LEDGER = next(p for p in HERE.resolve().parents if (p / "workbench" / "data").is_dir()) / "workbench" / "data" / "out" / "ledger.csv"
WINDOW = 5


def date(s):
    try:
        return dt.date.fromisoformat(s)
    except ValueError:
        return None


def ledger_purchases():
    rows = []
    for r in csv.DictReader(LEDGER.open(encoding="utf-8")):
        if r["account"] == "5000" and "2026-01-01" <= r["date"] <= "2026-02-31":
            rows.append({"id": r["entry_id"], "date": r["date"], "amount": round(float(r["debit"]), 2)})
    return rows


def swapped_digits(a, b):
    """True when b is a with two adjacent digits exchanged."""
    x, y = f"{a:.2f}", f"{b:.2f}"
    if len(x) != len(y) or x == y:
        return False
    diff = [i for i in range(len(x)) if x[i] != y[i]]
    return len(diff) == 2 and diff[1] == diff[0] + 1 and x[diff[0]] == y[diff[1]] and x[diff[1]] == y[diff[0]]


def reconcile(invoices, ledger):
    open_l = list(ledger)
    report, matched = [], 0
    for inv in sorted(invoices, key=lambda r: (r["date"], r["invoice_no"])):
        amt, d = round(float(inv["total"]), 2), date(inv["date"])
        same = [l for l in open_l if l["amount"] == amt]
        ok = [l for l in same if date(l["date"]) and d and 0 <= (date(l["date"]) - d).days <= WINDOW]
        if ok:
            open_l.remove(ok[0])
            matched += 1
            continue
        if same:
            l = same[0]
            open_l.remove(l)
            why = "ledger date not real" if not date(l["date"]) else f"booked {l['date']}"
            report.append(f"  {inv['invoice_no']}  {amt:>9,.2f}  same amount as {l['id']}, {why}")
            continue
        near = [l for l in open_l if d and date(l["date"]) and abs((date(l["date"]) - d).days) <= WINDOW
                and swapped_digits(amt, l["amount"])]
        if near:
            l = near[0]
            open_l.remove(l)
            diff = amt - l["amount"]
            report.append(f"  {inv['invoice_no']}  {amt:>9,.2f}  {l['id']} has {l['amount']:,.2f}: "
                          f"{diff:.2f} = 9 x {diff / 9:.2f}, swapped")
            continue
        report.append(f"  {inv['invoice_no']}  {amt:>9,.2f}  no booking found")
    for l in open_l:
        report.append(f"  {l['id']:<8} {l['amount']:>9,.2f}  booked {l['date']}, no invoice")
    return matched, report


def show(label, invoices, ledger):
    matched, report = reconcile(invoices, ledger)
    print(f"{label}: {len(invoices)} invoices, {len(ledger)} ledger purchases, {matched} matched")
    for line in report:
        print(line)


def main():
    ledger = ledger_purchases()
    truth = list(csv.DictReader((HERE / "invoices_truth.csv").open(encoding="utf-8")))
    model = [json.loads(json.loads(l)["text"]) for l in (HERE / "replay_extract.jsonl").read_text(encoding="utf-8").splitlines()]
    print("WB1.14-b  reconciliation with the ledger, January and February 2026")
    show("true invoice values", truth, ledger)
    show("model values", model, ledger)


if __name__ == "__main__":
    main()
