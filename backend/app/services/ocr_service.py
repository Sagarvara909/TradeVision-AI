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
    """Basic preprocessing: grayscale + contrast boost, saved as a temp file."""
    img = cv2.imread(image_path)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    enhanced = cv2.equalizeHist(gray)
    processed_path = image_path.replace(".", "_processed.")
    cv2.imwrite(processed_path, enhanced)
    return processed_path


def extract_text(image_path: str) -> list[str]:
    ocr = get_ocr_engine()
    result = ocr.ocr(image_path, cls=True)
    if not result or not result[0]:
        return []
    return [line[1][0] for line in result[0]]


# Common exchange prefixes/suffixes seen on chart screenshots (e.g. "NASDAQ:AAPL" or "IDEA NSE")
KNOWN_EXCHANGES = ["NASDAQ", "NYSE", "BINANCE", "NSE", "BSE", "FOREXCOM", "OANDA"]
TIMEFRAME_PATTERN = re.compile(r"\b(1m|3m|5m|15m|30m|1h|4h|1d|1w|1M)\b", re.IGNORECASE)
# OCR frequently misreads the "O" in "Open" as a digit "0" — match both
OHLC_PATTERN = re.compile(r"^[O0]\d+\.\d+\s*H\d+\.\d+\s*L\d+\.\d+", re.IGNORECASE)

BLACKLIST = {
    "NIFTY", "SENSEX", "BUY", "SELL", "SAVE", "WATCHLIST", "PORTFOLIO",
    "ORDERS", "POSITIONS", "TOOLS", "MARKETS", "CHART", "OVERVIEW",
    "SCALPER", "MODE", "INDICATORS", "SEARCH", "TRADEONE",
}


def parse_chart_metadata(texts: list[str]) -> dict:
    """
    Extract symbol, exchange, and timeframe from raw OCR text lines.

    Three-tier strategy, most reliable first:
      1. Anchor on the OHLC price line (most reliable, when present).
      2. Look for a line with a colon near an exchange keyword — the
         primary chart label uses "SYMBOL # : EXCHANGE", while sidebar
         watchlist rows never contain a colon.
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
            tokens = re.findall(r"[A-Z]+", cleaned)
            if any(t in KNOWN_EXCHANGES for t in tokens):
                for token in tokens:
                    if token in KNOWN_EXCHANGES:
                        exchange = token
                    elif not symbol and token not in BLACKLIST and 2 <= len(token) <= 10:
                        symbol = token
                break

    # Tier 2: colon + exchange keyword, anywhere in the text
    if not symbol:
        for text in texts:
            cleaned = text.strip().upper()
            if ":" not in cleaned:
                continue
            tokens = re.findall(r"[A-Z]+", cleaned)
            if any(t in KNOWN_EXCHANGES for t in tokens):
                for token in tokens:
                    if token in KNOWN_EXCHANGES:
                        exchange = token
                    elif not symbol and token not in BLACKLIST and 2 <= len(token) <= 10:
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

    for text in texts:
        cleaned = text.strip()
        stripped = cleaned[1:] if cleaned.startswith("C") else cleaned
        if TIMEFRAME_PATTERN.fullmatch(stripped):
            timeframe = TIMEFRAME_PATTERN.search(stripped).group(1)
            break

    if not timeframe:
        for text in texts:
            match = TIMEFRAME_PATTERN.search(text)
            if match:
                timeframe = match.group(1)
                break

    return {"symbol": symbol, "exchange": exchange, "timeframe": timeframe}