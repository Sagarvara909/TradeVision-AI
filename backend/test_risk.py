from app.services.market_service import get_time_series
from app.services.technical_analysis_service import run_full_analysis
from app.services.news_service import analyze_sentiment
from app.services.risk_service import calculate_volatility_risk, calculate_risk_level, calculate_confidence_score

symbol = "AAPL"

series = get_time_series(symbol, interval="1day", output_size=60)
candles = [
    {
        "datetime": c["datetime"], "open": c["open"], "high": c["high"],
        "low": c["low"], "close": c["close"], "volume": c["volume"],
    }
    for c in reversed(series["values"])
]

ta = run_full_analysis(candles)

ranges = [float(c["high"]) - float(c["low"]) for c in candles]
avg_price = sum(float(c["close"]) for c in candles) / len(candles)
volatility = calculate_volatility_risk(ranges, avg_price)
risk_level = calculate_risk_level(volatility, ta["rsi"])

sentiment = analyze_sentiment(symbol)

confidence = calculate_confidence_score(
    trend=ta["trend"],
    rsi=ta["rsi"],
    macd_histogram=ta["macd_histogram"],
    volume_ratio=ta["volume_analysis"]["volume_ratio"],
    sentiment_score=sentiment["sentiment_score"],
    risk_level=risk_level,
)

print(f"Symbol: {symbol}")
print(f"Trend: {ta['trend']}, RSI: {ta['rsi']}, Volatility: {volatility}%")
print(f"Sentiment: {sentiment['label']} ({sentiment['sentiment_score']})")
print(f"\nConfidence Score: {confidence['confidence_score']}/100")
print(f"Risk Level: {confidence['risk_level']}")
print("\nReasoning:")
for r in confidence["reasoning"]:
    print(f"  - {r}")