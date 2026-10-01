"""Run with python -m retail.pipeline from the project root (see README)."""

import json

import duckdb
import pandas as pd

from retail.clean import clean
from retail.download import ROOT, download
from retail.validate import reconcile

QUERIES = {
    "repeat": "02_repeat.sql",
    "cohorts": "03_cohorts.sql",
    "sales": "04_sales.sql",
    "candidates": "05_candidates.sql",
}


def build_database(frame, path=":memory:"):
    connection = duckdb.connect(str(path))
    connection.register("input_lines", frame)
    connection.execute((ROOT / "sql/01_models.sql").read_text())
    connection.unregister("input_lines")
    return connection


def query_outputs(connection):
    return {
        name: connection.execute((ROOT / "sql" / file).read_text()).df()
        for name, file in QUERIES.items()
    }


def json_records(frame):
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def run():
    source = download()
    raw = pd.read_excel(source, engine="openpyxl")
    frame, quality = clean(raw)
    processed = ROOT / "data/processed"
    processed.mkdir(exist_ok=True)
    reports = ROOT / "reports"
    reports.mkdir(exist_ok=True)
    connection = build_database(frame, processed / "retail.duckdb")
    outputs = query_outputs(connection)
    validation = reconcile(frame, outputs)  # Fail before updating demo when the engines disagree.
    quality["source_start"] = str(frame.invoice_date.min())
    quality["source_end"] = str(frame.invoice_date.max())
    quality["retained_unpriced_or_invalid_rows"] = int(
        connection.execute("SELECT COUNT(*) FROM lines WHERE NOT is_valid OR price = 0").fetchone()[
            0
        ]
    )
    duplicate_rows = raw[raw.duplicated(keep="first")]
    quality["duplicate_signed_value_removed"] = float(
        (duplicate_rows.Quantity * duplicate_rows.UnitPrice).sum()
    )
    quality["invoice_date_conflicts"] = int(
        connection.execute(
            "SELECT COUNT(*) FROM (SELECT invoice_no FROM sale_lines "
            "GROUP BY invoice_no HAVING COUNT(DISTINCT invoice_date)>1)"
        ).fetchone()[0]
    )
    quality["invoice_customer_conflicts"] = int(
        connection.execute(
            "SELECT COUNT(*) FROM (SELECT invoice_no FROM sale_lines "
            "GROUP BY invoice_no HAVING COUNT(DISTINCT customer_id)>1)"
        ).fetchone()[0]
    )
    profile = connection.execute("""
        SELECT country, DATE_TRUNC('month', invoice_date)::DATE AS month, COUNT(*) AS rows,
        COUNT(*) FILTER(WHERE customer_id IS NULL) AS missing_customer_rows,
        COUNT(*) FILTER(WHERE description IS NULL) AS missing_description_rows,
        COUNT(*) FILTER(WHERE line_type='invalid') AS invalid_rows,
        COUNT(*) FILTER(WHERE line_type='zero_price') AS zero_price_rows
        FROM lines GROUP BY country, month ORDER BY country, month
    """).df()
    outputs["quality_by_month_country"] = profile
    totals = (
        connection.execute("""
        SELECT SUM(CASE WHEN units>0 THEN amount ELSE 0 END) AS gross_positive_sales,
        -SUM(CASE WHEN units<0 THEN amount ELSE 0 END) AS negative_value,
        SUM(amount) AS net_sales,
        SUM(CASE WHEN customer_id IS NULL THEN amount ELSE 0 END) AS anonymous_net_sales
        FROM financial_lines
    """)
        .df()
        .iloc[0]
        .to_dict()
    )
    data = {
        "quality": quality,
        "validation": validation,
        "totals": totals,
        **{name: json_records(table) for name, table in outputs.items()},
    }
    for name, table in outputs.items():
        table.to_csv(reports / f"{name}.csv", index=False)
    (reports / "results.json").write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    (ROOT / "web/data.json").write_text(json.dumps(data, allow_nan=False) + "\n")
    (reports / "quality.json").write_text(json.dumps(quality, indent=2) + "\n")
    (reports / "reconciliation.json").write_text(json.dumps(validation, indent=2) + "\n")
    connection.execute(f"COPY lines TO '{processed / 'lines.parquet'}' (FORMAT PARQUET)")
    connection.close()
    write_summary(data)
    print(json.dumps({"quality": quality, "validation": validation, "totals": totals}, indent=2))


