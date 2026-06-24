# Project Spec: The Yield Curve Has Predicted Every Recession Since 1955. I Tested It.

## Project Goal

Pull every yield curve inversion since the 1950s from public Federal Reserve data, rigorously backtest the 10Y–2Y and 10Y–3M spreads as recession predictors, quantify their historical track record (lead times, false positives, signal depth), and then confront the elephant in the room: the 2022–2024 inversion — the deepest and longest in history — was followed by no recession. Did the signal break? Or did it just not fire yet?

**End deliverable:** a clean, well-documented GitHub repo with a reproducible analysis notebook, supporting a LinkedIn article. Title direction: *"The Yield Curve Has Predicted Every Recession Since 1955. I Tested It."*

**The honest thesis going in:** the data will tell the story. Don't force a conclusion. The 2022–2024 episode is genuinely unresolved and contested — the article's value is in laying out the evidence rigorously, not in pretending there's a clean answer.

**Constraints:**
- 100% free data via the FRED API (Federal Reserve Bank of St. Louis). No paid sources, no scraping.
- Personal project, no client data or employer tooling.
- Familiar Python stack — pandas, matplotlib/seaborn, statsmodels/scipy. No need to learn new frameworks for this one.
- Time-box the build. This is a macro/finance piece, not an ML project. The analysis is the product.

---

## Data Sources (All Free, All FRED)

All data pulled via the `fredapi` Python library. Requires a free API key from `fred.stlouisfed.org/docs/api/api_key.html`.

### Primary series

| FRED Series ID | Description | Frequency | History |
|---|---|---|---|
| `T10Y2Y` | 10-Year minus 2-Year Treasury spread (the "2s10s") | Daily | 1976–present |
| `T10Y3M` | 10-Year minus 3-Month Treasury spread | Daily | 1982–present |
| `DGS10` | 10-Year Treasury yield (raw) | Daily | 1962–present |
| `DGS2` | 2-Year Treasury yield (raw) | Daily | 1976–present |
| `DTB3` | 3-Month Treasury bill yield (raw) | Daily | 1954–present |
| `USREC` | NBER recession indicator (0/1, monthly) | Monthly | 1854–present |
| `FEDFUNDS` | Federal Funds Rate | Monthly | 1954–present |
| `UNRATE` | US Unemployment Rate | Monthly | 1948–present |
| `CPIAUCSL` | Consumer Price Index (inflation proxy) | Monthly | 1947–present |

### Notes on data quality
- `T10Y2Y` is only available from 1976. For recession analysis before 1976, compute the spread manually from `DGS10` and `DGS2` (both available earlier). There is a gap in `DGS2` before 1976, so pre-1976 analysis should either use `DTB3` (3-month) as the short leg, or be honest about the shorter history for the 2s10s measure.
- `USREC` is a monthly series (0 = expansion, 1 = recession). For daily-frequency analysis, forward-fill the monthly value to align with daily spread data.
- The NY Fed's preferred recession indicator uses `T10Y3M`, not `T10Y2Y`. Include both and compare — they tell a slightly different story and the divergence is itself interesting.
- No data revisions to worry about for yield curve data — it's a deterministic calculation from Treasury yields, published without revision.

---

## Step 1: Data Pull and Setup

```
yield-curve-recession/
├── README.md
├── data/
│   └── raw/              # Cached FRED pulls (save locally to avoid re-pulling)
├── notebooks/
│   ├── 01_data_pull.ipynb
│   ├── 02_eda.ipynb
│   ├── 03_signal_backtest.ipynb
│   └── 04_2022_episode.ipynb
├── src/
│   ├── fred_loader.py    # Wrapper around fredapi with local caching
│   ├── signal_utils.py   # Inversion detection, lead time calculations
│   └── viz.py            # Reusable chart functions
├── reports/
│   └── figures/          # Saved charts for the article
├── requirements.txt
└── .gitignore
```

**Build order:**
1. `fred_loader.py` — pull all series, save to `data/raw/` as CSVs. Cache locally so you're not hitting the API on every notebook run.
2. `01_data_pull.ipynb` — load, merge, resample to monthly frequency for the main analysis (daily is noisy and adds complexity without insight for this project).
3. The remaining notebooks in order.

