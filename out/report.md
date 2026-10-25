# Point-in-time fundamentals: data-quality report

50 companies, 44005 observations (every reported version), 18022 latest-known values, periods 2006-09-24 to 2026-09-30.

## Revisions of already-reported values

| kind      |   count |
|:----------|--------:|
| rounding  |     510 |
| other     |     380 |
| split     |      76 |
| amendment |      29 |

## Splits detected from restated share counts / EPS

| ticker   | new_filed   |   split_ratio |
|:---------|:------------|--------------:|
| KO       | 2013-02-27  |         2     |
| NKE      | 2013-07-23  |         2     |
| MA       | 2014-02-14  |        10     |
| CRM      | 2014-03-05  |         4     |
| AAPL     | 2014-10-27  |         7     |
| CELG     | 2015-02-20  |         2     |
| NFLX     | 2016-01-28  |         7     |
| NKE      | 2016-07-21  |         2     |
| AAPL     | 2020-10-30  |         4     |
| TSLA     | 2021-02-08  |         5     |
| GE       | 2022-02-11  |         0.125 |
| NVDA     | 2022-03-18  |         4     |
| TSLA     | 2023-01-31  |         3     |
| AMZN     | 2023-02-03  |        20     |
| GOOGL    | 2023-02-03  |        20     |
| WMT      | 2024-03-15  |         3     |
| AVGO     | 2024-12-20  |        10     |
| CMG      | 2025-02-05  |        50     |
| NVDA     | 2025-02-26  |        10     |
| NFLX     | 2026-01-23  |        10     |

## Split reconciliation: filings vs vendor (Yahoo) split events since 2009-06

| status                                        |   count |
|:----------------------------------------------|--------:|
| matched                                       |      19 |
| spin-off adjustment (not expected in filings) |       7 |
| missing_in_filings                            |       2 |
| missing_in_vendor                             |       1 |

| ticker   | vendor_date   |    ratio | filings_filed   |   lag_days | status                                        |
|:---------|:--------------|---------:|:----------------|-----------:|:----------------------------------------------|
| AAPL     | 2014-06-09    |  7       | 2014-10-27      |        140 | matched                                       |
| AAPL     | 2020-08-31    |  4       | 2020-10-30      |         60 | matched                                       |
| AMZN     | 2022-06-06    | 20       | 2023-02-03      |        242 | matched                                       |
| GOOGL    | 2014-04-03    |  1.998   | nan             |        nan | missing_in_filings                            |
| GOOGL    | 2022-07-18    | 20       | 2023-02-03      |        200 | matched                                       |
| NVDA     | 2021-07-20    |  4       | 2022-03-18      |        241 | matched                                       |
| NVDA     | 2024-06-10    | 10       | 2025-02-26      |        261 | matched                                       |
| TSLA     | 2020-08-31    |  5       | 2021-02-08      |        161 | matched                                       |
| TSLA     | 2022-08-25    |  3       | 2023-01-31      |        159 | matched                                       |
| WMT      | 2024-02-26    |  3       | 2024-03-15      |         18 | matched                                       |
| V        | 2015-03-19    |  4       | nan             |        nan | missing_in_filings                            |
| KO       | 2012-08-13    |  2       | 2013-02-27      |        198 | matched                                       |
| NFLX     | 2015-07-15    |  7       | 2016-01-28      |        197 | matched                                       |
| NFLX     | 2025-11-17    | 10       | 2026-01-23      |         67 | matched                                       |
| AVGO     | 2024-07-15    | 10       | 2024-12-20      |        158 | matched                                       |
| CMG      | 2024-06-26    | 50       | 2025-02-05      |        224 | matched                                       |
| GE       | 2019-02-26    |  1.04    | nan             |        nan | spin-off adjustment (not expected in filings) |
| GE       | 2021-08-02    |  0.125   | 2022-02-11      |        193 | matched                                       |
| GE       | 2023-01-04    |  1.281   | nan             |        nan | spin-off adjustment (not expected in filings) |
| GE       | 2024-04-02    |  1.253   | nan             |        nan | spin-off adjustment (not expected in filings) |
| MA       | 2014-01-22    | 10       | 2014-02-14      |         23 | matched                                       |
| MRK      | 2021-06-03    |  1.048   | nan             |        nan | spin-off adjustment (not expected in filings) |
| PFE      | 2020-11-17    |  1.054   | nan             |        nan | spin-off adjustment (not expected in filings) |
| CRM      | 2013-04-18    |  4       | 2014-03-05      |        321 | matched                                       |
| NKE      | 2012-12-26    |  2       | 2013-07-23      |        209 | matched                                       |
| NKE      | 2015-12-24    |  2       | 2016-07-21      |        210 | matched                                       |
| VZ       | 2010-07-02    |  1.06622 | nan             |        nan | spin-off adjustment (not expected in filings) |
| IBM      | 2021-11-04    |  1.046   | nan             |        nan | spin-off adjustment (not expected in filings) |
| CELG     | nan           |  2       | 2015-02-20      |        nan | missing_in_vendor                             |

