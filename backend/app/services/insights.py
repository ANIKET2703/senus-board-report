"""AI board commentary, generated from validated facts only.

Guardrail: the model receives the computed metrics table (never raw PDFs) and
every numeric claim in its output is verified against the fact/metric values
before the insight is stored. A number that doesn't match a known value fails
the insight closed. Insights are cached in the DB and versioned by prompt.
"""
from __future__ import annotations

import hashlib
import re

from sqlalchemy.orm import Session

from app.models import Insight

PROMPT_VERSION = "v3"


def _cache_version(metrics_context: str) -> str:
    """Cache key = prompt version + fingerprint of the metrics the commentary was
    grounded on. If any underlying fact or metric changes, the fingerprint changes
    and stale cached commentary is never served."""
    fp = hashlib.sha256(metrics_context.encode()).hexdigest()[:8]
    return f"{PROMPT_VERSION}-{fp}"


AUDIENCE_FRAMING = {
    "board": "the Board of Directors: balanced, strategic, focused on execution against Senus 2030 and risk oversight",
    "management": "the executive team: operational, action-oriented, highlighting cost lines and commercial pipeline",
    "investor": "equity investors: growth trajectory, unit economics, path to FY2028 EBITDA breakeven, dilution",
    "credit": "credit providers: liquidity, runway, debt service capacity, downside protection",
}

SYSTEM = """You write the commentary sections of a public-company board report.
You are given a table of VALIDATED financial metrics for Senus PLC (Irish
Natural Capital software micro-cap, listed Euronext Access Dublin Dec 2025,
pre-profit, Senus 2030 strategy targets >=50% revenue CAGR and EBITDA-positive
during FY2028).

Rules:
- Use ONLY numbers present in the metrics table. Never derive, extrapolate or
  round beyond one decimal place of a percentage.
- Be candid about weaknesses (losses widened at HY26, HY26 growth of 4.1% is
  far below the 50% CAGR commitment) - boards value honesty over polish.
- 120-180 words, plain professional prose, no bullet points, no headers."""


def _numbers_in(text: str) -> set[str]:
    return {m.replace(",", "") for m in
            re.findall(r"€?([\d,]+(?:\.\d+)?)[km%]?", text) if len(m.replace(",", "")) >= 2}


def _allowed_numbers(metrics_context: str) -> set[str]:
    allowed = set()
    for m in re.findall(r"-?[\d,]+(?:\.\d+)?", metrics_context):
        v = m.replace(",", "").lstrip("-")
        allowed.add(v)
        try:
            f = float(v)
            for scaled in (f / 1000, f * 100, round(f, 1), round(f, 0)):
                allowed.add(f"{scaled:g}")
                allowed.add(f"{abs(scaled):.1f}")
        except ValueError:
            pass
    return allowed


def verify_grounding(text: str, metrics_context: str) -> list[str]:
    """Return numeric tokens in the commentary not traceable to a metric value."""
    allowed = _allowed_numbers(metrics_context)
    trivial = {str(y) for y in range(2017, 2036)} | {"50", "100", "2030", "2028"}
    return [n for n in _numbers_in(text) if n not in allowed and n not in trivial]


def get_or_generate(db: Session, audience: str, section: str, period: str,
                    metrics_context: str) -> dict:
    version = _cache_version(metrics_context)
    cached = (db.query(Insight)
              .filter_by(audience=audience, section=section, period_label=period,
                         prompt_version=version)
              .order_by(Insight.id.desc()).first())
    if cached:
        return {"content": cached.content, "model": cached.model, "cached": True}

    from app.services.llm import complete, provider_available
    if not provider_available():
        return {"content": None, "model": None, "cached": False,
                "error": ("AI commentary is not configured in this deployment. "
                          "All metrics, statements and validations remain fully functional.")}

    prompt = (f"Audience: {AUDIENCE_FRAMING[audience]}.\n"
              f"Section: {section}. Reporting period focus: {period}.\n\n"
              f"Validated metrics:\n{metrics_context}\n\nWrite the commentary.")
    text, model_used = complete(SYSTEM, prompt, max_tokens=600)

    ungrounded = verify_grounding(text, metrics_context)
    if ungrounded:
        # fail closed: retry once with explicit correction, else refuse
        retry_prompt = (prompt + f"\n\nYour previous draft used numbers not in the metrics "
                        f"table: {ungrounded}. Rewrite using only table values.")
        text, model_used = complete(SYSTEM, retry_prompt, max_tokens=600)
        if verify_grounding(text, metrics_context):
            return {"content": None, "model": model_used, "cached": False,
                    "error": "Commentary failed numeric grounding verification and was rejected."}

    insight = Insight(audience=audience, section=section, period_label=period,
                      content=text, model=model_used,
                      prompt_version=version)
    db.add(insight)
    db.commit()
    return {"content": text, "model": model_used, "cached": False}
