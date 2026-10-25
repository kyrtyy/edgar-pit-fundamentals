# Point-in-time fundamentals

Fundamentals from SEC XBRL `companyfacts` for 50 US large caps over 2006–2026, including 7 later acquired (TWTR, ATVI, XLNX, CELG, MON, RTN, TWX). They are stored bitemporally so every reported version of a value is kept, linked to a FIGI security master and to market prices, then checked with rules, two anomaly detectors (robust z-score and isolation forest) and cross-dataset reconciliation.

- [`out/dashboard.html`](out/dashboard.html): scorecard, open exceptions, restatement history, charts
- [`out/report.md`](out/report.md): full results
- [`DATA_PRODUCT.md`](DATA_PRODUCT.md): who uses this data, what they need, and the field dictionary with lineage

## Findings

### Scale errors in SEC data, one still live
Four companies filed diluted share counts in the wrong unit. All are caught by the scale rule, the market-cap continuity check against prices, or both.

| company | periods | filed as | filings | status |
|---|---|---|---|---|
| McDonald's | FY2021–FY2025 | millions (751.8 for 751.8M) | every 10-K since `0000063908-24-000072` (Feb 2024) | **still wrong in the latest filing** |
| NVIDIA | FY2008–FY2011 | thousands | `0001045810-10-000006`, `0001045810-11-000015` | FY2010–11 corrected, FY2008–09 never |
| Merck | FY2010–FY2012 | millions | `0001193125-13-084618` | FY2011–12 corrected, FY2010 never |
| Monsanto | FY2009–FY2011 | millions | 10-Ks and 10-K/As from 2010–2012 | FY2011 corrected in 2013, FY2009–10 never |

Bank of America's FY2010 10-K (`0000950123-11-018743`) also reports total assets for 2008 as 0, overwriting $1.82T.

McDonald's shows a limit of the neighbour-based rules. When every recent year is wrong by the same factor, the neighbours agree with the error and only the first bad year stands out. The market-cap check catches it anyway, because the traded price doesn't move by 10⁶.

![NVIDIA share count](out/charts/nvda_scale_error.png)

### Most "restatements" aren't
Of 995 revisions of already-reported values: 510 are rounding, 380 are reclassifications or recasts (e.g. XOM and KO revenue), 76 are split-driven and 29 are amendments.

![Revisions by year](out/charts/revisions_by_year.png)

### Filings vs vendor market data
- **Splits:** all 19 splits inferred from filings of listed companies match a vendor split event. The restated figures first appeared 18–321 days after the split.
- **Spin-offs recorded as splits:** Yahoo records 7 spin-offs as "splits" with non-integer ratios: GE ×3, Merck/Organon, Pfizer/Viatris, IBM/Kyndryl and Verizon 2010. Share counts didn't change, so the filings correctly don't show them.
- **Delisted companies missing:** Yahoo and OpenFIGI have nothing for the 7 acquired companies, so vendor-side survivorship bias is visible. Celgene's 2015 2:1 split is in its filings but has no vendor record.
- **Two vendor splits with no filing match, both explained:** GOOGL 2014, because Google Inc. filed under a different CIK before Alphabet; and Visa 2015, because Visa reports EPS and share counts only per share class, which `companyfacts` omits.
- **Security master isn't point-in-time:** OpenFIGI now maps the XOM ticker to "ExxonMobil Holdings Corp". Exxon Mobil Corp (CIK 34088) filed an 8-K on 2026-07-01 (items 2.01, 3.01, 3.03) and a Form 25-NSE, and SEC no longer lists a ticker for that CIK. This is a holding-company reorganisation, so a join by today's ticker crosses legal entities.

![Split lag](out/charts/split_lag.png)

