# Metric dictionary

All monetary values are GBP. Grain starts at a retained source line, not an invoice. The ledger covers 2010-12-01 08:26 through 2011-12-09 12:50; timestamps are naive source times. No timezone conversion is invented.

| Metric | Definition / denominator | Population and limits |
|---|---|---|
| Positive ledger value | Sum Quantity × UnitPrice for valid priced positive lines | Includes anonymous customers and positive cancellation anomalies; these anomalies never create purchase activity. Not recognized accounting revenue. |
| Negative value | Absolute sum of valid priced negative line amounts | Separate C-prefixed cancellations from other negative adjustments. Not all negative lines are confirmed product returns. |
| Net recorded sales | Positive ledger value - negative value | Includes charge/discount/postage stock codes; excludes invalid and zero-price rows. Not profit; no cost data exists. |
| Negative / positive value ratio | Negative value / positive ledger value, if compared | A value ratio, not an invoice cancellation rate or item return rate. Dashboard presents the values directly. |
| Purchase invoice | Distinct (CustomerID, InvoiceNo) with ≥1 valid positive-priced, positive-quantity, non-C line | Timestamp = earliest qualifying line, country = minimum lexical country within invoice. 42 real invoices have differing line times; no invoice has conflicting known CustomerID. Purchase activity survives later credits. |
| Customer | CustomerID with at least one qualifying purchase invoice | Anonymous invoices excluded. Never assign each missing ID to a synthetic customer. |
| Cohort | Calendar month of first observed qualifying invoice | History before the extract is unknown; this is not lifetime acquisition. |
| Country for customer metrics | Country of first observed purchase invoice | Subsequent orders in another country remain with the initial cohort. Country for sales is each line's transaction country. |
| Cohort size | Customers first observed in the cohort month and selected initial country | Fixed denominator for all monthly cells. |
| Month index | Calendar month difference from cohort month (M0, M1, …) | Not elapsed 30-day periods. |
| Monthly active customers | Distinct cohort members with qualifying invoice in activity month | Zero for a fully observed month with no purchase. Does not mean revenue retention. |
| Monthly activity / retention | Active customers / cohort size | Output `retention_rate` is NULL for incomplete calendar months. Last month is incomplete; raw active counts remain visible in CSV. The UI uses “activity” to avoid suggesting revenue retention. |
| Eligible for N-day repeat | First invoice time + N elapsed days ≤ last valid source timestamp | N ∈ {30,60,90}. Conservative right-censoring. Customers without full windows are excluded, not counted as failures. |
| N-day repeat customer | Eligible customer whose second qualifying distinct invoice time ≤ first invoice time + N days | Inclusive boundary. Separate invoices at the same timestamp count; another line on the same invoice does not. |
| N-day repeat rate | Repeat customers / eligible customers | NULL when zero eligible. Different windows have different populations, so rates are not directly comparable intervention effects. Aggregation sums counts, never averages cohort percentages. |
| Cancellation line | Valid positive-price negative quantity with C-prefixed invoice (case-insensitive) | Primary UCI documentation states C indicates cancellation. No original-invoice reference is provided. |
| Negative adjustment | Valid positive-price negative quantity without C prefix | Kept separately. On this workbook all 1,336 retained negative non-C lines are zero-price, so none enters priced ledger linkage. |
| Candidate prior line | Same CustomerID, stock, four-decimal price; earlier timestamp; prior positive line units ≥ absolute negative units | No identity → missing_customer; otherwise 0, 1 or multiple candidates. This is not a confirmed match. A candidate can be reused by multiple negative lines; no allocation/depletion. Split positive lines are not combined, so some plausible returns may remain unmatched. |

## Filter scope

Country filters both financial and customer tables, using the definitions above. Cohort filters only customer repeat/activity tables. Financial KPIs, monthly sales and negative linkage stay on the selected transaction-country ledger. Empty customer filter combinations show no customers and null repeat rates, while that country's ledger can still have sales.
