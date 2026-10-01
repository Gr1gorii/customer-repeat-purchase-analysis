"""Regression baselines for this exact UCI workbook, not live business thresholds."""

import hashlib
import json
from decimal import Decimal

import duckdb
import pytest

from retail.download import ROOT
from retail.pipeline import query_outputs
from retail.validate import reconcile

DB = ROOT / "data/processed/retail.duckdb"
pytestmark = pytest.mark.skipif(not DB.exists(), reason="Run the real-data pipeline first")


def test_source_fingerprint():
    source = ROOT / "data/raw/Online Retail.xlsx"
    if not source.exists():
        pytest.skip("Downloaded workbook unavailable")
    manifest = json.loads((ROOT / "docs/source_manifest.json").read_text())
    assert hashlib.sha256(source.read_bytes()).hexdigest() == manifest["xlsx_sha256"]
    assert manifest["license"] == "CC BY 4.0"
    assert manifest["xlsx_sha256"] == (
        "43465a06f2ccf7c8b5bd2892bc7defb52f97487934fe93b16ae4c3936424676d"
    )


def test_real_aggregates_and_reconciliation():
    with duckdb.connect(str(DB), read_only=True) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lines").fetchone()[0] == 536641
        assert connection.execute("SELECT COUNT(*) FROM customer_history").fetchone()[0] == 4338
        frame = connection.execute(
            "SELECT * EXCLUDE(units, price, amount, line_type) FROM lines"
        ).df()
        outputs = query_outputs(connection)
        assert reconcile(frame, outputs)["status"] == "passed"
        assert connection.execute("SELECT SUM(amount) FROM financial_lines").fetchone()[
            0
        ] == Decimal("9748131.0740")
        windows = (
            outputs["repeat"].groupby("days")[["eligible_customers", "repeat_customers"]].sum()
        )
        assert windows.values.tolist() == [[4070, 907], [3731, 1403], [3370, 1605]]
        candidates = outputs["candidates"].groupby("candidate_status").negative_rows.sum().to_dict()
        assert candidates == {
            "missing_customer": 379,
            "multiple_candidates": 2172,
            "no_candidate": 1728,
            "one_candidate": 4972,
        }
