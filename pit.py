"""Point-in-time fundamentals from SEC XBRL companyfacts.

Usage:
  python pit.py ingest                 # fetch companyfacts -> facts.db
  python pit.py asof AAPL revenue 2019-06-30
  python pit.py serve [port]           # GET /bdh?ticker=&fields=&start=&end=&as_of=
  python pit.py report                 # restatements, checks, eval -> out/ (incl. dashboard.html)
  python pit.py selftest
"""
import json, os, sqlite3, sys, time, urllib.error, urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

DB = Path(__file__).with_name("facts.db")
OUT = Path(__file__).with_name("out")
UA = os.environ.get("SEC_USER_AGENT", "pit-fundamentals research")

# CIK is the stable key; tickers are labels only (they change, e.g. FB -> META).
# Includes a few companies that were later acquired, to avoid pure survivorship bias.
COMPANIES = {
    "AAPL": 320193, "MSFT": 789019, "AMZN": 1018724, "GOOGL": 1652044,
    "NVDA": 1045810, "TSLA": 1318605, "META": 1326801, "JPM": 19617,
    "JNJ": 200406, "WMT": 104169, "XOM": 34088, "PG": 80424,
    "V": 1403161, "UNH": 731766, "HD": 354950, "KO": 21344,
    "PEP": 77476, "INTC": 50863, "CSCO": 858877, "ORCL": 1341439,
    "NFLX": 1065280, "AVGO": 1730168, "CMG": 1058090, "GE": 40545,
    "LLY": 59478, "MA": 1141391, "ABBV": 1551152, "MRK": 310158,
    "PFE": 78003, "BAC": 70858, "CVX": 93410, "COST": 909832,
    "ADBE": 796343, "CRM": 1108524, "AMD": 2488, "MCD": 63908,
    "NKE": 320187, "VZ": 732712, "IBM": 51143, "QCOM": 804328,
    "TXN": 97476, "BA": 12927, "CAT": 18230,
    "TWTR": 1418091, "ATVI": 718877, "XLNX": 743988,
    "CELG": 816284, "MON": 1110783, "RTN": 1047122, "TWX": 1105705,
}
ACQUIRED = {"TWTR", "ATVI", "XLNX", "CELG", "MON", "RTN", "TWX"}  # stop filing by design, not a missed deadline

# canonical field -> (kind, tags in priority order). Flows are annual only:
# 10-Q flows are year-to-date and Q4 is never filed, so quarterly flows need derivation.
FIELDS = {
    "revenue": ("flow", ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax",
                         "SalesRevenueNet", "RevenueFromContractWithCustomerIncludingAssessedTax"]),
    "net_income": ("flow", ["NetIncomeLoss"]),
    "eps_diluted": ("flow", ["EarningsPerShareDiluted"]),
    "shares_diluted": ("flow", ["WeightedAverageNumberOfDilutedSharesOutstanding"]),
    "assets": ("instant", ["Assets"]),
    "liabilities": ("instant", ["Liabilities"]),
    "equity": ("instant", ["StockholdersEquity"]),
    "liab_and_equity": ("instant", ["LiabilitiesAndStockholdersEquity"]),
    "cash": ("instant", ["CashAndCashEquivalentsAtCarryingValue"]),
}
NONNEG = {"revenue", "shares_diluted", "assets", "liabilities", "liab_and_equity", "cash"}
SPLIT_FIELDS = {"eps_diluted": -1, "shares_diluted": 1}  # direction values move on a split
SPLIT_RATIOS = [2, 3, 4, 5, 7, 8, 10, 15, 20, 50]
FORMS = ("10-K", "10-K/A", "10-Q", "10-Q/A")


# ---------- ingest ----------

def fetch(cik):
    url = f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik:010d}.json"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def ingest():
    tag_field = {t: (f, k, i) for f, (k, tags) in FIELDS.items() for i, t in enumerate(tags)}
    rows, names = [], {}
    for ticker, cik in COMPANIES.items():
        data = fetch(cik)
        names[cik] = data["entityName"]
        print(f"{ticker:6} {data['entityName']}")
        for tag, body in data["facts"].get("us-gaap", {}).items():
            if tag not in tag_field:
                continue
            field, kind, prio = tag_field[tag]
            for unit, obs in body["units"].items():
                for o in obs:
                    if o["form"] not in FORMS:
                        continue
                    start = o.get("start")
                    if kind == "flow":
                        days = (pd.Timestamp(o["end"]) - pd.Timestamp(start)).days
                        if not 350 <= days <= 380:
                            continue
                    rows.append((cik, ticker, field, tag, prio, unit, start, o["end"],
                                 o["val"], o["accn"], o["form"], o["filed"]))
        time.sleep(0.2)  # SEC fair-access limit
    df = pd.DataFrame(rows, columns=["cik", "ticker", "field", "tag", "prio", "unit", "start",
                                     "end", "val", "accn", "form", "filed"])
    # One value per (company, field, period, filing): highest-priority tag wins.
    df = (df.sort_values("prio")
            .drop_duplicates(["cik", "field", "end", "accn"])
            .drop(columns="prio"))
    fetched = {t: fetch_vendor(t) for t in COMPANIES}
    vs = pd.DataFrame([s for v in fetched.values() if v for s in v[0]], columns=["ticker", "date", "ratio"])
    cov = pd.DataFrame({"ticker": list(fetched), "covered": [v is not None for v in fetched.values()]})
    security = fetch_figi(COMPANIES)
    figi = dict(zip(security.ticker, security.figi))
    price = pd.DataFrame([p for v in fetched.values() if v for p in v[1]], columns=["ticker", "month", "close_adj"])
    price["figi"] = price.ticker.map(figi)
    # Yahoo closes are split-adjusted; undo every split after the bar's month to get the traded price.
    price["close_raw"] = [c * np.prod(vs.ratio[(vs.ticker == t) & (vs.date.str[:7] > m)])
                          for t, m, c in zip(price.ticker, price.month, price.close_adj)]
    company = pd.DataFrame({"cik": list(COMPANIES.values()), "ticker": list(COMPANIES),
                            "name": [names[c] for c in COMPANIES.values()]})
    filing = df[["accn", "cik", "form", "filed"]].drop_duplicates("accn")
    with sqlite3.connect(DB) as con:
        for name, t in [("company", company), ("security", security), ("filing", filing),
                        ("fact", df), ("price", price), ("vendor_splits", vs), ("vendor_coverage", cov)]:
            t.to_sql(name, con, if_exists="replace", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS ix ON fact(cik, field, end, filed)")
    print(f"{len(df)} facts, {len(filing)} filings, {len(security)} securities, "
          f"{len(price)} monthly prices, {len(vs)} vendor split events -> {DB}")


def fetch_vendor(ticker):
    """Monthly closes and split events from Yahoo's (unofficial) chart API: the market-data side."""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
           f"?period1=1230768000&period2={int(time.time())}&interval=1mo&events=split")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    time.sleep(0.5)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            res = json.load(r)["chart"]["result"]
    except urllib.error.HTTPError:  # delisted tickers 404
        return None
    if not res:
        return None
    r = res[0]
    splits = [(ticker, pd.Timestamp(s["date"], unit="s").strftime("%Y-%m-%d"), s["numerator"] / s["denominator"])
              for s in r.get("events", {}).get("splits", {}).values()]
    prices = [(ticker, pd.Timestamp(ts, unit="s").strftime("%Y-%m"), c)
              for ts, c in zip(r.get("timestamp", []), r["indicators"]["quote"][0]["close"]) if c is not None]
    return splits, prices


