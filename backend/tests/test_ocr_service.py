"""
Unit tests for OCR chart metadata parsing.

Test cases are built from real PaddleOCR output collected during manual
testing (see backend/test_ocr.py). This protects the parsing heuristic
from regressing as it gets tuned further.
"""
import pytest
from app.services.ocr_service import parse_chart_metadata


# --- Real OCR output from an Angel One / TradeOne screenshot showing IDEA on NSE ---
# --- Real OCR output from a NIFTY index chart (Angel One / TradeOne, 5m).
# This case specifically guards against over-applying the BLACKLIST: NIFTY is
# blacklisted for Tier 3 (because it appears as dashboard chrome on other
# charts), but here it is genuinely the chart's own symbol, found via the
# Tier 1 OHLC anchor. The blacklist must NOT filter it out at that tier. ---
NIFTY_INDEX_CHART_TEXT = [
    "Chart", "Overview", "Option Chain", "Stock Composition", "SCALPER MODE",
    "5m", "f Indicators", "88", " Instant Orders", "Save", "?", "Save", "+",
    " NIFTY: 5 : NSE",
    "O23433.00 H23439.60 L23422.00 C234$9.40 +6.85 (+0.03%)",
    "23600.00", "Volume97", "23580.00", "23560.00", "23540.00", "23520.00",
    "23500.00", "D", "23480.00", "T", "23460.00", "23440.00", "23420.00",
    "23398.10", "23380.00", "n", "23360.00", "23340.00", "6", "23320.00",
    "23290.84", "23280.00", "g", "23260.00", "NIFTY",
    "23,398.10 -79.70 (-0.34%)", "CAL", "ATM", "Lots", "23398.10",
    "BUY @ 23398.10", "SET SL/TGT", "23220.00", "23200.00", "2:00", "14:00",
    "10", "10:30", "10 Sep '26 11:55", "14:00", "11", "10:30", "14:00", "15",
    "1D 5D 1M 3M 6M 1Y 5Y", "11:48:16 (UTC+5:30)", "% log auto", "ENG",
    "File Explo", " Angel One - Tradeone -", "C Upload chart", "TradeVi",
    "vite.config.ts - Project S", "Containers - Docker De", "Windows PowerShell",
    "Screenshot 2026-08-27", "US",
]


def test_nifty_index_chart_not_blocked_by_blacklist():
    """
    Regression test: when NIFTY is the actual chart symbol (found via the
    Tier 1 OHLC anchor), it must be returned — the Tier 3 blacklist must not
    suppress it. Previously this returned 'CAL' (a truncated 'CALL' button).
    """
    result = parse_chart_metadata(NIFTY_INDEX_CHART_TEXT)
    assert result["symbol"] == "NIFTY"
    assert result["exchange"] == "NSE"
    assert result["timeframe"] == "5m"


def test_blacklist_still_applies_to_unanchored_fallback():
    """
    The complementary case: with no OHLC anchor and no exchange keyword
    present, NIFTY appearing as dashboard chrome must still be skipped by
    the Tier 3 blacklist.
    """
    chrome_only_text = [
        "NIFTY", "24,317.15 +66.95 (+0.28%)", "SENSEX", "Watchlist", "Save",
        "TATAPOWER", "375.95",
    ]
    result = parse_chart_metadata(chrome_only_text)
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