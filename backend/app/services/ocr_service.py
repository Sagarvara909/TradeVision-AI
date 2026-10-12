import re
import cv2
from paddleocr import PaddleOCR

_ocr_engine = None


def get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en")
    return _ocr_engine


def preprocess_image(image_path: str) -> str:
    """
    PaddleOCR performs best directly on original color screenshots.
    Global histogram equalization washes out text/badge anti-aliasing (e.g. clipping 'T' from TATAPOWER).
    """
    return image_path


def extract_text(image_path: str) -> list[str]:
    ocr = get_ocr_engine()
    result = ocr.ocr(image_path, cls=True)
    if not result or not result[0]:
        return []
    return [line[1][0] for line in result[0]]


# Common exchange prefixes/suffixes seen on chart screenshots (e.g. "NASDAQ:AAPL" or "IDEA NSE")
KNOWN_EXCHANGES = ["NASDAQ", "NYSE", "BINANCE", "NSE", "BSE", "FOREXCOM", "OANDA"]
TIMEFRAME_PATTERN = re.compile(r"\b(1m|3m|5m|15m|30m|1h|4h|1d|1w|1M)\b", re.IGNORECASE)
RANGE_BAR_PATTERN = re.compile(r"\b(1D|5D|1M|3M|6M|1Y|5Y)\b.*\b(1D|5D|1M|3M|6M|1Y|5Y)\b", re.IGNORECASE)
# OCR frequently misreads the "O" in "Open" as a digit "0" — match both
OHLC_PATTERN = re.compile(r"^[O0]\d+\.\d+\s*H\d+\.\d+\s*L\d+\.\d+", re.IGNORECASE)

# Dashboard chrome terms that can be mistaken for a ticker symbol.
BLACKLIST = {
    "NIFTY", "SENSEX", "BUY", "SELL", "SAVE", "WATCHLIST", "PORTFOLIO",
    "ORDERS", "POSITIONS", "TOOLS", "MARKETS", "CHART", "OVERVIEW",
    "SCALPER", "MODE", "INDICATORS", "SEARCH", "TRADEONE",
}


def _normalize_timeframe_token(token: str) -> str | None:
    t = token.strip()
    if not t:
        return None
    if t.isdigit():
        val = int(t)
        if val in (1, 2, 3, 5, 10, 15, 30, 45):
            return f"{val}m"
        if val == 60:
            return "1h"
        if val in (120, 240):
            return f"{val // 60}h"
        return f"{val}m"
    if t.lower() in ("d", "1d"):
        return "1d"
    if t.lower() in ("w", "1w"):
        return "1w"
    if t.lower() in ("m", "1m", "1mo"):
        return "1M"
    m = TIMEFRAME_PATTERN.fullmatch(t)
    if m:
        return m.group(1)
    return None


def parse_chart_metadata(texts: list[str]) -> dict:
    """
    Extract symbol, exchange, and timeframe from raw OCR text lines.

    Three-tier strategy, most reliable first:
      1. Anchor on the OHLC price line (most reliable, when present).
      2. Look for a line with a colon/dash near an exchange keyword — the
         primary chart label uses "SYMBOL # : EXCHANGE" or "SYMBOL · # · EXCHANGE".
      3. Bare all-caps word scan, excluding known dashboard chrome terms.
    """
    symbol = None
    exchange = None
    timeframe = None

    # Tier 1: OHLC anchor
    ohlc_index = None
    for i, text in enumerate(texts):
        if OHLC_PATTERN.search(text.strip()):
            ohlc_index = i
            break

    if ohlc_index is not None:
        search_start = max(0, ohlc_index - 4)
        for line in reversed(texts[search_start:ohlc_index]):
            cleaned = line.strip().upper()
            tokens = re.findall(r"[A-Z]+|\d+", cleaned)
            if any(t in KNOWN_EXCHANGES for t in tokens):
                for token in tokens:
                    if token in KNOWN_EXCHANGES:
                        exchange = token
                    elif token.isdigit() and not timeframe:
                        timeframe = _normalize_timeframe_token(token)
                    elif not symbol and 2 <= len(token) <= 10 and not token.isdigit():
                        symbol = token
                if symbol and exchange:
                    break

    # Tier 2: colon / dash / separator + exchange keyword, anywhere in the text
    if not symbol:
        for text in texts:
            cleaned = text.strip().upper()
            tokens = re.findall(r"[A-Z]+|\d+", cleaned)
            if any(t in KNOWN_EXCHANGES for t in tokens):
                for token in tokens:
                    if token in KNOWN_EXCHANGES:
                        exchange = token
                    elif token.isdigit() and not timeframe:
                        timeframe = _normalize_timeframe_token(token)
                    elif not symbol and 2 <= len(token) <= 10 and not token.isdigit():
                        symbol = token
                if symbol:
                    break

    # Tier 3: last-resort bare word scan, blacklist-aware
    if not symbol:
        for text in texts:
            cleaned = text.strip().upper()
            if re.fullmatch(r"[A-Z]{2,6}", cleaned) and cleaned not in BLACKLIST:
                symbol = cleaned
                break

    # Timeframe extraction if not already resolved from header
    if not timeframe:
        for text in texts:
            cleaned = text.strip()
            if RANGE_BAR_PATTERN.search(cleaned):
                continue
            stripped = cleaned[1:] if cleaned.startswith("C") else cleaned
            if TIMEFRAME_PATTERN.fullmatch(stripped):
                timeframe = TIMEFRAME_PATTERN.search(stripped).group(1)
                break

    if not timeframe:
        for text in texts:
            cleaned = text.strip()
            if RANGE_BAR_PATTERN.search(cleaned):
                continue
            match = TIMEFRAME_PATTERN.search(cleaned)
            if match:
                timeframe = match.group(1)
                break

    return {"symbol": symbol, "exchange": exchange, "timeframe": timeframe}