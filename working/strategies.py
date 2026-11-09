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


def value(
    market: pd.DataFrame,
    portfolio_size: float,
    count: int = 50,
    include: tuple[str, ...] = VALUE_FIELDS,
    require_positive: tuple[str, ...] = (),
) -> pd.DataFrame:
    frame = market.dropna(subset=["price"]).copy()
    frame = frame[frame["price"] > 0]
    ratios = {
        "Price-to-Earnings Ratio": pd.to_numeric(frame["pe"], errors="coerce"),
        "Price-to-Book Ratio": pd.to_numeric(frame["pb"], errors="coerce"),
        "Price-to-Sales Ratio": pd.to_numeric(frame["ps"], errors="coerce"),
        "EV/EBITDA": _ratio(frame["enterprise_value"], frame["ebitda"]),
        "EV/GP": _ratio(frame["enterprise_value"], frame["gross_profit"]),
    }
    keep = pd.Series(True, index=frame.index)
    for column in require_positive:
        values = ratios[column]
        keep &= values.notna() & (values > 0)
    frame = frame.loc[keep]
    built = pd.DataFrame({"Ticker": frame["ticker"].to_numpy(), "Price": frame["price"].to_numpy()})
    for column in include:
        built[column] = ratios[column].loc[keep].to_numpy()
    if built.empty:
        return built
    for column in include:
        built[column] = built[column].fillna(built[column].mean())
    for column in include:
        built[f"{column} Percentile"] = _percentile(built[column])
    percentile_columns = [f"{column} Percentile" for column in include]
    built["RV Score"] = built[percentile_columns].mean(axis=1)
    built = built.sort_values("RV Score", ascending=True).head(count)
    position = portfolio_size / len(built)
    built.insert(2, "Number of Shares to Buy", np.floor(position / built["Price"].to_numpy()).astype(int))
    rename = {
        "Price-to-Earnings Ratio Percentile": "PE Percentile",
        "Price-to-Book Ratio Percentile": "PB Percentile",
        "Price-to-Sales Ratio Percentile": "PS Percentile",
        "EV/EBITDA Percentile": "EV/EBITDA Percentile",
        "EV/GP Percentile": "EV/GP Percentile",
    }
    order = ["Ticker", "Price", "Number of Shares to Buy"]
    for column in include:
        order.append(column)
        order.append(rename[f"{column} Percentile"])
    order.append("RV Score")
    return built.rename(columns=rename)[order].reset_index(drop=True)


def _percentile(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce").to_numpy(dtype=float)
    scores = [stats.percentileofscore(values, value) / 100 for value in values]
    return pd.Series(scores, index=series.index)


def _ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    top = pd.to_numeric(numerator, errors="coerce")
    bottom = pd.to_numeric(denominator, errors="coerce")
    result = top / bottom
    return result.where(bottom.notna() & (bottom != 0))
