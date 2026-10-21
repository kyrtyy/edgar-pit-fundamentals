# Point-in-time fundamentals

Fundamentals from SEC XBRL `companyfacts` for 27 US large caps (including 3 later acquired: TWTR, ATVI, XLNX), stored bitemporally so every reported version of a value is kept.

```
python -m venv .venv && .venv/bin/pip install pandas numpy tabulate
export SEC_USER_AGENT="Your Name your@email"   # SEC asks for contact info
.venv/bin/python pit.py ingest                   # ~1 min, writes facts.db
.venv/bin/python pit.py asof AAPL shares_diluted 2020-06-30
.venv/bin/python pit.py report                   # writes out/report.md + CSVs
.venv/bin/python pit.py selftest
```

## Model

One table, `obs`: `cik, ticker, field, tag, unit, start, end, val, accn, form, filed`.
`end` is the period a value describes; `filed` is when it became known. An as-of query takes the latest filing per `(cik, field, end)` with `filed <= as_of`, so there's no look-ahead.

| field | kind | XBRL tags (priority order) |
|---|---|---|
| revenue | annual | Revenues, RevenueFromContractWithCustomerExcludingAssessedTax, SalesRevenueNet, RevenueFromContractWithCustomerIncludingAssessedTax |
| net_income | annual | NetIncomeLoss |
| eps_diluted | annual | EarningsPerShareDiluted |
| shares_diluted | annual | WeightedAverageNumberOfDilutedSharesOutstanding |
| assets, liabilities, equity, liab_and_equity, cash | quarter-end | Assets, Liabilities, StockholdersEquity, LiabilitiesAndStockholdersEquity, CashAndCashEquivalentsAtCarryingValue |

## Checks

- **Revisions:** a later filing reports a different value for an already-reported period. These are classified as `split` (the ratio is a split ratio on a share or per-share field), `amendment` (a /A form), `rounding` (<0.5%) or `other` (reclassification, recast or restatement).
- **Rules:** Assets vs LiabilitiesAndStockholdersEquity (>0.5% gap); scale (>300× off the neighbouring periods); negative values in fields that can't be negative.
- **Anomaly:** a robust z-score of each value's relative gap to the median of its neighbouring periods.
- **Evaluation:** 2% of values are corrupted (scale ×1000, sign flip, stale value carried forward, ±30% drift), averaged over 5 seeds. The rules target scale and sign errors; stale and drift are held out.

## Known limitations

- Flows are annual only. 10-Q flows are year-to-date and Q4 isn't filed, so quarterly flows need derivation.
- "Known" means the day-level `filed` date. Use `acceptanceDateTime` from the submissions API if same-day timing matters.
- The universe is hand-picked and still mostly survivors.
- The anomaly z-score uses future neighbours, so it is retrospective QA rather than a trading-time signal, and it is weakest at the ends of a series.
- Evaluation precision counts genuine anomalies already in the data (M&A, IPOs, equity turning negative from buybacks) as false positives.
- No price data, so splits are detected from restated filings, not reconciled against prices.
