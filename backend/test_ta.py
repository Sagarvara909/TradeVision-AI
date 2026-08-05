from app.services.market_service import get_time_series
from app.services.technical_analysis_service import run_full_analysis

series = get_time_series("AAPL", interval="1day", output_size=60)
candles = [
    {
        "datetime": c["datetime"],
        "open": c["open"],
        "high": c["high"],
        "low": c["low"],
        "close": c["close"],
        "volume": c["volume"],
    }
    for c in reversed(series["values"])  # Twelve Data returns newest-first; we need oldest-first
]

result = run_full_analysis(candles)
print(result)