**Requirements:**
```
fredapi
pandas
numpy
matplotlib
seaborn
scipy
statsmodels
jupyter
python-dotenv   # for storing FRED API key in .env, not hardcoded
```

---

## Step 2: Define the Signal Rules

Before any analysis, write down the signal definitions explicitly. Don't let them drift during the analysis to improve results — that's p-hacking.

**Signal 1: 2s10s inversion** (`T10Y2Y < 0`)
- Simple threshold: spread goes negative.
- Consider a smoothed version: spread negative for X consecutive months (e.g. 3 months) to reduce noise from brief dips.

**Signal 2: 10Y–3M inversion** (`T10Y3M < 0`)
- Same threshold logic.
- This is the NY Fed's preferred measure and is often considered more reliable in academic literature.

**Signal 3: Depth-weighted version**
- Instead of just binary (inverted/not), consider the magnitude. Does a deeper inversion (e.g. -1.5% vs -0.1%) predict recessions with shorter lead times or more reliably? Test this.

**Recession definition:** NBER official dates from `USREC`. A recession "follows" an inversion if it starts within a defined window after the inversion begins (e.g. 6–30 months). This window is a judgment call — document it explicitly and test sensitivity to it.

---

## Step 3: Exploratory Data Analysis

Charts to produce (save all to `reports/figures/`):

1. **The classic chart:** 2s10s spread over full history with NBER recession bars shaded. This is the money shot for the LinkedIn article. Make it clean and readable.
2. **Both spreads overlaid:** 2s10s vs. 10Y–3M, with recessions shaded. Shows where they agree and diverge.
3. **Component yields:** 10-year and 2-year yields separately, to show *what's driving* inversions (rising short end vs. falling long end — these are different economic signals even when the spread is identical).
4. **Fed Funds Rate vs. yield curve:** how does the policy rate relate to inversion timing?
5. **The 2022–2024 episode in isolation:** zoom in on 2022–present with unemployment and CPI overlaid. This is where the "did it break?" story lives.

EDA questions to answer:
- How many inversions are in the historical record? (List them with start/end dates.)
- How many were followed by recessions within 24 months? (The hit rate.)
- Were there any false positives — inversions not followed by recessions?
- What is the distribution of lead times (inversion to recession start)?
- Is there a difference in predictive power between 2s10s and 10Y–3M?

---

## Step 4: Signal Backtest

This is the analytical core. For each historical inversion event, measure:

**Per-inversion metrics to calculate:**
- Inversion start date (first month spread goes negative)
- Inversion end date (first month spread returns positive)
- Inversion duration (months)
- Maximum inversion depth (most negative value)
- Time from inversion start to subsequent recession start (lead time, in months) — or "no recession" if none followed within 30 months
- Was it a true positive or false positive?

**Aggregate metrics across all inversions:**
- Hit rate: % of inversions followed by recession within 24 months
- Average lead time (inversion to recession start)
- Median lead time
- Range of lead times (min/max)
- Number of false positives

**The key table for the article:** one row per historical inversion, with all the above metrics. This is the most citable piece of analysis in the whole project.

**Important nuance to model:** the signal is often described as "every inversion is followed by a recession" — but this conflates two things. Inversions tend to cluster, and recessions also cluster. The right unit of analysis is *inversion episodes* (distinct periods of sustained inversion), not individual months below zero. Define an inversion episode as a period where the spread is negative for at least 3 consecutive months, with at least 12 months of positive spread required to separate episodes. Document this choice.

---

## Step 5: The 2022–2024 Episode

This is the section that makes the article timely and worth reading in 2025/2026.

**Context to build out:**
- The 2022–2024 inversion was the deepest since the early 1980s Volcker era and the longest in the history of the T10Y2Y series.
- As of mid-2025, no NBER recession has been declared for 2022–2024. The Fed began cutting rates in late 2024. The curve has since re-steepened.
- This is genuinely unresolved. The article should not claim to know the answer.

