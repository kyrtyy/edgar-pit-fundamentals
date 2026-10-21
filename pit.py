"""Point-in-time fundamentals from SEC XBRL companyfacts.

Usage:
  python pit.py ingest                 # fetch companyfacts -> facts.db
  python pit.py asof AAPL revenue 2019-06-30
  python pit.py report                 # restatements, checks, eval -> out/
  python pit.py selftest
"""
import json, os, sqlite3, sys, time, urllib.request
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
    "TWTR": 1418091, "ATVI": 718877, "XLNX": 743988,
}

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
    rows = []
    for ticker, cik in COMPANIES.items():
        data = fetch(cik)
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
    with sqlite3.connect(DB) as con:
        df.to_sql("obs", con, if_exists="replace", index=False)
        con.execute("CREATE INDEX IF NOT EXISTS ix ON obs(cik, field, end, filed)")
    print(f"{len(df)} observations -> {DB}")


# ---------- point-in-time ----------
# obs is bitemporal: `end` is the period described (valid time), `filed` is when it became
# known (transaction time). ponytail: day-level `filed`; use acceptanceDateTime from the
# submissions API if intraday look-ahead matters.

ASOF_SQL = """
SELECT * FROM (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY cik, field, end ORDER BY filed DESC, accn DESC) rn
  FROM obs WHERE filed <= :as_of {where}
) WHERE rn = 1 ORDER BY cik, field, end
"""


def as_of(con, as_of_date, ticker=None, field=None):
    where, params = "", {"as_of": as_of_date}
    if ticker:
        where += " AND ticker = :ticker"; params["ticker"] = ticker
    if field:
        where += " AND field = :field"; params["field"] = field
    return pd.read_sql(ASOF_SQL.format(where=where), con, params=params).drop(columns="rn")


def load(con):
    return pd.read_sql("SELECT * FROM obs", con)


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


# ---------- evaluation with injected errors ----------

def inject(s, rate=0.02, seed=0):
    rng = np.random.default_rng(seed)
    s = s.copy()
    s["err"] = ""
    idx = rng.choice(s.index, size=int(len(s) * rate), replace=False)
    kinds = ["scale", "sign", "stale", "drift"]  # rules target scale+sign; stale+drift held out
    for n, i in enumerate(idx):
        kind, v = kinds[n % 4], s.at[i, "val"]
        same = s[(s.cik == s.at[i, "cik"]) & (s.field == s.at[i, "field"]) & (s.end < s.at[i, "end"])]
        if kind == "stale":
            if same.empty or same["val"].iloc[-1] == v:
                continue
            new = same["val"].iloc[-1]
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


def evaluate(s, z_thresh=6.0, seeds=range(5)):
    rows = []
    for seed in seeds:
        d = inject(s, seed=seed)
        truth = d["err"] != ""
        r = rules(d).any(axis=1)
        z = robust_z(d) > z_thresh
        for name, flag in [("rules", r), ("robust_z", z), ("combined", r | z)]:
            row = dict(seed=seed, method=name, **pr(flag, truth))
            for kind in ["scale", "sign", "stale", "drift"]:
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

    ident = identity_breaches(snap)
    ident.to_csv(OUT / "identity_breaches.csv", index=False)
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
    sweep = pd.concat({t: evaluate(snap, z_thresh=t).loc[["robust_z", "combined"],
                                                         ["precision", "recall", "recall_drift"]]
                       for t in [4, 6, 8, 12, 20]}, names=["z_thresh"])
    sweep.to_csv(OUT / "eval_sweep.csv")

    # RAG scorecard per company
    sc = snap.groupby("ticker").agg(observations=("val", "size"), first=("end", "min"), last=("end", "max"))
    sc["identity_breaches"] = ident.groupby("ticker").size()
    sc["rule_flags"] = real_flags[real_flags.scale | real_flags.sign].groupby("ticker").size()
    sc["anomaly_flags"] = real_flags[real_flags.z > 6].groupby("ticker").size()
    sc["restatements_other"] = rev[rev.kind.isin(["other", "amendment"])].groupby("ticker").size()
    sc = sc.fillna(0).astype({c: int for c in ["identity_breaches", "rule_flags", "anomaly_flags", "restatements_other"]})
    sc["rag"] = np.where(sc.identity_breaches + sc.rule_flags > 0, "RED",
                np.where(sc.anomaly_flags + (sc.restatements_other > 5) > 0, "AMBER", "GREEN"))
    sc.to_csv(OUT / "scorecard.csv")

    md = [
        "# Point-in-time fundamentals: data-quality report", "",
        f"{obs.cik.nunique()} companies, {len(obs)} observations (every reported version), "
        f"{len(snap)} latest-known values, periods {snap.end.min()} to {snap.end.max()}.", "",
        "## Revisions of already-reported values", "", rev.kind.value_counts().to_frame("count").to_markdown(), "",
        "## Splits detected from restated share counts / EPS", "", splits.to_markdown(index=False), "",
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
        "## Detector evaluation (injected errors, 2% of values, mean of 5 seeds, z > 6)", "",
        "Rules target scale and sign errors; stale and drift are held out.", "", ev.to_markdown(), "",
        "Threshold sweep:", "", sweep.to_markdown(), "",
        "## Scorecard", "", sc.to_markdown(), "",
    ]
    (OUT / "report.md").write_text("\n".join(md))
    print("\n".join(md))


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
    obs.to_sql("obs", con, index=False)
    pit = as_of(con, "2021-03-01")
    assert set(pit.val) == {100, 50} and (pit.filed <= "2021-03-01").all()  # no look-ahead
    assert set(as_of(con, "2030-01-01").val) == {400, 55}
    s = pd.DataFrame(dict(cik=1, field="assets", end=[f"20{y}" for y in range(10, 22)],
                          val=[100.0 + i for i in range(12)]))
    s.loc[6, "val"] = 106_000.0
    assert rules(s).scale[6] and robust_z(s).idxmax() == 6
    print("selftest ok")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "report"
    if cmd == "ingest":
        ingest()
    elif cmd == "asof":
        _, _, ticker, field, date = sys.argv
        print(as_of(sqlite3.connect(DB), date, ticker, field).tail(12).to_string(index=False))
    elif cmd == "report":
        report()
    elif cmd == "selftest":
        selftest()
