import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="session")
def facts_by_period() -> dict:
    payload = json.loads((ROOT / "data" / "extracted" / "facts.json").read_text())
    by_period: dict[str, dict[str, float]] = {}
    for f in payload["facts"]:
        by_period.setdefault(f["period"], {})[f["line_code"]] = f["value"]
    return by_period
