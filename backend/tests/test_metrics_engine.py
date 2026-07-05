"""Every expected value below was hand-computed from the source documents
(docs/FINANCIAL_FACTS.md) — this is how we stand over the outputs."""
import pytest

from app.services import metrics_engine as m


def test_revenue_growth_fy25(facts_by_period):
    g = m.revenue_growth(facts_by_period["FY25"], facts_by_period["FY24"], "FY25")
    # (836,991 - 688,317) / 688,317 = 21.60%
    assert g.value == pytest.approx(0.21600, abs=1e-4)


def test_revenue_growth_hy26(facts_by_period):
    g = m.revenue_growth(facts_by_period["HY26"], facts_by_period["HY25"], "HY26")
    # (354,813 - 340,931) / 340,931 = 4.07%  (PR states "up 4.1%")
    assert g.value == pytest.approx(0.0407, abs=1e-3)


def test_gross_margin_fy25(facts_by_period):
    gm = m.gross_margin(facts_by_period["FY25"], "FY25")
    # 648,450 / 836,991 = 77.47% (InfoDoc states 77.5%)
    assert gm.value == pytest.approx(0.7748, abs=1e-3)


def test_gross_margin_hy26_matches_pr(facts_by_period):
    gm = m.gross_margin(facts_by_period["HY26"], "HY26")
    # PR states 81.7%
    assert gm.value == pytest.approx(0.817, abs=1e-3)


def test_ebitda_fy25(facts_by_period):
    e = m.ebitda(facts_by_period["FY25"], "FY25")
    # -633,694 + 20,381 = -613,313
    assert e.value == pytest.approx(-613313, abs=1)


def test_ebitda_margin_fy24(facts_by_period):
    em = m.ebitda_margin(facts_by_period["FY24"], "FY24")
    # (-1,130,729 + 19,412) / 688,317 = -161.45%
    assert em.value == pytest.approx(-1.6145, abs=1e-3)


def test_working_capital_hy26(facts_by_period):
    wc = m.working_capital(facts_by_period["HY26"], "HY26")
    # (188,149 + 735,189) - 387,105 = 536,233 (excl. contingent consideration)
    assert wc.value == pytest.approx(536233, abs=1)


def test_current_ratio_fy25(facts_by_period):
    cr = m.current_ratio(facts_by_period["FY25"], "FY25")
    # 263,138 / 243,846 = 1.079
    assert cr.value == pytest.approx(1.079, abs=1e-3)


def test_net_debt_fy25_is_net_cash_negative(facts_by_period):
    nd = m.net_debt(facts_by_period["FY25"], "FY25")
    # debt 83,655 + 10,112 = 93,767; cash 140,135 -> net cash 46,368
    assert nd.value == pytest.approx(-46368, abs=1)


def test_dscr_fy25_negative_with_caveat(facts_by_period):
    d = m.dscr(facts_by_period["FY25"], "FY25")
    # EBITDA -613,313 / (2,074 + 10,112) = -50.33x
    assert d.value == pytest.approx(-50.33, abs=0.05)
    assert d.caveat is not None


def test_roce_fy25(facts_by_period):
    r = m.roce(facts_by_period["FY25"], "FY25")
    # EBIT -633,694 / capital employed (48,788+123,003+140,135-243,846=68,080)
    assert r.value == pytest.approx(-633694 / 68080, abs=0.01)
    assert r.caveat is not None


def test_cash_runway_hy26(facts_by_period):
    f = facts_by_period["HY26"]
    runway = m.cash_runway(f["cash"], f["cf_operating"], f["cf_investing"], 6, "HY26")
    # burn (410,291+8,500)/6 = 69,798.5/mo; 735,189 / 69,798.5 = 10.53 months
    assert runway.value == pytest.approx(10.53, abs=0.05)


def test_fcf_bridge_fy25_ties_to_cashflow_statement(facts_by_period):
    bridge = m.ebitda_to_fcf_bridge(facts_by_period["FY25"], "FY25")
    # FCF = op CF -374,820 + capex -4,451 + disposal 1,000 = -378,271
    assert bridge["fcf"] == pytest.approx(-378271, abs=1)
    assert bridge["steps"][0]["value"] == pytest.approx(-613313, abs=1)


def test_ltm_revenue(facts_by_period):
    ltm = m._ltm_revenue(facts_by_period["FY25"], facts_by_period["HY25"],
                         facts_by_period["HY26"])
    # 836,991 - 340,931 + 354,813 = 850,873
    assert ltm == pytest.approx(850873, abs=1)


def test_senus2030_progress():
    p = m.required_cagr_progress(836991, 850873, 0.5)
    # required at Dec-25 (0.5y): 836,991 * 1.5^0.5 = 1,025,057 -> 83.0%
    assert p.value == pytest.approx(0.830, abs=0.005)


def test_revenue_per_employee_fy25(facts_by_period):
    r = m.revenue_per_employee(facts_by_period["FY25"], "FY25")
    # 836,991 / 18 = 46,499.5
    assert r.value == pytest.approx(46499.5, abs=1)


def test_compute_all_structure(facts_by_period):
    out = m.compute_all(facts_by_period)
    assert set(out) == {"growth", "profitability", "cash", "solvency", "returns"}
    assert all(len(v) > 0 for v in out.values())
