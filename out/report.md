# Point-in-time fundamentals: data-quality report

27 companies, 24124 observations (every reported version), 9837 latest-known values, periods 2006-09-30 to 2026-09-30.

## Revisions of already-reported values

| kind      |   count |
|:----------|--------:|
| rounding  |     234 |
| other     |     178 |
| split     |      57 |
| amendment |      17 |

## Splits detected from restated share counts / EPS

| ticker   | new_filed   |   split_ratio |
|:---------|:------------|--------------:|
| KO       | 2013-02-27  |         2     |
| AAPL     | 2014-10-27  |         7     |
| NFLX     | 2016-01-28  |         7     |
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

## Accounting identity breaches (Assets vs LiabilitiesAndStockholdersEquity, >0.5%): 4

|     cik | ticker   | end        |      assets |   liab_and_equity |         gap |
|--------:|:---------|:-----------|------------:|------------------:|------------:|
|   19617 | JPM      | 2009-12-31 | 2.11967e+12 |       2.03199e+12 |  0.0413668  |
|   40545 | GE       | 2013-12-31 | 6.63247e+11 |       6.5656e+11  |  0.0100822  |
|   40545 | GE       | 2016-12-31 | 3.59122e+11 |       3.65183e+11 | -0.0168773  |
| 1326801 | META     | 2016-09-30 | 6.0007e+10  |       5.9674e+10  |  0.00554935 |

## Flags on real data (no injection): 236, of which 30 are explained by an unadjusted split basis

Rule flags:

| ticker   | field          | end        |           val | form   | filed      | accn                 |
|:---------|:---------------|:-----------|--------------:|:-------|:-----------|:---------------------|
| XOM      | equity         | 2012-06-01 |     -2.56e+08 | 10-Q   | 2012-11-06 | 0000034088-12-000050 |
| NVDA     | shares_diluted | 2008-01-27 | 606732        | 10-K   | 2010-03-18 | 0001045810-10-000006 |
| NVDA     | shares_diluted | 2009-01-25 | 548126        | 10-K   | 2011-03-16 | 0001045810-11-000015 |

Top anomaly flags not explained by splits:

| ticker   | field           | end        |          val |     z |
|:---------|:----------------|:-----------|-------------:|------:|
| V        | equity          | 2007-09-30 | -5.01e+08    | 100.2 |
| V        | equity          | 2006-09-30 |  5.83e+08    |  92.3 |
| V        | equity          | 2008-09-30 |  2.1141e+10  |  79.1 |
| XOM      | equity          | 2012-06-01 | -2.56e+08    |  68.1 |
| XOM      | liab_and_equity | 2012-06-01 |  1.208e+10   |  61.3 |
| TWTR     | shares_diluted  | 2012-12-31 |  1.17401e+08 |  52.1 |
| GOOGL    | assets          | 2026-06-30 |  9.21983e+11 |  44.9 |
| GOOGL    | liab_and_equity | 2026-06-30 |  9.21983e+11 |  44.9 |
| HD       | equity          | 2020-05-03 | -3.49e+09    |  44   |
| ORCL     | equity          | 2021-11-30 | -1.0101e+10  |  43.9 |
| HD       | equity          | 2022-05-01 | -1.709e+09   |  42.4 |
| HD       | equity          | 2022-01-30 | -1.696e+09   |  42.1 |
| GOOGL    | equity          | 2026-06-30 |  6.4048e+11  |  39.8 |
| HD       | equity          | 2019-02-03 | -1.878e+09   |  35.4 |
| GE       | net_income      | 2018-12-31 | -2.2355e+10  |  32.8 |
| TWTR     | equity          | 2012-12-31 | -2.48172e+08 |  31.5 |
| META     | equity          | 2011-12-31 |  4.899e+09   |  31.4 |
| INTC     | eps_diluted     | 2024-12-28 | -4.38        |  29.8 |
| AMZN     | equity          | 2006-12-31 |  4.31e+08    |  29.5 |
| INTC     | net_income      | 2024-12-28 | -1.8756e+10  |  29.4 |
| CMG      | liabilities     | 2019-03-31 |  3.14168e+09 |  26   |
| AMZN     | equity          | 2007-12-31 |  1.197e+09   |  25.9 |
| HD       | equity          | 2018-10-28 |  1.32e+09    |  25.4 |
| CMG      | liabilities     | 2018-12-31 |  8.24179e+08 |  25.3 |
| GOOGL    | equity          | 2012-12-31 |  7.157e+10   |  22.9 |

## Detector evaluation (injected errors, 2% of values, mean of 5 seeds, z > 6)

Rules target scale and sign errors; stale and drift are held out.

| method   |   flagged |    tp |   precision |   recall |   recall_scale |   recall_sign |   recall_stale |   recall_drift |
|:---------|----------:|------:|------------:|---------:|---------------:|--------------:|---------------:|---------------:|
| rules    |      87.2 |  84.2 |       0.966 |    0.431 |          0.992 |         0.726 |          0     |          0     |
| robust_z |     350.6 | 125   |       0.357 |    0.64  |          1     |         0.947 |          0.029 |          0.575 |
| combined |     351.8 | 126.2 |       0.359 |    0.646 |          1     |         0.972 |          0.029 |          0.575 |