def write_summary(data):
    repeat = pd.DataFrame(data["repeat"])
    windows = repeat.groupby("days")[["eligible_customers", "repeat_customers"]].sum()
    candidates = pd.DataFrame(data["candidates"]).groupby("candidate_status").negative_rows.sum()
    monthly = pd.DataFrame(data["sales"]).groupby("month").net_sales.sum()
    peak = monthly.idxmax()[:7]
    q, t = data["quality"], data["totals"]
    lines = [
        "# Management summary",
        "",
        "## Observations from the supplied historical ledger",
        "",
        f"- {q['raw_rows']:,} source lines span {q['source_start']} to {q['source_end']}. "
        f"Removing {q['exact_duplicates_removed']:,} exact duplicate lines leaves "
        f"{q['retained_rows']:,} lines.",
        f"- Positive priced ledger value is £{t['gross_positive_sales']:,.2f}; negative "
        f"priced entries total £{t['negative_value']:,.2f}; net recorded sales are "
        f"£{t['net_sales']:,.2f}. These are sales, not profit.",
        f"- The raw file lacks CustomerID on {q['missing_customer_rows_raw']:,} lines "
        f"({q['missing_customer_rows_raw'] / q['raw_rows']:.1%}). Anonymous priced entries "
        f"contribute £{t['anonymous_net_sales']:,.2f} net sales, but cannot enter cohorts.",
        f"- {data['validation']['customers']:,} identified customers have an observed paid "
        f"non-cancelled purchase across {data['validation']['orders']:,} invoices.",
    ]
    for days, row in windows.iterrows():
        lines.append(
            f"- Within {days} elapsed days, {row.repeat_customers:,} of "
            f"{row.eligible_customers:,} eligible customers bought on another invoice "
            f"({row.repeat_customers / row.eligible_customers:.1%})."
        )
    lines += [
        f"- {peak} has the highest recorded monthly net sales (£{monthly.max():,.2f}); "
        "December 2011 ends on the 9th and is not comparable to full months.",
        "- Negative-line candidate linkage: "
        + "; ".join(f"{key.replace('_', ' ')}: {value:,}" for key, value in candidates.items())
        + ".",
        "",
        "## Decisions these observations can support",
        "",
        "Inspect repeat rates by first-purchase cohort and country before choosing a CRM "
        "test population. Compare only fully observed windows; measure any intervention "
        "with a future controlled experiment. Review unmatched/ambiguous negative lines "
        "against source accounting records before treating them as product returns.",
        "",
        "## Limits",
        "",
        "First purchase means first observed in this extract, not lifetime acquisition. "
        "The initial December 2010 cohort includes existing customers. Cohort activity "
        "counts paid positive invoices even if later credited; it is purchase activity, "
        "not retained revenue. Returns can arrive after the extract ends. Customer history "
        "is unavailable for anonymous invoices. The dataset includes wholesalers and one "
        "historic retailer, so findings are not general market benchmarks.",
        "",
        "Negative records have no original-invoice reference. Matching only checks "
        "same customer, stock, price, earlier time and sufficient individual-line units. "
        "Even a single candidate is not confirmed: no allocation or quantity depletion "
        "is attempted. Zero-price and negative-price entries are excluded from sales; "
        "non-product charge codes remain in the ledger. No cost, profit, tax, shipping "
        "allocation or causal business improvement is inferred.",
        "",
        "All SQL repeat, cohort and country/month monetary cells agree with independent "
        "pandas calculations. See reconciliation.json, the SQL files and metric dictionary.",
        "",
        "Source: Chen, D. (2015). [Online Retail](https://doi.org/10.24432/C5BW33). "
        "UCI Machine Learning Repository, "
        "[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). "
        "This project normalizes, deduplicates and aggregates the original data.",
    ]
    (ROOT / "reports/management_summary.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    run()
