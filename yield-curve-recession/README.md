# The Yield Curve Has Predicted Every Recession Since 1955. I Tested It.

A rigorous, reproducible backtest of the 10Y–2Y and 10Y–3M Treasury yield curve spreads as US recession predictors, using free FRED data. Built to support a LinkedIn article of the same name.

**The honest framing:** the data tells the story. The 2022–2024 inversion was the deepest and longest in the 2s10s series history — and was followed by no declared recession as of June 2026. This is the first confirmed false positive in a dataset going back to 1966. The analysis lays out the evidence and lets the reader decide what it means.

---

## Key findings

### 10Y–2Y spread (2s10s), 1976–present

| Episode | Start | End | Duration | Max Depth | Next Recession | Lead Time | Verdict |
|---|---|---|---|---|---|---|---|
| 1 | 1978-09 | 1982-06 | 46 months | −2.14 pp | 1980-02 | 17 months | ✓ True positive |
| 2 | 1989-01 | 1990-03 | 15 months | −0.32 pp | 1990-08 | 19 months | ✓ True positive |
| 3 | 2000-02 | 2000-12 | 11 months | −0.41 pp | 2001-04 | 14 months | ✓ True positive |
| 4 | 2006-02 | 2007-05 | 16 months | −0.15 pp | 2008-01 | 23 months | ✓ True positive |
| 5 | 2022-07 | 2024-08 | **26 months** | **−0.93 pp** | — | — | ✗ False positive |

**Hit rate (24-month window):** 4/5 episodes → **80%**
**Median lead time:** 18 months (range: 14–23 months)
**False positives:** 1 (2022–2024)

### 10Y–3M spread (extended), 1962–present

Extending the short leg to the 3-month T-bill (DTB3, available from 1962) adds three more recession cycles to the sample — 1969–70, 1973–75, and 1980.

| Episode | Start | Duration | Max Depth | Next Recession | Lead Time | Verdict |
|---|---|---|---|---|---|---|
| 1 | 1966-09 | 5 months | −0.34 pp | — | — | ✗ False positive |
| 2 | 1969-01 | 13 months | −0.29 pp | 1970-01 | 12 months | ✓ True positive |
| 3 | 1973-06 | 16 months | −1.27 pp | 1973-12 | 6 months | ✓ True positive |
| 4 | 1978-12 | 33 months | −2.65 pp | 1980-02 | 14 months | ✓ True positive |
| 5 | 1989-06 | 7 months | −0.16 pp | 1990-08 | 14 months | ✓ True positive |
| 6 | 2000-07 | 7 months | −0.70 pp | 2001-04 | 9 months | ✓ True positive |
| 7 | 2006-08 | 10 months | −0.52 pp | 2008-01 | 17 months | ✓ True positive |
| 8 | 2019-05 | 10 months | −0.36 pp | 2020-03 | 10 months | ✓ True positive |
| 9 | 2022-11 | 44 months | −1.73 pp | — | — | ✗ False positive |

**Hit rate (24-month window):** 7/9 episodes → **77.8%**
**Median lead time:** 12 months (range: 6–17 months)
**False positives:** 2 (1966, 2022–2024)

### The 2022–2024 episode

The 2022–2024 inversion was extraordinary by any measure:
- **Duration:** 26 months (2s10s) / 44 months (10Y–3M) — the longest in either series
- **Depth:** −0.93 pp (2s10s) / −1.73 pp (10Y–3M) — deepest since the Volcker era
- **Outcome:** No NBER recession declared as of June 2026

At 47 months since the inversion began, we are well beyond the 14–23 month historical lead-time range. At 21+ months since re-steepening, the post-uninversion danger window (historically 4–17 months) has also closed. This is an increasingly strong case for a confirmed false positive.

### Current conditions (June 2026)

| Indicator | Value | Signal |
|---|---|---|
| 2s10s spread | +0.38 pp | ✓ Normal |
| 10Y–3M spread | +0.69 pp | ✓ Normal |
| Probit 12-month recession probability | 14.7% | ✓ Low (threshold: ~30%) |
| Unemployment | 4.3% | — |
| Fed Funds Rate | 3.63% | Easing cycle underway |

**The yield curve is not currently signalling recession.** Both spreads are positive. The probit model sits well below its historical alert threshold.

---

## Methodology

### Signal definitions (set a priori — not tuned post-hoc)

| Parameter | Value | Rationale |
|---|---|---|
| Inversion threshold | spread < 0 | Standard definition |
| Minimum episode duration | 3 consecutive months | Excludes brief noise dips |
| Minimum episode separation | 12 months of positive spread | Separates distinct rate cycles |
| Primary look-ahead window | 24 months | Standard in academic literature |
| Sensitivity look-ahead | 36 months | Tests whether window choice matters |
| Recession definition | NBER official dates (`USREC`) | Authoritative, backward-looking |

### Data construction

The official FRED spread series have different start dates. To maximize history, short legs are extended using component yields:

| Spread | Official series | Extended using | Coverage |
|---|---|---|---|
| 10Y–2Y (2s10s) | `T10Y2Y` (1976+) | `DGS10 − DGS2` | 1976+ (DGS2 limit) |
| 10Y–3M | `T10Y3M` (1982+) | `DGS10 − DTB3` | 1962+ |

Where both exist, the official series is used. The manual calculation and official series correlate at >0.9999 in their overlap period.

### Recession probability model

A probit regression of the NBER recession indicator on the 10Y–3M spread, with a 12-month forward look — replicating the methodology of Estrella & Mishkin (1996) and the NY Fed's published model.

- Estimated on 1982–2019 data (COVID and 2022+ held out as out-of-sample)
- Spread coefficient: −0.80 (p < 0.001), constant: −0.50 (p < 0.001)
- Pseudo R²: 0.27

### Key nuance: uninversion timing

A detail often missed in yield curve discussions: in 3 of 4 historical true-positive episodes (1989, 2000, 2006), the recession began *after* the curve had already re-steepened, not while it was still inverted. The post-uninversion window (4–17 months in those cases) is as important to watch as the inversion itself.

---

## Quickstart

### 1. Get a free FRED API key

Register at [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html) — takes 30 seconds.

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set your API key

```bash
cp .env.example .env
# Edit .env and set FRED_API_KEY=your_key_here
```

### 4. Run notebooks in order

```bash
jupyter notebook notebooks/
```

| Notebook | What it does |
|---|---|
| `01_data_pull.ipynb` | Pull all FRED series, merge to monthly, sanity check |
| `02_eda.ipynb` | Five charts including the classic 2s10s visualization |
| `03_signal_backtest.ipynb` | Per-inversion table, hit rate, lead times, false positives — including extended 10Y–3M back to 1962 |
| `04_2022_episode.ipynb` | Deep dive on the 2022–2024 anomaly, probit model, and current conditions dashboard |

After the first run, data is cached in `data/raw/` — subsequent runs don't hit the API.

---

## Project structure

```
yield-curve-recession/
├── data/
│   └── raw/                        # Cached FRED pulls + backtest tables (not committed)
│       ├── merged_monthly.csv      # All series, monthly frequency
│       ├── backtest_2s10s.csv      # Per-episode backtest (1976+)
│       ├── backtest_10y3m.csv      # Per-episode backtest, official T10Y3M (1982+)
│       └── backtest_10y3m_extended.csv  # Per-episode backtest, extended (1962+)
├── notebooks/
│   ├── 01_data_pull.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_signal_backtest.ipynb
│   └── 04_2022_episode.ipynb
├── src/
│   ├── fred_loader.py    # FRED API wrapper with local caching; constructs extended spreads
│   ├── signal_utils.py   # Episode detection, lead times, aggregate metrics
│   └── viz.py            # Reusable chart functions (14 chart types)
├── reports/
│   └── figures/          # 14 saved charts
├── requirements.txt
└── .env.example
```

---

## Data sources

All data via the [FRED API](https://fred.stlouisfed.org/) (Federal Reserve Bank of St. Louis). Free, no scraping.

| Series | Description | Frequency | History |
|---|---|---|---|
| `T10Y2Y` | 10Y–2Y spread | Daily | 1976+ |
| `T10Y3M` | 10Y–3M spread | Daily | 1982+ |
| `DGS10` | 10-Year Treasury yield | Daily | 1962+ |
| `DGS2` | 2-Year Treasury yield | Daily | 1976+ |
| `DTB3` | 3-Month T-Bill yield | Daily | 1954+ |
| `USREC` | NBER recession indicator (0/1) | Monthly | 1854+ |
| `FEDFUNDS` | Federal Funds Rate | Monthly | 1954+ |
| `UNRATE` | Unemployment Rate | Monthly | 1948+ |
| `CPIAUCSL` | CPI All Urban | Monthly | 1947+ |
| `GDPC1` | Real GDP | Quarterly | 1947+ |

---

## Caveats

**Small sample.** Even with the extended 10Y–3M history, 9 episodes is a thin basis for claiming statistical reliability. Treat hit rates as descriptive, not inferential.

**Long, variable lead times.** 6–23 months historically (2s10s). By the time you observe an inversion, act on it, and a recession materializes, you could have been wrong for nearly two years. This is not a trading signal.

**NBER dates are backward-looking.** Recessions are typically declared 6–12 months after they begin. "No recession declared" is not the same as "no recession."

**The 2020 COVID recession is a genuine outlier.** Caused by an external shock, not a business cycle downturn. No yield curve inversion preceded it (the 2019 episode had a lead time of 10 months, which technically qualifies — but this is contested). Results are shown both including and excluding it.

**Correlation, not causation.** The yield curve reflects market expectations about future growth and policy. It doesn't cause recessions — it anticipates the conditions that tend to produce them. The mechanism matters for interpreting anomalies like 2022–2024.

---

## Article

*"The Yield Curve Has Predicted Every Recession Since 1955. I Tested It."*

[LinkedIn article link — add when published]