def fetch_figi(tickers):
    """Security master rows from OpenFIGI (no API key: 10 jobs per request)."""
    rows, tickers = [], list(tickers)
    for i in range(0, len(tickers), 10):
        chunk = tickers[i:i + 10]
        body = json.dumps([{"idType": "TICKER", "idValue": t, "exchCode": "US"} for t in chunk]).encode()
        req = urllib.request.Request("https://api.openfigi.com/v3/mapping", data=body,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as r:
            for t, res in zip(chunk, json.load(r)):
                for d in res.get("data", [])[:1]:  # delisted tickers return a warning, no data
                    rows.append(dict(figi=d["figi"], share_class_figi=d.get("shareClassFIGI"), ticker=t,
                                     cik=COMPANIES[t], name=d["name"], security_type=d.get("securityType")))
        time.sleep(3)
    return pd.DataFrame(rows)


# ---------- point-in-time ----------
# obs is bitemporal: `end` is the period described (valid time), `filed` is when it became
# known (transaction time). ponytail: day-level `filed`; use acceptanceDateTime from the
# submissions API if intraday look-ahead matters.

ASOF_SQL = """
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY cik, field, end ORDER BY filed DESC, accn DESC) rn
  FROM fact WHERE filed <= :as_of {where}
) WHERE rn = 1 ORDER BY cik, field, end
"""


def as_of(con, as_of_date, ticker=None, field=None):
    where, params = "", {"as_of": as_of_date}
    if ticker:
        where += " AND ticker = :ticker"; params["ticker"] = ticker
    if field:
        where += " AND field = :field"; params["field"] = field
    return pd.read_sql(ASOF_SQL.format(where=where), con, params=params).drop(columns="rn")


def bdh(con, ticker, fields, start, end, as_of_date):
    """BDH-style history: one row per period in [start, end], one column per field, using
    only what was filed on or before as_of_date."""
    d = as_of(con, as_of_date, ticker)
    d = d[d.field.isin(fields) & (d.end >= start) & (d.end <= end)]
    return d.pivot_table(index="end", columns="field", values="val").reindex(columns=fields).reset_index()


def serve(port=8000):
    """GET /bdh?ticker=AAPL&fields=revenue,eps_diluted&start=2015-01-01&end=2020-12-31&as_of=2019-06-30"""
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib.parse import parse_qs, urlparse

    class H(BaseHTTPRequestHandler):
        def do_GET(self):
            u = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                if u.path != "/bdh":
                    raise LookupError("only /bdh")
                fields = q["fields"].split(",")
                unknown = set(fields) - set(FIELDS)
                if unknown:
                    raise ValueError(f"unknown fields: {sorted(unknown)}")
                with sqlite3.connect(DB) as con:
                    df = bdh(con, q["ticker"], fields, q.get("start", "0000"), q.get("end", "9999"),
                             q.get("as_of", "9999-12-31"))
                code, body = 200, df.to_json(orient="records")
            except (KeyError, ValueError, LookupError) as e:
                code, body = 400, json.dumps({"error": str(e)})
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body.encode())

    print(f"http://localhost:{port}/bdh?ticker=AAPL&fields=revenue,shares_diluted&as_of=2020-06-30")
    HTTPServer(("127.0.0.1", port), H).serve_forever()


def load(con):
    return pd.read_sql("SELECT * FROM fact", con)


# ---------- restatements ----------

def split_ratio(old, new, direction, tol=0.02):
    if old == 0 or new == 0 or np.sign(old) != np.sign(new):
        return None
    r = (new / old) if direction > 0 else (old / new)
    for s in SPLIT_RATIOS:
        if abs(r / s - 1) < tol:
            return s
        if abs(r * s - 1) < tol:  # reverse split, e.g. GE 1-for-8
            return 1 / s
    return None


