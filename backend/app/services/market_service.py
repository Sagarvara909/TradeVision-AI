"""
Market data service — Yahoo Finance via `yfinance`.

Switched from Twelve Data because its free tier does not serve NSE/BSE
(Indian exchange) symbols or most indices, which this project's charts are
mostly about. yfinance is free and covers NSE, BSE, NASDAQ, NYSE, and most
global exchanges, keyed through ticker suffixes (see _resolve_symbol).

Public functions keep the ORIGINAL (Twelve Data-shaped) return contract —
a dict with a "values" list, NEWEST candle first, every OHLCV field as a
string — so technical_analysis_service.py and risk_service.py did not need
to change at all.
"""

from concurrent.futures import ThreadPoolExecutor

import yfinance as yf
from fastapi import HTTPException

# Known Indian indices don't trade as plain tickers; Yahoo Finance uses a
# dedicated symbol for each instead of a NSE/BSE-suffixed ticker.
INDEX_SYMBOL_MAP = {
    "NIFTY": "^NSEI",
    "NIFTY50": "^NSEI",
    "NIFTY 50": "^NSEI",
    "BANKNIFTY": "^NSEBANK",
    "NIFTYBANK": "^NSEBANK",
    "SENSEX": "^BSESN",
}

# Twelve Data-style / OCR timeframe string -> (yfinance interval string, lookback period).
INTERVAL_LOOKUP = {
    "1m": ("1m", "7d"),
    "1min": ("1m", "7d"),
    "2m": ("2m", "60d"),
    "3m": ("5m", "60d"),
    "5m": ("5m", "60d"),
    "5min": ("5m", "60d"),
    "15m": ("15m", "60d"),
    "15min": ("15m", "60d"),
    "30m": ("30m", "60d"),
    "30min": ("30m", "60d"),
    "1h": ("60m", "730d"),
    "60m": ("60m", "730d"),
    "60min": ("60m", "730d"),
    "4h": ("60m", "730d"),
    "1d": ("1d", "2y"),
    "d": ("1d", "2y"),
    "1day": ("1d", "2y"),
    "daily": ("1d", "2y"),
    "1w": ("1wk", "5y"),
    "w": ("1wk", "5y"),
    "1wk": ("1wk", "5y"),
    "1week": ("1wk", "5y"),
    "weekly": ("1wk", "5y"),
    "1mo": ("1mo", "10y"),
    "1month": ("1mo", "10y"),
    "monthly": ("1mo", "10y"),
}


def normalize_interval(interval: str | None) -> tuple[str, str]:
    """Resolve any OCR / user timeframe string into valid (yf_interval, period)."""
    if not interval:
        return "1d", "2y"
    clean = interval.strip()
    if clean in ("1M", "M", "1mo", "1month", "month"):
        return "1mo", "10y"
    return INTERVAL_LOOKUP.get(clean.lower(), ("1d", "2y"))



def _resolve_symbol(symbol: str, exchange: str | None = None) -> str:
    """Map a plain ticker + exchange (as OCR/the user gives them) to the
    actual Yahoo Finance symbol. Indices come first since they ignore
    exchange suffixing entirely."""
    upper = symbol.upper().strip()
    if upper in INDEX_SYMBOL_MAP:
        return INDEX_SYMBOL_MAP[upper]

    exch = (exchange or "").upper().strip()
    if exch == "NSE":
        return f"{upper}.NS"
    if exch == "BSE":
        return f"{upper}.BO"
    # US tickers (NASDAQ/NYSE/none given) and already-suffixed symbols pass through.
    return upper


def get_quote(symbol: str, exchange: str | None = None) -> dict:
    """Fetch the latest quote for a symbol."""
    yf_symbol = _resolve_symbol(symbol, exchange)
    ticker = yf.Ticker(yf_symbol)

    try:
        info = ticker.fast_info
        price = float(info["last_price"])
    except Exception:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch quote for '{symbol}' (tried '{yf_symbol}'). "
            f"Check the symbol and exchange.",
        )

    prev_close = None
    try:
        prev_close = float(info["previous_close"])
    except Exception:
        pass

    change = (price - prev_close) if prev_close else None
    percent_change = (change / prev_close * 100) if (change is not None and prev_close) else None

    volume = None
    try:
        volume = int(info["last_volume"])
    except Exception:
        pass

    return {
        "symbol": symbol,
        "name": yf_symbol,
        "exchange": exchange,
        "close": str(price),
        "change": str(change) if change is not None else None,
        "percent_change": str(percent_change) if percent_change is not None else None,
        "volume": str(volume) if volume is not None else None,
    }


def get_time_series(
    symbol: str,
    interval: str = "1day",
    output_size: int = 30,
    exchange: str | None = None,
) -> dict:
    """
    Fetch historical OHLCV candles for a symbol.

    Returns {"values": [...]} with the NEWEST candle first and every field
    as a string — matching the original Twelve Data contract exactly, so
    callers' `float(c["close"])` etc. keep working unchanged.
    """
    yf_symbol = _resolve_symbol(symbol, exchange)
    yf_interval, period = normalize_interval(interval)

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period, interval=yf_interval)

    # If intraday data is empty (e.g., market closed/no intraday), gracefully fall back to daily
    if df.empty and yf_interval != "1d":
        df = ticker.history(period="2y", interval="1d")

    if df.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No market data found for '{symbol}' (tried '{yf_symbol}'). "
            f"Check the symbol and exchange — Yahoo Finance may not list this ticker.",
        )

    df = df.tail(output_size)

    values = []
    for ts, row in df.iloc[::-1].iterrows():  # newest first, matches old contract
        volume = row["Volume"]
        values.append(
            {
                "datetime": ts.strftime("%Y-%m-%d %H:%M:%S") if hasattr(ts, "strftime") else str(ts),
                "open": str(round(float(row["Open"]), 4)),
                "high": str(round(float(row["High"]), 4)),
                "low": str(round(float(row["Low"]), 4)),
                "close": str(round(float(row["Close"]), 4)),
                "volume": str(int(volume)) if volume == volume else "0",  # NaN check
            }
        )

    return {"values": values}


