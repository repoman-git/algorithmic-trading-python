"""The three course portfolios: equal weight, momentum, and value.

Share counts use the course rule: one portfolio amount, split equally, floored at the last price.
Momentum keeps the 50 highest high-quality-momentum scores. Value keeps the 50 lowest robust-value scores.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

RETURN_FIELDS = (
    ("One-Year", "year_1"),
    ("Six-Month", "month_6"),
    ("Three-Month", "month_3"),
    ("One-Month", "month_1"),
)
VALUE_FIELDS = (
    "Price-to-Earnings Ratio",
    "Price-to-Book Ratio",
    "Price-to-Sales Ratio",
    "EV/EBITDA",
    "EV/GP",
)


def equal_weight(market: pd.DataFrame, portfolio_size: float) -> pd.DataFrame:
    frame = market.dropna(subset=["price"]).copy()
    frame = frame[frame["price"] > 0]
    position = portfolio_size / len(frame)
    out = pd.DataFrame(
        {
            "Ticker": frame["ticker"].to_numpy(),
            "Price": frame["price"].to_numpy(),
            "Market Capitalization": frame["market_cap"].to_numpy(),
            "Number Of Shares to Buy": np.floor(position / frame["price"].to_numpy()).astype(int),
        }
    )
    return out.reset_index(drop=True)


def momentum(market: pd.DataFrame, portfolio_size: float, count: int = 50) -> pd.DataFrame:
    needed = ["price", *[field for _, field in RETURN_FIELDS]]
    frame = market.dropna(subset=needed).copy()
    frame = frame[frame["price"] > 0]
    for label, field in RETURN_FIELDS:
        frame[f"{label} Price Return"] = frame[field]
        frame[f"{label} Return Percentile"] = _percentile(frame[field])
    score_columns = [f"{label} Return Percentile" for label, _ in RETURN_FIELDS]
    frame["HQM Score"] = frame[score_columns].mean(axis=1)
    frame = frame.sort_values("HQM Score", ascending=False).head(count)
    position = portfolio_size / len(frame)
    columns = [
        "Ticker",
        "Price",
        "Number of Shares to Buy",
        "One-Year Price Return",
        "One-Year Return Percentile",
        "Six-Month Price Return",
        "Six-Month Return Percentile",
        "Three-Month Price Return",
        "Three-Month Return Percentile",
        "One-Month Price Return",
        "One-Month Return Percentile",
        "HQM Score",
    ]
    out = pd.DataFrame(
        {
            "Ticker": frame["ticker"].to_numpy(),
            "Price": frame["price"].to_numpy(),
            "Number of Shares to Buy": np.floor(position / frame["price"].to_numpy()).astype(int),
            "HQM Score": frame["HQM Score"].to_numpy(),
        }
    )
    for label, _ in RETURN_FIELDS:
        out[f"{label} Price Return"] = frame[f"{label} Price Return"].to_numpy()
        out[f"{label} Return Percentile"] = frame[f"{label} Return Percentile"].to_numpy()
    return out[columns].reset_index(drop=True)


def value(market: pd.DataFrame, portfolio_size: float, count: int = 50) -> pd.DataFrame:
    frame = market.dropna(subset=["price"]).copy()
    frame = frame[frame["price"] > 0]
    built = pd.DataFrame(
        {
            "Ticker": frame["ticker"].to_numpy(),
            "Price": frame["price"].to_numpy(),
            "Price-to-Earnings Ratio": frame["pe"].to_numpy(),
            "Price-to-Book Ratio": frame["pb"].to_numpy(),
            "Price-to-Sales Ratio": frame["ps"].to_numpy(),
            "EV/EBITDA": _ratio(frame["enterprise_value"], frame["ebitda"]),
            "EV/GP": _ratio(frame["enterprise_value"], frame["gross_profit"]),
        }
    )
    for column in VALUE_FIELDS:
        built[column] = built[column].fillna(built[column].mean())
    for column in VALUE_FIELDS:
        built[f"{column} Percentile"] = _percentile(built[column])
    percentile_columns = [f"{column} Percentile" for column in VALUE_FIELDS]
    built["RV Score"] = built[percentile_columns].mean(axis=1)
    built = built.sort_values("RV Score", ascending=True).head(count)
    position = portfolio_size / len(built)
    built.insert(2, "Number of Shares to Buy", np.floor(position / built["Price"].to_numpy()).astype(int))
    rename = {
        "Price-to-Earnings Ratio Percentile": "PE Percentile",
        "Price-to-Book Ratio Percentile": "PB Percentile",
        "Price-to-Sales Ratio Percentile": "PS Percentile",
    }
    return built.rename(columns=rename)[
        [
            "Ticker",
            "Price",
            "Number of Shares to Buy",
            "Price-to-Earnings Ratio",
            "PE Percentile",
            "Price-to-Book Ratio",
            "PB Percentile",
            "Price-to-Sales Ratio",
            "PS Percentile",
            "EV/EBITDA",
            "EV/EBITDA Percentile",
            "EV/GP",
            "EV/GP Percentile",
            "RV Score",
        ]
    ].reset_index(drop=True)


def _percentile(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    scores = [stats.percentileofscore(values, value) / 100 for value in values]
    return pd.Series(scores, index=series.index)


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    top = pd.to_numeric(numerator, errors="coerce")
    bottom = pd.to_numeric(denominator, errors="coerce")
    result = top / bottom
    return result.where(bottom.notna() & (bottom != 0))