def revisions(obs):
    """Every time a later filing reports a different value for an already-reported period."""
    out = []
    for (cik, field, end), g in obs.sort_values(["filed", "accn"]).groupby(["cik", "field", "end"]):
        prev = None
        for r in g.itertuples():
            if prev is not None and not np.isclose(r.val, prev.val, rtol=1e-9):
                ratio = split_ratio(prev.val, r.val, SPLIT_FIELDS[field]) if field in SPLIT_FIELDS else None
                kind = ("split" if ratio else "amendment" if r.form.endswith("/A")
                        else "rounding" if np.isclose(r.val, prev.val, rtol=5e-3)
                        else "other")
                out.append(dict(cik=cik, ticker=r.ticker, field=field, end=end, old=prev.val,
                                new=r.val, old_filed=prev.filed, new_filed=r.filed,
                                new_form=r.form, kind=kind, split_ratio=ratio))
            prev = r
    return pd.DataFrame(out)


def reconcile_splits(filing_splits, vendor, since="2009-06-01", max_lag=450):
    """Match vendor split events to splits inferred from restated filings.
    Non-integer vendor ratios (e.g. GE 1281:1000) are spin-off price adjustments, which
    don't change share counts, so filings aren't expected to show them."""
    rows, used = [], set()
    for v in vendor[vendor.date >= since].itertuples():
        r = v.ratio if v.ratio >= 1 else 1 / v.ratio
        integer = abs(r - round(r)) < 0.01
        cand = filing_splits[(filing_splits.ticker == v.ticker)
                             & (abs(filing_splits.split_ratio / v.ratio - 1) < 0.02)]
        lag = (pd.to_datetime(cand.new_filed) - pd.Timestamp(v.date)).dt.days
        cand = cand[(lag >= 0) & (lag <= max_lag)]
        if len(cand):
            i = cand.index[0]; used.add(i)
            rows.append(dict(ticker=v.ticker, vendor_date=v.date, ratio=v.ratio, filings_filed=cand.at[i, "new_filed"],
                             lag_days=(pd.Timestamp(cand.at[i, "new_filed"]) - pd.Timestamp(v.date)).days,
                             status="matched"))
        else:
            rows.append(dict(ticker=v.ticker, vendor_date=v.date, ratio=v.ratio,
                             status="missing_in_filings" if integer else "spin-off adjustment (not expected in filings)"))
    for f in filing_splits.drop(index=list(used)).itertuples():
        rows.append(dict(ticker=f.ticker, ratio=f.split_ratio, filings_filed=f.new_filed, status="missing_in_vendor"))
    return pd.DataFrame(rows)


def splits_between(vendor, ticker, after, upto):
    v = vendor[(vendor.ticker == ticker) & (vendor.date > after) & (vendor.date <= upto)]
    return float(np.prod(v.ratio))


def market_cap(fact, price, vendor, jump=0.25):
    """Price x diluted shares at each fiscal year end, two ways:
    pit   - the first-reported share count, put on the period-end basis (a split between
            year end and the filing date is already baked into the filed number);
    naive - today's restated share count, which is on a later split basis.
    A share-count jump between years must be explained by a vendor split, or it's flagged."""
    r = np.maximum(vendor.ratio, 1 / vendor.ratio)
    vendor = vendor[np.abs(r - r.round()) < 0.01]  # spin-off price adjustments don't change share counts
    sh = fact[fact.field == "shares_diluted"].sort_values(["filed", "accn"])
    first = sh.drop_duplicates(["cik", "end"])
    latest = sh.drop_duplicates(["cik", "end"], keep="last")[["cik", "end", "val"]].rename(columns={"val": "val_latest"})
    m = first.merge(latest, on=["cik", "end"]).assign(month=lambda d: d.end.str[:7])
    m = m.merge(price[["ticker", "month", "close_raw"]], on=["ticker", "month"]).sort_values(["ticker", "end"])
    m["shares_pe"] = [v / splits_between(vendor, t, e, f) for t, e, f, v in zip(m.ticker, m.end, m.filed, m.val)]
    m["cap_pit"] = m.shares_pe * m.close_raw
    m["cap_naive"] = m.val_latest * m.close_raw
    m["naive_error"] = m.cap_naive / m.cap_pit
    # A restated count reflects the first k splits after the period (old years stop being
    # re-reported), so the gap should equal one of the running products of those splits.
    def is_later_splits(t, end, err):
        r = vendor[(vendor.ticker == t) & (vendor.date > end)].sort_values("date").ratio
        return bool(np.isclose(err, np.cumprod(r), rtol=0.02).any())
    m["naive_error_is_later_splits"] = [is_later_splits(t, e, x) for t, e, x in zip(m.ticker, m.end, m.naive_error)]
    prev = m.groupby("ticker")[["end", "shares_pe"]].shift()
    expected = [splits_between(vendor, t, pe, e) if pd.notna(pe) else np.nan
                for t, pe, e in zip(m.ticker, prev.end, m.end)]
    m["unexplained_share_change"] = m.shares_pe / prev.shares_pe / expected
    m["flag"] = (np.abs(np.log(m.unexplained_share_change)) > np.log(1 + jump)).fillna(False)
    return m[["ticker", "end", "filed", "close_raw", "val", "shares_pe", "val_latest",
              "cap_pit", "cap_naive", "naive_error", "naive_error_is_later_splits", "unexplained_share_change", "flag"]]


# ---------- quality: rules + robust z-score ----------

def series(snap):
    """Latest-known value per period, one row per (cik, field, end)."""
    return snap.sort_values(["cik", "field", "end"]).reset_index(drop=True)


def neighbour_median(v, k):
    """Median of up to k values each side of each point, excluding the point itself."""
    return np.array([np.median(np.r_[v[max(0, i - k):i], v[i + 1:i + 1 + k]]) if len(v) > 1 else v[i]
                     for i in range(len(v))])


