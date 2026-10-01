# Verification record

Verification completed on the local Mac environment on 2026-09-30. This is the actual task date, not a backdated project history. No commits, pushes or deployments were made.

| Check | Result | Evidence |
|---|---|---|
| Original UCI source and data license | Passed | Dataset DOI/page, CC BY 4.0, `source_manifest.json` |
| End-to-end pipeline on 541,909 Excel rows | Passed | `reports/quality.json`, DuckDB database, Parquet ledger, reviewed CSV/JSON and summary |
| SQL vs independent pandas | Passed | Every repeat, cohort and country/month financial cell; `reports/reconciliation.json` |
| Synthetic + real-data tests | Passed: 12 tests | `pytest -q`; inclusive boundary, censoring, same-time invoices, split lines, anonymous identities, prices, nonfinite/missing required fields, duplicate removal, candidacy reuse, source fingerprint and real aggregate baselines |
| Ruff lint | Passed | `ruff check src tests scripts` |
| Ruff formatting | Passed | `ruff format --check src tests scripts` |
| Python compilation | Passed | `python -m compileall -q src scripts` |
| Repeat pipeline determinism | Passed | SHA-256 identical for 7 CSV/JSON aggregate files; `reports/reproducibility.json` |
| Local Chromium UI QA | Passed | `reports/browser_qa.json`; real default metrics, country/cohort filtering, repeated selections, explicit empty combination, three resets, quality panel, source artifact links, missing-data recovery |
| Mobile 390px viewport | Passed | No page-level horizontal overflow; heatmap intentionally scrolls inside its container; `reports/qa-mobile.png` |
| Visual screenshot review | Passed | Desktop/mobile/empty screenshots reviewed; month label placement repaired and UI QA rerun |
| JavaScript runtime errors | None observed | Browser QA captures page errors |
| Separate static type checker | Not configured | No claim of mypy/pyright validation; annotations are kept light for this MVP |
| Native Codex Browser / Computer Use | Blocked | Required `node_repl js` tool is absent from callable catalog. Standalone Playwright exercised the local interface instead. |
| Codex project registration | Pending / blocked | Listing and moving existing projects are supported; no add/register folder tool or callable UI control is exposed. No internal Codex database was edited. |

Initial checks found an ambiguous SQL ORDER BY alias, a misadded synthetic-fixture expected total, a link before its documentation file existed and chart label placement. These were corrected; the table records final rerun results, not those intermediate failures.

The local demo is served only on loopback. Tests do not rely on paid services or model APIs. The project is isolated from DocLens RAG; no other project files or shared configuration/order were changed.

## README presentation update

Long Unicode dashes were replaced with ASCII hyphens in project text and UI. README now opens with application-only dashboard and cohort screenshots plus actual result counts. These images were captured directly from headless Chromium page content, with no desktop, Codex interface or pointer overlay. Images were visually reviewed; the overview crop was repaired to include the complete charts. All 12 tests and Ruff passed again, and local browser checks reported no JavaScript errors.

## Dashboard presentation update, 2026-10-01

The public title is now `customer-repeat-purchase-analysis`. The directory, Python package and working commands retain their original names. Project ordinal labels, the oversized marketing header, decorative badge and outer card treatment were removed. Filters, metric definitions, quality notes, chart geometry/colors, repeat bars and the cohort heatmap remain. `web/app.js` is unchanged.

All 12 tests, Ruff lint and formatting passed again. Standalone Chromium passed the country/cohort filters, exact UK January cohort baseline, repeated selections, three resets, empty selection, quality panel, links, 390px layout and missing-data recovery. No JavaScript errors occurred. SHA-256 checks confirmed all 29 tracked source/SQL/test/data/result files and the dashboard calculation/data files were unchanged by this presentation update. No separate static type checker is configured.

Both English and Italian README image/document links resolve locally. Neither README contains Russian, long Unicode dashes or a project ordinal. All five QA screenshots were refreshed and desktop/mobile/empty-state images were visually reviewed. `reports/customer-repeat-purchase-analysis.png` was captured directly from the continuing loopback demo at `http://127.0.0.1:8764/web/`, which returned HTTP 200. Screenshots include application content only, with no desktop, assistant interface or cursor overlay.

The supplied Library reference `libfile_c96aab1098088191afb220cdcb5f8677` could not be downloaded after two supported materialization attempts. Its pixels were not inspected. The existing application and its previous real screenshots guided this update instead. Native Browser control and automatic project registration remain unavailable as described above.

The final screenshot was saved successfully to Library as `libfile_c0469416a6488191b852eb1d0affa355` (`customer-repeat-purchase-analysis.png`).
