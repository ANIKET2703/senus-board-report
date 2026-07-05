"""The validation layer must PASS the identities that hold and CATCH the two
genuine inconsistencies present in the published source documents."""
from pipeline.validate import run_checks


def _by_name(checks, name, period=None):
    return [c for c in checks
            if c["check_name"] == name and (period is None or c["period_label"] == period)]


def test_balance_sheets_balance(facts_by_period):
    checks = run_checks(facts_by_period)
    for c in _by_name(checks, "balance_sheet_balances"):
        assert c["status"] == "pass", c


def test_cashflow_ties_to_balance_sheet(facts_by_period):
    checks = run_checks(facts_by_period)
    assert all(c["status"] == "pass" for c in _by_name(checks, "cashflow_ties_to_bs"))


def test_cashflow_internally_consistent(facts_by_period):
    checks = run_checks(facts_by_period)
    assert all(c["status"] == "pass" for c in _by_name(checks, "cashflow_internally_consistent"))


def test_fy25_gross_profit_ties(facts_by_period):
    checks = run_checks(facts_by_period)
    assert _by_name(checks, "gross_profit_ties", "FY25")[0]["status"] == "pass"


def test_hy25_gross_profit_inconsistency_is_caught(facts_by_period):
    """Real finding: HY26 PR states HY25 GP 272,331 but 340,931 - 69,600 = 271,331."""
    checks = run_checks(facts_by_period)
    c = _by_name(checks, "gross_profit_ties", "HY25")[0]
    assert c["status"] == "warn"
    assert "inconsistency" in c["detail"]


def test_customer_channels_sum(facts_by_period):
    checks = run_checks(facts_by_period)
    assert _by_name(checks, "customer_channels_sum", "FY25")[0]["status"] == "pass"


def test_cross_period_cash_continuity(facts_by_period):
    checks = run_checks(facts_by_period)
    assert _by_name(checks, "fy25_opening_ties_fy24_closing")[0]["status"] == "pass"
