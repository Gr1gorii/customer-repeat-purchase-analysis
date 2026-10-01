# Data quality and modeling decisions

## Source and integrity

[UCI Online Retail](https://archive.ics.uci.edu/dataset/352/online%2Bretail), DOI [10.24432/C5BW33](https://doi.org/10.24432/C5BW33), Chen, D. (2015), is the sole source. UCI identifies 541,909 lines, GBP prices, C-prefixed cancellation invoices and a retailer with many wholesale customers. Dataset license: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Data is provided without warranties; this project modifies it through normalization, deduplication, classification and aggregation. Preserve this attribution when reusing the workbook or derived data. `source_manifest.json` records actual ZIP/XLSX SHA-256 and byte size; the real-data test pins the known workbook fingerprint.

The UCI website says “Has Missing Values? No”. The actual workbook has 135,080 missing CustomerID and 1,454 missing descriptions. Actual file profiling governs the analysis. No missing customer IDs are imputed. Description is not needed to compute monetary or customer metrics.

## Rules at source-line grain

1. Validate required source columns. Remove exact duplicates across the original eight source fields, before normalization. Keep the first occurrence. Store its original Excel row as `line_id`. Do not deduplicate by invoice/stock key: legitimate split lines can share it. Exact identity is only a practical assumption; repeated identical legitimate lines could be removed.
2. Trim descriptive/categorical strings; blank strings become NULL. Keep nonnumeric stock/charge codes. CustomerID uses nullable integers; this known workbook contains integer IDs and missing values.
3. Parse source dates and numeric values. Reject from metrics missing required invoice/stock/time/quantity/price, nonfinite numbers, fractional/zero quantities and negative prices. Keep those rows in `lines` with `is_valid=false` for audit. Two real lines have UnitPrice -11,062.06; their signed total is -£22,124.12.
4. Retain zero-price lines in audit storage but exclude them from priced sales and paid purchase events. There are 2,510 after deduplication, including 1,336 negative non-C stock adjustments. These must not be relabeled as refunds.
5. Keep valid positive-price negative quantities in financial metrics. Classify C cancellations and non-C adjustments separately. A positive C anomaly, if present, stays in ledger totals but does not count as a customer purchase.
6. Use all identified qualifying invoices for activity, including later credited invoices. There is no trustworthy exact invoice credit allocation. Missing customer rows contribute to sales; never to customer cohorts.
7. Group purchase invoices by customer and invoice number; earliest qualifying time handles 42 invoice timestamp conflicts. Known-customer conflicts within invoice are zero. These counts are exported by the pipeline, not assumed.
8. Decimal prices retain four decimal places (the source includes fractional-penny prices). CSV/JSON retain precision; prose rounds to pennies and KPI cards to whole pounds. pandas independently sums integer ten-thousandths for reconciliation.
9. Use the last valid source timestamp as global observation cutoff. December 2011 is partial. For monthly activity, exclude incomplete months from rates. For repeat rates, require the individual customer's entire elapsed window; unknown outcomes are NULL/excluded.

## Quantified sensitivity

- 5,268 exact duplicate lines are removed, signed value £21,740.98. Removing them reduces priced net value by that amount compared with retaining them. Deduplication is documented, not claimed to establish ledger truth.
- Raw signed Quantity × UnitPrice total: £9,747,747.934. Subtract duplicate signed value £21,740.98 and exclude the two invalid negative-price lines (-£22,124.12) → cleaned net recorded sales £9,748,131.074. Zero-price lines do not change value.
- 135,037 retained lines have missing CustomerID. Anonymous priced net sales: £1,469,611.65. Customer metrics describe the identifiable purchasing subset, not all sales.
- 10,587 retained lines have negative quantities; only 9,251 are valid priced negatives. Candidate linkage covers the latter. Matching on same price and sufficient individual units is restrictive; it is a diagnostic, not a confirmed returns fact table.

`reports/quality.json` and `reports/quality_by_month_country.csv` provide counts and segmented missingness. Critical schema failures stop the pipeline; reconciliation disagreement stops demo refresh. The dataset is historical and finite, so no artificial “freshness SLA” is introduced.