No vendor data (delisted): TWTR, ATVI, XLNX, CELG, MON, RTN, TWX

## Market cap: price x diluted shares at fiscal year end

674 company-years. Today's restated share count and the as-filed count give market caps more than 15% apart in 44 of them. 38 are exactly the later splits (today's count is on the wrong basis for the traded price); the other 6: MCD, MRK, NVDA.

Share-count changes of more than 25% not explained by a vendor split: 8

| ticker   | end        | filed      |            val |      shares_pe |   unexplained_share_change |
|:---------|:-----------|:-----------|---------------:|---------------:|---------------------------:|
| AMD      | 2022-12-31 | 2023-02-27 |    1.571e+09   |    1.571e+09   |                      1.278 |
| BAC      | 2010-12-31 | 2011-02-25 |    9.79047e+09 |    9.79047e+09 |                      1.267 |
| MCD      | 2023-12-31 | 2024-02-22 |  732.3         |  732.3         |                      0     |
| MRK      | 2010-12-31 | 2011-02-28 |    3.12e+09    |    3.12e+09    |                      1.373 |
| MRK      | 2012-12-31 | 2013-02-28 | 3076           | 3076           |                      0     |
| MRK      | 2013-12-31 | 2014-02-27 |    2.996e+09   |    2.996e+09   |                 973992     |
| NVDA     | 2012-01-29 | 2012-03-13 |    6.16371e+08 |    6.16371e+08 |                   1047.03  |
| VZ       | 2014-12-31 | 2015-02-23 |    3.981e+09   |    3.981e+09   |                      1.385 |

## Accounting identity breaches (Assets vs LiabilitiesAndStockholdersEquity, >0.5%): 9

|     cik | ticker   | end        |      assets |   liab_and_equity |           gap |
|--------:|:---------|:-----------|------------:|------------------:|--------------:|
|   19617 | JPM      | 2009-12-31 | 2.11967e+12 |       2.03199e+12 |    0.0413668  |
|   40545 | GE       | 2013-12-31 | 6.63247e+11 |       6.5656e+11  |    0.0100822  |
|   40545 | GE       | 2016-12-31 | 3.59122e+11 |       3.65183e+11 |   -0.0168773  |
|   70858 | BAC      | 2008-12-31 | 0           |       1.81794e+12 | -inf          |
|  909832 | COST     | 2014-08-31 | 3.2662e+10  |       3.3024e+10  |   -0.0110832  |
|  909832 | COST     | 2015-02-15 | 3.3217e+10  |       3.36e+10    |   -0.0115302  |
|  909832 | COST     | 2015-05-10 | 3.3109e+10  |       3.3491e+10  |   -0.0115376  |
|  909832 | COST     | 2015-11-22 | 3.5037e+10  |       3.5451e+10  |   -0.0118161  |
| 1326801 | META     | 2016-09-30 | 6.0007e+10  |       5.9674e+10  |    0.00554935 |

