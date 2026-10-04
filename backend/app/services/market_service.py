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

# Twelve Data-style interval string -> yfinance interval string.
INTERVAL_MAP = {
    "1min": "1m", "5min": "5m", "15min": "15m", "30min": "30m",
    "1h": "60m", "1day": "1d", "1week": "1wk", "1month": "1mo",
}

# yfinance takes a lookback *period*, not a candle count; pick one generous
# enough that tail(output_size) always has enough rows for EMA50 etc.
PERIOD_MAP = {
    "1m": "7d", "5m": "60d", "15m": "60d", "30m": "60d",
    "60m": "730d", "1d": "2y", "1wk": "5y", "1mo": "10y",
}


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
    yf_interval = INTERVAL_MAP.get(interval, "1d")
    period = PERIOD_MAP.get(yf_interval, "2y")

    ticker = yf.Ticker(yf_symbol)
    df = ticker.history(period=period, interval=yf_interval)

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