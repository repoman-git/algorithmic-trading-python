"""Build the three course portfolios and write them to output/."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from working.strategies import equal_weight, momentum, value
from working.universe import load_constituents, load_etfs
from working.yahoo import load_market

OUTPUT = Path("output")


def _present(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    for column in out.columns:
        if not pd.api.types.is_numeric_dtype(out[column]):
            continue
        if "Share" in column or column == "Market Capitalization":
            out[column] = out[column].round(0).astype("Int64")
        elif "Percentile" in column or "Return" in column or column.endswith("Score"):
            out[column] = out[column].round(4)
        else:
            out[column] = out[column].round(2)
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the three course portfolios from Yahoo Finance.")
    parser.add_argument("--portfolio", type=float, default=1_000_000, help="Dollar amount to split equally. Default matches the course demo.")
    parser.add_argument("--refresh", action="store_true", help="Ignore the saved fundamentals cache.")
    parser.add_argument("--limit", type=int, default=0, help="Use only the first N constituents. 0 means the full list.")
    parser.add_argument("--universe", choices=("sp500", "etf"), default="sp500")
    args = parser.parse_args()

    universe = load_etfs() if args.universe == "etf" else load_constituents()
    if args.limit:
        universe = universe.head(args.limit).reset_index(drop=True)
    print(f"constituents {len(universe)}", flush=True)
    market = load_market(universe, refresh=args.refresh)
    as_of = market.attrs["as_of"].isoformat()
    priced = int(market["price"].notna().sum())
    print(f"priced {priced}/{len(market)} as of {as_of}", flush=True)

    if args.universe == "etf":
        momentum_book = momentum(market, args.portfolio, count=10)
        value_book = value(
            market,
            args.portfolio,
            count=10,
            include=("Price-to-Earnings Ratio", "Price-to-Book Ratio"),
            require_positive=("Price-to-Earnings Ratio", "Price-to-Book Ratio"),
        )
    else:
        momentum_book = momentum(market, args.portfolio)
        value_book = value(market, args.portfolio)
    tables = {
        "Tickers": universe.rename(columns={"ticker": "Ticker", "security": "Security", "sector": "GICS Sector", "yahoo": "Yahoo"}),
        "Recommended Trades": _present(equal_weight(market, args.portfolio)),
        "Momentum": _present(momentum_book),
        "Value": _present(value_book),
    }
    output = OUTPUT / "etf" if args.universe == "etf" else OUTPUT
    output.mkdir(parents=True, exist_ok=True)
    filenames = {
        "Tickers": "tickers.csv",
        "Recommended Trades": "recommended_trades.csv",
        "Momentum": "momentum.csv",
        "Value": "value.csv",
    }
    for name, frame in tables.items():
        frame.to_csv(output / filenames[name], index=False)
        print(f"wrote {name} {len(frame)} rows", flush=True)
    workbook = "etf_strategies.xlsx" if args.universe == "etf" else "sp500_strategies.xlsx"
    with pd.ExcelWriter(output / workbook, engine="xlsxwriter") as writer:
        for name, frame in tables.items():
            frame.to_excel(writer, sheet_name=name, index=False)
    (output / "as_of.txt").write_text(as_of + "\n")
    print(f"portfolio {args.portfolio:.0f} as of {as_of}", flush=True)


if __name__ == "__main__":
    main()