def rules(s):
    flags = pd.DataFrame(index=s.index)
    # Compare to neighbouring periods, not the whole history, so real growth isn't a "scale error".
    nb = s.groupby(["cik", "field"])["val"].transform(lambda v: neighbour_median(np.abs(v.to_numpy(float)), 3))
    ratio = s["val"].abs() / nb.replace(0, np.nan)
    flags["scale"] = (ratio > 300) | (ratio < 1 / 300)
    flags["sign"] = s["field"].isin(NONNEG) & (s["val"] < 0)
    return flags


def identity_breaches(s, tol=0.005):
    w = s[s.field.isin(["assets", "liab_and_equity"])].pivot_table(
        index=["cik", "ticker", "end"], columns="field", values="val").dropna()
    w["gap"] = (w.assets - w.liab_and_equity) / w.assets
    return w[w.gap.abs() > tol].reset_index()


def missed_filings(filing, company, today, max_gap=150, since="2011-06-15"):
    """Expected 10-Q/10-K that hasn't arrived. Large accelerated filers file a 10-Q within
    40 days of quarter end and a 10-K within 60 of year end, so consecutive filings are
    ~3 months apart (16-week fiscal quarters, e.g. Costco, stretch that to ~140 days),
    so >150 days means one is missing. Starts after XBRL phase-in."""
    rows = []
    f = filing[filing.form.isin(FORMS)].merge(company[["cik", "ticker"]], on="cik")  # e.g. MSFT Jan 2012 is a 10-Q/A
    for t, g in f[f.filed >= since].groupby("ticker"):
        d = pd.to_datetime(g.filed).sort_values().tolist() + [pd.Timestamp(today)]
        for a, b in zip(d, d[1:]):
            gap = (b - a).days
            if gap > max_gap:
                last = b == d[-1]
                rows.append(dict(ticker=t, last_filed=a.date().isoformat(), next_filed=None if last else b.date().isoformat(),
                                 gap_days=gap, status="ceased filing (acquired)" if last and t in ACQUIRED
                                 else "overdue" if last else "gap"))
    return pd.DataFrame(rows, columns=["ticker", "last_filed", "next_filed", "gap_days", "status"])


def robust_z(s, k=2, min_len=6):
    """|z| of each point's relative gap to the median of its k neighbours each side, scaled by
    the series' robust spread. Uses future neighbours: this is retrospective QA, not a signal."""
    z = pd.Series(0.0, index=s.index)
    for _, g in s.groupby(["cik", "field"]):
        v = g["val"].to_numpy(float)
        if len(v) < min_len:
            continue
        nb = neighbour_median(v, k)
        # Local scale so growth companies aren't flagged; floor it for values that cross zero.
        e = (v - nb) / np.maximum(np.abs(nb), 0.1 * np.median(np.abs(v)) + 1e-9)
        mad = 1.4826 * np.median(np.abs(e - np.median(e)))
        z[g.index] = np.abs(e - np.median(e)) / max(mad, 1e-3)
    return z


def features(s, k=2):
    """Scale-free per-value features, so one model can be fit across all series:
    gap to the neighbour median, log-ratio to it and to each adjacent period, sign flip."""
    cols = ["gap", "log_nb", "log_prev", "log_next", "sign_flip"]
    X = pd.DataFrame(0.0, index=s.index, columns=cols)
    for _, g in s.groupby(["cik", "field"]):
        v = g["val"].to_numpy(float)
        nb = neighbour_median(v, k)
        a = np.log(np.abs(v) + 1e-9)
        X.loc[g.index, cols] = np.c_[
            (v - nb) / np.maximum(np.abs(nb), 0.1 * np.median(np.abs(v)) + 1e-9),
            a - np.log(np.abs(nb) + 1e-9), np.r_[0, np.diff(a)], np.r_[np.diff(a), 0],
            np.sign(v) != np.sign(nb)]
    return X.clip(-50, 50)


def iforest(s, seed=0):
    """Isolation-forest anomaly score (higher = more anomalous), fit on all series pooled."""
    from sklearn.ensemble import IsolationForest
    X = features(s)
    return pd.Series(-IsolationForest(n_estimators=300, random_state=seed, n_jobs=-1).fit(X).score_samples(X),
                     index=s.index)


# ---------- evaluation with injected errors ----------

ERR_KINDS = ["scale", "sign", "stale", "drift", "shift"]  # rules target scale+sign; the rest held out


def inject(s, rate=0.02, seed=0):
    rng = np.random.default_rng(seed)
    s = s.copy()
    s["err"] = ""
    idx = rng.choice(s.index, size=int(len(s) * rate), replace=False)
    for n, i in enumerate(idx):
        kind, v = ERR_KINDS[n % len(ERR_KINDS)], s.at[i, "val"]
        same = s[(s.cik == s.at[i, "cik"]) & (s.field == s.at[i, "field"])]
        if kind in ("stale", "shift"):  # previous period carried forward / next period's value
            other = same[same.end < s.at[i, "end"]] if kind == "stale" else same[same.end > s.at[i, "end"]]
            if other.empty:
                continue
            new = other["val"].iloc[-1 if kind == "stale" else 0]
        else:
            new = {"scale": v * 1000, "sign": -v, "drift": v * rng.choice([0.7, 1.3])}[kind]
        if new == v:
            continue
        s.at[i, "val"], s.at[i, "err"] = new, kind
    return s


def pr(flag, truth):
    tp = (flag & truth).sum()
    return dict(flagged=int(flag.sum()), tp=int(tp),
                precision=round(tp / max(flag.sum(), 1), 3), recall=round(tp / max(truth.sum(), 1), 3))


