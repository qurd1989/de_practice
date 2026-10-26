"""
Undervalued Stock Screener (recent-decline focused)
---------------------------------------------------
- Fetches S&P 500 + S&P 400 + Nasdaq 100 from Wikipedia with a real User-Agent
- Bulk-downloads 1y price history; derives current price, 52w high, and
  1-/3-month returns directly from prices (no .info needed for these)
- Pulls fundamentals (P/E, P/B, margins, etc.) per-ticker via yfinance .info
- Hard filters: down >= 15% from 52w high AND 3-month return <= 0
- Score weights drawdown + recent decline higher than valuation ratios
"""

from __future__ import annotations

import io
import time
import logging
from typing import Iterable

import pandas as pd
import requests
import yfinance as yf

try:
    from .config import *
except Exception:
    from undervalued_stocks.config import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
log = logging.getLogger("screener")

REQUIRED_COLS = {
    "ticker", "price", "fifty_two_high", "pct_3mo", "market_cap",
    "forward_pe", "price_to_book", "price_to_sales", "ev_to_ebitda",
}


# -------------------- universe (Wikipedia with UA) --------------------
def _wiki_html(url: str) -> io.StringIO:
    resp = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=20)
    resp.raise_for_status()
    return io.StringIO(resp.text)


def get_sp500_tickers() -> list[str]:
    df = pd.read_html(_wiki_html("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"))[0]
    return df["Symbol"].astype(str).str.replace(".", "-", regex=False).tolist()


def get_sp400_tickers() -> list[str]:
    df = pd.read_html(_wiki_html("https://en.wikipedia.org/wiki/List_of_S%26P_400_companies"))[0]
    col = "Symbol" if "Symbol" in df.columns else df.columns[0]
    return df[col].astype(str).str.replace(".", "-", regex=False).tolist()


def get_nasdaq100_tickers() -> list[str]:
    tables = pd.read_html(_wiki_html("https://en.wikipedia.org/wiki/Nasdaq-100"))
    for t in tables:
        cols_lower = [str(c).lower() for c in t.columns]
        if "ticker" in cols_lower or "symbol" in cols_lower:
            idx = cols_lower.index("ticker") if "ticker" in cols_lower else cols_lower.index("symbol")
            col = t.columns[idx]
            return t[col].astype(str).str.replace(".", "-", regex=False).tolist()
    return []


def build_universe() -> list[str]:
    universe: set[str] = set()
    for fn, name in [
        (get_sp500_tickers, "S&P 500"),
        (get_sp400_tickers, "S&P 400"),
        (get_nasdaq100_tickers, "Nasdaq 100"),
    ]:
        try:
            tix = fn()
            log.info("Loaded %d from %s", len(tix), name)
            universe.update(tix)
        except Exception as e:
            log.warning("Could not load %s: %s", name, e)
    log.info("Total unique tickers: %d", len(universe))
    if not universe:
        raise RuntimeError("Universe is empty - all index fetches failed")
    return sorted(universe)


# -------------------- bulk price + return calc --------------------
def fetch_bulk_prices(tickers: list[str]) -> dict[str, dict]:
    """Bulk 1y daily history; derive price, 52w high, 1mo & 3mo returns."""
    log.info("Bulk-downloading 1y history for %d tickers...", len(tickers))
    data = yf.download(
        tickers=" ".join(tickers),
        period="1y",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
        threads=True,
    )
    out: dict[str, dict] = {}
    for t in tickers:
        try:
            sub = data[t] if isinstance(data.columns, pd.MultiIndex) else data
            close = sub["Close"].dropna()
            high  = sub["High"].dropna()
            if len(close) < 65:  # need ~3 months of data
                continue
            price = float(close.iloc[-1])
            out[t] = {
                "price":          price,
                "fifty_two_high": float(high.max()),
                "fifty_two_low":  float(sub["Low"].dropna().min()),
                "pct_1mo":        price / float(close.iloc[-21]) - 1,   # ~21 trading days
                "pct_3mo":        price / float(close.iloc[-63]) - 1,   # ~63 trading days
            }
        except Exception as e:
            log.debug("price extract failed for %s: %s", t, e)
    log.info("Got prices for %d / %d tickers", len(out), len(tickers))
    return out


# -------------------- per-ticker fundamentals --------------------
def chunked(seq: list, n: int) -> Iterable[list]:
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def _fetch_info(ticker: str, retries: int = 2) -> dict | None:
    for attempt in range(retries + 1):
        try:
            t = yf.Ticker(ticker)
            try:
                info = t.get_info()
            except Exception:
                info = t.info
            if info:
                return info
        except Exception as e:
            log.debug("info attempt %d for %s: %s", attempt + 1, ticker, e)
        time.sleep(0.4 * (attempt + 1))
    return None


def fetch_fundamentals(tickers: list[str]) -> pd.DataFrame:
    prices = fetch_bulk_prices(tickers)

    # only fetch fundamentals for names where we got bulk prices
    pricey_tickers = [t for t in tickers if t in prices]
    log.info("Fetching fundamentals for %d priced tickers", len(pricey_tickers))

    rows = []
    for batch in chunked(pricey_tickers, BATCH_SIZE):
        log.info("Info batch (first=%s)", batch[0])
        for tkr in batch:
            info = _fetch_info(tkr) or {}
            row = _extract_row(tkr, info)
            row.update(prices[tkr])  # overlay reliable price/return data
            rows.append(row)
        time.sleep(SLEEP_BETWEEN)
    df = pd.DataFrame(rows)
    log.info("Built %d row dataframe", len(df))
    return df


