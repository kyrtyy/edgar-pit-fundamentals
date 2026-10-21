# Point-in-time fundamentals

Fundamentals from SEC XBRL `companyfacts` for 27 US large caps (including 3 later acquired: TWTR, ATVI, XLNX), stored bitemporally so every reported version of a value is kept, then checked with rules, a robust z-score and a cross-check against market-data split events.

## Findings

Full output: [`out/report.md`](out/report.md).

- **A 1000× scale error in SEC data.** NVIDIA's diluted share count for FY2008 and FY2009 was filed as 606,732 and 548,126, about 1000× too small (10-Ks `0001045810-10-000006` and `0001045810-11-000015`).
- **486 revisions of already-reported values:** 234 rounding, 178 other (reclassifications and recasts, e.g. XOM and KO revenue), 57 split-driven and 17 amendments. Most re-reported values are not restatements.
- **15 splits inferred from filings alone**, including GE's 1-for-8 reverse split. All 15 match a vendor split event. The restated figures first appeared 18–261 days after the split.
- **Vendor data issues the reconciliation surfaced:**
  - Yahoo records three GE spin-offs as "splits" (1.04, 1.281, 1.253). Share counts didn't change, so the filings correctly don't show them.
  - Yahoo has no data at all for the three delisted companies. SEC still does, so vendor-side survivorship bias is visible.
- **Two vendor splits with no match in the filings, both explained:**
  - GOOGL 2014: before 2015, Google Inc. filed under a different CIK.
  - Visa 2015: Visa reports EPS and share counts only per share class, which `companyfacts` omits.
- **4 accounting-identity breaches.** For JPM 2009, a later filing revised Assets but not the matching total, so the latest-known snapshot doesn't balance.
- **A point-in-time effect:** share counts from years that were never restated sit on a pre-split basis. 30 of 236 anomaly flags on the real data come from this.

Detection on injected errors (2% of values corrupted, mean of 5 seeds; stale and drift errors are held out from the rules):

| method | precision | recall | drift recall | stale recall |
|---|---|---|---|---|
| rules | 96% | 43% | 0% | 0% |
| rules + robust z (z > 6) | 36% | 64% | 56% | 2% |

The z-score catches drift errors the rules can't, at a precision cost. `out/eval_sweep.csv` has the threshold tradeoff. Neither method catches stale values.

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
- **Split reconciliation:** vendor split events (Yahoo chart API) are matched to splits inferred from filings, by the same ratio within 450 days.
- **Scorecard:** RED means an identity breach or a rule flag. AMBER means more than 3 anomaly flags (not explained by splits) per 100 values, or more than 10 other or amended revisions.
- **Evaluation:** 2% of values are corrupted (scale ×1000, sign flip, stale value carried forward, ±30% drift), averaged over 5 seeds. The rules target scale and sign errors; stale and drift are held out.

## Known limitations

- Flows are annual only. 10-Q flows are year-to-date and Q4 isn't filed, so quarterly flows need derivation.
- "Known" means the day-level `filed` date. Use `acceptanceDateTime` from the submissions API if same-day timing matters.
- The universe is hand-picked and still mostly survivors.
- The anomaly z-score uses future neighbours, so it is retrospective QA rather than a trading-time signal, and it is weakest at the ends of a series.
- Evaluation precision counts genuine anomalies already in the data (M&A, IPOs, equity turning negative from buybacks) as false positives.
- `companyfacts` has no dimensional facts, so per-class figures (e.g. Visa's EPS) are missing.
- One CIK per company, so history from predecessor filers (e.g. Google Inc. before Alphabet) is not linked.
- Vendor split events come from Yahoo's unofficial chart API, which may change without notice.