def evaluate(s, z_thresh=6.0, if_rate=0.03, seeds=range(5)):
    """if_rate: the isolation forest flags its top if_rate share of values."""
    rows = []
    for seed in seeds:
        d = inject(s, seed=seed)
        truth = d["err"] != ""
        r = rules(d).any(axis=1)
        z = robust_z(d) > z_thresh
        f = iforest(d, seed)
        f = f > f.quantile(1 - if_rate)
        for name, flag in [("rules", r), ("robust_z", z), ("iforest", f),
                           ("rules + robust_z", r | z), ("rules + iforest", r | f)]:
            row = dict(seed=seed, method=name, **pr(flag, truth))
            for kind in ERR_KINDS:
                m = d["err"] == kind
                row[f"recall_{kind}"] = round((flag & m).sum() / max(m.sum(), 1), 3)
            rows.append(row)
    res = pd.DataFrame(rows)
    return res.drop(columns="seed").groupby("method", sort=False).mean().round(3)


# ---------- report ----------

def report():
    OUT.mkdir(exist_ok=True)
    con = sqlite3.connect(DB)
    obs = load(con)
    snap = series(as_of(con, "9999-12-31"))

    rev = revisions(obs)
    rev.to_csv(OUT / "revisions.csv", index=False)
    splits = (rev[rev.kind == "split"].sort_values("new_filed")
                 .drop_duplicates(["cik", "new_filed", "split_ratio"])
                 [["ticker", "new_filed", "split_ratio"]])
    splits.to_csv(OUT / "splits_detected.csv", index=False)
    vendor = pd.read_sql("SELECT * FROM vendor_splits", con)
    recon = reconcile_splits(splits, vendor)
    no_vendor = pd.read_sql("SELECT ticker FROM vendor_coverage WHERE NOT covered", con).ticker.tolist()
    recon.to_csv(OUT / "split_reconciliation.csv", index=False)
    mc = market_cap(obs, pd.read_sql("SELECT * FROM price", con), vendor)
    mc.to_csv(OUT / "market_cap.csv", index=False)
    naive_bad = mc[np.abs(np.log(mc.naive_error)) > np.log(1.15)]

    ident = identity_breaches(snap)
    ident.to_csv(OUT / "identity_breaches.csv", index=False)
    # "Today" is the feed's latest filing date, so a re-run on the same facts.db reproduces.
    filing = pd.read_sql("SELECT * FROM filing", con)
    missed = missed_filings(filing, pd.read_sql("SELECT * FROM company", con), filing.filed.max())
    missed.to_csv(OUT / "missed_filings.csv", index=False)
    late = missed[missed.status != "ceased filing (acquired)"]
    rf = rules(snap)
    z = robust_z(snap)
    real = snap.assign(scale=rf.scale, sign=rf.sign, z=z.round(1))
    # Old periods that were never restated after a split sit on a different share basis.
    # Looser tolerance: adjacent years also differ by a year of buybacks/issuance.
    prev = real.groupby(["cik", "field"])["val"].shift()
    real["split_basis"] = [f in SPLIT_FIELDS and pd.notna(p) and split_ratio(p, v, SPLIT_FIELDS[f], 0.1) is not None
                           for f, p, v in zip(real.field, prev, real.val)]
    nxt = real.groupby(["cik", "field"])["split_basis"].shift(-1, fill_value=False)
    real["split_basis"] |= nxt.astype(bool)
    real_flags = real[real.scale | real.sign | (real.z > 6)]
    real_flags.to_csv(OUT / "real_data_flags.csv", index=False)

    ev = evaluate(snap)
    ev.to_csv(OUT / "eval.csv")
    # Each step tightens both detectors: z threshold up, iforest flag rate down.
    sweep = pd.concat({(t, q): evaluate(snap, z_thresh=t, if_rate=q).loc[
                           ["robust_z", "iforest", "rules + robust_z", "rules + iforest"],
                           ["precision", "recall", "recall_drift"]]
                       for t, q in [(4, 0.1), (6, 0.05), (8, 0.03), (12, 0.02), (20, 0.01)]},
                      names=["z_thresh", "if_rate"])
    sweep.to_csv(OUT / "eval_sweep.csv")

    # RAG scorecard per company
    sc = snap.groupby("ticker").agg(observations=("val", "size"), first=("end", "min"), last=("end", "max"))
    sc["identity_breaches"] = ident.groupby("ticker").size()
    sc["rule_flags"] = real_flags[real_flags.scale | real_flags.sign].groupby("ticker").size()
    unexplained = real_flags[(real_flags.z > 6) & ~real_flags.split_basis]
    sc["anomaly_flags"] = unexplained.groupby("ticker").size()
    sc["restatements_other"] = rev[rev.kind.isin(["other", "amendment"])].groupby("ticker").size()
    sc["share_jumps"] = mc[mc.flag].groupby("ticker").size()
    sc["missed_filings"] = late.groupby("ticker").size()
    counts = ["identity_breaches", "rule_flags", "anomaly_flags", "restatements_other", "share_jumps", "missed_filings"]
    sc = sc.fillna(0).astype({c: int for c in counts})
    # Anomaly flags are a review queue, not errors: amber once they're dense (per 100 values).
    density = 100 * sc.anomaly_flags / sc.observations
    sc["rag"] = np.where(sc.identity_breaches + sc.rule_flags > 0, "RED",
                np.where((density > 3) | (sc.restatements_other > 10) | (sc.share_jumps > 0) | (sc.missed_filings > 0),
                         "AMBER", "GREEN"))
    sc.to_csv(OUT / "scorecard.csv")

    md = [
        "# Point-in-time fundamentals: data-quality report", "",
        f"{obs.cik.nunique()} companies, {len(obs)} observations (every reported version), "
        f"{len(snap)} latest-known values, periods {snap.end.min()} to {snap.end.max()}.", "",
        "## Revisions of already-reported values", "", rev.kind.value_counts().to_frame("count").to_markdown(), "",
        "## Splits detected from restated share counts / EPS", "", splits.to_markdown(index=False), "",
        "## Split reconciliation: filings vs vendor (Yahoo) split events since 2009-06", "",
        recon.status.value_counts().to_frame("count").to_markdown(), "",
        recon.to_markdown(index=False), "",
        f"No vendor data (delisted): {', '.join(no_vendor) or 'none'}", "",
        "## Market cap: price x diluted shares at fiscal year end", "",
        f"{len(mc)} company-years. Today's restated share count and the as-filed count give market caps "
        f"more than 15% apart in {len(naive_bad)} of them. {int(naive_bad.naive_error_is_later_splits.sum())} "
        f"are exactly the later splits (today's count is on the wrong basis for the traded price); "
        f"the other {int((~naive_bad.naive_error_is_later_splits).sum())}: "
        f"{', '.join(sorted(set(naive_bad.ticker[~naive_bad.naive_error_is_later_splits]))) or 'none'}.", "",
        f"Share-count changes of more than 25% not explained by a vendor split: {int(mc.flag.sum())}", "",
        mc[mc.flag][["ticker", "end", "filed", "val", "shares_pe", "unexplained_share_change"]]
            .round(3).to_markdown(index=False), "",
        f"## Accounting identity breaches (Assets vs LiabilitiesAndStockholdersEquity, >0.5%): {len(ident)}", "",
        ident.to_markdown(index=False), "",
        f"## Flags on real data (no injection): {len(real_flags)}, "
        f"of which {int(real_flags.split_basis.sum())} are explained by an unadjusted split basis", "",
        "Rule flags:", "",
        real_flags[real_flags.scale | real_flags.sign][["ticker", "field", "end", "val", "form", "filed", "accn"]]
            .to_markdown(index=False), "",
        "Top anomaly flags not explained by splits:", "",
        real_flags[~real_flags.split_basis].nlargest(25, "z")[["ticker", "field", "end", "val", "z"]]
            .to_markdown(index=False), "",
        f"## Missed filings (10-Q/10-K gap > 150 days since 2011-06): {len(late)}, "
        f"plus {len(missed) - len(late)} acquired companies that stopped filing", "",
        missed.to_markdown(index=False), "",
        "## Detector evaluation (injected errors, 2% of values, mean of 5 seeds, z > 6, iforest top 3%)", "",
        "Rules target scale and sign errors; stale, drift and shift are held out.", "", ev.to_markdown(), "",
        "Threshold sweep:", "", sweep.to_markdown(), "",
        "## Scorecard", "", sc.to_markdown(), "",
    ]
    (OUT / "report.md").write_text("\n".join(md))
    print("\n".join(md))
    charts(snap, real, rev, recon, sweep, ev, mc)

    exceptions = pd.concat([
        real_flags[real_flags.scale | real_flags.sign].assign(
            check=lambda d: np.where(d.scale, "scale", "sign"), detail=lambda d: d.val.map("{:,.0f}".format)),
        ident.assign(check="identity", detail=ident.gap.map("assets vs L+E off {:.1%}".format)),
        mc[mc.flag].assign(check="share jump", detail=mc.unexplained_share_change.map("unexplained x{:.2f}".format)),
        late.assign(check="missed filing", end=late.last_filed,
                    detail=late.gap_days.astype(str) + " days without a 10-Q/10-K (" + late.status + ")"),
        unexplained.nlargest(15, "z").assign(check="anomaly", detail=lambda d: "z = " + d.z.astype(str)),
    ])[["check", "ticker", "field", "end", "detail"]].fillna("")
    restated = (rev[rev.kind.isin(["other", "amendment"])].sort_values("new_filed", ascending=False)
                [["ticker", "field", "end", "old", "new", "old_filed", "new_filed", "new_form", "kind"]])
    dashboard(sc, exceptions, restated)


