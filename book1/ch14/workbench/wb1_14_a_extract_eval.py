#!/usr/bin/env python3
"""WB1.14-a  Invoice extractor evaluation.

Two extractors read the 14 invoices in invoices/: a rule-based one (regular expressions written
for one supplier's layout) and a model (replay: answers recorded in replay_extract.jsonl, written
for this book with planted errors).  Each extracted field is compared with invoices_truth.csv
and counted as correct, wrong (a different value), missing (nothing returned) or invented
(a value where the truth is empty).  Then the validation rules run, which need no truth.

Run:  python wb1_14_a_extract_eval.py
      python wb1_14_a_extract_eval.py run config.json   (your own model, via the ch 9 adapter)
"""
import csv
import datetime as dt
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).parent
sys.path.insert(0, str(HERE.parents[1] / "ch09" / "workbench"))
import wb1_9_b_adapter as ad  # noqa: E402

FIELDS = ["invoice_no", "date", "supplier", "net", "vat", "total", "po_number"]
SCHEMA = {   # the schema: field -> (required, pattern the value must match)
    "invoice_no": (True, r"[A-Z]{2}-\d{4}"), "date": (True, r"\d{4}-\d{2}-\d{2}"), "supplier": (True, r".+"),
    "net": (True, r"\d+\.\d{2}"), "vat": (True, r"\d+\.\d{2}"), "total": (True, r"\d+\.\d{2}"),
    "po_number": (False, r"PO-\d{3}"),
}
PO_REGISTER = {"PO-118", "PO-121", "PO-125", "PO-131", "PO-133"}   # orders Alder and Finch actually placed
PROMPT = ("Extract these fields from the invoice below and answer with JSON only: invoice_no, date (YYYY-MM-DD), "
          "supplier, net, vat, total (numbers with two decimals, no thousands separator), po_number (null if absent).\n\n")


def truth():
    return {r["invoice_no"]: r for r in csv.DictReader((HERE / "invoices_truth.csv").open(encoding="utf-8"))}


def docs():
    return {p.stem: p.read_text(encoding="utf-8") for p in sorted((HERE / "invoices").glob("*.txt"))}


def amount(text):
    return f"{float(text.replace(',', '')):.2f}"


def rule_extract(text):
    """Written for the Brightwell layout: 'Label: value' lines, ISO dates, amounts with EUR."""
    out = {"supplier": text.splitlines()[0].strip()}
    pats = {"invoice_no": r"Invoice no: ([A-Z]{2}-\d{4})", "date": r"Date: (\d{4}-\d{2}-\d{2})",
            "po_number": r"Your order: (PO-\d{3})", "net": r"Net amount: ([\d,]+\.\d{2}) EUR",
            "vat": r"VAT 20%: ([\d,]+\.\d{2}) EUR", "total": r"Total: ([\d,]+\.\d{2}) EUR"}
    for f, p in pats.items():
        m = re.search(p, text)
        if m:
            out[f] = amount(m.group(1)) if f in ("net", "vat", "total") else m.group(1)
    return out


class ReplayModel:
    label = "replay demo-model"

    def __init__(self):
        self.b = ad.Replay(HERE / "replay_extract.jsonl", "demo-model")

    def extract(self, inv_no, text):
        return json.loads(self.b.complete(PROMPT + text, {}, inv_no).text)


class LiveModel:
    def __init__(self, cfg):
        self.b, self.label = ad.make_backend(cfg), cfg.get("label", "live")

    def extract(self, inv_no, text):
        raw = self.b.complete(PROMPT + text, {"temperature": 0}).text
        m = re.search(r"\{.*\}", raw, flags=re.S)
        return json.loads(m.group()) if m else {}


def norm(field, v):
    if v is None or str(v).strip() == "":
        return ""
    v = str(v).strip()
    return v.casefold() if field == "supplier" else v


def score(extracted, truth_rows):
    """counts[field][outcome] with outcome in correct, wrong, missing, invented."""
    counts = {f: {"correct": 0, "wrong": 0, "missing": 0, "invented": 0} for f in FIELDS}
    for no, t in truth_rows.items():
        e = extracted.get(no, {})
        for f in FIELDS:
            tv, ev = norm(f, t[f]), norm(f, e.get(f))
            if tv == "" and ev == "":
                continue
            outcome = ("invented" if tv == "" else "missing" if ev == "" else
                       "correct" if ev == tv else "wrong")
            counts[f][outcome] += 1
    return counts


def pr(c):
    returned = c["correct"] + c["wrong"] + c["invented"]
    present = c["correct"] + c["wrong"] + c["missing"]
    return (c["correct"] / returned if returned else float("nan"), c["correct"] / present if present else float("nan"))


def validate(rec):
    """Validation rules: schema, arithmetic, reference data, plausibility.  Return a list of problems."""
    probs = []
    for f, (req, pat) in SCHEMA.items():
        v = norm(f, rec.get(f))
        if v == "":
            if req:
                probs.append(f"{f} missing")
        elif not re.fullmatch(pat, str(rec.get(f)).strip()):
            probs.append(f"{f} '{rec.get(f)}' wrong format")
    try:
        net, vat, total = (float(rec[k]) for k in ("net", "vat", "total"))
        if abs(net + vat - total) > 0.01:
            probs.append(f"net + vat = {net + vat:.2f}, not total {total:.2f}")
        if abs(vat - 0.2 * net) > 0.01:
            probs.append("vat is not 20% of net")
    except (KeyError, TypeError, ValueError):
        pass
    po = norm("po_number", rec.get("po_number"))
    if po and po.upper() not in PO_REGISTER:
        probs.append(f"order {po} not in our order register")
    try:
        d = dt.date.fromisoformat(str(rec.get("date")))
        if not dt.date(2026, 1, 1) <= d <= dt.date(2026, 2, 28):
            probs.append(f"date {d} outside the period")
    except ValueError:
        pass
    return probs


def run(model):
    t, d = truth(), docs()
    results = {"rules": {no: rule_extract(x) for no, x in d.items()},
               "model": {no: model.extract(no, x) for no, x in d.items()}}
    print(f"WB1.14-a  extraction on {len(d)} invoices, {sum(1 for r in t.values() for f in FIELDS if r[f])} true fields")
    print(f"  {'field':<11}{'rules P':>8}{'rules R':>8}{'model P':>9}{'model R':>8}")
    totals = {}
    for f in FIELDS:
        row = f"  {f:<11}"
        for name in ("rules", "model"):
            c = score(results[name], t)[f]
            p, r = pr(c)
            row += f"{p:>8.2f}{r:>8.2f}" if name == "rules" else f"{p:>9.2f}{r:>8.2f}"
        print(row)
    for name in ("rules", "model"):
        cs = score(results[name], t)
        agg = {k: sum(c[k] for c in cs.values()) for k in ("correct", "wrong", "missing", "invented")}
        totals[name] = agg
        p, r = pr(agg)
        print(f"  {name:<6} {agg['correct']} right, {agg['wrong']} wrong, {agg['missing']} missing, "
              f"{agg['invented']} invented: P {p:.3f}, R {r:.3f}")
    print(f"validation rules on the {model.label} output (no truth used):")
    flagged = 0
    for no, rec in results["model"].items():
        probs = validate(rec)
        if probs:
            flagged += 1
            print(f"  {no}  " + "; ".join(probs))
    print(f"  {flagged} of {len(d)} invoices flagged")
    return results, totals


def main():
    if len(sys.argv) >= 3 and sys.argv[1] == "run":
        run(LiveModel(json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))["backend"]))
    else:
        run(ReplayModel())


if __name__ == "__main__":
    main()
