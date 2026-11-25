import hashlib
import io
import pathlib
from contextlib import redirect_stdout

import pytest

import wb1_1_a_rules_or_learning as wa
import wb1_1_b_model_is_function as wb

HERE = pathlib.Path(__file__).parent


def captured(module):
    buf = io.StringIO()
    with redirect_stdout(buf):
        module.main()
    return buf.getvalue()


def test_ticket_counts_and_labels():
    assert len(wa.TICKETS) == 40 and len(wa.HELD_OUT) == 10
    for label in ("billing", "login", "shipping", "other"):
        assert sum(l == label for _, l in wa.TICKETS) == 10
    assert not {t for t, _ in wa.TICKETS} & {t for t, _ in wa.HELD_OUT}


def test_rule_router_numbers():
    assert len(wa.RULES_V1) == 6 and len(wa.RULES_V2) == 26
    assert wa.accuracy(wa.TICKETS, wa.RULES_V1) == (21, 40)
    assert wa.accuracy(wa.TICKETS, wa.RULES_V2) == (40, 40)
    assert wa.accuracy(wa.HELD_OUT, wa.RULES_V2) == (6, 10)


def test_least_squares_methods_agree():
    ys = wb.noisy_data()
    a1, b1 = wb.fit_closed_form(wb.XS, ys)
    a2, b2 = wb.fit_gradient_descent(wb.XS, ys)
    assert abs(a1 - a2) < 1e-9 and abs(b1 - b2) < 1e-9
    assert round(a1, 4) == 2.5584 and round(b1, 4) == 0.6824


def test_closed_form_matches_numpy():
    np = pytest.importorskip("numpy")
    ys = wb.noisy_data()
    a, b = wb.fit_closed_form(wb.XS, ys)
    na, nb = np.polyfit(wb.XS, ys, 1)
    assert abs(a - na) < 1e-9 and abs(b - nb) < 1e-9


@pytest.mark.parametrize("module,name", [(wa, "wb1_1_a"), (wb, "wb1_1_b")])
def test_output_matches_expected(module, name):
    expected = (HERE / "expected" / f"{name}.txt").read_text(encoding="utf-8")
    assert captured(module) == expected
    digest = hashlib.sha256(expected.encode("utf-8")).hexdigest()
    recorded = (HERE / "expected" / f"{name}.sha256").read_text().split()[0]
    assert digest == recorded


def test_wb1_1_b_options():
    import io
    import contextlib
    import wb1_1_b_model_is_function as wbm
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        wbm.main(["--noise", "0"])
    assert "a = 2.5000, b = 1.0000, MSE = 0.0000" in buf.getvalue()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        wbm.main(["--points", "5"])
    assert "data: 5 points" in buf.getvalue()
