from decimal import Decimal

import pandas as pd
import pytest

from retail.clean import clean
from retail.validate import reconcile


def test_exact_duplicates_and_quality(edge_data):
    raw, frame, quality, _, _ = edge_data
    assert len(frame) == len(raw) - 1
    assert quality["exact_duplicates_removed"] == 1
    assert quality["invalid_rows"] == 3
    assert quality["positive_cancelled_rows"] == 1
    assert quality["negative_non_cancelled_rows"] == 1


def test_anonymous_and_cancellation_anomalies_do_not_create_customers(edge_data):
    connection = edge_data[3]
    assert connection.execute("SELECT customer_id FROM customer_history ORDER BY 1").fetchall() == [
        (1,),
        (2,),
        (3,),
        (4,),
        (7,),
    ]
    # Both positive/negative anonymous records and the positive C anomaly remain in ledger totals.
    totals = connection.execute("SELECT SUM(amount) FROM financial_lines").fetchone()[0]
    assert float(totals) == -31  # £140 positive ledger value minus £171 negative value.


def test_repeat_eligibility_boundary_and_same_time_invoice(edge_data):
    results = edge_data[4]["repeat"]
    january = results[
        (results.cohort_month == pd.Timestamp("2011-01-01")) & (results.days == 30)
    ].iloc[0]
    assert january.eligible_customers == 3
    assert january.repeat_customers == 2
    march = results[
        (results.cohort_month == pd.Timestamp("2011-03-01")) & (results.days == 30)
    ].iloc[0]
    assert march.eligible_customers == 0
    assert pd.isna(march.repeat_rate)  # Unobserved is not zero retention.


def test_cohorts_full_zero_month_and_partial_month(edge_data):
    cohorts = edge_data[4]["cohorts"]
    january = cohorts[cohorts.cohort_month == pd.Timestamp("2011-01-01")]
    march = january[january.activity_month == pd.Timestamp("2011-03-01")].iloc[0]
    assert march.active_customers == 0 and march.retention_rate == 0
    april = january[january.activity_month == pd.Timestamp("2011-04-01")].iloc[0]
    assert not april.complete_month and pd.isna(april.retention_rate)


def test_negative_candidate_is_evidence_without_allocation(edge_data):
    connection = edge_data[3]
    counts = dict(
        connection.execute("""
        SELECT l.invoice_no, n.candidate_count FROM negative_candidates n
        JOIN lines l USING(line_id)
    """).fetchall()
    )
    assert counts["C100"] == counts["C101"] == 1
    assert counts["C102"] == counts["C103"] == counts["C104"] == 0
    assert counts["C105"] == 0
    assert edge_data[4]["candidates"].negative_rows.sum() == 7


def test_independent_pandas_sql_reconciliation(edge_data):
    assert reconcile(edge_data[1], edge_data[4])["status"] == "passed"


def test_missing_schema_fails_clearly():
    with pytest.raises(ValueError, match="Missing source columns"):
        clean(pd.DataFrame({"InvoiceNo": [1]}))


def test_split_lines_are_one_purchase_and_fractional_penny_prices():
    from conftest import line

    from retail.pipeline import build_database

    raw = pd.DataFrame(
        [
            line("same", "2011-01-01", quantity=2, price=0.001),
            line("same", "2011-01-01", quantity=3, price=0.001),
            line("Csame", "2011-02-01", quantity=-1, price=0.001),
        ]
    )
    frame, quality = clean(raw)
    assert quality["exact_duplicates_removed"] == 0
    with build_database(frame) as connection:
        assert connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0] == 1
        assert connection.execute("SELECT SUM(amount) FROM financial_lines").fetchone()[
            0
        ] == Decimal("0.0040")
        assert (
            connection.execute("SELECT second_order_date FROM customer_history").fetchone()[0]
            is None
        )


def test_entirely_anonymous_ledger_has_no_cohorts():
    from conftest import line

    from retail.pipeline import build_database, query_outputs

    frame, _ = clean(pd.DataFrame([line("anon", "2011-01-01", customer=None)]))
    with build_database(frame) as connection:
        outputs = query_outputs(connection)
        assert outputs["cohorts"].empty and outputs["repeat"].empty
        assert outputs["sales"].net_sales.sum() == 10


def test_nonfinite_and_missing_fields_remain_auditable_without_breaking_sql():
    from conftest import line

    from retail.pipeline import build_database, query_outputs

    raw = pd.DataFrame(
        [
            line("good", "2011-01-01"),
            line("badunits", "2011-01-02", quantity=float("inf")),
            line("badprice", "2011-01-02", price=float("inf")),
            line("baddate", None),
        ]
    )
    frame, quality = clean(raw)
    assert quality["invalid_rows"] == 3
    with build_database(frame) as connection:
        assert connection.execute("SELECT COUNT(*) FROM lines").fetchone()[0] == 4
        assert query_outputs(connection)["sales"].net_sales.sum() == 10
