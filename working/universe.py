"""S&P 500 constituents from the Wikipedia list."""

import urllib.request
from io import StringIO

import pandas as pd

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"


def load_constituents() -> pd.DataFrame:
    request = urllib.request.Request(WIKI_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        html = response.read().decode("utf-8")
    table = pd.read_html(StringIO(html))[0]
    frame = pd.DataFrame(
        {
            "ticker": table["Symbol"].astype(str).str.strip(),
            "security": table["Security"].astype(str),
            "sector": table["GICS Sector"].astype(str),
        }
    )
    frame["yahoo"] = frame["ticker"].str.replace(".", "-", regex=False)
    return frame.drop_duplicates("yahoo").reset_index(drop=True)


# A liquid mix of broad equity, sector, factor, international, bond, and real-asset funds.
ETF_UNIVERSE = (
    ("SPY", "SPDR S&P 500", "US equity"),
    ("QQQ", "Invesco QQQ", "US equity"),
    ("IWM", "iShares Russell 2000", "US equity"),
    ("DIA", "SPDR Dow Jones", "US equity"),
    ("VTI", "Vanguard Total Stock Market", "US equity"),
    ("XLK", "Technology Select Sector SPDR", "US sector"),
    ("XLF", "Financial Select Sector SPDR", "US sector"),
    ("XLE", "Energy Select Sector SPDR", "US sector"),
    ("XLV", "Health Care Select Sector SPDR", "US sector"),
    ("XLY", "Consumer Discretionary Select Sector SPDR", "US sector"),
    ("XLP", "Consumer Staples Select Sector SPDR", "US sector"),
    ("XLI", "Industrial Select Sector SPDR", "US sector"),
    ("XLB", "Materials Select Sector SPDR", "US sector"),
    ("XLU", "Utilities Select Sector SPDR", "US sector"),
    ("XLRE", "Real Estate Select Sector SPDR", "US sector"),
    ("XLC", "Communication Services Select Sector SPDR", "US sector"),
    ("MTUM", "iShares MSCI USA Momentum Factor", "US factor"),
    ("VLUE", "iShares MSCI USA Value Factor", "US factor"),
    ("QUAL", "iShares MSCI USA Quality Factor", "US factor"),
    ("USMV", "iShares MSCI USA Min Vol Factor", "US factor"),
    ("VUG", "Vanguard Growth", "US factor"),
    ("VTV", "Vanguard Value", "US factor"),
    ("EFA", "iShares MSCI EAFE", "International equity"),
    ("EEM", "iShares MSCI Emerging Markets", "International equity"),
    ("VEA", "Vanguard FTSE Developed Markets", "International equity"),
    ("VWO", "Vanguard FTSE Emerging Markets", "International equity"),
    ("TLT", "iShares 20+ Year Treasury", "Bond"),
    ("IEF", "iShares 7-10 Year Treasury", "Bond"),
    ("SHY", "iShares 1-3 Year Treasury", "Bond"),
    ("AGG", "iShares Core US Aggregate Bond", "Bond"),
    ("HYG", "iShares iBoxx High Yield Corporate Bond", "Bond"),
    ("LQD", "iShares iBoxx Investment Grade Corporate Bond", "Bond"),
    ("TIP", "iShares TIPS Bond", "Bond"),
    ("GLD", "SPDR Gold Shares", "Real asset"),
    ("SLV", "iShares Silver Trust", "Real asset"),
    ("VNQ", "Vanguard Real Estate", "Real asset"),
    ("DBC", "Invesco DB Commodity Index", "Real asset"),
)


def load_etfs() -> pd.DataFrame:
    frame = pd.DataFrame(ETF_UNIVERSE, columns=["ticker", "security", "sector"])
    frame["yahoo"] = frame["ticker"]
    return frame
