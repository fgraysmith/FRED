"""
FRED API wrapper with local CSV caching.

Usage:
    loader = FredLoader()
    df = loader.get_series("T10Y2Y")
    merged = loader.load_all()
"""

import os
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from fredapi import Fred

load_dotenv()

DATA_DIR = Path(__file__).parent.parent / "data" / "raw"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SERIES = {
    "T10Y2Y":   "10Y-2Y Spread (daily, 1976+)",
    "T10Y3M":   "10Y-3M Spread (daily, 1982+)",
    "DGS10":    "10-Year Treasury Yield (daily, 1962+)",
    "DGS2":     "2-Year Treasury Yield (daily, 1976+)",
    "DTB3":     "3-Month T-Bill Yield (daily, 1954+)",
    "USREC":    "NBER Recession Indicator (monthly, 0/1)",
    "FEDFUNDS": "Federal Funds Rate (monthly)",
    "UNRATE":   "Unemployment Rate (monthly)",
    "CPIAUCSL": "CPI All Urban (monthly)",
    "GDPC1":    "Real GDP (quarterly)",
}

START_DATE = "1954-01-01"


class FredLoader:
    def __init__(self, api_key: str | None = None):
        key = api_key or os.environ.get("FRED_API_KEY")
        if not key:
            raise ValueError(
                "FRED API key not found. Set FRED_API_KEY in your .env file "
                "or pass api_key= to FredLoader()."
            )
        self.fred = Fred(api_key=key)

    def get_series(
        self,
        series_id: str,
        force_refresh: bool = False,
        start: str = START_DATE,
    ) -> pd.Series:
        """Return a series, pulling from local cache when available."""
        cache_path = DATA_DIR / f"{series_id}.csv"

        if cache_path.exists() and not force_refresh:
            s = pd.read_csv(cache_path, index_col=0, parse_dates=True).squeeze()
            s.name = series_id
            return s

        print(f"  Pulling {series_id} from FRED...")
        s = self.fred.get_series(series_id, observation_start=start)
        s.name = series_id
        s.to_csv(cache_path, header=True)
        return s

    def pull_all(self, force_refresh: bool = False) -> dict[str, pd.Series]:
        """Pull every series in SERIES, returning a dict keyed by series ID."""
        data = {}
        for sid in SERIES:
            data[sid] = self.get_series(sid, force_refresh=force_refresh)
        print(f"\nAll {len(data)} series loaded.")
        return data

    def load_all(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Pull all series and return a single DataFrame aligned to a monthly
        date index. Daily series are resampled to month-end means; quarterly
        GDP is forward-filled.
        """
        raw = self.pull_all(force_refresh=force_refresh)

        daily_ids = ["T10Y2Y", "T10Y3M", "DGS10", "DGS2", "DTB3"]
        monthly_ids = ["USREC", "FEDFUNDS", "UNRATE", "CPIAUCSL"]
        quarterly_ids = ["GDPC1"]

        frames = []

        for sid in daily_ids:
            s = raw[sid].resample("ME").mean()
            frames.append(s)

        for sid in monthly_ids:
            s = raw[sid].copy()
            s.index = s.index + pd.offsets.MonthEnd(0)
            frames.append(s)

        for sid in quarterly_ids:
            s = raw[sid].resample("ME").ffill()
            frames.append(s)

        df = pd.concat(frames, axis=1)
        df.index.name = "date"

        # 2s10s: manual from components (DGS2 starts 1976); use official T10Y2Y where available
        df["SPREAD_2S10S_MANUAL"] = df["DGS10"] - df["DGS2"]
        df["SPREAD_2S10S"] = df["T10Y2Y"].combine_first(df["SPREAD_2S10S_MANUAL"])

        # 10Y–3M: extend back to 1962 using DGS10 - DTB3 (official T10Y3M only starts 1982)
        df["SPREAD_10Y3M_MANUAL"] = df["DGS10"] - df["DTB3"]
        df["SPREAD_10Y3M"] = df["T10Y3M"].combine_first(df["SPREAD_10Y3M_MANUAL"])
        df["SPREAD_10Y3M_EXTENDED"] = df["SPREAD_10Y3M"]  # alias used by backtest notebooks

        return df

    @staticmethod
    def series_info() -> pd.DataFrame:
        return pd.DataFrame(
            [(k, v) for k, v in SERIES.items()],
            columns=["series_id", "description"],
        )