def dashboard(sc, exceptions, restated):
    """Static data-quality dashboard: scorecard, open exceptions, restatement history, charts."""
    colors = {"RED": CRITICAL, "AMBER": SERIES[3], "GREEN": SERIES[2]}
    rag = sc.rag.value_counts().reindex(["RED", "AMBER", "GREEN"], fill_value=0)
    tiles = "".join(f'<div class="tile"><b style="color:{colors[k]}">{n}</b>{k}</div>' for k, n in rag.items())
    table = sc.reset_index()[["ticker", "rag"] + [c for c in sc if c != "rag"]].to_html(index=False, classes="t", border=0)
    for k, c in colors.items():
        table = table.replace(f"<td>{k}</td>", f'<td><span class="pill" style="background:{c}">{k}</span></td>')
    pd.options.display.float_format = lambda v: f"{v:,.0f}" if abs(v) >= 1000 else f"{v:.2f}"
    charts_html = "".join(f'<figure><img src="charts/{p}.png" alt="{p}"></figure>' for p in
                          ["nvda_scale_error", "aapl_market_cap", "revisions_by_year", "split_lag", "eval_tradeoff"])
    html = f"""<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Fundamentals data quality</title>
<style>
body {{ font: 14px/1.45 system-ui, sans-serif; color: {INK}; background: {SURFACE}; margin: 0 auto; max-width: 1100px; padding: 24px 16px; }}
h2 {{ margin-top: 2em; }} .muted {{ color: {MUTED}; }}
.tiles {{ display: flex; gap: 12px; }} .tile {{ border: 1px solid {GRID}; border-radius: 8px; padding: 10px 18px; }}
.tile b {{ display: block; font-size: 28px; }}
.scroll {{ overflow-x: auto; max-height: 480px; overflow-y: auto; }}
.t {{ border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }}
.t th {{ position: sticky; top: 0; background: {SURFACE}; text-align: left; border-bottom: 2px solid {GRID}; }}
.t th, .t td {{ padding: 4px 10px; border-bottom: 1px solid {GRID}; white-space: nowrap; }}
.pill {{ color: #fff; border-radius: 10px; padding: 1px 8px; font-size: 12px; font-weight: 600; }}
figure {{ margin: 0 0 20px; }} img {{ max-width: 100%; }}
</style></head><body>
<h1>Point-in-time fundamentals: data quality</h1>
<p class="muted">Generated {pd.Timestamp.today():%Y-%m-%d} by <code>pit.py report</code>. RED: identity breach or rule flag.
AMBER: dense anomaly flags, many restatements, an unexplained share jump or a missed filing.</p>
<div class="tiles">{tiles}</div>
<h2>Scorecard</h2><div class="scroll">{table}</div>
<h2>Open exceptions ({len(exceptions)})</h2><div class="scroll">{exceptions.to_html(index=False, classes="t", border=0)}</div>
<h2>Restatement history ({len(restated)} non-split, non-rounding revisions)</h2>
<div class="scroll">{restated.to_html(index=False, classes="t", border=0)}</div>
<h2>Flagged values</h2>{charts_html}
</body></html>"""
    pd.reset_option("display.float_format")
    (OUT / "dashboard.html").write_text(html)


