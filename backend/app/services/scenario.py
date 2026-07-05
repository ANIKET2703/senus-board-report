"""Senus 2030 scenario model.

Deterministic projection of the company's public commitment: revenue CAGR
>= 50% from the FY25 base (EUR 836,991) through FY30, EBITDA-positive during
FY2028. The UI lets users vary growth and margin assumptions; this module
just computes — assumptions are explicit inputs, never hidden.
"""
from __future__ import annotations

FY25_REVENUE = 836_991.0
FY25_OPEX = 1_286_058.0 + 1_084.0          # admin + distribution, FY25 actual
FY25_GROSS_MARGIN = 0.7748                  # FY25 actual


def project(
    growth_rate: float = 0.50,
    gross_margin: float = FY25_GROSS_MARGIN,
    opex_growth: float = 0.18,
    base_revenue: float = FY25_REVENUE,
    base_opex: float = FY25_OPEX,
    years: int = 5,
) -> dict:
    rows = []
    revenue, opex = base_revenue, base_opex
    for i in range(1, years + 1):
        revenue *= (1 + growth_rate)
        opex *= (1 + opex_growth)
        gp = revenue * gross_margin
        ebitda = gp - opex
        rows.append({
            "year": f"FY{25 + i}",
            "revenue": round(revenue, 0),
            "gross_profit": round(gp, 0),
            "opex": round(opex, 0),
            "ebitda": round(ebitda, 0),
            "ebitda_margin": round(ebitda / revenue, 4) if revenue else None,
        })
    breakeven = next((r["year"] for r in rows if r["ebitda"] > 0), None)
    return {
        "assumptions": {
            "revenue_cagr": growth_rate, "gross_margin": gross_margin,
            "opex_growth": opex_growth, "base_revenue": base_revenue,
            "base_opex": base_opex,
            "note": ("Base = FY25 audited actuals. Company guidance: >=50% revenue CAGR "
                     "(Senus 2030) and EBITDA-positive during FY2028."),
        },
        "projection": rows,
        "ebitda_breakeven_year": breakeven,
        "guidance_breakeven_year": "FY28",
    }
