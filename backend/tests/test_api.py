"""End-to-end API tests against a seeded in-memory database."""
import os
import tempfile

os.environ["DATABASE_URL"] = f"sqlite:///{tempfile.gettempdir()}/test_senus.db"
# Tests must never hit a live LLM API, even when a developer has keys in .env:
# empty strings are falsy to Settings, so every provider reads as unavailable.
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["GITHUB_TOKEN"] = ""
os.environ["OPENAI_API_KEY"] = ""
os.environ["SKIP_EMBED"] = "1"  # no PDF chunking during unit tests

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture(scope="session", autouse=True)
def cleanup():
    yield
    Path(tempfile.gettempdir(), "test_senus.db").unlink(missing_ok=True)


@pytest.fixture(scope="session")
def token():
    with client:
        r = client.post("/api/auth/login",
                        data={"username": "ceo@senus.com", "password": "senus2030"})
        assert r.status_code == 200, r.text
        return r.json()["access_token"]


def auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_health():
    with client:
        assert client.get("/health").json()["status"] == "ok"


def test_login_rejects_bad_credentials():
    with client:
        r = client.post("/api/auth/login", data={"username": "ceo@senus.com", "password": "wrong"})
        assert r.status_code == 401


def test_metrics_requires_auth():
    with client:
        assert client.get("/api/metrics").status_code == 401


def test_metrics(token):
    with client:
        data = client.get("/api/metrics", headers=auth(token)).json()
        fy25 = next(m for m in data["growth"]
                    if m["key"] == "revenue_growth" and m["period"] == "FY25")
        assert fy25["value"] == pytest.approx(0.216, abs=1e-3)


def test_statements_pnl(token):
    with client:
        rows = client.get("/api/statements/pnl", headers=auth(token)).json()
        fy25_rev = next(r for r in rows if r["period"] == "FY25" and r["line_code"] == "revenue")
        assert fy25_rev["value"] == 836991
        assert fy25_rev["source"]["page"] == 10  # provenance travels with every fact


def test_statements_bs_includes_maturity_profile(token):
    """Loan maturity buckets come from the fact store (ADF FS note 13, p.21),
    not from hardcoded frontend arrays."""
    with client:
        rows = client.get("/api/statements/bs", headers=auth(token)).json()
        buckets = {r["line_code"]: r["value"] for r in rows
                   if r["period"] == "FY25" and r["line_code"].startswith("debt_maturity_")}
        assert buckets == {"debt_maturity_lt_1yr": 10112, "debt_maturity_1_2yr": 10500,
                           "debt_maturity_2_5yr": 34500, "debt_maturity_gt_5yr": 38655}
        page = next(r["source"]["page"] for r in rows
                    if r["line_code"] == "debt_maturity_lt_1yr")
        assert page == 21


def test_fcf_bridge(token):
    with client:
        b = client.get("/api/metrics/fcf-bridge/FY25", headers=auth(token)).json()
        assert b["fcf"] == pytest.approx(-378271, abs=1)


def test_validation_endpoint_surfaces_findings(token):
    with client:
        v = client.get("/api/validation", headers=auth(token)).json()
        assert v["summary"]["pass"] > 10
        assert v["summary"]["warn"] >= 1  # the real HY25 GP inconsistency


def test_hy26_dscr_suppressed_not_meaningless(token):
    """HY26 has no disclosed scheduled principal, so DSCR must be suppressed
    with an explanatory caveat instead of an interest-only -340x."""
    with client:
        data = client.get("/api/metrics", headers=auth(token)).json()
        hy26 = next(m for m in data["solvency"]
                    if m["key"] == "dscr" and m["period"] == "HY26")
        assert hy26["value"] is None
        assert "suppressed" in hy26["caveat"].lower()


def test_scenario_default_matches_guidance(token):
    with client:
        s = client.get("/api/scenario", headers=auth(token)).json()
        assert s["projection"][-1]["year"] == "FY30"
        # 836,991 * 1.5^5 = 6.36m
        assert s["projection"][-1]["revenue"] == pytest.approx(6355940, rel=1e-3)


def test_valuation_endpoint(token):
    with client:
        v = client.get("/api/valuation", headers=auth(token)).json()
        assert v["available"] is True
        # 6.15 x 2,561,332 shares = 15,752,192
        assert v["market_cap"] == pytest.approx(15752192, abs=1)
        # EV = mcap + net debt (HY26 net cash -658,715) = 15,093,477
        assert v["enterprise_value"] == pytest.approx(15093477, abs=1)
        assert v["price_vs_admission"] == pytest.approx(0.1998, abs=1e-3)


def test_chat_without_api_key_degrades_gracefully(token):
    with client:
        r = client.post("/api/chat", json={"question": "What was FY25 revenue?"},
                        headers=auth(token))
        assert r.status_code == 200
        assert "citations" in r.json()


def test_documents_provenance(token):
    with client:
        docs = client.get("/api/documents", headers=auth(token)).json()
        adf = next(d for d in docs if "ADF" in d["title"])
        assert adf["has_text_layer"] is False  # scanned -> vision extraction
        assert adf["facts_extracted"] > 30
