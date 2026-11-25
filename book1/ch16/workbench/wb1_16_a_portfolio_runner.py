#!/usr/bin/env python3
"""WB1.16-a  Portfolio runner.

Runs the test file of every chapter's Workbench (chapters 1 to 15) with pytest and prints one
table: how many apps each chapter has and how many of its checks pass.  Each test file reruns
the chapter's apps and compares their output with the saved files in its expected/ folder, so a
full row of passes means the chapter reproduces exactly on this computer.

Needs pytest (python -m pip install pytest) and, for chapter 13, Git; numpy for some chapters.
Run from the book folder or anywhere:  python wb1_16_a_portfolio_runner.py
"""
import pathlib
import re
import subprocess
import sys

BOOK = pathlib.Path(__file__).resolve().parents[2]


def run_chapter(wb):
    tests = sorted(wb.glob("test_*.py"))
    out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", *map(str, tests)],
                         capture_output=True, text=True, cwd=wb).stdout
    last = out.strip().splitlines()[-1] if out.strip() else ""
    counts = {k: int(n) for n, k in re.findall(r"(\d+) (passed|failed|skipped|error)", last)}
    return counts


def main():
    rows, total = [], {"apps": 0, "passed": 0, "failed": 0, "skipped": 0, "error": 0}
    for ch in sorted(BOOK.glob("ch[0-9][0-9]")):
        wb = ch / "workbench"
        if ch.name == "ch16" or not wb.is_dir():
            continue
        apps = len(list(wb.glob("wb1_*.py")))
        c = run_chapter(wb)
        rows.append((ch.name, apps, c))
        total["apps"] += apps
        for k in ("passed", "failed", "skipped", "error"):
            total[k] += c.get(k, 0)
    print(f"WB1.16-a  portfolio runner: {len(rows)} chapters")
    print(f"  {'chapter':<9}{'apps':>5}{'passed':>8}{'failed':>8}{'skipped':>9}")
    for name, apps, c in rows:
        print(f"  {name:<9}{apps:>5}{c.get('passed', 0):>8}{c.get('failed', 0) + c.get('error', 0):>8}{c.get('skipped', 0):>9}")
    bad = total["failed"] + total["error"]
    print(f"  {'total':<9}{total['apps']:>5}{total['passed']:>8}{bad:>8}{total['skipped']:>9}")
    print("all chapters reproduce" if bad == 0 else f"{bad} checks fail: rerun that chapter's tests to see which")
    return bad


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