# ---------------------------------------------------------------------------
# "Did you mean...?" suggestions
#
# OCR on small chart-title fonts confuses look-alike characters (T/F, O/0,
# S/5 ...). When a symbol returns no data, we try single-character swaps of
# those look-alikes and report which variants really exist on Yahoo Finance.
# These are only ever SUGGESTIONS for the person to accept — a symbol is never
# silently rewritten, because analysing the wrong stock without telling anyone
# would be worse than showing an error.
# ---------------------------------------------------------------------------

import difflib

OCR_CONFUSABLES = {
    "F": "TEP", "T": "FIL", "E": "FP", "P": "FR", "R": "P",
    "I": "L1T", "L": "I1", "1": "IL",
    "O": "0QD", "0": "OQD", "Q": "O0", "D": "O0",
    "S": "5", "5": "S", "B": "8", "8": "B",
    "G": "6C", "6": "G", "C": "GO",
    "U": "V", "V": "UY", "Y": "V", "M": "N", "N": "M", "Z": "2", "2": "Z",
}

POPULAR_SYMBOLS = [
    # Prominent Indian tickers (NSE/BSE)
    "TATAPOWER", "TATASTEEL", "TATAMOTORS", "TCS", "INFY", "RELIANCE",
    "HDFCBANK", "ICICIBANK", "SBIN", "BHARTIARTL", "ITC", "KOTAKBANK",
    "LT", "AXISBANK", "HINDUNILVR", "BAJFINANCE", "MARUTI", "ASIANPAINT",
    "SUNPHARMA", "TITAN", "ULTRACEMCO", "WIPRO", "POWERGRID", "NTPC",
    "COALINDIA", "ONGC", "JSWSTEEL", "ADANIENT", "ADANIPORTS", "ADANIPOWER",
    "NHPC", "IDFCFIRSTB", "ZOMATO", "PAYTM", "JIOFIN", "VEDL", "IRCTC",
    "BEL", "HAL", "BHEL", "IOC", "BPCL", "GAIL", "SAIL", "PFC", "REC",
    # Prominent US tickers
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "NFLX", "AMD", "INTC",
]

MAX_SUGGEST_CANDIDATES = 16  # each candidate is a network lookup, so keep it bounded
MAX_SUGGESTIONS = 3


def _confusable_variants(symbol: str) -> list[str]:
    """Look-alike, fuzzy, and missing-boundary variants of `symbol`."""
    s = symbol.upper().strip()
    seen = {s}
    variants: list[str] = []

    # 1. Fuzzy match against popular stocks first (e.g. ATAPOWER -> TATAPOWER)
    fuzzy_matches = difflib.get_close_matches(s, POPULAR_SYMBOLS, n=4, cutoff=0.55)
    for fm in fuzzy_matches:
        if fm not in seen:
            seen.add(fm)
            variants.append(fm)

    # 2. Check single-character missing prefix/suffix (e.g. clipped 'T' -> TATAPOWER, or duplicate trailing char)
    for ch in "TSRNPB":
        candidate = ch + s
        if candidate not in seen:
            seen.add(candidate)
            variants.append(candidate)
    if len(s) > 3 and s[-1] == s[-2]:  # e.g. TATAPOWERR -> TATAPOWER
        cand = s[:-1]
        if cand not in seen:
            seen.add(cand)
            variants.append(cand)

    # 3. Single-character look-alike swaps
    for i, ch in enumerate(s):
        for alt in OCR_CONFUSABLES.get(ch, ""):
            candidate = s[:i] + alt + s[i + 1:]
            if candidate not in seen:
                seen.add(candidate)
                variants.append(candidate)
            if len(variants) >= MAX_SUGGEST_CANDIDATES:
                break
        if len(variants) >= MAX_SUGGEST_CANDIDATES:
            break

    return variants[:MAX_SUGGEST_CANDIDATES]


def _last_close_if_listed(symbol: str, exchange: str | None) -> float | None:
    """Last daily close if Yahoo has data for this ticker, else None."""
    try:
        df = yf.Ticker(_resolve_symbol(symbol, exchange)).history(period="5d", interval="1d")
        if df.empty:
            return None
        return round(float(df["Close"].iloc[-1]), 2)
    except Exception:
        return None


def suggest_symbols(symbol: str, exchange: str | None = None) -> list[dict]:
    """
    Look-alike variants of `symbol` that actually have market data, each with
    its last close so the person can sanity-check it against their chart.
    Returns [{"symbol": "TCS", "last_close": 2075.25}, ...], at most
    MAX_SUGGESTIONS, in the order the variants were generated.
    """
    candidates = _confusable_variants(symbol)
    if not candidates:
        return []
    with ThreadPoolExecutor(max_workers=6) as pool:
        closes = list(pool.map(lambda c: _last_close_if_listed(c, exchange), candidates))
    found = [
        {"symbol": c, "last_close": price}
        for c, price in zip(candidates, closes)
        if price is not None
    ]
    return found[:MAX_SUGGESTIONS]