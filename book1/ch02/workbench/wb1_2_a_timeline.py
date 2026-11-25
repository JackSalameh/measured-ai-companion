"""WB1.2-a  Timeline builder

Reads milestones.csv (date, year, milestone, idea, ledger) and draws a timeline as SVG.
It refuses to draw if any row has no ledger ID: a date without a source is not printed.
Run:  python wb1_2_a_timeline.py            (reads milestones.csv, writes timeline.svg)
      python wb1_2_a_timeline.py my.csv     (reads another file, for example your own copy)
"""
import csv
import pathlib
import sys

HERE = pathlib.Path(__file__).parent


def load(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    bad = [r for r in rows if not r["ledger"].strip().startswith("L-")]
    if bad:
        sys.exit("rows without a source ID: " + "; ".join(r["milestone"] for r in bad))
    years = [int(r["year"]) for r in rows]
    if years != sorted(years):
        sys.exit("rows are not in date order")
    return rows


def svg(rows, width=900, row_h=34):
    y0, y1 = int(rows[0]["year"]), int(rows[-1]["year"])
    x = lambda yr: 60 + (width - 120) * (yr - y0) / (y1 - y0)
    h = 70 + row_h * len(rows)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{h}" font-family="serif" font-size="12">',
           f'<line x1="{x(y0)}" y1="40" x2="{x(y1)}" y2="40" stroke="#0F3D5E" stroke-width="2"/>']
    for dec in range((y0 // 10 + 1) * 10, y1 + 1, 10):
        out.append(f'<text x="{x(dec)}" y="30" text-anchor="middle" fill="#6B7280">{dec}</text>')
    for i, r in enumerate(rows):
        yr, ty = int(r["year"]), 70 + row_h * i
        out.append(f'<circle cx="{x(yr):.1f}" cy="40" r="4" fill="#1D6FA5"/>')
        out.append(f'<line x1="{x(yr):.1f}" y1="44" x2="{x(yr):.1f}" y2="{ty - 12}" stroke="#D1D5DB"/>')
        anchor = "start" if x(yr) < width / 2 else "end"
        out.append(f'<text x="{x(yr):.1f}" y="{ty}" text-anchor="{anchor}">{r["date"]}  {r["milestone"]} [{r["ledger"]}]</text>')
    out.append("</svg>")
    return "\n".join(out)


def main(argv=()):
    src = pathlib.Path(argv[0]) if argv else HERE / "milestones.csv"
    rows = load(src)
    (HERE / "timeline.svg").write_text(svg(rows), encoding="utf-8")
    print("WB1.2-a  Timeline builder")
    print(f"{len(rows)} milestones from {rows[0]['year']} to {rows[-1]['year']}, every row has a source ID")
    gaps = [(int(b["year"]) - int(a["year"]), a["year"], b["year"]) for a, b in zip(rows, rows[1:])]
    g = max(gaps)
    print(f"longest gap between listed milestones: {g[0]} years ({g[1]} to {g[2]})")
    print("wrote timeline.svg")


if __name__ == "__main__":
    main(sys.argv[1:])