### Point-in-time matters for market cap
Market cap = traded price × diluted shares at fiscal year end. In 44 of 674 company-years, today's restated share count and the as-filed count give caps more than 15% apart:
- **38 are split-basis effects.** The restated count is on a later split basis than the price.
- **6 are the scale errors above** (McDonald's, Merck and NVIDIA).

Year-on-year share changes of more than 25% that no split explains: 8. Four are the scale errors, and four are real share issuance: AMD/Xilinx 2022, Merck/Schering-Plough 2010, Bank of America's 2009 capital raise (to repay TARP), and Verizon's 2014 buyout of Vodafone's stake in Verizon Wireless.

Other cases this handles:
- **Partially restated years:** Apple FY2012 was restated for the 2014 split but never for the 2020 one.
- **Splits between year end and filing:** Walmart's FY2024 10-K was filed after its 2024 split, so even the as-filed number is post-split.

![Apple market cap](out/charts/aapl_market_cap.png)

### Other checks
- **Accounting identity:** 9 breaches. For JPM 2009, a later filing revised Assets but not the matching total, so the latest-known snapshot doesn't balance. Costco is off by about 1.1% in four quarters of 2014–15, and BAC 2008 is the zero-assets error.
- **Anomaly flags:** 43 of 436 z-score flags on the real data come from share counts in years that were never restated after a split.
- **Missed filings:** SEC's feed is missing filings that were made. Coca-Cola, Visa and Exxon Mobil each filed a Q2 2026 10-Q with inline XBRL (29 Jul, 29 Jul and 3 Aug), but none are in `companyfacts` nearly three months later. Exxon's is explained by the reorganisation above. Coca-Cola and Visa still trade under the same CIK and ticker, so theirs look like plain feed gaps. A CIK-keyed dataset would silently stop updating, and only this check notices. The 7 acquired companies stop filing as expected and aren't flagged.

### Detection on injected errors
2% of values were corrupted with five error kinds, averaged over 5 seeds. The rules target scale and sign errors. Stale, drift and shifted-period errors are held out. The isolation forest is fit on scale-free features of every value (gap to the neighbour median, log-ratios to the adjacent periods, sign flip) across all series at once, and flags its top 3%.

| method | precision | recall | scale | sign | drift | stale | shift |
|---|---|---|---|---|---|---|---|
| rules | 94% | 35% | 99% | 75% | 0% | 0% | 0% |
| robust z (z > 6) | 30% | 52% | 100% | 94% | 57% | 3% | 1% |
| isolation forest (top 3%) | 28% | 42% | 100% | 99% | 5% | 3% | 1% |
| rules + robust z | 30% | 52% | 100% | 96% | 57% | 3% | 1% |
| rules + isolation forest | 28% | 42% | 100% | 100% | 5% | 3% | 1% |

The robust z-score beats the isolation forest at every threshold in the sweep below. The forest catches sign flips slightly better but misses most drifts. A 30% drift is ordinary across 50 companies' histories and only unusual within one series, and a per-series score sees that while a pooled model doesn't. Neither detector catches stale or shifted values. Adjacent years of fundamentals are close, so copying a neighbour's value looks normal. These need a cross-source check (the price-implied market cap, or the filing's own prior-year column) rather than a better outlier score.

![Detection tradeoff](out/charts/eval_tradeoff.png)

## Run

```
python -m venv .venv && .venv/bin/pip install pandas numpy tabulate matplotlib scikit-learn
export SEC_USER_AGENT="Your Name your@email"   # SEC asks for contact info
.venv/bin/python pit.py ingest                   # ~1-2 min: SEC, Yahoo, OpenFIGI -> facts.db
.venv/bin/python pit.py asof AAPL shares_diluted 2020-06-30
.venv/bin/python pit.py report                   # out/report.md, out/dashboard.html, CSVs, out/charts/
.venv/bin/python pit.py serve                    # point-in-time API on localhost:8000
.venv/bin/python pit.py selftest
```

## Point-in-time API

`GET /bdh?ticker=&fields=&start=&end=&as_of=` returns one row per period with one column per field. It uses only facts filed on or before `as_of`, which defaults to everything known. Apple, as known before and after its 2020 4:1 split:

