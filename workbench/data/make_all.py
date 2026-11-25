"""Regenerate every data file of the series and write checksums. Run: python make_all.py"""
import hashlib
import pathlib

import gen_ledger
import gen_signals
import gen_tickets

OUT = pathlib.Path(__file__).parent / "out"
OUT.mkdir(exist_ok=True)
counts = {"tickets.csv": gen_tickets.write(OUT / "tickets.csv"), "ledger.csv": gen_ledger.write(OUT / "ledger.csv"),
          "signal_features.csv": gen_signals.write(OUT / "signal_features.csv")}
with open(OUT / "checksums.sha256", "w") as f:
    for name in counts:
        f.write(f"{hashlib.sha256((OUT / name).read_bytes()).hexdigest()}  {name}\n")
for k, v in counts.items():
    print(f"{k}: {v} rows")