def _extract_row(ticker: str, info: dict) -> dict:
    return {
        "ticker":          ticker,
        "name":            info.get("shortName") or info.get("longName") or ticker,
        "sector":          info.get("sector"),
        "industry":        info.get("industry"),
        "price":           None,            # filled by bulk
        "market_cap":      info.get("marketCap"),
        "trailing_pe":     info.get("trailingPE"),
        "forward_pe":      info.get("forwardPE"),
        "peg":             info.get("pegRatio"),
        "price_to_book":   info.get("priceToBook"),
        "price_to_sales":  info.get("priceToSalesTrailing12Months"),
        "ev_to_ebitda":    info.get("enterpriseToEbitda"),
        "dividend_yield":  info.get("dividendYield"),
        "fifty_two_high":  None,            # filled by bulk
        "fifty_two_low":   None,            # filled by bulk
        "pct_1mo":         None,            # filled by bulk
        "pct_3mo":         None,            # filled by bulk
        "profit_margin":   info.get("profitMargins"),
        "roe":             info.get("returnOnEquity"),
        "debt_to_equity":  info.get("debtToEquity"),
        "free_cashflow":   info.get("freeCashflow"),
    }


def _validate_df(df: pd.DataFrame, ctx: str) -> None:
    if df.empty:
        raise RuntimeError(f"{ctx}: dataframe is empty")
    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise RuntimeError(f"{ctx}: missing required columns: {sorted(missing)}")
    valid = df["price"].notna().sum()
    if valid < MIN_VALID_ROWS:
        raise RuntimeError(f"{ctx}: only {valid} priced rows (need >= {MIN_VALID_ROWS})")


# -------------------- scoring --------------------
def score(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["off_high_pct"] = (df["fifty_two_high"] - df["price"]) / df["fifty_two_high"]

    # HARD FILTERS - must be undervalued AND recently declining
    mask = (
        (df["market_cap"].fillna(0) >= MIN_MARKET_CAP)
        & (df["forward_pe"].between(0, MAX_FORWARD_PE))
        & (df["off_high_pct"] >= MIN_OFF_HIGH_PCT)
        & (df["pct_3mo"] <= MAX_3MO_RETURN)        # actually dropped recently
    )
    df = df[mask].copy()
    log.info("After filters (>=15%% off high, 3mo return <=0): %d rows", len(df))
    if df.empty:
        return df

    def pct_rank(s, ascending=True):
        return s.rank(pct=True, ascending=ascending)

    # value signals (lower = better)
    rank_pe    = pct_rank(df["forward_pe"], ascending=True)
    rank_pb    = pct_rank(df["price_to_book"].fillna(df["price_to_book"].median()), ascending=True)
    rank_ps    = pct_rank(df["price_to_sales"].fillna(df["price_to_sales"].median()), ascending=True)
    rank_ev    = pct_rank(df["ev_to_ebitda"].fillna(df["ev_to_ebitda"].median()), ascending=True)
    # decline signals (more negative / larger drawdown = better)
    rank_dd    = pct_rank(df["off_high_pct"], ascending=False)
    rank_3mo   = pct_rank(df["pct_3mo"], ascending=True)   # lower (more negative) = better
    rank_1mo   = pct_rank(df["pct_1mo"].fillna(0), ascending=True)
    # quality signals (higher = better)
    rank_div   = pct_rank(df["dividend_yield"].fillna(0), ascending=False)
    rank_roe   = pct_rank(df["roe"].fillna(0), ascending=False)

    # weighted composite - emphasize drawdown + recent decline
    df["undervalued_score"] = (
        0.15 * rank_pe
      + 0.10 * rank_pb
      + 0.10 * rank_ps
      + 0.10 * rank_ev
      + 0.20 * rank_dd
      + 0.15 * rank_3mo
      + 0.10 * rank_1mo
      + 0.05 * rank_div
      + 0.05 * rank_roe
    )

    keep = [
        "ticker", "name", "sector", "industry", "price", "market_cap",
        "trailing_pe", "forward_pe", "peg", "price_to_book", "price_to_sales",
        "ev_to_ebitda", "dividend_yield", "off_high_pct", "pct_1mo", "pct_3mo",
        "profit_margin", "roe", "debt_to_equity", "undervalued_score",
    ]
    return df[keep].sort_values("undervalued_score", ascending=False)


# -------------------- main --------------------
def main():
    df = None
    if CACHE_FILE.exists():
        try:
            df = pd.read_parquet(CACHE_FILE)
            _validate_df(df, "cache")
            log.info("Cache OK: %d rows", len(df))
        except Exception as e:
            log.warning("Cache invalid (%s) -> deleting and refetching", e)
            CACHE_FILE.unlink(missing_ok=True)
            df = None

    if df is None:
        universe = build_universe()
        df = fetch_fundamentals(universe)
        _validate_df(df, "fresh fetch")
        df.to_parquet(CACHE_FILE)
        log.info("Cached %d rows to %s", len(df), CACHE_FILE)

    ranked = score(df).head(TOP_N)
    ranked.to_csv(OUTPUT_FILE, index=False)
    log.info("Wrote %d rows to %s", len(ranked), OUTPUT_FILE)
    if not ranked.empty:
        print(ranked.head(20).to_string(index=False))
    else:
        print("No stocks passed the filters - try loosening config thresholds")


if __name__ == "__main__":
    main()