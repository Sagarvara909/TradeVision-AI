from fastapi import APIRouter, Depends, Query

from app.core.security import get_current_user
from app.domain.schemas import QuoteResponse, TimeSeriesResponse, CandleData
from app.services.market_service import get_quote, get_time_series

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