# ---------- charts ----------
# Reference palette (dataviz skill), light mode: categorical slots in fixed order + status critical.
INK, MUTED, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100"]
CRITICAL = "#d03b3b"


def charts(snap, real, rev, recon, sweep, ev, mc):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "axes.edgecolor": GRID,
                         "axes.labelcolor": MUTED, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
                         "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "axes.axisbelow": True,
                         "axes.spines.top": False, "axes.spines.right": False, "font.size": 10,
                         "axes.titlesize": 12, "axes.titleweight": "bold", "axes.titlelocation": "left",
                         "legend.frameon": False})
    from matplotlib.ticker import FuncFormatter, LogLocator, NullFormatter

    def human(v, _):
        for u, sfx in [(1e12, "T"), (1e9, "B"), (1e6, "M"), (1e3, "K")]:
            if v >= u:
                return f"{v / u:g}{sfx}"
        return f"{v:g}"

    def log_y(ax, subs=(1.0,)):
        ax.set_yscale("log")
        ax.yaxis.set_major_locator(LogLocator(subs=subs))
        ax.yaxis.set_major_formatter(FuncFormatter(human))
        ax.yaxis.set_minor_formatter(NullFormatter())

    d = OUT / "charts"
    d.mkdir(exist_ok=True)

    # 1. A flagged value on its series: NVIDIA's 1000x share-count error.
    s = real[(real.ticker == "NVDA") & (real.field == "shares_diluted")]
    x = pd.to_datetime(s.end)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, s.val, color=SERIES[0], lw=2, marker="o", ms=5)
    bad = s.scale
    ax.scatter(x[bad], s.val[bad], s=90, color=CRITICAL, zorder=3, edgecolor=SURFACE, linewidth=2)
    vals = " and ".join(f"{v:,.0f}" for v in s.val[bad])
    ax.annotate(f"Flagged: FY2008-09 filed as {vals}\n(about 1000x too small)", (x[bad].iloc[-1], s.val[bad].iloc[-1]),
                xytext=(18, 10), textcoords="offset points", color=INK, fontsize=9)
    log_y(ax)
    ax.set_ylabel("diluted shares (log scale)")
    ax.set_title("NVIDIA diluted share count, latest-known values", pad=22)
    ax.text(0, 1.03, "Red points fail the scale rule. The later steps are the 2021 and 2024 splits: "
            "older years were never restated.",
            transform=ax.transAxes, color=MUTED, fontsize=9)
    fig.tight_layout(); fig.savefig(d / "nvda_scale_error.png", dpi=150); plt.close(fig)

    # 2. Revisions per filing year, by kind (stacked).
    kinds = ["other", "split", "amendment", "rounding"]
    t = rev.assign(year=rev.new_filed.str[:4]).pivot_table(index="year", columns="kind", values="end",
                                                           aggfunc="size", fill_value=0).reindex(columns=kinds, fill_value=0)
    fig, ax = plt.subplots(figsize=(8, 4))
    bottom = np.zeros(len(t))
    for k, c in zip(kinds, SERIES):
        ax.bar(t.index, t[k], bottom=bottom, color=c, label=k, edgecolor=SURFACE, linewidth=1.5, width=0.75)
        bottom += t[k].to_numpy()
    ax.set_ylabel("revised values")
    ax.set_ylim(top=bottom.max() * 1.18)
    ax.set_title("Revisions of already-reported values, by year of the revising filing")
    ax.legend(ncol=4, loc="upper left")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="x", visible=False)
    fig.tight_layout(); fig.savefig(d / "revisions_by_year.png", dpi=150); plt.close(fig)

    # 3. Days from the split to the first filing that restates for it.
    m = recon[recon.status == "matched"].sort_values("lag_days")
    labels = [f"{tk} {dt[:4]} ({'1:%d' % round(1 / r) if r < 1 else '%d:1' % r})"
              for tk, dt, r in zip(m.ticker, m.vendor_date, m.ratio)]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(labels, m.lag_days, color=SERIES[0], height=0.6)
    for i, v in enumerate(m.lag_days):
        ax.text(v + 3, i, f"{int(v)}", va="center", color=MUTED, fontsize=9)
    ax.set_xlabel("days from split to first restated filing")
    ax.set_title("Splits matched between vendor data and SEC filings")
    ax.grid(axis="y", visible=False)
    fig.tight_layout(); fig.savefig(d / "split_lag.png", dpi=150); plt.close(fig)

    # 4. Precision/recall: rules alone vs rules + each detector across thresholds.
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for method, c, lab in [("rules + robust_z", SERIES[0], "z > {}"), ("rules + iforest", SERIES[2], "top {:.0%}")]:
        comb = sweep.xs(method, level=2)
        ax.plot(comb.recall, comb.precision, color=c, lw=2, marker="o", ms=6, label=method.replace("_", " "))
        for (th, q), r in comb.iterrows():
            ax.annotate(lab.format(th if "z" in lab else q), (r.recall, r.precision), xytext=(6, 4),
                        textcoords="offset points", color=MUTED, fontsize=9)
    ax.scatter([ev.loc["rules", "recall"]], [ev.loc["rules", "precision"]], s=70, color=SERIES[1],
               zorder=3, label="rules alone")
    ax.set_xlim(0, 1); ax.set_ylim(0, 1.05)
    ax.set_xlabel("recall on injected errors"); ax.set_ylabel("precision")
    ax.set_title("Detection tradeoff (mean of 5 injection seeds)")
    ax.legend(loc="lower left")
    fig.tight_layout(); fig.savefig(d / "eval_tradeoff.png", dpi=150); plt.close(fig)

    # 5. Why point-in-time matters: Apple market cap with today's vs as-filed share counts.
    a = mc[mc.ticker == "AAPL"]
    x = pd.to_datetime(a.end)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(x, a.cap_pit / 1e9, color=SERIES[0], lw=2, marker="o", ms=5, label="as-filed shares (point-in-time)")
    ax.plot(x, a.cap_naive / 1e9, color=SERIES[1], lw=2, marker="o", ms=5, label="today's restated shares")
    log_y(ax, subs=(1.0, 2.0, 5.0))
    ax.set_ylabel("market cap, $bn (log scale)")
    ax.set_title("Apple market cap at fiscal year end: price x diluted shares", pad=22)
    ax.text(0, 1.03, "Gaps: years where today's count was restated for a split that came after the price.",
            transform=ax.transAxes, color=MUTED, fontsize=9)
    ax.legend(loc="lower right")
    fig.tight_layout(); fig.savefig(d / "aapl_market_cap.png", dpi=150); plt.close(fig)


