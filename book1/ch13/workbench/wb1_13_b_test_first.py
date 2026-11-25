#!/usr/bin/env python3
"""WB1.13-b  Test first.

The tests in spec_parse_amount.py define parse_amount.  This app runs them against two
implementations: A, the kind of one-line answer a coding assistant often gives first, and
B, a version written to pass every test.  Both are in this file so you can read them.
The tests decide, not the look of the code.

Run:  python wb1_13_b_test_first.py            (both candidates)
      python wb1_13_b_test_first.py mymodule   (your own parse_amount in mymodule.py)
"""
import importlib
import re
import sys

import spec_parse_amount as spec


def candidate_a(text):
    """First attempt: remove the commas and convert."""
    return float(text.replace(",", ""))


def candidate_b(text):
    """Written against the tests: brackets mean negative, an optional 3-letter currency code."""
    t = text.strip().replace(",", "")
    negative = t.startswith("(") and t.endswith(")")
    if negative:
        t = t[1:-1]
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)(?: [A-Z]{3})?", t)
    if not m:
        raise ValueError(f"not an amount: {text!r}")
    value = float(m.group(1))
    return -value if negative else value


def run(impl):
    """Run every test; return a list of (test name, passed, reason)."""
    results = []
    for test in spec.TESTS:
        try:
            test(impl)
            results.append((test.__name__, True, ""))
        except AssertionError as e:
            results.append((test.__name__, False, str(e) or "wrong value"))
        except Exception as e:  # the implementation itself crashed
            results.append((test.__name__, False, f"{type(e).__name__}"))
    return results


def report(label, results):
    passed = sum(ok for _, ok, _ in results)
    print(f"  {label}: {passed} of {len(results)} tests pass")
    for name, ok, why in results:
        if not ok:
            print(f"    FAIL {name:<26}{why}")
    return passed == len(results)


def main():
    print(f"WB1.13-b  test first: {len(spec.TESTS)} tests for parse_amount")
    if len(sys.argv) > 1:
        mod = importlib.import_module(sys.argv[1])
        report(sys.argv[1], run(mod.parse_amount))
        return
    report("candidate A", run(candidate_a))
    report("candidate B", run(candidate_b))


if __name__ == "__main__":
    main()
