"""
Reusable chart functions for yield curve / recession analysis.

All functions accept an optional `ax` parameter for embedding in subplots,
and an optional `save_path` to write the figure to reports/figures/.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns

FIGURES_DIR = Path(__file__).parent.parent / "reports" / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Style defaults
RECESSION_COLOR = "#d4e6f1"
RECESSION_ALPHA = 0.6
INVERSION_COLOR = "#fadbd8"
INVERSION_ALPHA = 0.5
PALETTE = sns.color_palette("tab10")


def _shade_recessions(
    ax: plt.Axes,
    bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    label: bool = True,
) -> None:
    for i, (start, end) in enumerate(bands):
        ax.axvspan(
            start,
            end,
            color=RECESSION_COLOR,
            alpha=RECESSION_ALPHA,
            label="NBER Recession" if (label and i == 0) else None,
            zorder=0,
        )


def _save(fig: plt.Figure, save_path: str | Path | None) -> None:
    if save_path is not None:
        p = Path(save_path)
        if not p.is_absolute():
            p = FIGURES_DIR / p
        fig.savefig(p, dpi=150, bbox_inches="tight")
        print(f"  Saved: {p}")


# ---------------------------------------------------------------------------
# Chart 1: Classic 2s10s with recession shading
# ---------------------------------------------------------------------------

def plot_spread_history(
    spread: pd.Series,
    recession_bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    title: str = "10Y–2Y Treasury Spread (2s10s)",
    ylabel: str = "Spread (percentage points)",
    highlight_zero: bool = True,
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(14, 5))

    _shade_recessions(ax, recession_bands)

    ax.plot(spread.index, spread.values, color="#2c3e50", linewidth=1.2, label=spread.name or "Spread")

    if highlight_zero:
        ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
        ax.fill_between(
            spread.index,
            spread.values,
            0,
            where=(spread.values < 0),
            color="#e74c3c",
            alpha=0.3,
            label="Inversion",
        )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=10)
    ax.set_ylabel(ylabel)
    ax.set_xlabel("")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.tick_params(axis="x", rotation=0)
    ax.legend(loc="upper left", framealpha=0.8)
    ax.grid(axis="y", alpha=0.3)
    sns.despine(ax=ax)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax


# ---------------------------------------------------------------------------
# Chart 2: Both spreads overlaid
# ---------------------------------------------------------------------------

def plot_both_spreads(
    spread_2s10s: pd.Series,
    spread_10y3m: pd.Series,
    recession_bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(14, 5))

    _shade_recessions(ax, recession_bands)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)

    ax.plot(spread_2s10s.index, spread_2s10s.values, color="#2980b9",
            linewidth=1.3, label="10Y–2Y (2s10s)", alpha=0.9)
    ax.plot(spread_10y3m.index, spread_10y3m.values, color="#e67e22",
            linewidth=1.3, label="10Y–3M", alpha=0.9)

    ax.set_title("2s10s vs. 10Y–3M Treasury Spreads", fontsize=14, fontweight="bold", pad=10)
    ax.set_ylabel("Spread (percentage points)")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", framealpha=0.8)
    ax.grid(axis="y", alpha=0.3)
    sns.despine(ax=ax)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax


# ---------------------------------------------------------------------------
# Chart 3: Component yields
# ---------------------------------------------------------------------------

def plot_component_yields(
    dgs10: pd.Series,
    dgs2: pd.Series,
    recession_bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(14, 5))

    _shade_recessions(ax, recession_bands)
    ax.plot(dgs10.index, dgs10.values, color="#2c3e50", linewidth=1.3, label="10-Year Yield")
    ax.plot(dgs2.index, dgs2.values, color="#e74c3c", linewidth=1.3, label="2-Year Yield")

    ax.set_title("10-Year and 2-Year Treasury Yields", fontsize=14, fontweight="bold", pad=10)
    ax.set_ylabel("Yield (%)")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper right", framealpha=0.8)
    ax.grid(axis="y", alpha=0.3)
    sns.despine(ax=ax)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax


# ---------------------------------------------------------------------------
# Chart 4: Fed Funds Rate vs. spread
# ---------------------------------------------------------------------------

def plot_fedfunds_vs_spread(
    spread: pd.Series,
    fedfunds: pd.Series,
    recession_bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(14, 5))

    ax2 = ax.twinx()

    _shade_recessions(ax, recession_bands)
    ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.5)

    l1, = ax.plot(spread.index, spread.values, color="#2980b9",
                  linewidth=1.3, label="2s10s Spread")
    l2, = ax2.plot(fedfunds.index, fedfunds.values, color="#e74c3c",
                   linewidth=1.0, alpha=0.7, label="Fed Funds Rate")

    ax.set_title("2s10s Spread vs. Federal Funds Rate", fontsize=14, fontweight="bold", pad=10)
    ax.set_ylabel("Spread (pp)", color="#2980b9")
    ax2.set_ylabel("Fed Funds Rate (%)", color="#e74c3c")
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.grid(axis="y", alpha=0.3)

    lines = [l1, l2]
    labels = [l.get_label() for l in lines]
    ax.legend(lines, labels, loc="upper left", framealpha=0.8)
    sns.despine(ax=ax, right=False)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax


# ---------------------------------------------------------------------------
# Chart 5: 2022–present zoom with unemployment & CPI
# ---------------------------------------------------------------------------

def plot_2022_episode(
    spread: pd.Series,
    unrate: pd.Series,
    cpi_yoy: pd.Series,
    recession_bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    start: str = "2021-01-01",
    save_path: str | None = None,
) -> plt.Figure:
    fig, axes = plt.subplots(3, 1, figsize=(13, 10), sharex=True)

    spread_zoom = spread.loc[start:]
    unrate_zoom = unrate.loc[start:]
    cpi_zoom = cpi_yoy.loc[start:]

    rec_zoom = [(s, e) for s, e in recession_bands if e >= pd.Timestamp(start)]

    # Top: spread
    _shade_recessions(axes[0], rec_zoom)
    axes[0].axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.6)
    axes[0].plot(spread_zoom.index, spread_zoom.values, color="#2980b9", linewidth=1.5)
    axes[0].fill_between(spread_zoom.index, spread_zoom.values, 0,
                         where=(spread_zoom.values < 0),
                         color="#e74c3c", alpha=0.3, label="Inversion")
    axes[0].set_ylabel("2s10s Spread (pp)")
    axes[0].set_title("The 2022–2024 Inversion: Spread, Unemployment, and Inflation",
                      fontsize=13, fontweight="bold", pad=10)
    axes[0].legend(loc="lower right", framealpha=0.8)
    axes[0].grid(axis="y", alpha=0.3)

    # Middle: unemployment
    _shade_recessions(axes[1], rec_zoom)
    axes[1].plot(unrate_zoom.index, unrate_zoom.values, color="#27ae60", linewidth=1.5)
    axes[1].set_ylabel("Unemployment Rate (%)")
    axes[1].grid(axis="y", alpha=0.3)

    # Bottom: CPI YoY
    _shade_recessions(axes[2], rec_zoom)
    axes[2].plot(cpi_zoom.index, cpi_zoom.values, color="#e67e22", linewidth=1.5)
    axes[2].axhline(2.0, color="gray", linewidth=0.8, linestyle=":", alpha=0.8,
                    label="2% Fed target")
    axes[2].set_ylabel("CPI YoY (%)")
    axes[2].legend(loc="upper right", framealpha=0.8)
    axes[2].grid(axis="y", alpha=0.3)
    axes[2].xaxis.set_major_locator(mdates.YearLocator(1))
    axes[2].xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    for ax in axes:
        sns.despine(ax=ax)

    plt.tight_layout()
    _save(fig, save_path)
    return fig


# ---------------------------------------------------------------------------
# Backtest summary: lead time distribution
# ---------------------------------------------------------------------------

def plot_lead_time_distribution(
    bt: pd.DataFrame,
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(8, 5))

    lead = bt[bt["result"] == "true positive"]["lead_time_months"].dropna()

    ax.bar(range(len(lead)), sorted(lead.values), color="#2980b9", alpha=0.8)
    ax.axhline(lead.mean(), color="#e74c3c", linestyle="--",
               linewidth=1.2, label=f"Mean: {lead.mean():.0f} months")
    ax.axhline(lead.median(), color="#27ae60", linestyle=":",
               linewidth=1.2, label=f"Median: {lead.median():.0f} months")
    ax.set_xlabel("Inversion Episode (sorted by lead time)")
    ax.set_ylabel("Months from Inversion to Recession")
    ax.set_title("Lead Time: Inversion to Recession Start", fontsize=13, fontweight="bold")
    ax.legend(framealpha=0.8)
    ax.grid(axis="y", alpha=0.3)
    sns.despine(ax=ax)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax


# ---------------------------------------------------------------------------
# Episode comparison: 2022 vs. history
# ---------------------------------------------------------------------------

def plot_episode_comparison(
    episodes_with_metrics: pd.DataFrame,
    col_x: str = "duration_months",
    col_y: str = "max_depth",
    label_col: str = "start",
    highlight_id: int | None = None,
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(9, 6))

    for _, row in episodes_with_metrics.iterrows():
        is_highlight = (highlight_id is not None and row.get("episode_id") == highlight_id)
        color = "#e74c3c" if is_highlight else "#2980b9"
        size = 120 if is_highlight else 70
        ax.scatter(row[col_x], row[col_y], color=color, s=size, zorder=3)
        label_val = pd.Timestamp(row[label_col]).strftime("%Y")
        ax.annotate(
            label_val,
            (row[col_x], row[col_y]),
            textcoords="offset points",
            xytext=(6, 4),
            fontsize=9,
            color=color,
        )

    ax.set_xlabel(col_x.replace("_", " ").title())
    ax.set_ylabel(col_y.replace("_", " ").title())
    ax.set_title("Inversion Episodes: Duration vs. Depth", fontsize=13, fontweight="bold")
    ax.grid(alpha=0.3)
    sns.despine(ax=ax)

    if highlight_id is not None:
        highlight_patch = mpatches.Patch(color="#e74c3c", label="2022–2024 episode")
        history_patch = mpatches.Patch(color="#2980b9", label="Prior episodes")
        ax.legend(handles=[highlight_patch, history_patch], framealpha=0.8)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax


# ---------------------------------------------------------------------------
# Probit model: recession probability over time
# ---------------------------------------------------------------------------

def plot_recession_probability(
    prob: pd.Series,
    recession_bands: list[tuple[pd.Timestamp, pd.Timestamp]],
    ax: plt.Axes | None = None,
    save_path: str | None = None,
) -> plt.Axes:
    standalone = ax is None
    if standalone:
        fig, ax = plt.subplots(figsize=(14, 4))

    _shade_recessions(ax, recession_bands)
    ax.plot(prob.index, prob.values * 100, color="#8e44ad", linewidth=1.4,
            label="Recession probability (%)")
    ax.axhline(30, color="gray", linewidth=0.8, linestyle=":", alpha=0.7,
               label="30% threshold")

    ax.set_title("NY Fed–Style Probit: 12-Month Recession Probability (10Y–3M spread)",
                 fontsize=13, fontweight="bold", pad=10)
    ax.set_ylabel("Probability (%)")
    ax.set_ylim(0, 105)
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.legend(loc="upper left", framealpha=0.8)
    ax.grid(axis="y", alpha=0.3)
    sns.despine(ax=ax)

    if standalone:
        plt.tight_layout()
        _save(fig, save_path)

    return ax
