# Management summary

## Observations from the supplied historical ledger

- 541,909 source lines span 2010-12-01 08:26:00 to 2011-12-09 12:50:00. Removing 5,268 exact duplicate lines leaves 536,641 lines.
- Positive priced ledger value is £10,642,110.80; negative priced entries total £893,979.73; net recorded sales are £9,748,131.07. These are sales, not profit.
- The raw file lacks CustomerID on 135,080 lines (24.9%). Anonymous priced entries contribute £1,469,611.65 net sales, but cannot enter cohorts.
- 4,338 identified customers have an observed paid non-cancelled purchase across 18,532 invoices.
- Within 30 elapsed days, 907 of 4,070 eligible customers bought on another invoice (22.3%).
- Within 60 elapsed days, 1,403 of 3,731 eligible customers bought on another invoice (37.6%).
- Within 90 elapsed days, 1,605 of 3,370 eligible customers bought on another invoice (47.6%).
- 2011-11 has the highest recorded monthly net sales (£1,456,145.80); December 2011 ends on the 9th and is not comparable to full months.
- Negative-line candidate linkage: missing customer: 379; multiple candidates: 2,172; no candidate: 1,728; one candidate: 4,972.

## Decisions these observations can support

Inspect repeat rates by first-purchase cohort and country before choosing a CRM test population. Compare only fully observed windows; measure any intervention with a future controlled experiment. Review unmatched/ambiguous negative lines against source accounting records before treating them as product returns.

## Limits

First purchase means first observed in this extract, not lifetime acquisition. The initial December 2010 cohort includes existing customers. Cohort activity counts paid positive invoices even if later credited; it is purchase activity, not retained revenue. Returns can arrive after the extract ends. Customer history is unavailable for anonymous invoices. The dataset includes wholesalers and one historic retailer, so findings are not general market benchmarks.

Negative records have no original-invoice reference. Matching only checks same customer, stock, price, earlier time and sufficient individual-line units. Even a single candidate is not confirmed: no allocation or quantity depletion is attempted. Zero-price and negative-price entries are excluded from sales; non-product charge codes remain in the ledger. No cost, profit, tax, shipping allocation or causal business improvement is inferred.

All SQL repeat, cohort and country/month monetary cells agree with independent pandas calculations. See reconciliation.json, the SQL files and metric dictionary.

Source: Chen, D. (2015). [Online Retail](https://doi.org/10.24432/C5BW33). UCI Machine Learning Repository, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). This project normalizes, deduplicates and aggregates the original data.
