# Data product note

## Who uses this dataset and what they need

| User | What they do with it | What they need from the data | Checks that matter most |
|---|---|---|---|
| Quant researcher | Backtests factors such as value, quality and size | No look-ahead: each value as it was known on the trade date; a share basis consistent with the traded price | As-of query, revision classification, split basis, market-cap continuity |
| Fundamental analyst | Compares a company's history and its peers | The current best value, with a visible restatement history | Revisions (other/amendment), accounting identity |
| Risk / portfolio analytics | Market cap, leverage and exposure reports | Correct scale and sign; market cap that matches the traded price | Scale and sign rules, market-cap check |
| Data operations | Owns the feed and triages exceptions | A short, ranked exception queue with an explanation for each flag | Scorecard, split-explained vs unexplained flags, vendor reconciliation |

The researcher and the analyst want different "truths" for the same cell. The researcher needs the value as filed, and the analyst needs the latest restated value. The bitemporal model serves both from one table: `as_of(date)` for the first, `as_of(today)` for the second. Mixing them up is the most expensive error a user can make with this data. The Apple market-cap chart shows the effect: 38 of 674 company-years are off by a factor of 2 to 50 (8 for GE's reverse split) when today's share count is used with the historical price.

## Service levels this would need in production

- **Freshness:** facts appear within a day of the filing. `companyfacts` is updated as filings are processed.
- **Timestamp:** "known" is currently the filing date. Intraday-sensitive users need `acceptanceDateTime`.
- **Exception handling:** RED companies are reviewed before publishing. AMBER companies go in a weekly review queue.

## Field dictionary

Every fact is sourced from SEC XBRL `companyfacts` (`https://data.sec.gov/api/xbrl/companyfacts/CIK##########.json`), `us-gaap` taxonomy. Lineage: the raw fact is filtered to forms 10-K, 10-K/A, 10-Q and 10-Q/A. Flows are kept only for 350–380 day periods. Within a filing, the highest-priority tag is kept, and the result is stored in `fact` with its `accn` and `filed` date.

| Field | Definition | Period | XBRL tags (priority) | Unit |
|---|---|---|---|---|
| `revenue` | Total revenue for the fiscal year | annual | Revenues → RevenueFromContractWithCustomerExcludingAssessedTax → SalesRevenueNet → RevenueFromContractWithCustomerIncludingAssessedTax | USD |
| `net_income` | Net income attributable to the parent | annual | NetIncomeLoss | USD |
| `eps_diluted` | Diluted earnings per share | annual | EarningsPerShareDiluted | USD/share |
| `shares_diluted` | Weighted-average diluted shares; restated by later filings after splits | annual | WeightedAverageNumberOfDilutedSharesOutstanding | shares |
| `assets` | Total assets | quarter-end | Assets | USD |
| `liabilities` | Total liabilities (not tagged by every filer) | quarter-end | Liabilities | USD |
| `equity` | Stockholders' equity, parent only | quarter-end | StockholdersEquity | USD |
| `liab_and_equity` | Total liabilities and equity (balances to assets) | quarter-end | LiabilitiesAndStockholdersEquity | USD |
| `cash` | Cash and cash equivalents | quarter-end | CashAndCashEquivalentsAtCarryingValue | USD |

Market data comes from Yahoo's chart API (unofficial): monthly split-adjusted closes and split events. `close_raw` = the adjusted close × every split after that month. Spin-offs are recorded as splits with non-integer ratios. They are applied to prices and excluded from the share-count basis.

Security master: OpenFIGI mapping by today's ticker on US exchanges. It is not point-in-time, so delisted tickers don't resolve, and a reorganised issuer can resolve to a different legal entity (see XOM in the README).

## Known gaps, in the order a user would hit them

1. Multi-class issuers that report EPS and share counts only per class (Visa) have no `eps_diluted` or `shares_diluted`.
2. Predecessor filers (Google Inc. before Alphabet) aren't linked, so history starts at the newer CIK.
3. There are no quarterly flows yet. They need Q4 derived as the full year minus nine months.
4. Stale values (a number carried forward unchanged) and shifted periods (a neighbouring period's value) are not detected: on injected errors both rules and the z-score catch about 3%.
5. `companyfacts` can silently omit filings: Q2 2026 10-Qs for KO, V and XOM are missing. The missed-filing check catches this. Telling a late filer from a feed gap or a successor CIK needs the submissions API.
