"""Valuation math, hand-computed from the fact store (same discipline as
test_metrics_engine.py: every expected value traced to a source document)."""
import pytest

from app.services.valuation import compute_valuation


def test_market_cap(facts_by_period):
    v = compute_valuation(facts_by_period)
    # 6.15 (close, 3 Jul 26) x 2,561,332 shares (listing PR p.3) = 15,752,191.80
    assert v["market_cap"] == pytest.approx(15752192, abs=1)


def test_enterprise_value_uses_hy26_net_cash(facts_by_period):
    v = compute_valuation(facts_by_period)
    # HY26 bank debt 76,474 - cash 735,189 = net cash -658,715
    assert v["net_debt"] == pytest.approx(-658715, abs=1)
    # EV = 15,752,192 - 658,715 = 15,093,477
    assert v["enterprise_value"] == pytest.approx(15093477, abs=1)


def test_ev_ltm_revenue_multiple(facts_by_period):
    v = compute_valuation(facts_by_period)
    # LTM revenue to Dec-25 = 836,991 - 340,931 + 354,813 = 850,873
    assert v["ltm_revenue"] == pytest.approx(850873, abs=1)
    # 15,093,477 / 850,873 = 17.74x
    assert v["ev_ltm_revenue"] == pytest.approx(17.74, abs=0.01)


def test_price_vs_admission_ties_to_market_export(facts_by_period):
    v = compute_valuation(facts_by_period)
    # 6.15 / 5.126 - 1 = 19.98% — independently ties to the 52w change printed
    # in the performance export (validated by listing_price_change_ties)
    assert v["price_vs_admission"] == pytest.approx(0.1998, abs=1e-3)


def test_guidance_path_multiple_compression(facts_by_period):
    v = compute_valuation(facts_by_period)
    path = {r["year"]: r["implied_ev_revenue"] for r in v["guidance_path"]}
    # FY26E revenue 1,255,487 (836,991 x 1.5) -> 15,093,477 / 1,255,487 = 12.02x
    assert path["FY26"] == pytest.approx(12.02, abs=0.01)
    # FY30E revenue 6,355,940 -> 2.37x if the 50% CAGR commitment is delivered
    assert path["FY30"] == pytest.approx(2.37, abs=0.01)


def test_degrades_without_market_facts(facts_by_period):
    stripped = {k: v for k, v in facts_by_period.items() if k != "MKT"}
    v = compute_valuation(stripped)
    assert v["available"] is False
