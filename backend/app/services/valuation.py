"""Deterministic valuation view (investor audience).

Same contract as the metrics engine: pure functions over fact-store values,
no LLM anywhere near the arithmetic, unit-tested against hand-computed values
(tests/test_valuation.py).

Sources (all in the fact store with provenance, never hardcoded here):
- shares in issue, admission price, admission market cap -> Direct Listing
  press release p.3 (unchanged per the AGM Circular, June 2026)
- share price, 52-week range, 52-week change -> Euronext market-data exports
  (data/market/*.xlsx), loaded as printed
- net debt -> HY26 balance sheet (latest published)
- LTM revenue and the Senus 2030 guidance path -> metrics/scenario engines

Honesty rule: Euronext Access is a low-liquidity venue and SENUS shows zero
reported volume in the sampled window, so every output carries that caveat.
"""
from __future__ import annotations

from app.services.metrics_engine import _ltm_revenue, total_debt
from app.services.scenario import project

LIQUIDITY_CAVEAT = (
    "Euronext Access is a low-liquidity venue: SENUS shows zero reported trading "
    "volume in the sampled window, so the quoted price is indicative and may not be "
    "achievable in size. Market-based multiples are directional at this liquidity."
)


def compute_valuation(facts_by_period: dict[str, dict[str, float]],
                      as_of: str | None = None) -> dict:
    mkt = facts_by_period.get("MKT", {})
    hy26 = facts_by_period.get("HY26", {})
    fy25 = facts_by_period.get("FY25", {})
    hy25 = facts_by_period.get("HY25", {})

    price, shares = mkt.get("share_price_close"), mkt.get("shares_in_issue")
    if price is None or shares is None:
        return {"available": False,
                "reason": "Market data facts (share price / shares in issue) not loaded."}

    market_cap = price * shares
    net_debt = total_debt(hy26) - (hy26.get("cash", 0) or 0)  # negative = net cash
    enterprise_value = market_cap + net_debt
    ltm_revenue = _ltm_revenue(fy25, hy25, hy26)

    admission_price = mkt.get("admission_price")
    price_vs_admission = (price / admission_price - 1) if admission_price else None

    # implied EV/revenue along the company's own >=50% CAGR guidance path,
    # holding today's EV constant: what the market is paying IF Senus delivers
    guidance = project()  # defaults = published Senus 2030 guidance
    path = [{"year": r["year"],
             "revenue": r["revenue"],
             "implied_ev_revenue": round(enterprise_value / r["revenue"], 2)}
            for r in guidance["projection"]]

    return {
        "available": True,
        "as_of": as_of,  # end date of the market-data period (passed by the API layer)
        "share_price": price,
        "price_52w_high": mkt.get("price_52w_high"),
        "price_52w_low": mkt.get("price_52w_low"),
        "admission_price": admission_price,
        "price_vs_admission": round(price_vs_admission, 4) if price_vs_admission is not None else None,
        "shares_in_issue": shares,
        "market_cap": round(market_cap, 0),
        "net_debt": round(net_debt, 0),
        "enterprise_value": round(enterprise_value, 0),
        "ltm_revenue": round(ltm_revenue, 0),
        "ev_ltm_revenue": round(enterprise_value / ltm_revenue, 2) if ltm_revenue else None,
        "guidance_path": path,
        "caveats": [
            LIQUIDITY_CAVEAT,
            "EV uses the HY26 (31 Dec 2025) balance sheet, the latest published. "
            "Contingent consideration of EUR 850k (Loamin, performance-linked) is "
            "excluded from net debt and itemised on the Solvency page.",
        ],
    }