## Flags on real data (no injection): 436, of which 43 are explained by an unadjusted split basis

Rule flags:

| ticker   | field          | end        |           val | form   | filed      | accn                 |
|:---------|:---------------|:-----------|--------------:|:-------|:-----------|:---------------------|
| XOM      | equity         | 2012-06-01 |     -2.56e+08 | 10-Q   | 2012-11-06 | 0000034088-12-000050 |
| MCD      | shares_diluted | 2021-12-31 |    751.8      | 10-K   | 2024-02-22 | 0000063908-24-000072 |
| BAC      | assets         | 2008-12-31 |      0        | 10-K   | 2011-02-25 | 0000950123-11-018743 |
| MRK      | shares_diluted | 2010-12-31 |   3120        | 10-K   | 2013-02-28 | 0001193125-13-084618 |
| NVDA     | shares_diluted | 2008-01-27 | 606732        | 10-K   | 2010-03-18 | 0001045810-10-000006 |
| NVDA     | shares_diluted | 2009-01-25 | 548126        | 10-K   | 2011-03-16 | 0001045810-11-000015 |
| MON      | shares_diluted | 2009-08-31 |    555.6      | 10-K/A | 2011-12-01 | 0001193125-11-327542 |
| MON      | shares_diluted | 2010-08-31 |    550.8      | 10-K   | 2012-10-19 | 0001193125-12-428583 |

Top anomaly flags not explained by splits:

| ticker   | field           | end        |            val |     z |
|:---------|:----------------|:-----------|---------------:|------:|
| MCD      | shares_diluted  | 2021-12-31 |  751.8         | 130.6 |
| MCD      | shares_diluted  | 2020-12-31 |    7.501e+08   | 125.5 |
| MRK      | shares_diluted  | 2010-12-31 | 3120           | 118.3 |
| MRK      | shares_diluted  | 2008-12-31 |    2.143e+09   | 104.8 |
| V        | equity          | 2007-09-30 |   -5.01e+08    | 100.2 |
| V        | equity          | 2006-09-30 |    5.83e+08    |  92.3 |
| V        | equity          | 2008-09-30 |    2.1141e+10  |  79.1 |
| AMD      | equity          | 2007-12-29 |    3.23e+09    |  77.3 |
| BAC      | eps_diluted     | 2007-12-31 |    3.29        |  70.3 |
| XOM      | equity          | 2012-06-01 |   -2.56e+08    |  68.1 |
| XOM      | liab_and_equity | 2012-06-01 |    1.208e+10   |  61.3 |
| BAC      | assets          | 2008-12-31 |    0           |  55.5 |
| TWX      | net_income      | 2008-12-31 |   -1.3398e+10  |  55.1 |
| TWX      | eps_diluted     | 2008-12-31 |  -11.22        |  54   |
| TWTR     | shares_diluted  | 2012-12-31 |    1.17401e+08 |  52.1 |
| GOOGL    | assets          | 2026-06-30 |    9.21983e+11 |  44.9 |
| GOOGL    | liab_and_equity | 2026-06-30 |    9.21983e+11 |  44.9 |
| HD       | equity          | 2020-05-03 |   -3.49e+09    |  44   |
| ORCL     | equity          | 2021-11-30 |   -1.0101e+10  |  43.9 |
| HD       | equity          | 2022-05-01 |   -1.709e+09   |  42.4 |
| HD       | equity          | 2022-01-30 |   -1.696e+09   |  42.1 |
| GOOGL    | equity          | 2026-06-30 |    6.4048e+11  |  39.8 |
| HD       | equity          | 2019-02-03 |   -1.878e+09   |  35.4 |
| TWX      | assets          | 2008-12-31 |    1.14059e+11 |  34.9 |
| MRK      | assets          | 2009-12-31 |    1.12314e+11 |  33.8 |

## Missed filings (10-Q/10-K gap > 150 days since 2011-06): 3, plus 7 acquired companies that stopped filing

