# A short interview walkthrough

1. **Start with grain.** An Excel row is an invoice line. Counting rows as purchases would inflate purchase frequency. The qualifying purchase table groups by customer and invoice.
2. **Explain the two populations.** Sales include valid priced anonymous ledger lines. Customer behavior requires known CustomerID. 24.9% missing IDs means cohorts cannot describe every sale.
3. **Open the SQL.** `01_models.sql` uses ROW_NUMBER to choose first observed orders and LEAD to identify the next invoice. `02_repeat.sql` uses a CROSS JOIN to three horizons and conditional aggregation; eligibility prevents late customers from becoming false non-repeaters.
4. **Explain calendar vs elapsed time.** Cohort heatmap columns are calendar months; repeat windows are 30/60/90 elapsed days. A 31 January customer has a February M1 cell almost immediately; that is why these metrics answer different questions.
5. **Explain the JOIN risks.** Negative linkage groups back to one row per negative line after joining possible earlier purchase lines. `candidate_count` describes ambiguity; summing money after an unaggregated many-to-many join would inflate totals. No candidate is claimed as a confirmed return.
6. **Show a real quality decision.** There are 5,268 exact duplicates, but invoice/product keys are not unique. Remove exact source-row duplicates only; document the £21,740.98 signed-value sensitivity. Two negative-price lines are excluded from metrics but remain auditable.
7. **Show independent evidence.** `validate.py` rebuilds invoices, repeat flags, cohort grids and monetary aggregates in pandas; integer ten-thousandths provide an independent money calculation. Tests exercise the exact boundary, anonymous IDs, reused candidates, zero/negative prices and censored months.
8. **State limits plainly.** First observed is not new acquisition. The final month is partial. Wholesalers may dominate. Purchase activity survives later credits. There is no cost of goods sold, so no profit or business improvement claim.

## Deliberate MVP choices

DuckDB can query local analytical data directly and keeps SQL readable. pandas is used for Excel ingestion and independent verification. Static aggregate JSON keeps the demo easy to run and avoids exposing customer-level history through a web API. It has no scheduler, authentication layer, data warehouse service or unnecessary object hierarchy.

A production extension would need accounting credit references, known extraction boundaries, better customer identity coverage and treatment of paid/fulfilled orders. Any CRM intervention needs a prospective measurement design; this dataset cannot estimate its uplift.