```
$ curl 'localhost:8000/bdh?ticker=AAPL&fields=shares_diluted,eps_diluted&start=2018&end=2019-12-31&as_of=2020-06-30'
[{"end":"2018-09-29","shares_diluted":5000109000.0,"eps_diluted":11.91},{"end":"2019-09-28","shares_diluted":4648913000.0,"eps_diluted":11.89}]
$ curl 'localhost:8000/bdh?ticker=AAPL&fields=shares_diluted,eps_diluted&start=2018&end=2019-12-31'
[{"end":"2018-09-29","shares_diluted":20000435000.0,"eps_diluted":2.98},{"end":"2019-09-28","shares_diluted":18595651000.0,"eps_diluted":2.97}]
```

## Dashboard

[`out/dashboard.html`](out/dashboard.html) is regenerated by `report`. It shows the RAG scorecard, the open exceptions (rule flags, identity breaches, unexplained share jumps, missed filings and the top anomaly flags), the restatement history and the charts.

## Data model

| table | key | links to | source |
|---|---|---|---|
| `company` | `cik` | | SEC |
| `security` | `figi` | `company.cik` | OpenFIGI |
| `filing` | `accn` | `company.cik` | SEC |
| `fact` | `(cik, field, end, accn)` | `filing.accn`, `company.cik` | SEC XBRL |
| `price` | `(figi, month)` | `security.figi` | Yahoo, monthly; `close_raw` has splits undone |
| `vendor_splits` | `(ticker, date)` | | Yahoo |

`fact` is bitemporal: `end` is the period a value describes, and `filed` is when it became known. An as-of query takes the latest filing per `(cik, field, end)` with `filed <= as_of`. For example, Microsoft's market cap using only what was known on 2020-01-01:

```sql
SELECT c.name, s.figi, f.end, g.form, g.filed, f.val * p.close_raw / 1e9 AS cap_bn
FROM fact f
JOIN filing g   ON g.accn = f.accn
JOIN company c  ON c.cik = f.cik
JOIN security s ON s.cik = f.cik
JOIN price p    ON p.figi = s.figi AND p.month = substr(f.end, 1, 7)
WHERE c.ticker = 'MSFT' AND f.field = 'shares_diluted' AND g.filed <= '2020-01-01'
ORDER BY f.end DESC, g.filed DESC;
```

Fields and XBRL tags are listed in [`DATA_PRODUCT.md`](DATA_PRODUCT.md#field-dictionary).

## Checks

- **Revisions:** a later filing reports a different value for an already-reported period. Each is classified as `split` (the ratio is a split ratio on a share or per-share field), `amendment` (a /A form), `rounding` (<0.5%) or `other`.
- **Rules:** Assets vs LiabilitiesAndStockholdersEquity (>0.5%); scale (>300× off the neighbouring periods); negative values in fields that can't be negative.
- **Anomaly:** a robust z-score of each value's relative gap to the median of its neighbouring periods.
- **Split reconciliation:** vendor split events are matched to splits inferred from filings, by the same ratio within 450 days.
- **Market cap:** traded price × as-filed shares, moved to the period-end split basis. A year-on-year share change of more than 25% that no vendor split explains is flagged.
- **Missed filings:** more than 140 days without a 10-Q or 10-K (amendments count) since mid-2011, including the time from the last filing to the feed's latest filing date. Large accelerated filers file every ~3 months. Acquired companies that stop filing are labelled, not flagged.
- **Scorecard:** RED means an identity breach or a rule flag. AMBER means more than 3 unexplained anomaly flags per 100 values, more than 10 other or amended revisions, an unexplained share jump, or a missed filing.

## Known limitations

- Flows are annual only. 10-Q flows are year-to-date and Q4 isn't filed, so quarterly flows need derivation.
- "Known" means the day-level `filed` date, not `acceptanceDateTime`.
- The universe is hand-picked: 7 of 50 companies were later acquired, but it still leans towards survivors.
- The z-score uses future neighbours, so it is retrospective QA rather than a trading-time signal.
- Evaluation precision counts genuine anomalies already in the data (M&A, IPOs, buyback-driven negative equity) as false positives.
- `companyfacts` has no dimensional facts (per-class figures), and predecessor CIKs aren't linked.
- The security master maps by today's ticker. Yahoo's API is unofficial.