Threshold sweep:

|                  |   precision |   recall |   recall_drift |
|:-----------------|------------:|---------:|---------------:|
| (4, 'robust_z')  |       0.228 |    0.676 |          0.686 |
| (4, 'combined')  |       0.229 |    0.678 |          0.686 |
| (6, 'robust_z')  |       0.357 |    0.64  |          0.575 |
| (6, 'combined')  |       0.359 |    0.646 |          0.575 |
| (8, 'robust_z')  |       0.44  |    0.594 |          0.441 |
| (8, 'combined')  |       0.446 |    0.608 |          0.441 |
| (12, 'robust_z') |       0.531 |    0.512 |          0.233 |
| (12, 'combined') |       0.543 |    0.55  |          0.233 |
| (20, 'robust_z') |       0.628 |    0.435 |          0.045 |
| (20, 'combined') |       0.648 |    0.492 |          0.045 |

## Scorecard

| ticker   |   observations | first      | last       |   identity_breaches |   rule_flags |   anomaly_flags |   restatements_other | rag   |
|:---------|---------------:|:-----------|:-----------|--------------------:|-------------:|----------------:|---------------------:|:------|
| AAPL     |            433 | 2006-09-30 | 2026-06-27 |                   0 |            0 |               7 |                   17 | AMBER |
| AMZN     |            421 | 2006-12-31 | 2026-06-30 |                   0 |            0 |              13 |                    2 | AMBER |
| ATVI     |            348 | 2006-12-31 | 2023-06-30 |                   0 |            0 |               9 |                   11 | AMBER |
| AVGO     |            189 | 2015-11-01 | 2026-08-02 |                   0 |            0 |              14 |                    0 | AMBER |
| CMG      |            401 | 2007-12-31 | 2026-06-30 |                   0 |            0 |               8 |                    3 | AMBER |
| CSCO     |            428 | 2007-07-28 | 2026-07-25 |                   0 |            0 |               2 |                    0 | AMBER |
| GE       |            378 | 2006-12-31 | 2026-09-30 |                   2 |            0 |              13 |                   57 | RED   |
| GOOGL    |            272 | 2012-12-31 | 2026-06-30 |                   0 |            0 |              12 |                    2 | AMBER |
| HD       |            433 | 2007-01-28 | 2026-08-02 |                   0 |            0 |              18 |                    5 | AMBER |
| INTC     |            350 | 2006-12-30 | 2026-06-27 |                   0 |            0 |               6 |                    3 | AMBER |
| JNJ      |            363 | 2006-12-31 | 2026-06-28 |                   0 |            0 |               1 |                    6 | AMBER |
| JPM      |            367 | 2007-12-31 | 2026-06-30 |                   1 |            0 |               6 |                   13 | RED   |
| KO       |            348 | 2006-12-31 | 2026-04-03 |                   0 |            0 |               4 |                    8 | AMBER |
| META     |            359 | 2009-12-31 | 2026-06-30 |                   1 |            0 |              18 |                    7 | RED   |
| MSFT     |            426 | 2007-06-30 | 2026-06-30 |                   0 |            0 |               2 |                   17 | AMBER |
| NFLX     |            439 | 2006-12-31 | 2026-09-30 |                   0 |            0 |               9 |                    1 | AMBER |
| NVDA     |            409 | 2007-01-28 | 2026-07-26 |                   0 |            2 |              15 |                    3 | RED   |
| ORCL     |            361 | 2007-05-31 | 2026-08-31 |                   0 |            0 |               7 |                    7 | AMBER |
| PEP      |            430 | 2006-12-30 | 2026-09-05 |                   0 |            0 |               8 |                    3 | AMBER |
| PG       |            331 | 2007-06-30 | 2026-06-30 |                   0 |            0 |               6 |                    9 | AMBER |
| TSLA     |            373 | 2008-12-31 | 2026-06-30 |                   0 |            0 |              17 |                    0 | AMBER |
| TWTR     |            221 | 2011-12-31 | 2022-06-30 |                   0 |            0 |               7 |                    1 | AMBER |
| UNH      |            390 | 2006-12-31 | 2026-06-30 |                   0 |            0 |               1 |                    0 | AMBER |
| V        |            333 | 2006-09-30 | 2026-03-31 |                   0 |            0 |              19 |                    3 | AMBER |
| WMT      |            369 | 2008-01-31 | 2026-07-31 |                   0 |            0 |               4 |                    1 | AMBER |
| XLNX     |            255 | 2008-03-29 | 2022-01-01 |                   0 |            0 |               0 |                   12 | AMBER |
| XOM      |            410 | 2006-12-31 | 2026-03-31 |                   0 |            1 |              10 |                    4 | RED   |
