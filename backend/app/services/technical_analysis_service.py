import pandas as pd
import numpy as np


def calculate_ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def calculate_sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.
    RSI = 100 - (100 / (1 + RS)), where RS = avg gain / avg loss over the period.
    """
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)  # neutral RSI when undefined (e.g. no losses yet)


def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    MACD = EMA(fast) - EMA(slow)
    Signal line = EMA(MACD, signal period)
    Histogram = MACD - Signal
    """
    ema_fast = calculate_ema(series, fast)
    ema_slow = calculate_ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = calculate_ema(macd_line, signal)
    histogram = macd_line - signal_line
    return {
        "macd": macd_line,
        "signal": signal_line,
        "histogram": histogram,
    }


def detect_trend(ema20: pd.Series, ema50: pd.Series) -> str:
    """Simple trend classification from EMA relationship."""
    latest_ema20 = ema20.iloc[-1]
    latest_ema50 = ema50.iloc[-1]

    if latest_ema20 > latest_ema50 * 1.005:
        return "uptrend"
    elif latest_ema20 < latest_ema50 * 0.995:
        return "downtrend"
    return "sideways"


def find_support_resistance(df: pd.DataFrame, window: int = 5) -> dict:
    """
    Naive swing high/low detection: a local max/min over a rolling window.
    Returns the most recent significant support and resistance levels.
    """
    highs = df["high"]
    lows = df["low"]

    resistance = highs.rolling(window=window, center=True).max()
    support = lows.rolling(window=window, center=True).min()

    recent_resistance = highs[highs == resistance].dropna()
    recent_support = lows[lows == support].dropna()

    return {
        "resistance": float(recent_resistance.iloc[-1]) if not recent_resistance.empty else None,
        "support": float(recent_support.iloc[-1]) if not recent_support.empty else None,
    }


def analyze_volume(df: pd.DataFrame, period: int = 20) -> dict:
    """Compare latest volume against its rolling average."""
    avg_volume = df["volume"].rolling(window=period).mean().iloc[-1]
    latest_volume = df["volume"].iloc[-1]
    ratio = latest_volume / avg_volume if avg_volume else None

    return {
        "latest_volume": int(latest_volume),
        "average_volume": int(avg_volume) if not pd.isna(avg_volume) else None,
        "volume_ratio": round(ratio, 2) if ratio else None,
        "above_average": ratio > 1.2 if ratio else None,
    }


def run_full_analysis(candles: list[dict]) -> dict:
    """
    candles: list of dicts with keys datetime, open, high, low, close, volume
    (matches the CandleData shape from market_service), oldest first.
    """
    df = pd.DataFrame(candles)
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    ema20 = calculate_ema(df["close"], 20)
    ema50 = calculate_ema(df["close"], 50)
    rsi = calculate_rsi(df["close"])
    macd = calculate_macd(df["close"])

    return {
        "ema20": round(float(ema20.iloc[-1]), 2),
        "ema50": round(float(ema50.iloc[-1]), 2) if len(df) >= 50 else None,
        "rsi": round(float(rsi.iloc[-1]), 2),
        "macd": round(float(macd["macd"].iloc[-1]), 4),
        "macd_signal": round(float(macd["signal"].iloc[-1]), 4),
        "macd_histogram": round(float(macd["histogram"].iloc[-1]), 4),
        "trend": detect_trend(ema20, ema50) if len(df) >= 50 else "insufficient_data",
        "support_resistance": find_support_resistance(df),
        "volume_analysis": analyze_volume(df),
    }