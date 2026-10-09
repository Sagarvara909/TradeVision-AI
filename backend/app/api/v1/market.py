from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.security import get_current_user
from app.domain.schemas import QuoteResponse, TimeSeriesResponse, CandleData
from app.services.market_service import get_quote, get_time_series, suggest_symbols
from app.services.technical_analysis_service import run_full_analysis
from app.domain.schemas import TechnicalAnalysisResponse
from app.services.risk_service import analyze_symbol, InsufficientDataError
from app.domain.schemas import RiskAnalysisResponse, SentimentResponse
from app.domain.schemas import SymbolSuggestion, SymbolSuggestionsResponse


router = APIRouter(prefix="/api/v1/market", tags=["market"])


@router.get("/quote/{symbol}", response_model=QuoteResponse)
def quote(symbol: str, current_user=Depends(get_current_user)):
    data = get_quote(symbol)
    return QuoteResponse(
        symbol=data["symbol"],
        name=data.get("name"),
        exchange=data.get("exchange"),
        price=float(data["close"]),
        change=float(data["change"]) if data.get("change") else None,
        percent_change=float(data["percent_change"]) if data.get("percent_change") else None,
        volume=int(float(data["volume"])) if data.get("volume") else None,
    )


@router.get("/candles/{symbol}", response_model=TimeSeriesResponse)
def candles(
    symbol: str,
    interval: str = Query(default="1day", description="1min, 5min, 15min, 1h, 1day, 1week"),
    output_size: int = Query(default=30, ge=1, le=200),
    current_user=Depends(get_current_user),
):
    data = get_time_series(symbol, interval=interval, output_size=output_size)
    candle_list = [
        CandleData(
            datetime=c["datetime"],
            open=float(c["open"]),
            high=float(c["high"]),
            low=float(c["low"]),
            close=float(c["close"]),
            volume=int(float(c["volume"])) if c.get("volume") else None,
        )
        for c in data.get("values", [])
    ]
    return TimeSeriesResponse(symbol=symbol, interval=interval, candles=candle_list)


@router.get("/analysis/{symbol}", response_model=TechnicalAnalysisResponse)
def analysis(
    symbol: str,
    interval: str = Query(default="1day"),
    exchange: str | None = Query(default=None, description="e.g. NSE, BSE, NASDAQ"),
    current_user=Depends(get_current_user),
):
    series = get_time_series(symbol, interval=interval, output_size=60, exchange=exchange)
    values = series.get("values", [])
    if not values:
        raise HTTPException(status_code=404, detail=f"No market data found for symbol '{symbol}'.")

    candles = [
        {
            "datetime": c["datetime"],
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": c["volume"],
        }
        for c in reversed(values)
    ]

    result = run_full_analysis(candles)
    vol = result["volume_analysis"]
    sr = result["support_resistance"]

    return TechnicalAnalysisResponse(
        symbol=symbol,
        ema20=result["ema20"],
        ema50=result["ema50"],
        rsi=result["rsi"],
        macd=result["macd"],
        macd_signal=result["macd_signal"],
        macd_histogram=result["macd_histogram"],
        trend=result["trend"],
        support=sr["support"],
        resistance=sr["resistance"],
        latest_volume=vol["latest_volume"],
        average_volume=vol["average_volume"],
        volume_ratio=vol["volume_ratio"],
        above_average_volume=vol["above_average"],
    )


@router.get("/risk/{symbol}", response_model=RiskAnalysisResponse)
def risk_analysis(
    symbol: str,
    interval: str = Query(default="1day"),
    exchange: str | None = Query(default=None, description="e.g. NSE, BSE, NASDAQ"),
    current_user=Depends(get_current_user),
):
    # analyze_symbol is the SAME function the /reports endpoint calls, so the
    # confidence score shown here always matches what gets saved and explained.
    try:
        result = analyze_symbol(symbol, interval=interval, exchange=exchange)
    except InsufficientDataError as e:
        # Previously this path could divide by zero on an empty candle list
        # (e.g. a wrong OCR symbol) and return a raw 500. Now it's a clean 404.
        raise HTTPException(status_code=404, detail=str(e))

    sentiment_dict = result.pop("sentiment")
    return RiskAnalysisResponse(
        **result,
        sentiment=SentimentResponse(**sentiment_dict),
    )


@router.get("/suggest/{symbol}", response_model=SymbolSuggestionsResponse)
def suggest(
    symbol: str,
    exchange: str | None = Query(default=None, description="e.g. NSE, BSE, NASDAQ"),
    current_user=Depends(get_current_user),
):
    """
    "Did you mean...?" for a symbol that returned no data. OCR on small chart
    fonts confuses look-alike characters (T/F, O/0, S/5), so this tries those
    swaps and returns only variants that really have market data. Suggestions
    only — the caller decides whether to accept one; nothing is rewritten here.
    """
    return SymbolSuggestionsResponse(
        suggestions=[SymbolSuggestion(**s) for s in suggest_symbols(symbol, exchange)]
    )