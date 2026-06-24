"""
Signal utilities for yield curve inversion analysis.

Key concepts:
- Inversion: spread < 0
- Episode: sustained inversion period (>=3 consecutive months negative,
  separated from the next episode by >=12 months of positive spread)
- Lead time: months from episode start to the next recession start
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Episode detection
# ---------------------------------------------------------------------------

def find_inversion_episodes(
    spread: pd.Series,
    min_duration_months: int = 3,
    min_separation_months: int = 12,
) -> pd.DataFrame:
    """
    Identify sustained inversion episodes in a monthly spread series.

    Parameters
    ----------
    spread : monthly pd.Series of spread values (e.g. T10Y2Y or T10Y3M)
    min_duration_months : minimum consecutive months below zero to qualify
    min_separation_months : minimum months of positive spread to split episodes

    Returns
    -------
    DataFrame with columns:
        episode_id, start, end, duration_months, max_depth, mean_depth
    """
    s = spread.dropna().copy()
    inverted = (s < 0).astype(int)

    episodes = []
    in_episode = False
    ep_start = None
    pos_streak = 0

    for date, val in inverted.items():
        if not in_episode:
            if val == 1:
                in_episode = True
                ep_start = date
                pos_streak = 0
        else:
            if val == 0:
                pos_streak += 1
                if pos_streak >= min_separation_months:
                    ep_end = date - pd.offsets.MonthEnd(pos_streak)
                    ep_spread = s.loc[ep_start:ep_end]
                    if (ep_spread < 0).sum() >= min_duration_months:
                        episodes.append(_episode_row(ep_spread, ep_start, ep_end))
                    in_episode = False
                    ep_start = None
                    pos_streak = 0
            else:
                pos_streak = 0

    # Close any open episode at end of series
    if in_episode and ep_start is not None:
        ep_end = s.index[-1]
        ep_spread = s.loc[ep_start:ep_end]
        if (ep_spread < 0).sum() >= min_duration_months:
            episodes.append(_episode_row(ep_spread, ep_start, ep_end, ongoing=True))

    if not episodes:
        return pd.DataFrame(
            columns=["episode_id", "start", "end", "duration_months",
                     "max_depth", "mean_depth", "ongoing"]
        )

    df = pd.DataFrame(episodes)
    df.insert(0, "episode_id", range(1, len(df) + 1))
    return df.reset_index(drop=True)


def _episode_row(
    ep_spread: pd.Series,
    start: pd.Timestamp,
    end: pd.Timestamp,
    ongoing: bool = False,
) -> dict:
    neg = ep_spread[ep_spread < 0]
    return {
        "start": start,
        "end": end,
        "duration_months": len(ep_spread),
        "max_depth": neg.min() if len(neg) else np.nan,
        "mean_depth": neg.mean() if len(neg) else np.nan,
        "ongoing": ongoing,
    }


# ---------------------------------------------------------------------------
# Lead time calculation
# ---------------------------------------------------------------------------

def compute_lead_times(
    episodes: pd.DataFrame,
    recession: pd.Series,
    max_lead_months: int = 36,
) -> pd.DataFrame:
    """
    For each inversion episode, find the next recession start and compute
    the lead time in months.

    Parameters
    ----------
    episodes : output of find_inversion_episodes()
    recession : monthly 0/1 USREC series
    max_lead_months : look-ahead window; 'no recession' if none found within

    Returns
    -------
    episodes DataFrame with added columns:
        recession_start, lead_time_months, result
    """
    rec = recession.copy()
    rec.index = rec.index + pd.offsets.MonthEnd(0)

    rows = []
    for _, ep in episodes.iterrows():
        ep_start = pd.Timestamp(ep["start"])
        window_end = ep_start + pd.DateOffset(months=max_lead_months)

        # Find first month with USREC=1 after the inversion started
        future_rec = rec.loc[ep_start:window_end]
        rec_starts = future_rec[future_rec == 1]

        # The "recession start" is the first run of 1s; find where it begins
        if len(rec_starts) == 0:
            rec_start = None
            lead_months = None
            result = "no recession"
        else:
            # Walk back to find the true start of that recession episode
            first_rec_month = rec_starts.index[0]
            # Look back up to 3 months to find the actual run start
            lookback = rec.loc[
                first_rec_month - pd.DateOffset(months=3) : first_rec_month
            ]
            run_start = lookback[lookback == 1].index[0]
            rec_start = run_start
            lead_months = _months_between(ep_start, rec_start)
            result = "true positive" if lead_months >= 0 else "concurrent"

        row = ep.to_dict()
        row["recession_start"] = rec_start
        row["lead_time_months"] = lead_months
        row["result"] = result
        rows.append(row)

    return pd.DataFrame(rows)


def _months_between(t0: pd.Timestamp, t1: pd.Timestamp) -> int:
    return (t1.year - t0.year) * 12 + (t1.month - t0.month)


# ---------------------------------------------------------------------------
# Aggregate metrics
# ---------------------------------------------------------------------------

def aggregate_metrics(bt: pd.DataFrame) -> dict:
    """
    Compute aggregate backtest metrics across all inversion episodes.

    Parameters
    ----------
    bt : output of compute_lead_times()

    Returns
    -------
    dict of summary statistics
    """
    total = len(bt)
    tp = bt[bt["result"] == "true positive"]
    fp = bt[bt["result"] == "no recession"]

    lead = tp["lead_time_months"].dropna()

    return {
        "total_episodes": total,
        "true_positives": len(tp),
        "false_positives": len(fp),
        "hit_rate_pct": round(100 * len(tp) / total, 1) if total else None,
        "lead_time_mean": round(lead.mean(), 1) if len(lead) else None,
        "lead_time_median": round(lead.median(), 1) if len(lead) else None,
        "lead_time_min": int(lead.min()) if len(lead) else None,
        "lead_time_max": int(lead.max()) if len(lead) else None,
    }


# ---------------------------------------------------------------------------
# Recession boundary helpers
# ---------------------------------------------------------------------------

def recession_bands(recession: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """
    Return a list of (start, end) tuples for each NBER recession period.
    Used for shading charts.
    """
    rec = recession.copy()
    rec.index = pd.to_datetime(rec.index)

    bands = []
    in_rec = False
    start = None

    for date, val in rec.items():
        if not in_rec and val == 1:
            in_rec = True
            start = date
        elif in_rec and val == 0:
            in_rec = False
            bands.append((start, date))

    if in_rec and start is not None:
        bands.append((start, rec.index[-1]))

    return bands


def inversion_flag(spread: pd.Series) -> pd.Series:
    """Return a 0/1 series marking months where spread < 0."""
    return (spread < 0).astype(int)


# ---------------------------------------------------------------------------
# Smoothed signal
# ---------------------------------------------------------------------------

def smoothed_inversion(
    spread: pd.Series,
    window_months: int = 3,
) -> pd.Series:
    """
    Return True where the rolling mean of the spread over `window_months`
    is negative. Reduces noise from brief dips.
    """
    return spread.rolling(window_months).mean() < 0


# ---------------------------------------------------------------------------
# Depth analysis
# ---------------------------------------------------------------------------

def depth_vs_lead_time(bt: pd.DataFrame) -> pd.DataFrame:
    """
    Return a DataFrame with max_depth and lead_time_months for plotting
    the relationship between inversion severity and lead time.
    """
    tp = bt[bt["result"] == "true positive"].copy()
    return tp[["episode_id", "start", "max_depth", "lead_time_months"]].dropna()
