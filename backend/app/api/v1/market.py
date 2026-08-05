from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.domain.schemas import QuoteResponse, TimeSeriesResponse, CandleData
from app.services.market_service import get_quote, get_time_series
from app.services.technical_analysis_service import run_full_analysis
from app.domain.schemas import TechnicalAnalysisResponse

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
    current_user=Depends(get_current_user),
):
    series = get_time_series(symbol, interval=interval, output_size=60)
    candles = [
        {
            "datetime": c["datetime"],
            "open": c["open"],
            "high": c["high"],
            "low": c["low"],
            "close": c["close"],
            "volume": c["volume"],
        }
        for c in reversed(series.get("values", []))
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