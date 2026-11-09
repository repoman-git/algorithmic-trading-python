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