| ticker   | last_filed   | next_filed   |   gap_days | status                   |
|:---------|:-------------|:-------------|-----------:|:-------------------------|
| ATVI     | 2023-07-31   |              |       1180 | ceased filing (acquired) |
| CELG     | 2019-10-31   |              |       2549 | ceased filing (acquired) |
| KO       | 2026-04-30   |              |        176 | overdue                  |
| MON      | 2018-04-05   |              |       3123 | ceased filing (acquired) |
| RTN      | 2020-02-12   |              |       2445 | ceased filing (acquired) |
| TWTR     | 2022-07-26   |              |       1550 | ceased filing (acquired) |
| TWX      | 2018-04-26   |              |       3102 | ceased filing (acquired) |
| V        | 2026-04-29   |              |        177 | overdue                  |
| XLNX     | 2022-01-27   |              |       1730 | ceased filing (acquired) |
| XOM      | 2026-05-04   |              |        172 | overdue                  |

## Detector evaluation (injected errors, 2% of values, mean of 5 seeds, z > 6, iforest top 3%)

Rules target scale and sign errors; stale, drift and shift are held out.

| method           |   flagged |    tp |   precision |   recall |   recall_scale |   recall_sign |   recall_stale |   recall_drift |   recall_shift |
|:-----------------|----------:|------:|------------:|---------:|---------------:|--------------:|---------------:|---------------:|---------------:|
| rules            |     133.6 | 125.4 |       0.939 |    0.353 |          0.992 |         0.745 |          0.003 |          0     |          0.003 |
| robust_z         |     614.8 | 183.4 |       0.298 |    0.516 |          1     |         0.939 |          0.029 |          0.569 |          0.011 |
| iforest          |     541   | 150   |       0.277 |    0.422 |          1     |         0.994 |          0.029 |          0.05  |          0.011 |
| rules + robust_z |     617.4 | 184.8 |       0.299 |    0.52  |          1     |         0.956 |          0.031 |          0.569 |          0.011 |
| rules + iforest  |     542.4 | 150.4 |       0.277 |    0.423 |          1     |         0.997 |          0.032 |          0.05  |          0.011 |

Threshold sweep:

|                                |   precision |   recall |   recall_drift |
|:-------------------------------|------------:|---------:|---------------:|
| (4, 0.1, 'robust_z')           |       0.197 |    0.552 |          0.653 |
| (4, 0.1, 'iforest')            |       0.095 |    0.48  |          0.231 |
| (4, 0.1, 'rules + robust_z')   |       0.197 |    0.552 |          0.653 |
| (4, 0.1, 'rules + iforest')    |       0.095 |    0.48  |          0.231 |
| (6, 0.05, 'robust_z')          |       0.298 |    0.516 |          0.569 |
| (6, 0.05, 'iforest')           |       0.17  |    0.432 |          0.075 |
| (6, 0.05, 'rules + robust_z')  |       0.299 |    0.52  |          0.569 |
| (6, 0.05, 'rules + iforest')   |       0.17  |    0.432 |          0.075 |
| (8, 0.03, 'robust_z')          |       0.371 |    0.484 |          0.456 |
| (8, 0.03, 'iforest')           |       0.277 |    0.422 |          0.05  |
| (8, 0.03, 'rules + robust_z')  |       0.375 |    0.493 |          0.456 |
| (8, 0.03, 'rules + iforest')   |       0.277 |    0.423 |          0.05  |
| (12, 0.02, 'robust_z')         |       0.454 |    0.423 |          0.275 |
| (12, 0.02, 'iforest')          |       0.364 |    0.37  |          0.028 |
| (12, 0.02, 'rules + robust_z') |       0.466 |    0.451 |          0.275 |
| (12, 0.02, 'rules + iforest')  |       0.383 |    0.403 |          0.028 |
| (20, 0.01, 'robust_z')         |       0.559 |    0.362 |          0.075 |
| (20, 0.01, 'iforest')          |       0.415 |    0.211 |          0.008 |
| (20, 0.01, 'rules + robust_z') |       0.579 |    0.404 |          0.075 |
| (20, 0.01, 'rules + iforest')  |       0.541 |    0.36  |          0.008 |

