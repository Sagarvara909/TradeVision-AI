from app.services.market_service import get_quote, get_time_series

quote = get_quote("AAPL")
print("Quote:", quote)

series = get_time_series("AAPL", interval="1day", output_size=10)
print("\nTime series:")
for candle in series.get("values", []):
    print(f"  {candle['datetime']}: O={candle['open']} H={candle['high']} L={candle['low']} C={candle['close']}")