# ---------- self-check ----------

def selftest():
    assert split_ratio(100, 400, 1) == 4 and split_ratio(4.0, 0.2, -1) == 20
    assert split_ratio(800, 100, 1) == 1 / 8
    assert split_ratio(100, 130, 1) is None and split_ratio(1, -1, 1) is None
    obs = pd.DataFrame(dict(
        cik=1, ticker="X", field=["shares_diluted"] * 3 + ["revenue"] * 2,
        end=["2020-12-31"] * 3 + ["2020-12-31"] * 2, val=[100, 100, 400, 50, 55],
        filed=["2021-02-01", "2022-02-01", "2023-02-01", "2021-02-01", "2021-06-01"],
        accn=list("abcde"), form=["10-K", "10-K", "10-K", "10-K", "10-K/A"]))
    rv = revisions(obs)
    assert sorted(rv.kind) == ["amendment", "split"], rv
    con = sqlite3.connect(":memory:")
    obs.to_sql("fact", con, index=False)
    pit = as_of(con, "2021-03-01")
    assert set(pit.val) == {100, 50} and (pit.filed <= "2021-03-01").all()  # no look-ahead
    assert set(as_of(con, "2030-01-01").val) == {400, 55}
    s = pd.DataFrame(dict(cik=1, field="assets", end=[f"20{y}" for y in range(10, 22)],
                          val=[100.0 + i for i in range(12)]))
    s.loc[6, "val"] = 106_000.0
    assert rules(s).scale[6] and robust_z(s).idxmax() == 6 and iforest(s).idxmax() == 6
    # Split after year end but before the 10-K: the filed count is post-split, the price isn't.
    fact = pd.DataFrame(dict(ticker="W", cik=1, field="shares_diluted", end=["2023-01-31", "2024-01-31"],
                             filed=["2023-03-10", "2024-03-15"], accn=["a", "b"], val=[2.7e9, 8.1e9]))
    price = pd.DataFrame(dict(ticker="W", month=["2023-01", "2024-01"], close_raw=[140.0, 165.0]))
    vendor = pd.DataFrame(dict(ticker="W", date=["2024-02-26"], ratio=[3.0]))
    mc = market_cap(fact, price, vendor)
    assert np.allclose(mc.shares_pe, [2.7e9, 2.7e9]) and not mc.flag.any(), mc
    # Missed filings: a 200-day hole is a gap; an acquired company going quiet is not overdue.
    filing = pd.DataFrame(dict(cik=[1, 1, 1, 2], form="10-Q", filed=["2020-01-01", "2020-04-01", "2020-10-18", "2020-01-01"]))
    company = pd.DataFrame(dict(cik=[1, 2], ticker=["X", "TWTR"]))
    mf = missed_filings(filing, company, "2020-12-01", since="2019")
    assert list(mf.status) == ["ceased filing (acquired)", "gap"] and mf.gap_days.iloc[1] == 200, mf
    # BDH: as-of hides the later restatement; injected shifts take the next period's value.
    assert bdh(con, "X", ["shares_diluted", "revenue"], "2020", "2021", "2021-03-01").values.tolist() == \
        [["2020-12-31", 100, 50]]
    s2 = s.assign(ticker="X")
    d = inject(s2, rate=0.5, seed=1)
    for i in d.index[d.err == "shift"]:
        assert d.at[i, "val"] == s2.at[i + 1, "val"]
    print("selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "ingest":
        ingest()
    elif cmd == "asof":
        _, _, ticker, field, date = sys.argv
        print(as_of(sqlite3.connect(DB), date, ticker, field).tail(12).to_string(index=False))
    elif cmd == "serve":
        serve(int(sys.argv[2]) if len(sys.argv) > 2 else 8000)
    elif cmd == "report":
        report()
    elif cmd == "selftest":
        selftest()
