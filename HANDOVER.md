# Handover

Written 9 November 2026, for the next agent who picks this up. Simon expects a gap of some weeks. Read this file before changing anything.

This is Simon's fork of Nick McCullum's freeCodeCamp course *Algorithmic Trading in Python* (December 2020). The course notebooks are kept as the record of the course. They do not run. The runnable path is the `working/` package added on 9 November 2026.

## Where things are

| What | Where |
|---|---|
| This clone | `/Users/simonerses/code/algorithmic-trading-python` |
| GitHub | https://github.com/repoman-git/algorithmic-trading-python |
| Remote | `origin` fetches and pushes only that URL. Branch `master`. |
| Course notebooks | `starter_files/` and `finished_files/`, three notebooks each. Untouched. |
| Runnable code | `working/universe.py`, `working/yahoo.py`, `working/strategies.py`, `working/run.py` |
| Python | 3.13.7, venv at `.venv` (gitignored). Recreate it; do not commit it. |
| Last prices used | 6 November 2026 close, both the stock run and the ETF run |
| Local results | `output/` and `output/etf/` (gitignored). A fresh clone has none of them. |
| Fundamentals cache | `data/cache/fundamentals.jsonl` (gitignored). 540 lines on this machine on 9 November 2026. |
| Sheets, stocks only | Drive folder [Algorithmic Trading Python](https://drive.google.com/drive/folders/1Jv-FmrhxvM-4FcTW9Dc4dhQPqqhOs0qs) |

Account on this machine for `git` and `gh` is **repoman-git** (display name Repoman). Do not push to `nickmccullum/algorithmic-trading-python`. A push there already failed with 403. Nick's public repository was not deleted and must not be. Simon asked only to drop the local remote that pointed at it, after this fork held the course history plus the new runner. That remote is gone. History still starts at Nick's last commit, `e1e3c2e` ("corrected link for S&P 500 stocks", 4 December 2020).

At the moment this note was committed, GitHub `master` was still `064558d`. The ETF commit `268039d` and this note were local only. Push only if Simon asks.

This repository is not tradeview-obots. Do not import that repo's broker, evidence-file, or pull-request rules. Ordinary hygiene still applies: no secrets in git, no force-push, no push to someone else's repository.

## Why the notebooks were left alone

The published course cannot run, for three separate reasons.

1. IEX Cloud is gone. The notebooks call `https://sandbox.iexapis.com`. That host shut down in 2024. The sandbox prices were randomly generated even when it was alive. Do not try to revive IEX.
2. The constituent CSV and `secrets.py` were external downloads. They are not in the clone. `secrets.py` is gitignored. None was created for this work.
3. `requirements.txt` originally pinned pandas 0.25.3 and numpy 1.17.4. Those pins do not install on this Mac's Python 3.13. `DataFrame.append` was removed in pandas 2.0. The new code never uses it.

Simon asked to upgrade the libraries and keep the course notebooks as they are. `requirements.txt` is now lower bounds: jupyter, numpy, pandas, requests, scipy, XlsxWriter, yfinance, lxml. See that file for the numbers.

## What the runner does

One command builds all three course portfolios.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m working.run --portfolio 1000000
.venv/bin/python -m working.run --universe etf --portfolio 1000000
```

`--portfolio` defaults to `1000000`, the course demo. The amount is split equally across the names that survive the screen. Shares are `floor(slot / last price)`. `--limit N` keeps the first N names. `--refresh` ignores the fundamentals cache. `--universe` is `sp500` (default) or `etf`.

Stock output lands in `output/`. ETF output lands in `output/etf/`. Each run writes `tickers.csv`, `recommended_trades.csv`, `momentum.csv`, `value.csv`, `as_of.txt`, and one workbook (`sp500_strategies.xlsx` or `etf_strategies.xlsx`) with those four tables as sheets.

### Data

S&P 500 names come from the Wikipedia list, not from the course CSV. On 9 November 2026 that list had 503 rows. Dots in tickers become dashes so Yahoo accepts them (`BRK.B` to `BRK-B`, `BF.B` to `BF-B`). Wikipedia blocks a bare urllib client, so the request sends a browser User-Agent. `pandas.read_html` must receive an `io.StringIO` of the decoded HTML. Passing the raw string makes lxml treat it as a filename and raises `OSError`.

The ETF list is the 37-name tuple `ETF_UNIVERSE` in `working/universe.py`: broad US equity, the 11 SPDR sectors, six factor funds, four international funds, seven bond funds, and four real-asset funds. It is a chosen liquid mix, not an index membership.

Prices come from Yahoo Finance through `yfinance`, period `2y`, `auto_adjust=False`, downloaded in chunks of 80. The trade price is the last unadjusted `Close`. Returns use `Adj Close` over 21, 63, 126, and 252 sessions (one month, three months, six months, one year). If a download has no `Adj Close` column, the code falls back to `Close` for that chunk.

Fundamentals are `Ticker.info`, six workers, three attempts, appended to `data/cache/fundamentals.jsonl` only on success. The cache is shared by both universes. A row is a success when `marketCap`, `trailingPE`, or `totalAssets` is present. The `market_cap` column stores `marketCap`, or `totalAssets` when that is all Yahoo has, so for an ETF that column is assets under management and the equal-weight sheet still labels it Market Capitalization.

Yahoo field map:

| Column | Yahoo key |
|---|---|
| market_cap | `marketCap`, else `totalAssets` |
| pe | `trailingPE` |
| pb | `priceToBook` |
| ps | `priceToSalesTrailing12Months` |
| enterprise_value | `enterpriseValue` |
| ebitda | `ebitda` |
| gross_profit | `grossProfits` |

### The three portfolios

Equal weight keeps every name with a positive price. One slot is `portfolio / n`.

Momentum builds the course high-quality-momentum score: the mean of the percentile ranks of the four returns. Higher is stronger. Stocks keep 50. ETFs keep 10, because the universe is 37. The course notebook sorts the frame and then slices `[:51]` without assigning the sort back, so the notebook does not actually keep the top names. This runner sorts and keeps the highest scores, which is what the course markdown describes.

Value builds the course robust-value score: the mean of the percentile ranks of the valuation ratios. Lower is cheaper. Missing ratios are filled with that column's mean, which is the course method. Stocks use all five ratios and keep 50. ETFs use only price-to-earnings and price-to-book, and a name must have both strictly positive. Yahoo does not return price-to-sales, enterprise value, EBITDA, or gross profit for these funds. Scoring the three missing ratios would fill entire columns with the column mean and invent a rank.

Percentiles are `scipy.stats.percentileofscore(values, value) / 100`, computed against the set being ranked, including the value itself.

### Column names

Equal weight writes `Number Of Shares to Buy`. Momentum and value write `Number of Shares to Buy`. That capital-O difference is in the code on purpose so the equal-weight sheet matches the course notebook's heading. Do not "normalize" it without a reason.

The ticker sheet always renames `sector` to `GICS Sector`, including the ETF run, where the values are the labels from `ETF_UNIVERSE` (`US equity`, `Bond`, and so on) rather than GICS sectors.

## Results already produced

Both runs used `$1,000,000` and the 6 November 2026 close. Returns below are fractions, so `9.7890` is about 979 percent. These numbers live in the gitignored CSVs on this machine and, for the stock run only, in Google Sheets. A later run will differ.

### S&P 500

503 names priced. Equal-weight slot is about `$1,988`. AZO at `$3,216.35` and NVR at `$6,298.29` get 0 shares. Every other name got a positive count.

Momentum, highest HQM first: MRNA (price 254.19, 78 shares, one-year return 9.7890, HQM 0.9965), SWK, CRL, BDX, HAS. The MRNA one-year return is an extreme print. It was reported and left in.

Value, cheapest RV first: HPQ (RV 0.0433, price-to-book `-279.02`), CMCSA, APTV, UHS, SMCI. HPQ leads because a large negative book value ranks as the cheapest price-to-book. The course fill-with-mean method keeps negative ratios. Other names with a very low or negative book multiple in that list included names such as BRK.B. This was reported and left in.

Sheets, stock run only, created 9 November 2026. Drive's create-file call turns one CSV into one single-tab Google Sheet, so the four tables are four files rather than one workbook. The local xlsx has all four tabs.

- [S&P 500 tickers](https://docs.google.com/spreadsheets/d/1pzO43G0aPxNxXCE-ZN1Eey2Bzba2UKfm0KABkrAFd6o/edit), id `1pzO43G0aPxNxXCE-ZN1Eey2Bzba2UKfm0KABkrAFd6o`
- [Equal-weight S&P 500](https://docs.google.com/spreadsheets/d/1ZE_DkHjsTOF0C5hD4_LP0p0p31Z8w_ZFO_THJLIfIRM/edit), id `1ZE_DkHjsTOF0C5hD4_LP0p0p31Z8w_ZFO_THJLIfIRM`
- [Quantitative momentum 2026-11-06](https://docs.google.com/spreadsheets/d/1O4yDQtUs-VkdkXoNpNiPbKhU34tm2UBzihV0PCyOdDY/edit), id `1O4yDQtUs-VkdkXoNpNiPbKhU34tm2UBzihV0PCyOdDY`. Read back as 52 lines (title, header, 50 names).
- [Quantitative value 2026-11-06](https://docs.google.com/spreadsheets/d/1A_CCaNAbptcyOOXRiBWhhOTWsPTb1CJszOlakjGgM58/edit), id `1A_CCaNAbptcyOOXRiBWhhOTWsPTb1CJszOlakjGgM58`. Read back the same way.

After those creates, a further Sheets read returned HTTP 429, `ReadRequestsPerMinutePerProject` limit 300. The equal-weight and ticker files were created and returned ids. They were not read back after the quota error. Do not retry in a tight loop.

### ETFs

37 names, all with a positive price and a positive share count. Equal-weight slot is about `$27,027`. Examples: SPY 735.29, market-cap column about 797 billion (that is `totalAssets`), 36 shares. DBC 31.54, 856 shares in the equal-weight book.

Momentum top 10, highest HQM first: XLV (184.80, 541 shares, one-year 0.2899, HQM 0.9797), XLP, VTV, XLE, DBC, XLRE, XLB, XLF, USMV, VNQ. Defensive sectors and real assets led. QQQ and XLK were not in the top 10.

Value top 10, cheapest RV first, scored only on positive P/E and price-to-book: TIP (RV 0.1923), HYG (same RV, next on the sort), XLU, XLB, EEM, VWO, DBC, XLE, VUG, XLY. TIP and HYG lead because Yahoo returned both ratios for those bond funds and the ratios are low. Gold, silver, and the Treasury funds that lack a positive trailing P/E drop out before scoring. VUG is in the list with price-to-book `0.38`, which is a suspicious print for a growth fund and pulled it up. ETF tables were not uploaded to Drive.

## What Simon already decided

- Use this fork, not the 2022 stale copy that was the first URL he pasted (`hi99Free/https-github.com-nickmccullum-algorithmic-trading-python`).
- Upgrade the libraries. Leave the 2020 notebooks in place.
- Yahoo supplies the fields. Google Sheets holds the finished stock tables. `GOOGLEFINANCE` alone cannot supply price-to-book, price-to-sales, enterprise value, EBITDA, or gross profit, and historical `GOOGLEFINANCE` cells cannot be read back through the Sheets API. The design is Yahoo in Python, then write the tables.
- Portfolio amount stays the course demo of `$1,000,000`.
- ETF value scoring uses only the ratios Yahoo actually returns, and those ratios must be positive.
- The odd ranks (negative book value, the MRNA return, bond funds and VUG on the ETF value list) were described to him. He did not ask to change the score. Do not silently drop them.

## Left undone

- Push `268039d` and this note. GitHub `master` was `064558d` when this note was written.
- Upload the ETF tables to the Drive folder.
- Re-read the equal-weight and ticker sheets after the 429, if anyone needs to confirm those two files cell by cell. Momentum and value were already confirmed.
- Any rescoring: winsorize or drop non-positive book values, cap one-year returns, or stop treating a bond fund's P/E as a value signal. That is the natural next analytical pass. It is not a bugfix until Simon asks for it.
- The course README is still Nick's outline. It does not mention `working/`.
- Stale Dependabot branches were visible on the fork on 9 November 2026 (`numpy-1.22.0`, `requests-2.31.0`, `scipy-1.10.0`). They were left alone. The pins they propose are behind the bounds in `requirements.txt`.

## Commits that matter

| SHA | What it is |
|---|---|
| `e1e3c2e` | Nick's last commit. The fork starts here. |
| `064558d` | `Replace the dead IEX calls with a Yahoo Finance run of the three course portfolios.` On GitHub at the time of this note. Adds `working/`, replaces `requirements.txt`, extends `.gitignore`. |
| `268039d` | `Add an ETF universe and score value on the ratios Yahoo returns for funds.` Local at the time of this note. |
| the commit that adds this file | This handover. |

`.gitignore` covers `.venv/`, `venv/`, `data/cache/`, `output/`, `__pycache__/`, `secrets.py`, `sp_500_stocks.csv`, and the course's old xlsx names. Generated tables stay out of git.
