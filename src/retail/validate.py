"""Independent pandas calculations check every SQL cohort/repeat/sales cell."""

from decimal import Decimal

import pandas as pd
from pandas.testing import assert_frame_equal


def compare(actual, expected, keys, values):
    left = actual.sort_values(keys)[keys + values].reset_index(drop=True)
    right = expected.sort_values(keys)[keys + values].reset_index(drop=True)
    for column in keys:
        # DuckDB DATE returns datetime64; normalize dates on both sides.
        left[column] = left[column].astype(str).str[:10] if "month" in column else left[column]
        right[column] = right[column].astype(str).str[:10] if "month" in column else right[column]
    assert_frame_equal(left, right, check_dtype=False, atol=1e-8, rtol=1e-10)


def reconcile(frame, outputs):
    valid = frame[frame.is_valid].copy()
    sales = valid[(valid.quantity > 0) & (valid.unit_price > 0) & ~valid.is_cancelled]
    known = sales[sales.customer_id.notna()]
    orders = (
        known.groupby(["customer_id", "invoice_no"], as_index=False)
        .agg(order_date=("invoice_date", "min"), country=("country", "min"))
        .sort_values(["customer_id", "order_date", "invoice_no"])
    )
    history = orders.groupby("customer_id").head(1).copy()
    seconds = orders.groupby("customer_id").nth(1).set_index("customer_id").order_date
    history["second_order_date"] = history.customer_id.map(seconds)
    history["cohort_month"] = history.order_date.dt.to_period("M").dt.to_timestamp()
    cutoff = valid.invoice_date.max()
    repeat = []
    for days in [30, 60, 90]:
        flags = history.copy()
        deadline = flags.order_date + pd.Timedelta(days=days)
        flags["eligible_customers"] = deadline <= cutoff
        flags["repeat_customers"] = flags.eligible_customers & (flags.second_order_date <= deadline)
        grouped = (
            flags.groupby(["country", "cohort_month"], dropna=False)
            .agg(
                customers=("customer_id", "size"),
                eligible_customers=("eligible_customers", "sum"),
                repeat_customers=("repeat_customers", "sum"),
            )
            .reset_index()
        )
        grouped["days"] = days
        grouped["repeat_rate"] = grouped.repeat_customers / grouped.eligible_customers.replace(
            0, float("nan")
        )
        repeat.append(grouped)
    compare(
        outputs["repeat"],
        pd.concat(repeat),
        ["country", "cohort_month", "days"],
        ["customers", "eligible_customers", "repeat_customers", "repeat_rate"],
    )

    activity = orders.merge(
        history[["customer_id", "cohort_month", "country"]],
        on="customer_id",
        suffixes=("_order", ""),
    )
    activity["activity_month"] = activity.order_date.dt.to_period("M").dt.to_timestamp()
    counts = activity.groupby(
        ["country", "cohort_month", "activity_month"], dropna=False
    ).customer_id.nunique()
    cells = []
    for (country, cohort), members in history.groupby(["country", "cohort_month"], dropna=False):
        for month in pd.date_range(cohort, cutoff.to_period("M").to_timestamp(), freq="MS"):
            active = counts.get((country, cohort, month), 0)
            complete = month + pd.offsets.MonthBegin(1) <= cutoff
            cells.append(
                {
                    "country": country,
                    "cohort_month": cohort,
                    "activity_month": month,
                    "cohort_size": len(members),
                    "active_customers": active,
                    "complete_month": complete,
                    "retention_rate": active / len(members) if complete else float("nan"),
                }
            )
    compare(
        outputs["cohorts"],
        pd.DataFrame(cells),
        ["country", "cohort_month", "activity_month"],
        ["cohort_size", "active_customers", "complete_month", "retention_rate"],
    )

    financial = valid[valid.unit_price > 0].copy()
    # Integer ten-thousandths avoid letting binary floats decide reconciliation.
    financial["amount_scaled"] = [
        int(Decimal(str(p)) * 10000) * int(q)
        for p, q in zip(financial.unit_price, financial.quantity)
    ]
    financial["gross_positive_sales"] = financial.amount_scaled.clip(lower=0)
    financial["negative_value"] = -financial.amount_scaled.clip(upper=0)
    financial["net_sales"] = financial.amount_scaled
    financial["cancellation_value"] = financial.negative_value.where(financial.is_cancelled, 0)
    financial["adjustment_value"] = financial.negative_value.where(~financial.is_cancelled, 0)
    financial["month"] = financial.invoice_date.dt.to_period("M").dt.to_timestamp()
    values = [
        "gross_positive_sales",
        "negative_value",
        "net_sales",
        "cancellation_value",
        "adjustment_value",
    ]
    totals = financial.groupby(["country", "month"], dropna=False)[values].sum().reset_index()
    totals[values] = totals[values] / 10000
    compare(outputs["sales"], totals, ["country", "month"], values)
    return {
        "status": "passed",
        "checks": ["all repeat window cells", "all cohort cells", "all country/month sales cells"],
        "orders": len(orders),
        "customers": len(history),
    }