**Questions to examine with data:**
1. How does the 2022–2024 episode compare to prior inversions in depth and duration?
2. What has happened to unemployment, GDP growth, and inflation over the same period? (Use FRED: `UNRATE`, `GDPC1` for real GDP, `CPIAUCSL`.)
3. Historically, what happened to the economy *after* the curve re-steepened? (This is the key: recessions have often started *after* un-inversion, not during it.)
4. Where does the 2022–2024 episode fit if we extend the "look-ahead window" to 36 months instead of 24?

**Honest framings to consider for the article narrative:**
- "The signal is delayed, not broken" — still within historical range if you allow 30–36 months.
- "This time was different" — fiscal stimulus and COVID distortions disrupted the normal business cycle mechanics.
- "The signal worked, just not as a recession predictor — it predicted the Fed's eventual rate cuts, which is what it actually measures."
- Don't pick one. Present all three and let the reader decide. That's more intellectually honest and more engaging than a forced conclusion.

---

## Step 6: Optional Extension — Recession Probability Model

If time allows, replicate a simple version of the NY Fed's recession probability model. It's a probit regression of NBER recession indicator on the 10Y–3M spread with a 12-month forward look. Clean, explainable, and well-documented in public research.

- Estimate on data through 2019 (exclude COVID and 2022+ as out-of-sample)
- Plot the implied probability over history
- Show what the model "says" about current conditions

This adds a modeling layer that differentiates the project from a pure data visualization piece, and it's directly citable (NY Fed publishes this model publicly).

Only include this if it adds to the story. Don't force it in.

---

## Step 7: Honest Caveats (Include in Article and README)

**The yield curve is not a trading signal.** Lead times are long and variable (6–30 months historically). By the time you observe an inversion, act on it, and the recession materializes, you could have been wrong for 2 years. This is for understanding macro context, not timing trades.

**NBER recession dates are backward-looking.** The NBER typically declares recessions 6–12 months *after* they begin. So "did a recession follow the inversion?" is a question you can only fully answer in hindsight.

**Survivorship bias in the narrative.** The "every inversion was followed by a recession" claim is true in the FRED T10Y2Y data (since 1976), but the sample size is small — roughly 6–7 inversion episodes. Statistically, this is not a large enough sample to claim predictive reliability with confidence. Say this.

**Correlation, not causation.** The yield curve doesn't *cause* recessions. It reflects market expectations about future policy and growth. The mechanism matters for interpreting the 2022–2024 anomaly.

**The 2020 COVID recession is a genuine outlier.** It was caused by an external shock (pandemic), not a business cycle downturn. Including or excluding it changes the yield curve's track record. Flag this and show both versions.

---

## Step 8: Article Structure (LinkedIn)

The article should mirror the NHL and MMM pieces in tone — technically rigorous underneath, accessible and a little provocative on the surface.

**Suggested flow:**
1. Hook: "The yield curve inverted in 2022. Economists panicked. Two years later... nothing happened. So was the most reliable recession indicator in history finally wrong?"
2. What the yield curve is and why inversions are supposed to matter (2–3 paragraphs, accessible)
3. The historical track record — the table of every inversion, visualized
4. The 2022–2024 anomaly — what the data shows
5. Three possible interpretations — let the reader sit with the ambiguity
6. What this means for anyone making decisions (business leaders, planners) — probabilistic thinking applied to macro uncertainty
7. The repo link + "run it yourself"

---

## Suggested Build Order for Claude Code in VS Code

1. Set up repo structure, `requirements.txt`, `.env` file for FRED API key.
2. Build `fred_loader.py` — pull all series, save to local CSVs with timestamps.
3. Build `01_data_pull.ipynb` — load, merge, align frequencies, sanity check all series.
4. Build `signal_utils.py` — inversion detection logic, episode segmentation, lead time calculation functions. Unit test these functions with known historical inversions before using them in analysis.
5. Build `02_eda.ipynb` — the classic chart + supporting visuals.
6. Build `03_signal_backtest.ipynb` — the per-inversion table and aggregate metrics. This is the heart of the project.
7. Build `04_2022_episode.ipynb` — the current episode analysis with economic context.
8. Optional: probit model notebook.
9. Write `README.md` — lead with the key finding, include the main chart inline, link to article.
10. Final cleanup pass: clear notebook outputs, add markdown commentary cells, confirm all charts saved cleanly to `reports/figures/`.
