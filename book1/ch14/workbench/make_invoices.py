#!/usr/bin/env python3
"""Writes the chapter 14 teaching documents: 14 fictional supplier invoices to Alder and Finch
Trading for January and February 2026, as the text a PDF or an OCR engine would give.

invoices_truth.csv  the correct value of every field (the ground truth)
invoices/*.txt      the documents, in two supplier layouts; one is a noisy scan

The invoices were written for this book to match the P3 ledger (workbench/data/out/ledger.csv),
with differences planted for chapter 14: one invoice not in the ledger, one ledger purchase with
no invoice, one amount whose digits were swapped when it was booked. Tax is a flat 20% rate
chosen for the exercise. All companies are fictional.
Run: python make_invoices.py   (rewrites the files; output is the same every time)
"""
import csv
import pathlib

HERE = pathlib.Path(__file__).parent
ADDRESS = {"BW": "Mill Lane 4, Westford", "OT": "Weavers Yard 9, Eastbury", "KM": "Hafenstrasse 12, Nordhaven"}
SUPPLIERS = {"BW": "Brightwell Supplies Ltd", "KM": "Kestrel Metals GmbH", "OT": "Orchard Textiles Ltd"}
# invoice number, invoice date, total in EUR, purchase-order number ('' if none)
ROWS = [
    ("BW-2601", "2026-01-02", 1557.20, "PO-118"), ("KM-0447", "2026-01-02", 3129.85, ""),
    ("BW-2614", "2026-01-16", 3014.08, "PO-121"), ("OT-9002", "2026-01-22", 2471.17, ""),
    ("KM-0461", "2026-01-23", 1116.53, "PO-125"), ("BW-2630", "2026-01-30", 488.17, ""),
    ("OT-9015", "2026-01-31", 403.97, ""), ("KM-0472", "2026-01-30", 1596.56, ""),
    ("OT-9021", "2026-02-02", 2175.37, ""), ("BW-2649", "2026-02-06", 2073.28, "PO-131"),
    ("KM-0490", "2026-02-12", 742.50, "PO-133"), ("OT-9040", "2026-02-19", 2883.82, ""),
    ("BW-2661", "2026-02-24", 2997.24, ""), ("KM-0503", "2026-02-26", 1653.65, ""),
]
FIELDS = ["invoice_no", "date", "supplier", "net", "vat", "total", "po_number"]
SCANNED = "OT-9040"     # this one arrives as a poor scan: OCR confuses O/0 and l/1


def money(x):
    return f"{x:,.2f}"


def truth():
    out = []
    for no, date, total, po in ROWS:
        net = round(total / 1.2, 2)
        vat = round(total - net, 2)
        out.append({"invoice_no": no, "date": date, "supplier": SUPPLIERS[no[:2]], "net": f"{net:.2f}",
                    "vat": f"{vat:.2f}", "total": f"{total:.2f}", "po_number": po})
    return out


def layout_a(r):            # Brightwell and Orchard
    lines = [r["supplier"].upper(), ADDRESS[r["invoice_no"][:2]], "", "To: Alder and Finch Trading", "",
             f"Invoice no: {r['invoice_no']}", f"Date: {r['date']}"]
    if r["po_number"]:
        lines.append(f"Your order: {r['po_number']}")
    lines += ["", "Goods as per delivery note", "",
              f"Net amount: {money(float(r['net']))} EUR", f"VAT 20%: {money(float(r['vat']))} EUR",
              f"Total: {money(float(r['total']))} EUR", "", "Payment within 30 days."]
    return "\n".join(lines) + "\n"


def layout_b(r):            # Kestrel: day/month/year dates and other labels
    y, m, d = r["date"].split("-")
    lines = [r["supplier"], ADDRESS[r["invoice_no"][:2]], "",
             f"Invoice # {r['invoice_no']}    Issued {d}/{m}/{y}"]
    if r["po_number"]:
        lines.append(f"Order ref. {r['po_number']}")
    lines += ["Customer: Alder and Finch Trading", "",
              f"Subtotal        {money(float(r['net']))}", f"Tax (20%)       {money(float(r['vat']))}",
              f"Amount due EUR  {money(float(r['total']))}", "", "Thank you for your business."]
    return "\n".join(lines) + "\n"


def scan_noise(text):
    return text.replace("Date: 2026-02-19", "Date: 2026-O2-19").replace("Total: 2,883.82", "Tota1: 2,883.82")


def main():
    rows = truth()
    with (HERE / "invoices_truth.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        text = layout_b(r) if r["invoice_no"].startswith("KM") else layout_a(r)
        if r["invoice_no"] == SCANNED:
            text = scan_noise(text)
        (HERE / "invoices" / f"{r['invoice_no']}.txt").write_text(text, encoding="utf-8", newline="\n")
    print(f"wrote invoices_truth.csv and {len(rows)} documents")


if __name__ == "__main__":
    main()
