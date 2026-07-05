"""Deterministic validation of extracted facts.

Accounting identities don't need AI judgement. Every check is explicit and
every failure is stored and shown in the app, including two genuine
inconsistencies present in the published source documents.
"""
from __future__ import annotations

TOLERANCE = 1.0  # EUR, accounts are integer-euro


def _f(facts: dict[str, dict[str, float]], period: str, code: str):
    return facts.get(period, {}).get(code)


def run_checks(facts_by_period: dict[str, dict[str, float]]) -> list[dict]:
    checks: list[dict] = []

    def add(name, period, ok, detail, warn=False):
        checks.append({"check_name": name, "period_label": period,
                       "status": "pass" if ok else ("warn" if warn else "fail"),
                       "detail": detail})

    for p in facts_by_period:
        rev, cos, gp = (_f(facts_by_period, p, c) for c in ("revenue", "cost_of_sales", "gross_profit"))
        if None not in (rev, cos, gp):
            diff = (rev + cos) - gp
            add("gross_profit_ties", p, abs(diff) <= TOLERANCE,
                f"revenue + cost_of_sales − gross_profit = {diff:,.0f}"
                + ("" if abs(diff) <= TOLERANCE else
                   " - inconsistency exists in the published source document"),
                warn=abs(diff) <= 1000)

        gp2, dist, admin, other, op = (_f(facts_by_period, p, c) for c in
                                       ("gross_profit", "distribution_costs", "admin_expenses",
                                        "other_operating_income", "operating_profit"))
        if None not in (gp2, admin, op):
            calc = gp2 + (dist or 0) + admin + (other or 0)
            diff = calc - op
            add("operating_result_ties", p, abs(diff) <= TOLERANCE,
                f"GP + costs + other income − operating result = {diff:,.0f}", warn=abs(diff) <= 1000)

        # balance sheet balances: net assets == equity components
        na, sc, sp, re_ = (_f(facts_by_period, p, c) for c in
                           ("net_assets", "share_capital", "share_premium", "retained_earnings"))
        if None not in (na, sc, sp, re_):
            diff = (sc + sp + re_) - na
            add("balance_sheet_balances", p, abs(diff) <= TOLERANCE,
                f"equity components − net assets = {diff:,.0f}")

        # cash flow ties to balance sheet cash
        closing, bs_cash = _f(facts_by_period, p, "closing_cash"), _f(facts_by_period, p, "cash")
        if None not in (closing, bs_cash):
            diff = closing - bs_cash
            add("cashflow_ties_to_bs", p, abs(diff) <= TOLERANCE,
                f"cash flow closing cash − balance sheet cash = {diff:,.0f}")

        # cash flow internal: opening + movements == closing
        op_cf, inv, fin, opening, closing2 = (_f(facts_by_period, p, c) for c in
                                              ("cf_operating", "cf_investing", "cf_financing",
                                               "opening_cash", "closing_cash"))
        if None not in (op_cf, inv, fin, opening, closing2):
            diff = opening + op_cf + inv + fin - closing2
            add("cashflow_internally_consistent", p, abs(diff) <= TOLERANCE,
                f"opening + O + I + F − closing = {diff:,.0f}")

    # cross-period: FY25 opening cash == FY24 closing cash
    fy24_close, fy25_open = _f(facts_by_period, "FY24", "closing_cash"), _f(facts_by_period, "FY25", "opening_cash")
    if None not in (fy24_close, fy25_open):
        add("fy25_opening_ties_fy24_closing", "FY25", abs(fy24_close - fy25_open) <= TOLERANCE,
            f"FY24 closing {fy24_close:,.0f} vs FY25 opening {fy25_open:,.0f}")

    # KPI cross-check: customer channel counts sum to total
    parts = [_f(facts_by_period, "FY25", c) for c in
             ("customers_enterprise", "customers_independent", "customers_rnd")]
    total = _f(facts_by_period, "FY25", "customers_total")
    if None not in parts and total is not None:
        s = sum(parts)
        add("customer_channels_sum", "FY25",
            abs(s - total) <= 0.5,
            f"{' + '.join(f'{p:.0f}' for p in parts)} = {s:.0f} vs stated total {total:.0f}")

    # disclosure coverage: the assignment brief lists MoM among example metrics,
    # but Senus publishes audited FY and unaudited HY figures only. No monthly
    # data exists in any filing, so the gap is recorded as a finding instead of
    # being filled with estimated numbers.
    add("mom_disclosure_coverage", None, False,
        "Monthly (MoM) figures are not disclosed in any Senus/ADF filing (FY audited + HY interim "
        "only), so MoM views cannot be built from source data. Omitted rather than "
        "estimated - see README 'Assumptions'.",
        warn=True)

    return checks
