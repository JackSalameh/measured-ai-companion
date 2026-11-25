"""Tests that specify parse_amount, written before any implementation (WB1.13-b).

parse_amount(text) reads an amount as it appears in the P3 ledger exports and returns a float.
Each test is one requirement.  `impl` is the function under test.
"""


def test_plain(impl):
    assert impl("250.00") == 250.0


def test_thousands(impl):
    assert impl("1,601.98") == 1601.98


def test_minus(impl):
    assert impl("-75.50") == -75.5


def test_brackets_negative(impl):
    # accounting style: (75.50) means minus 75.50
    assert impl("(75.50)") == -75.5


def test_currency_code(impl):
    assert impl("1,601.98 EUR") == 1601.98


def test_spaces(impl):
    assert impl("  42.10 ") == 42.1


def test_empty_rejected(impl):
    try:
        impl("")
    except ValueError:
        return
    raise AssertionError("empty text must raise ValueError")


def test_two_points_rejected(impl):
    try:
        impl("12.3.4")
    except ValueError:
        return
    raise AssertionError("'12.3.4' must raise ValueError")


TESTS = [f for name, f in list(globals().items()) if name.startswith("test_")]   # in the order written
