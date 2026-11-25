"""Check that out/ matches what the generators produce now. Exit code 1 on any mismatch."""
import hashlib
import pathlib
import sys
import tempfile

import gen_ledger
import gen_signals
import gen_tickets

OUT = pathlib.Path(__file__).parent / "out"
expected = {l.split()[1]: l.split()[0] for l in (OUT / "checksums.sha256").read_text().splitlines()}
ok = True
with tempfile.TemporaryDirectory() as d:
    for name, mod in (("tickets.csv", gen_tickets), ("ledger.csv", gen_ledger), ("signal_features.csv", gen_signals)):
        p = pathlib.Path(d) / name
        mod.write(p)
        new = hashlib.sha256(p.read_bytes()).hexdigest()
        same = new == expected[name] == hashlib.sha256((OUT / name).read_bytes()).hexdigest()
        ok &= same
        print(f"{name:<22} {'OK' if same else 'MISMATCH'}")
sys.exit(0 if ok else 1)
