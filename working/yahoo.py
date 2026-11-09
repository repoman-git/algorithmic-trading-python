"""Prices and fundamentals from Yahoo Finance, with a resumable cache."""

from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd
import yfinance as yf

CACHE_PATH = Path("data/cache/fundamentals.jsonl")
_CACHE_LOCK = Lock()
RETURN_SESSIONS = {
    "month_1": 21,
    "month_3": 63,
    "month_6": 126,
    "year_1": 252,
}


def load_market(universe: pd.DataFrame, refresh: bool = False) -> pd.DataFrame:
    symbols = universe["yahoo"].tolist()
    close, adjusted = _download_prices(symbols)
    prices = _price_frame(close, adjusted)
    fundamentals = _load_fundamentals(symbols, refresh=refresh)
    frame = universe.merge(prices, on="yahoo", how="left").merge(fundamentals, on="yahoo", how="left")
    frame.attrs["as_of"] = _as_of(close)
    return frame


def _download_prices(symbols: list[str]) -> tuple[pd.DataFrame, pd.DataFrame]:
    closes = []
    adjusted = []
    for start in range(0, len(symbols), 80):
        chunk = symbols[start : start + 80]
        raw = yf.download(
            chunk,
            period="2y",
            auto_adjust=False,
            progress=False,
            threads=True,
            group_by="column",
        )
        closes.append(_extract(raw, "Close", chunk))
        adjusted.append(_extract(raw, "Adj Close", chunk))
        print(f"prices {min(start + 80, len(symbols))}/{len(symbols)}", flush=True)
    return pd.concat(closes, axis=1), pd.concat(adjusted, axis=1)


def _extract(raw: pd.DataFrame, field: str, symbols: list[str]) -> pd.DataFrame:
    if isinstance(raw.columns, pd.MultiIndex):
        level0 = raw.columns.get_level_values(0)
        if field in level0:
            out = raw[field]
        elif field == "Adj Close" and "Close" in level0:
            out = raw["Close"]
        else:
            out = raw.xs(field, axis=1, level=-1)
    else:
        column = field if field in raw.columns else "Close"
        out = raw[[column]].copy()
        out.columns = symbols[:1]
    if isinstance(out, pd.Series):
        out = out.to_frame(symbols[0])
    out = out.reindex(columns=symbols)
    out.columns = symbols
    return out


def _price_frame(close: pd.DataFrame, adjusted: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for symbol in close.columns:
        last = close[symbol].dropna()
        history = adjusted[symbol].dropna()
        row = {"yahoo": symbol, "price": float(last.iloc[-1]) if len(last) else np.nan}
        for name, sessions in RETURN_SESSIONS.items():
            if len(history) <= sessions:
                row[name] = np.nan
            else:
                row[name] = float(history.iloc[-1] / history.iloc[-1 - sessions] - 1)
        rows.append(row)
    return pd.DataFrame(rows)


def _as_of(close: pd.DataFrame) -> date:
    stamp = pd.Timestamp(close.index.max())
    return stamp.date()


def _load_fundamentals(symbols: list[str], refresh: bool) -> pd.DataFrame:
    cached = {} if refresh else _read_cache()
    missing = [symbol for symbol in symbols if symbol not in cached]
    if missing:
        print(f"fundamentals {len(missing)} to fetch", flush=True)
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {pool.submit(_one_fundamental, symbol): symbol for symbol in missing}
            done = 0
            for future in as_completed(futures):
                row = future.result()
                if row is not None:
                    cached[row["yahoo"]] = row
                    _append_cache(row)
                done += 1
                if done % 25 == 0 or done == len(missing):
                    print(f"fundamentals {done}/{len(missing)}", flush=True)
    rows = [cached[symbol] for symbol in symbols if symbol in cached]
    frame = pd.DataFrame(rows)
    expected = ["yahoo", "market_cap", "pe", "pb", "ps", "enterprise_value", "ebitda", "gross_profit"]
    if frame.empty:
        return pd.DataFrame(columns=expected)
    return frame.reindex(columns=expected)


def _one_fundamental(symbol: str) -> dict | None:
    info = {}
    for attempt in range(3):
        try:
            info = yf.Ticker(symbol).info or {}
        except Exception as error:
            print(f"fundamentals {symbol} failed ({attempt + 1}): {error}", flush=True)
            info = {}
        if info.get("marketCap") or info.get("trailingPE"):
            break
    if not info:
        return None
    return {
        "yahoo": symbol,
        "market_cap": info.get("marketCap"),
        "pe": info.get("trailingPE"),
        "pb": info.get("priceToBook"),
        "ps": info.get("priceToSalesTrailing12Months"),
        "enterprise_value": info.get("enterpriseValue"),
        "ebitda": info.get("ebitda"),
        "gross_profit": info.get("grossProfits"),
    }


def _read_cache() -> dict[str, dict]:
    if not CACHE_PATH.exists():
        return {}
    rows = {}
    for line in CACHE_PATH.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        rows[row["yahoo"]] = row
    return rows


def _append_cache(row: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(row) + "\n"
    with _CACHE_LOCK:
        with CACHE_PATH.open("a") as handle:
            handle.write(line)
