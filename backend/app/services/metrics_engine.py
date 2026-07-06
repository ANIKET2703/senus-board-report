"""Deterministic financial metrics engine.

Design contract: this module NEVER calls an LLM. Every metric is a pure
function over validated facts, unit-tested against hand-computed values
(tests/test_metrics_engine.py). AI narrates these numbers; it never produces
them.

Conventions
-----------
- Facts arrive as {line_code: value} per period, signed as printed in the
  source accounts (costs negative).
- On a pre-profit company several classic ratios are not meaningful in their
  textbook form. Rather than emitting misleading numbers, metrics carry an
  optional `caveat` explaining interpretation - a deliberate product decision
  for a board/credit audience.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Metric:
    key: str
    label: str
    value: float | None
    unit: str  # EUR | pct | ratio | months | count | x
    period: str
    caveat: str | None = None
    inputs: dict[str, float] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "key": self.key, "label": self.label, "value": self.value,
            "unit": self.unit, "period": self.period, "caveat": self.caveat,
            "inputs": self.inputs,
        }


Facts = dict[str, float]  # line_code -> value for one period


def _get(facts: Facts, code: str, default: float | None = None) -> float | None:
    return facts.get(code, default)


# ---------------------------------------------------------------- growth ----

def revenue_growth(current: Facts, prior: Facts, period: str) -> Metric:
    rev_c, rev_p = current.get("revenue"), prior.get("revenue")
    value = None
    if rev_c is not None and rev_p:
        value = (rev_c - rev_p) / rev_p
    return Metric("revenue_growth", "Revenue growth", value, "pct", period,
                  inputs={"revenue_current": rev_c or 0, "revenue_prior": rev_p or 0})


def required_cagr_progress(fy25_revenue: float, actual_ltm_revenue: float,
                           years_elapsed: float, target_cagr: float = 0.50) -> Metric:
    """Actual trajectory vs the Senus 2030 >=50% CAGR commitment (base FY25)."""
    required = fy25_revenue * (1 + target_cagr) ** years_elapsed
    value = actual_ltm_revenue / required if required else None
    return Metric(
        "senus2030_progress", "Revenue vs Senus 2030 trajectory", value, "ratio", "LTM",
        caveat="Ratio of LTM revenue to the level implied by the 50% CAGR commitment.",
        inputs={"required_revenue": round(required, 2), "actual_revenue": actual_ltm_revenue},
    )


# ---------------------------------------------------------- profitability ----

def gross_margin(facts: Facts, period: str) -> Metric:
    rev, gp = facts.get("revenue"), facts.get("gross_profit")
    value = gp / rev if rev and gp is not None else None
    return Metric("gross_margin", "Gross margin", value, "pct", period,
                  inputs={"gross_profit": gp or 0, "revenue": rev or 0})


def operating_margin(facts: Facts, period: str) -> Metric:
    rev, op = facts.get("revenue"), facts.get("operating_profit")
    value = op / rev if rev and op is not None else None
    return Metric("operating_margin", "Operating margin", value, "pct", period,
                  inputs={"operating_profit": op or 0, "revenue": rev or 0})


def ebitda(facts: Facts, period: str) -> Metric:
    """EBITDA = operating profit + depreciation & amortisation.

    Note: FRS 102 small-company accounts don't present EBITDA; we reconstruct
    it from disclosed operating loss + depreciation (source: P&L + notes).
    """
    op, dep = facts.get("operating_profit"), facts.get("depreciation", 0.0)
    amort = facts.get("amortisation", 0.0)
    value = op + (dep or 0) + (amort or 0) if op is not None else None
    return Metric("ebitda", "EBITDA", value, "EUR", period,
                  inputs={"operating_profit": op or 0, "depreciation": dep or 0})


def ebitda_margin(facts: Facts, period: str) -> Metric:
    e = ebitda(facts, period).value
    rev = facts.get("revenue")
    value = e / rev if rev and e is not None else None
    return Metric("ebitda_margin", "EBITDA margin", value, "pct", period,
                  inputs={"ebitda": e or 0, "revenue": rev or 0})


def cost_breakdown(facts: Facts, period: str) -> list[Metric]:
    out = []
    for code, label in [("cost_of_sales", "Cost of sales"),
                        ("admin_expenses", "Administrative expenses"),
                        ("distribution_costs", "Distribution costs")]:
        v = facts.get(code)
        rev = facts.get("revenue")
        pct = abs(v) / rev if rev and v is not None else None
        out.append(Metric(f"{code}_pct_revenue", f"{label} as % of revenue", pct, "pct",
                          period, inputs={code: v or 0, "revenue": rev or 0}))
    return out


# ------------------------------------------------------- cash & liquidity ----

def ebitda_to_fcf_bridge(facts: Facts, period: str) -> dict:
    """Ordered bridge: EBITDA → working capital → tax → interest → capex → FCF.

    FCF here = operating cash flow + investing cash flow (pre-financing),
    the definition a credit provider uses for debt service capacity.
    """
    e = ebitda(facts, period).value or 0.0
    wc = facts.get("working_capital_movement", 0.0) or 0.0
    tax = facts.get("tax_repaid", 0.0) or 0.0
    interest = facts.get("interest_paid", 0.0) or 0.0
    capex = (facts.get("capex", 0.0) or 0.0) + (facts.get("asset_disposal_proceeds", 0.0) or 0.0)
    cf_op = facts.get("cf_operating")
    other = (cf_op - (e + wc + tax + interest)) if cf_op is not None else 0.0
    fcf = (cf_op if cf_op is not None else e + wc + tax + interest) + capex
    return {
        "period": period,
        "steps": [
            {"label": "EBITDA", "value": e},
            {"label": "Working capital movement", "value": wc},
            {"label": "Tax repaid / (paid)", "value": tax},
            {"label": "Interest paid", "value": interest},
            {"label": "Other operating items", "value": round(other, 2)},
            {"label": "Net capex", "value": capex},
        ],
        "fcf": round(fcf, 2),
    }


def cash_runway(cash: float, operating_outflow: float, investing_outflow: float,
                months_in_period: int, period: str) -> Metric:
    """Months of runway at the period's average monthly pre-financing burn.

    Deliberately excludes financing inflows: runway answers 'how long before
    the company must raise again?'.
    """
    burn = -(operating_outflow + investing_outflow)
    if burn <= 0:
        return Metric("cash_runway", "Cash runway", None, "months", period,
                      caveat="Company was cash-generative pre-financing in the period.")
    monthly = burn / months_in_period
    return Metric("cash_runway", "Cash runway", cash / monthly, "months", period,
                  caveat="At average monthly pre-financing burn for the period; excludes future fundraising.",
                  inputs={"cash": cash, "monthly_burn": round(monthly, 2)})


def working_capital(facts: Facts, period: str) -> Metric:
    ca = (facts.get("debtors", 0) or 0) + (facts.get("cash", 0) or 0)
    cl = facts.get("creditors_lt_1yr", 0) or 0  # stored negative
    return Metric("working_capital", "Working capital", ca + cl, "EUR", period,
                  inputs={"current_assets": ca, "current_liabilities": cl})


def current_ratio(facts: Facts, period: str) -> Metric:
    ca = (facts.get("debtors", 0) or 0) + (facts.get("cash", 0) or 0)
    cl = abs(facts.get("creditors_lt_1yr", 0) or 0)
    value = ca / cl if cl else None
    return Metric("current_ratio", "Current ratio", value, "x", period,
                  inputs={"current_assets": ca, "current_liabilities": cl})


# ----------------------------------------------------- solvency & leverage ----

def total_debt(facts: Facts) -> float:
    """Bank debt only (excludes directors' loans & contingent consideration,
    which are itemised separately for the credit view)."""
    lt = abs(facts.get("creditors_gt_1yr", 0) or 0)
    st = facts.get("debt_due_lt_1yr", 0) or 0
    return lt + st


def net_debt(facts: Facts, period: str) -> Metric:
    debt = total_debt(facts)
    cash = facts.get("cash", 0) or 0
    return Metric("net_debt", "Net debt / (net cash)", debt - cash, "EUR", period,
                  inputs={"total_debt": debt, "cash": cash})


def dscr(facts: Facts, period: str, annualise: float = 1.0) -> Metric:
    """Debt Service Coverage = EBITDA / (interest + scheduled principal <1yr).

    On a pre-profit company EBITDA is negative, so DSCR is reported negative
    with an explicit caveat: debt service is currently funded from equity,
    not operations. Reporting a raw negative honestly is more useful to a
    credit provider than suppressing the metric.

    Suppression rule: if scheduled principal is NOT disclosed for the period
    (HY balance sheets don't split creditors by maturity), an interest-only
    denominator would produce an enormous, meaningless ratio (e.g. -340x next
    to FY25's -50x). Incomplete debt service => no ratio, with the reason.
    """
    e = (ebitda(facts, period).value or 0.0) * annualise
    interest = abs(facts.get("interest_expense", 0) or 0) * annualise
    if "debt_due_lt_1yr" not in facts:
        return Metric(
            "dscr", "Debt service coverage ratio", None, "x", period,
            caveat=("Scheduled principal due <1yr is not disclosed at this date "
                    "(interim balance sheets don't split creditors by maturity), so full "
                    "debt service is unknown. Ratio suppressed rather than computed "
                    "interest-only - the last complete figure is FY25."),
            inputs={"ebitda": round(e, 2), "interest": interest})
    principal = facts.get("debt_due_lt_1yr", 0) or 0
    service = interest + principal
    value = e / service if service else None
    caveat = None
    if value is not None and value < 1:
        caveat = ("DSCR < 1: debt service is funded from equity/cash reserves, not "
                  "operating earnings - expected at this stage; EBITDA-positive guidance is FY2028.")
    return Metric("dscr", "Debt service coverage ratio", value, "x", period, caveat=caveat,
                  inputs={"ebitda": round(e, 2), "interest": interest, "scheduled_principal": principal})


def gearing(facts: Facts, period: str) -> Metric:
    debt = total_debt(facts)
    equity = facts.get("net_assets", 0) or 0
    value = debt / equity if equity > 0 else None
    caveat = None if equity > 0 else "Equity is negative/near-zero at this date; gearing not meaningful."
    return Metric("gearing", "Gearing (debt / equity)", value, "x", period, caveat=caveat,
                  inputs={"total_debt": debt, "equity": equity})


# ---------------------------------------------------------------- returns ----

def roce(facts: Facts, period: str, annualise: float = 1.0) -> Metric:
    """ROCE = EBIT / capital employed (total assets - current liabilities).

    Negative while the company invests ahead of revenue; trend matters more
    than level. Caveated, not hidden.
    """
    op = facts.get("operating_profit")
    fixed = ((facts.get("goodwill", 0) or 0) + (facts.get("development_costs", 0) or 0)
             + (facts.get("tangible_assets", 0) or 0))
    ca = (facts.get("debtors", 0) or 0) + (facts.get("cash", 0) or 0)
    cl = facts.get("creditors_lt_1yr", 0) or 0
    capital_employed = fixed + ca + cl
    value = (op * annualise) / capital_employed if capital_employed and op is not None else None
    caveat = None
    if value is not None and value < 0:
        caveat = ("Negative while operating losses persist; the trend toward the FY2028 "
                  "EBITDA guidance matters more than the level.")
    return Metric("roce", "Return on capital employed", value, "pct", period, caveat=caveat,
                  inputs={"ebit_annualised": round((op or 0) * annualise, 2),
                          "capital_employed": capital_employed})


def revenue_per_employee(facts: Facts, period: str) -> Metric:
    rev, emp = facts.get("revenue"), facts.get("employees")
    value = rev / emp if rev and emp else None
    return Metric("revenue_per_employee", "Revenue per employee", value, "EUR", period,
                  inputs={"revenue": rev or 0, "employees": emp or 0})


# ---------------------------------------------------------------- summary ----

def compute_all(facts_by_period: dict[str, Facts]) -> dict:
    """Full metric set for API. facts_by_period: {'FY24': {...}, 'FY25': {...}, ...}"""
    out: dict[str, list[dict]] = {"growth": [], "profitability": [], "cash": [],
                                  "solvency": [], "returns": []}
    fy24, fy25 = facts_by_period.get("FY24", {}), facts_by_period.get("FY25", {})
    hy25, hy26 = facts_by_period.get("HY25", {}), facts_by_period.get("HY26", {})

    if fy24 and fy25:
        out["growth"].append(revenue_growth(fy25, fy24, "FY25").as_dict())
    if hy25 and hy26:
        out["growth"].append(revenue_growth(hy26, hy25, "HY26").as_dict())
    if fy25.get("revenue"):
        out["growth"].append(required_cagr_progress(fy25["revenue"],
                             _ltm_revenue(fy25, hy25, hy26), 0.5).as_dict())

    for label, f in [("FY24", fy24), ("FY25", fy25), ("HY25", hy25), ("HY26", hy26)]:
        if not f:
            continue
        out["profitability"] += [gross_margin(f, label).as_dict(),
                                 operating_margin(f, label).as_dict(),
                                 ebitda(f, label).as_dict(),
                                 ebitda_margin(f, label).as_dict()]
        out["profitability"] += [m.as_dict() for m in cost_breakdown(f, label)]
        out["cash"].append(working_capital(f, label).as_dict())
        out["cash"].append(current_ratio(f, label).as_dict())
        annualise = 2.0 if label.startswith("HY") else 1.0
        out["solvency"].append(net_debt(f, label).as_dict())
        out["solvency"].append(dscr(f, label, annualise).as_dict())
        out["solvency"].append(gearing(f, label).as_dict())
        out["returns"].append(roce(f, label, annualise).as_dict())
        out["returns"].append(revenue_per_employee(f, label).as_dict())

    if fy25:
        out["cash"].append(cash_runway(fy25.get("cash", 0), fy25.get("cf_operating", 0),
                                       fy25.get("cf_investing", 0), 12, "FY25").as_dict())
    if hy26:
        out["cash"].append(cash_runway(hy26.get("cash", 0), hy26.get("cf_operating", 0),
                                       hy26.get("cf_investing", 0), 6, "HY26").as_dict())
    return out


def _ltm_revenue(fy25: Facts, hy25: Facts, hy26: Facts) -> float:
    """LTM to Dec-25 = FY25 - HY25 + HY26."""
    return (fy25.get("revenue", 0) or 0) - (hy25.get("revenue", 0) or 0) + (hy26.get("revenue", 0) or 0)
