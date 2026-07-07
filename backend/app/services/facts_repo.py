"""Read-side helpers for facts."""
from __future__ import annotations

from sqlalchemy.orm import Session, joinedload

from app.models import FinancialFact


def facts_by_period(db: Session) -> dict[str, dict[str, float]]:
    out: dict[str, dict[str, float]] = {}
    rows = db.query(FinancialFact).options(joinedload(FinancialFact.period)).all()
    for f in rows:
        out.setdefault(f.period.label, {})[f.line_code] = float(f.value)
    return out


def statement_rows(db: Session, statement: str) -> list[dict]:
    rows = (db.query(FinancialFact)
            .options(joinedload(FinancialFact.period), joinedload(FinancialFact.document))
            .filter(FinancialFact.statement == statement).all())
    return [{
        "id": f.id, "period": f.period.label, "line_code": f.line_code, "label": f.label,
        "value": float(f.value), "unit": f.unit,
        "source": {"document": f.document.title, "filename": f.document.filename,
                   "page": f.page_number, "method": f.extraction_method,
                   "confidence": f.confidence},
    } for f in rows]


def metrics_context_string(db: Session) -> str:
    """Compact metrics table given to the LLM for commentary/chat grounding."""
    from app.services.metrics_engine import compute_all
    fbp = facts_by_period(db)
    lines = []
    for period, facts in sorted(fbp.items()):
        for code, value in sorted(facts.items()):
            # small values (share price, ratios) keep their decimals; rounding
            # 6.15 to "6" would break the numeric grounding check downstream
            v = f"{value:g}" if abs(value) < 1000 else f"{value:,.0f}"
            lines.append(f"{period} {code} = {v}")
    for category, metrics in compute_all(fbp).items():
        for m in metrics:
            if m["value"] is not None:
                v = f"{m['value']:.4f}" if m["unit"] in ("pct", "ratio", "x") else f"{m['value']:,.0f}"
                lines.append(f"{m['period']} {m['key']} = {v} ({m['unit']})")
    # valuation outputs (market cap, EV, multiples) so commentary about the
    # Valuation page can ground its numbers too
    from app.services.valuation import compute_valuation
    val = compute_valuation(fbp)
    if val.get("available"):
        for key in ("market_cap", "net_debt", "enterprise_value", "ltm_revenue"):
            lines.append(f"MKT {key} = {val[key]:,.0f}")
        lines.append(f"MKT ev_ltm_revenue = {val['ev_ltm_revenue']} (x)")
        if val.get("price_vs_admission") is not None:
            lines.append(f"MKT price_vs_admission = {val['price_vs_admission']:.4f} (pct)")
        for r in val["guidance_path"]:
            lines.append(f"{r['year']}E guidance_revenue = {r['revenue']:,.0f}; implied_ev_revenue = {r['implied_ev_revenue']} (x)")
    return "\n".join(lines)
