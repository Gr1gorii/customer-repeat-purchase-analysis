"""Normalize line records without inventing identities or confirmed return links."""

import pandas as pd

COLUMNS = {
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "UnitPrice": "unit_price",
    "CustomerID": "customer_id",
    "Country": "country",
}


def clean(raw):
    missing = set(COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing source columns: {sorted(missing)}")
    # Exact source-row duplicates only. Identical invoice/product keys may be valid split lines.
    duplicate = raw.duplicated(subset=list(COLUMNS), keep="first")
    frame = raw.loc[~duplicate, list(COLUMNS)].rename(columns=COLUMNS).copy()
    frame.insert(0, "line_id", frame.index + 2)  # Original Excel row for auditability.
    for column in ["invoice_no", "stock_code", "description", "country"]:
        frame[column] = frame[column].astype("string").str.strip().replace("", pd.NA)
    frame["customer_id"] = pd.to_numeric(frame.customer_id, errors="coerce").astype("Int64")
    frame["invoice_date"] = pd.to_datetime(frame.invoice_date, errors="coerce")
    for column in ["quantity", "unit_price"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["is_cancelled"] = frame.invoice_no.str.upper().str.startswith("C").fillna(False)
    required = ["invoice_no", "stock_code", "invoice_date", "quantity", "unit_price"]
    invalid = frame[required].isna().any(axis=1) | (frame.unit_price < 0)
    invalid |= (frame.quantity % 1 != 0) | (frame.quantity == 0)
    invalid |= ~frame.quantity.map(lambda x: pd.notna(x) and abs(x) != float("inf"))
    invalid |= ~frame.unit_price.map(lambda x: pd.notna(x) and abs(x) != float("inf"))
    frame["is_valid"] = ~invalid
    quality = {
        "raw_rows": len(raw),
        "exact_duplicates_removed": int(duplicate.sum()),
        "retained_rows": len(frame),
        "invalid_rows": int(invalid.sum()),
        "missing_customer_rows_raw": int(raw.CustomerID.isna().sum()),
        "missing_customer_rows_retained": int(frame.customer_id.isna().sum()),
        "missing_description_rows_raw": int(raw.Description.isna().sum()),
        "zero_price_rows": int((frame.unit_price == 0).sum()),
        "negative_quantity_rows": int((frame.quantity < 0).sum()),
        "positive_cancelled_rows": int((frame.is_cancelled & (frame.quantity > 0)).sum()),
        "negative_non_cancelled_rows": int((~frame.is_cancelled & (frame.quantity < 0)).sum()),
    }
    return frame, quality
