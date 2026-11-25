"""P3 Ledger Analytics Assistant: seeded generator of a fictional company's double-entry ledger for 2026.
Company: Alder and Finch Trading (fictional). Output: out/ledger.csv, one row per journal line.
Planted for chapter 3: one transaction entered twice, three missing descriptions, one impossible date."""
import csv
import datetime as dt
import pathlib

from rng import Rng

SEED, N_TX, YEAR = 3301, 360, 2026
ACCOUNTS = {"1000": "Bank", "1200": "Accounts receivable", "2000": "Accounts payable", "4000": "Sales",
            "5000": "Purchases", "6100": "Rent", "6200": "Salaries", "6300": "Utilities", "6400": "Travel"}
TYPES = [  # (description, debit account, credit account, amount range in EUR, weight)
    ("Sale on credit", "1200", "4000", (200, 4800), 0.30), ("Customer payment received", "1000", "1200", (200, 4800), 0.22),
    ("Purchase of goods on credit", "5000", "2000", (150, 3500), 0.18), ("Supplier payment", "2000", "1000", (150, 3500), 0.14),
    ("Office rent", "6100", "1000", (2400, 2400), 0.04), ("Salaries", "6200", "1000", (9000, 11000), 0.04),
    ("Electricity and water", "6300", "1000", (180, 420), 0.04), ("Travel expenses", "6400", "1000", (60, 900), 0.04)]


def make():
    g = Rng(SEED)
    lines, tx = [], []
    for i in range(N_TX):
        desc, dr, cr, (lo, hi), _ = g.weighted(TYPES, [t[4] for t in TYPES])
        amount = round(g.uniform(lo, hi), 2) if hi > lo else float(lo)
        date = dt.date(YEAR, 1, 1) + dt.timedelta(days=g.index(365))
        tx.append([date.isoformat(), desc, dr, cr, amount])
    tx.sort(key=lambda t: t[0])
    tx.insert(100, list(tx[99]))                       # planted: the same transaction entered twice
    for k in (40, 180, 300):                           # planted: missing descriptions
        tx[k][1] = ""
    tx[222][0] = f"{YEAR}-02-30"                       # planted: impossible date
    for n, (date, desc, dr, cr, amount) in enumerate(tx, 1):
        tid = f"J{n:04d}"
        lines.append([tid, date, dr, ACCOUNTS[dr], desc, f"{amount:.2f}", "0.00", "EUR"])
        lines.append([tid, date, cr, ACCOUNTS[cr], desc, "0.00", f"{amount:.2f}", "EUR"])
    return lines


def write(path):
    lines = make()
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["entry_id", "date", "account", "account_name", "description", "debit", "credit", "currency"])
        w.writerows(lines)
    return len(lines)


if __name__ == "__main__":
    print(write(pathlib.Path(__file__).parent / "out" / "ledger.csv"), "ledger lines")
