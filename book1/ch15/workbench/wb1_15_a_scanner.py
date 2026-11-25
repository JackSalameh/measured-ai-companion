#!/usr/bin/env python3
"""WB1.15-a  Sensitive-data scanner.

Finds and redacts e-mail addresses, phone numbers, IBAN-like account numbers and card numbers
(16 digits passing the Luhn check) in a text before it is sent to a model.  The demo text is a
fictional support ticket written for this book; every person and address is invented.
The numbers cannot reach anyone: the phone number is in a range Ofcom reserves for drama, the
account number has check digits 00, which no valid IBAN has, and the card number is a public
test number from Stripe's documentation.
The answer key lists every sensitive item a careful person would remove, so the app can also
show what the patterns MISS.

Run:  python wb1_15_a_scanner.py            (demo with the answer key)
      python wb1_15_a_scanner.py file.txt   (scan your own text; prints the redacted version)
"""
import pathlib
import re
import sys

TICKET = """Ticket 4471, from marta.kowalski@example.org
Hello, my name is Marta Kowalski; I was charged twice for order 88213.
Please refund to IBAN DE00 1234 5678 9012 3456 78
or call me on +44 20 7946 0123.
The card I used was 4242 4242 4242 4242, expiring 12/34.
I live at 14 Linden Street, Westford. My colleague Tom
(tom dot reyes at example dot org) had the same problem;
his number is oh-seven-seven, nine-one-two, three-four-five-six.
"""
# what a careful person would remove (the answer key)
SENSITIVE = ["marta.kowalski@example.org", "Marta Kowalski", "DE00 1234 5678 9012 3456 78",
             "+44 20 7946 0123", "4242 4242 4242 4242", "12/34", "14 Linden Street, Westford",
             "Tom", "tom dot reyes at example dot org", "oh-seven-seven, nine-one-two, three-four-five-six"]

PATTERNS = [
    ("EMAIL", r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"),
    ("IBAN", r"\b[A-Z]{2}\d{2}(?: ?[A-Z0-9]{4}){3,7}(?: ?[A-Z0-9]{1,3})?\b"),
    ("CARD", r"\b(?:\d[ -]?){15}\d\b"),
    ("PHONE", r"\+\d{1,3}(?:[ -]?\d{2,4}){2,4}\b"),
]


def luhn_ok(number):
    digits = [int(c) for c in number if c.isdigit()][::-1]
    total = sum(d if i % 2 == 0 else (d * 2 - 9 if d * 2 > 9 else d * 2) for i, d in enumerate(digits))
    return total % 10 == 0


def scan(text):
    """Return a list of (kind, start, end, matched text), earlier patterns taking priority."""
    found, taken = [], []
    for kind, pat in PATTERNS:
        for m in re.finditer(pat, text):
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            if kind == "CARD" and not luhn_ok(m.group()):
                continue
            found.append((kind, m.start(), m.end(), m.group()))
            taken.append((m.start(), m.end()))
    return sorted(found, key=lambda f: f[1])


def redact(text, found):
    out, last = [], 0
    for kind, s, e, _ in found:
        out += [text[last:s], f"[{kind}]"]
        last = e
    return "".join(out + [text[last:]])


def main():
    text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8") if len(sys.argv) > 1 else TICKET
    found = scan(text)
    print(f"WB1.15-a  sensitive-data scanner: {len(found)} items found")
    for kind, _, _, t in found:
        print(f"  {kind:<6}{t}")
    print("redacted text:")
    for line in redact(text, found).rstrip("\n").split("\n"):
        print("  " + line)
    if len(sys.argv) == 1:
        hits = [s for s in SENSITIVE if any(s in t or t in s for _, _, _, t in found)]
        missed = [s for s in SENSITIVE if s not in hits]
        print(f"answer key: {len(hits)} of {len(SENSITIVE)} sensitive items caught; missed:")
        for s in missed:
            print(f"  {s}")


if __name__ == "__main__":
    main()
