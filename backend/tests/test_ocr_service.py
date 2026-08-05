"""
Unit tests for OCR chart metadata parsing.

Test cases are built from real PaddleOCR output collected during manual
testing (see backend/test_ocr.py). This protects the parsing heuristic
from regressing as it gets tuned further.
"""
import pytest
from app.services.ocr_service import parse_chart_metadata


# --- Real OCR output from an Angel One / TradeOne screenshot showing IDEA on NSE ---
IDEA_FULL_CROP_TEXT = [
    "Angel One - Tradeone: IDEA.", ". angelone.in/t", "NIFTY", "0", "0",
    " Markets", "TradeOne", " Portfolio", "Orders", "Positions", "Tools ", "4",
    "24,317.15  +66.95 (+0.28%)", "77,928.15  +273.55 (+0.35%)", "Watchlist", "3",
    "x", " Chart", "Overview", " Option Chain", " SCALPER MODE ", "mywatchlist",
    "+", "C5m", "f Indicators", "8", "0", "Save", "Instant Orders O", "Save",
    "IDEA 5 : NSE", "013.03 H13.04 L13.02 13.03 0.00 (0.00%)", "Q Search",
    "13.22", " Positions", "BUY @ 12.87", "SElL @ 12.87", "13.20", "0",
    "IDEA NSE 3", "Voturme 1.056M", "13.18", "Orders", "246.95 V", "13.16",
    "JIOFIN NSE", "2.53 (-1.01%)", "13.14", "Methet", "47.40 V", "SUZLON NSE",
    "13.12", "-0.05 (-0.11%)", "D", "13.10", "186.92 v", "Ooption",
    "-0.35 (-0.19%)", "13.08", "28E0", "344.85 ", "NTPC NSE ", "+1.35 (+0.39%)",
    "13.04", "88.92 V", "IRFC NSE", "13.02", "-0.21 (-0.24%)", "Q", "13.00",
    "22.54 V", "YESBANK NSE", "-0.30 (-1.31%)", "12.98", "334.20 ", "12.96",
    "TMPV NSE 4", "+4.40 (+1.33%)", "12.94", "6", "78.07 ", " NHPC NSE", "o",
    "12.92", "+0.17 (+0.22%)", "12.90", "241.59 ", "ONGC NSE ", "+3.28 (+1.38%)",
    "0", ".88", "375.95 V", "TATAPOWER NSE", "12.86", "-1.30 (-0.34%)", "12.84",
    "119.88 V", "IREDA NSE", "0.94 (-0.78%)", "12.82", "12:00", "14:00", "29",
    "10:30", "14:00", "30", "10:30", "12:00", "14:00", "1D 5D 1M 3M 6M 1Y 5Y",
    "22:11:46 (UTC+5:30) |% log auto",
]


def test_idea_full_crop_extracts_correctly():
    """Real regression test: full crop including OHLC line, symbol label with colon."""
    result = parse_chart_metadata(IDEA_FULL_CROP_TEXT)
    assert result["symbol"] == "IDEA"
    assert result["exchange"] == "NSE"
    assert result["timeframe"] == "5m"


# --- Representative reconstruction of a cropped screenshot missing the OHLC
# anchor, where NIFTY (dashboard chrome) could be mistaken for the symbol.
# NOTE: replace with real captured OCR text for a strict regression test. ---
CROPPED_NO_OHLC_TEXT = [
    "NIFTY", "24,317.15  +66.95 (+0.28%)", "SENSEX", "77,928.15  +273.55 (+0.35%)",
    "Watchlist", "mywatchlist", "C5m", "Indicators", "Save",
    "IDEA NSE 3", "Voturme 1.056M", "JIOFIN NSE", "246.95 V",
]


def test_cropped_screenshot_ignores_dashboard_chrome():
    """
    Without an OHLC anchor, the parser must not fall back to picking up
    dashboard chrome (NIFTY/SENSEX) as the symbol — it should skip
    blacklisted terms and prefer a real ticker even via the weaker
    fallback tiers.
    """
    result = parse_chart_metadata(CROPPED_NO_OHLC_TEXT)
    assert result["symbol"] != "NIFTY"
    assert result["symbol"] != "SENSEX"


# --- Representative reconstruction of the TATASTEEL screenshot ---
TATASTEEL_TEXT = [
    "Chart", "Overview", "Option Chain", "SCALPER MODE", "5m", "Indicators",
    "Instant Orders", "Save",
    "TATASTEEL . 5 . NSE", "O190.03 H190.79 L189.54 C189.99 -0.01 (-0.01%)",
    "BUY @ 189.69", "SELL @ 189.69", "Volume 1.337M",
    "1D 5D 1M 3M 6M 1Y 5Y", "11:45:04 (UTC+5:30)",
]


def test_tatasteel_extracts_correctly():
    """
    NOTE: reconstructed from the visible chart label, not exact raw OCR
    output — replace with real captured text for full fidelity.
    """
    result = parse_chart_metadata(TATASTEEL_TEXT)
    assert result["symbol"] == "TATASTEEL"
    assert result["exchange"] == "NSE"
    assert result["timeframe"] == "5m"


def test_empty_input_returns_all_none():
    """Edge case: no text detected at all should not crash, just return nulls."""
    result = parse_chart_metadata([])
    assert result == {"symbol": None, "exchange": None, "timeframe": None}