## Scorecard

| ticker   |   observations | first      | last       |   identity_breaches |   rule_flags |   anomaly_flags |   restatements_other |   share_jumps |   missed_filings | rag   |
|:---------|---------------:|:-----------|:-----------|--------------------:|-------------:|----------------:|---------------------:|--------------:|-----------------:|:------|
| AAPL     |            433 | 2006-09-30 | 2026-06-27 |                   0 |            0 |               2 |                   17 |             0 |                0 | AMBER |
| ABBV     |            282 | 2010-12-31 | 2026-06-30 |                   0 |            0 |              19 |                    0 |             0 |                0 | AMBER |
| ADBE     |            438 | 2006-12-01 | 2026-08-28 |                   0 |            0 |              10 |                    3 |             0 |                0 | GREEN |
| AMD      |            339 | 2007-12-29 | 2026-06-27 |                   0 |            0 |              12 |                   10 |             1 |                0 | AMBER |
| AMZN     |            421 | 2006-12-31 | 2026-06-30 |                   0 |            0 |              11 |                    2 |             0 |                0 | GREEN |
| ATVI     |            348 | 2006-12-31 | 2023-06-30 |                   0 |            0 |               9 |                   11 |             0 |                0 | AMBER |
| AVGO     |            189 | 2015-11-01 | 2026-08-02 |                   0 |            0 |              11 |                    0 |             0 |                0 | AMBER |
| BA       |            398 | 2006-12-31 | 2026-06-30 |                   0 |            0 |              16 |                   11 |             0 |                0 | AMBER |
| BAC      |            409 | 2006-12-31 | 2026-06-30 |                   1 |            1 |              16 |                   23 |             1 |                0 | RED   |
| CAT      |            305 | 2006-12-31 | 2026-06-30 |                   0 |            0 |               4 |                    3 |             0 |                0 | GREEN |
| CELG     |            269 | 2006-12-31 | 2019-09-30 |                   0 |            0 |               5 |                    0 |             0 |                0 | GREEN |
| CMG      |            401 | 2007-12-31 | 2026-06-30 |                   0 |            0 |               6 |                    3 |             0 |                0 | GREEN |
| COST     |            428 | 2007-09-02 | 2026-08-30 |                   4 |            0 |               5 |                    7 |             0 |                0 | RED   |
| CRM      |            433 | 2007-01-31 | 2026-07-31 |                   0 |            0 |               7 |                   12 |             0 |                0 | AMBER |
| CSCO     |            428 | 2007-07-28 | 2026-07-25 |                   0 |            0 |               2 |                    0 |             0 |                0 | GREEN |
| CVX      |            423 | 2006-12-31 | 2026-06-30 |                   0 |            0 |              11 |                    4 |             0 |                0 | GREEN |
| GE       |            378 | 2006-12-31 | 2026-09-30 |                   2 |            0 |              10 |                   57 |             0 |                0 | RED   |
| GOOGL    |            272 | 2012-12-31 | 2026-06-30 |                   0 |            0 |              12 |                    2 |             0 |                0 | AMBER |
| HD       |            433 | 2007-01-28 | 2026-08-02 |                   0 |            0 |              18 |                    5 |             0 |                0 | AMBER |
| IBM      |            428 | 2006-12-31 | 2026-09-30 |                   0 |            0 |               2 |                   11 |             0 |                0 | AMBER |
| INTC     |            350 | 2006-12-30 | 2026-06-27 |                   0 |            0 |               6 |                    3 |             0 |                0 | GREEN |
| JNJ      |            368 | 2006-12-31 | 2026-09-27 |                   0 |            0 |               1 |                    6 |             0 |                0 | GREEN |
| JPM      |            367 | 2007-12-31 | 2026-06-30 |                   1 |            0 |               6 |                   13 |             0 |                0 | RED   |
| KO       |            348 | 2006-12-31 | 2026-04-03 |                   0 |            0 |               1 |                    8 |             0 |                1 | AMBER |
| LLY      |            342 | 2006-12-31 | 2026-06-30 |                   0 |            0 |               5 |                    6 |             0 |                0 | GREEN |
| MA       |            419 | 2006-12-31 | 2026-06-30 |                   0 |            0 |               3 |                    2 |             0 |                0 | GREEN |
| MCD      |            364 | 2006-12-31 | 2026-06-30 |                   0 |            1 |               7 |                    5 |             1 |                0 | RED   |
| META     |            364 | 2009-12-31 | 2026-09-30 |                   1 |            0 |              14 |                    7 |             0 |                0 | RED   |
| MON      |            187 | 2007-08-31 | 2018-02-28 |                   0 |            2 |               2 |                   18 |             0 |                0 | RED   |
| MRK      |            355 | 2006-12-31 | 2026-06-30 |                   0 |            1 |              17 |                   13 |             3 |                0 | RED   |
| MSFT     |            426 | 2007-06-30 | 2026-06-30 |                   0 |            0 |               2 |                   17 |             0 |                0 | AMBER |
| NFLX     |            439 | 2006-12-31 | 2026-09-30 |                   0 |            0 |               5 |                    1 |             0 |                0 | GREEN |
| NKE      |            362 | 2007-05-31 | 2026-08-31 |                   0 |            0 |               1 |                   16 |             0 |                0 | AMBER |
| NVDA     |            409 | 2007-01-28 | 2026-07-26 |                   0 |            2 |              13 |                    3 |             1 |                0 | RED   |
| ORCL     |            361 | 2007-05-31 | 2026-08-31 |                   0 |            0 |               7 |                    7 |             0 |                0 | GREEN |
| PEP      |            430 | 2006-12-30 | 2026-09-05 |                   0 |            0 |               8 |                    3 |             0 |                0 | GREEN |
| PFE      |            430 | 2006-12-31 | 2026-06-28 |                   0 |            0 |               9 |                   23 |             0 |                0 | AMBER |
| PG       |            334 | 2007-06-30 | 2026-09-30 |                   0 |            0 |               6 |                    9 |             0 |                0 | GREEN |
| QCOM     |            402 | 2006-09-24 | 2026-06-28 |                   0 |            0 |              10 |                    8 |             0 |                0 | GREEN |
| RTN      |            232 | 2006-12-31 | 2019-12-31 |                   0 |            0 |               2 |                   11 |             0 |                0 | AMBER |
| TSLA     |            378 | 2008-12-31 | 2026-09-30 |                   0 |            0 |              16 |                    0 |             0 |                0 | AMBER |
| TWTR     |            221 | 2011-12-31 | 2022-06-30 |                   0 |            0 |               5 |                    1 |             0 |                0 | GREEN |
| TWX      |            197 | 2006-12-31 | 2018-03-31 |                   0 |            0 |               9 |                   19 |             0 |                0 | AMBER |
| TXN      |            434 | 2006-12-31 | 2026-09-30 |                   0 |            0 |               3 |                    5 |             0 |                0 | GREEN |
| UNH      |            390 | 2006-12-31 | 2026-06-30 |                   0 |            0 |               1 |                    0 |             0 |                0 | GREEN |
| V        |            333 | 2006-09-30 | 2026-03-31 |                   0 |            0 |              19 |                    3 |             0 |                1 | AMBER |
| VZ       |            291 | 2006-12-31 | 2026-06-30 |                   0 |            0 |              15 |                    4 |             1 |                0 | AMBER |
| WMT      |            369 | 2008-01-31 | 2026-07-31 |                   0 |            0 |               1 |                    1 |             0 |                0 | GREEN |
| XLNX     |            255 | 2008-03-29 | 2022-01-01 |                   0 |            0 |               0 |                   12 |             0 |                0 | AMBER |
| XOM      |            410 | 2006-12-31 | 2026-03-31 |                   0 |            1 |              10 |                    4 |             0 |                1 | RED   |
