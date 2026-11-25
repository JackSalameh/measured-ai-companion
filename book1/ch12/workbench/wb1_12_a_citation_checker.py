"""WB1.12-a  Citation checker.

Checks each reference in a list in two steps:
  1. syntax: DOI (prefix 10.NNNN/suffix), arXiv (YYMM.NNNN or YYMM.NNNNN since 2007), ISBN-13 check digit
  2. match: is the identifier in your local library, and do the year and title agree with it?
A reference that is not in the library is NOT proven false: look it up at its source.

  python wb1_12_a_citation_checker.py                       bundled list (constructed, with planted errors)
  python wb1_12_a_citation_checker.py refs.csv library.csv  your own files (same columns)
"""
import csv
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
DOI = re.compile(r"^10\.\d{4,9}/\S+$")
ARXIV = re.compile(r"^(\d{2})(\d{2})\.(\d{4,5})(v\d+)?$")


def doi_ok(s):
    return bool(DOI.match(s))


def arxiv_ok(s):
    m = ARXIV.match(s)
    if not m:
        return False
    yy, mm, num = int(m.group(1)), int(m.group(2)), m.group(3)
    if not 1 <= mm <= 12 or (yy, mm) < (7, 4):
        return False
    return len(num) == (5 if (yy, mm) >= (15, 1) else 4)


def isbn13_ok(s):
    d = re.sub(r"[-\s]", "", s)
    if not re.fullmatch(r"\d{13}", d):
        return False
    return sum(int(c) * (1 if i % 2 == 0 else 3) for i, c in enumerate(d)) % 10 == 0


def words(t):
    return set(re.findall(r"[a-z0-9]+", t.lower()))


def similar(a, b):
    wa, wb = words(a), words(b)
    return len(wa & wb) / len(wa | wb) if wa | wb else 0.0


def check(ref, library):
    ids = [(k, ref[k].strip()) for k in ("doi", "arxiv", "isbn") if ref[k].strip()]
    if not ids:
        return "NO ID", "no identifier: search for the title at a library or index"
    for kind, val in ids:
        if not {"doi": doi_ok, "arxiv": arxiv_ok, "isbn": isbn13_ok}[kind](val):
            return "SYNTAX", f"{kind} {val} is not a valid {kind}"
    for kind, val in ids:
        hit = [w for w in library if w[kind].strip().lower() == val.lower()]
        if hit:
            w = hit[0]
            problems = []
            if ref["year"] != w["year"]:
                problems.append(f"year {ref['year']} vs {w['year']}")
            if similar(ref["title"], w["title"]) < 0.8:
                problems.append(f"title differs from '{w['title']}'")
            if problems:
                return "MISMATCH", f"{kind} found ({w['key']}): " + "; ".join(problems)
            return "OK", f"{kind} found ({w['key']})"
    return "NOT FOUND", "valid identifier, not in the library: open it at its source"


def main(refs_path, lib_path):
    refs = list(csv.DictReader(open(refs_path, encoding="utf-8")))
    library = list(csv.DictReader(open(lib_path, encoding="utf-8")))
    print(f"WB1.12-a  citation checker: {len(refs)} references, library of {len(library)} works")
    counts = {}
    for r in refs:
        verdict, note = check(r, library)
        counts[verdict] = counts.get(verdict, 0) + 1
        print(f"  {r['id']:<4}{verdict:<10}{note}")
    print(", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        main(HERE / "report_references.csv", HERE / "library.csv")
