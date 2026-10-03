"""
Risk and Confidence Score engine.

Combines technical analysis output and news sentiment into a single
confidence score (0-100) with an accompanying risk level. This is the
project's core explainable-AI contribution — every input to the score
is traceable back to a concrete number, not a black-box model.

`analyze_symbol` is the single shared pipeline: market data -> technical
analysis -> sentiment -> confidence score. Both the /market/risk endpoint
and the report generator call this, so there is exactly one implementation
of the scoring logic instead of two copies that could drift apart.
"""

from app.services.market_service import get_time_series
from app.services.technical_analysis_service import run_full_analysis
from app.services.news_service import analyze_sentiment


class InsufficientDataError(Exception):
    """Raised when there isn't enough market data to analyze a symbol.

    Callers should turn this into an HTTP 404/422 with str(exc) as the detail,
    instead of letting a ZeroDivisionError or IndexError reach the client.
    """


def calculate_volatility_risk(candles_high_low_ranges: list[float], avg_price: float) -> float:
    """
    Simple volatility proxy: average daily high-low range as a percentage
    of average price. Higher = more volatile = higher risk.
    """
    if not candles_high_low_ranges or avg_price == 0:
        return 0.0
    avg_range = sum(candles_high_low_ranges) / len(candles_high_low_ranges)
    return round((avg_range / avg_price) * 100, 2)


def calculate_risk_level(volatility_pct: float, rsi: float) -> str:
    """
    Classify risk as low/medium/high based on volatility and RSI extremes.
    RSI > 70 (overbought) or < 30 (oversold) both increase risk of reversal.
    """
    risk_points = 0

    if volatility_pct > 3.0:
        risk_points += 2
    elif volatility_pct > 1.5:
        risk_points += 1

    if rsi > 70 or rsi < 30:
        risk_points += 2
    elif rsi > 65 or rsi < 35:
        risk_points += 1

    if risk_points >= 3:
        return "high"
    elif risk_points >= 1:
        return "medium"
    return "low"


def calculate_confidence_score(
    trend: str,
    rsi: float,
    macd_histogram: float,
    volume_ratio: float | None,
    sentiment_score: float,
    risk_level: str,
) -> dict:
    """
    Combine trend, momentum, volume, sentiment, and risk into a 0-100
    confidence score representing how well-aligned the signals are —
    NOT a prediction of future price movement.

    Scoring logic (each component is explainable in isolation):
      - Trend clarity: uptrend/downtrend = +15, sideways = 0
      - RSI in healthy range (40-60) = +10, extreme (>70 or <30) = -10
      - MACD histogram direction agrees with trend = +15
      - Volume above average = +10 (confirms conviction behind the move)
      - Sentiment alignment with trend = +20 (scaled by sentiment strength)
      - Risk level: low = +10, medium = 0, high = -15
    Base score starts at 40 (neutral), so a fully aligned bullish or
    bearish setup can reach ~90-100, and a fully misaligned one can fall
    toward 0-20.
    """
    score = 40.0
    reasons = []

    # Trend clarity
    if trend in ("uptrend", "downtrend"):
        score += 15
        reasons.append(f"Clear {trend} identified (+15)")
    else:
        reasons.append("No clear trend — sideways price action (+0)")

    # RSI health
    if 40 <= rsi <= 60:
        score += 10
        reasons.append(f"RSI ({rsi}) in healthy range (+10)")
    elif rsi > 70 or rsi < 30:
        score -= 10
        reasons.append(f"RSI ({rsi}) at extreme — possible reversal risk (-10)")

    # MACD agreement with trend
    if trend == "uptrend" and macd_histogram > 0:
        score += 15
        reasons.append("MACD histogram confirms upward momentum (+15)")
    elif trend == "downtrend" and macd_histogram < 0:
        score += 15
        reasons.append("MACD histogram confirms downward momentum (+15)")
    else:
        reasons.append("MACD does not confirm trend direction (+0)")

    # Volume confirmation
    if volume_ratio is not None and volume_ratio > 1.2:
        score += 10
        reasons.append(f"Volume {volume_ratio}x average — move has conviction (+10)")
    else:
        reasons.append("Volume not significantly above average (+0)")

    # Sentiment alignment
    sentiment_contribution = 0
    if trend == "uptrend" and sentiment_score > 0:
        sentiment_contribution = round(sentiment_score * 20, 1)
    elif trend == "downtrend" and sentiment_score < 0:
        sentiment_contribution = round(abs(sentiment_score) * 20, 1)
    elif trend == "uptrend" and sentiment_score < 0:
        sentiment_contribution = round(sentiment_score * 20, 1)  # negative
    elif trend == "downtrend" and sentiment_score > 0:
        sentiment_contribution = round(-sentiment_score * 20, 1)  # negative

    score += sentiment_contribution
    if sentiment_contribution != 0:
        direction = "supports" if sentiment_contribution > 0 else "contradicts"
        reasons.append(f"News sentiment {direction} the trend ({sentiment_contribution:+.1f})")

    # Risk adjustment
    risk_adjustment = {"low": 10, "medium": 0, "high": -15}[risk_level]
    score += risk_adjustment
    reasons.append(f"Risk level: {risk_level} ({risk_adjustment:+d})")

    final_score = max(0, min(100, round(score)))

    return {
        "confidence_score": final_score,
        "risk_level": risk_level,
        "reasoning": reasons,
    }


def analyze_symbol(symbol: str, interval: str = "1day", output_size: int = 60) -> dict:
    """
    Runs the full pipeline for one symbol: fetch candles -> technical
    analysis -> volatility/risk -> sentiment -> confidence score.

    Returns a flat dict matching RiskAnalysisResponse's fields (with
    "sentiment" as a nested dict), so callers can do:
        result = analyze_symbol("AAPL")
        sentiment_dict = result.pop("sentiment")
        RiskAnalysisResponse(**result, sentiment=SentimentResponse(**sentiment_dict))

    It is also exactly the dict shape llm_service.generate_report() expects,
    so a report can be generated directly from this output.

    Raises:
        InsufficientDataError: if the symbol has no or too little candle data
        (e.g. a bad OCR read, a delisted ticker, or an unsupported symbol).
        Callers should turn this into a 404, not let it crash as a 500.
    """
    series = get_time_series(symbol, interval=interval, output_size=output_size)
    values = series.get("values", [])
    if not values:
        raise InsufficientDataError(f"No market data found for symbol '{symbol}'.")

    candles = [
        {
            "datetime": c["datetime"], "open": c["open"], "high": c["high"],
            "low": c["low"], "close": c["close"], "volume": c["volume"],
        }
        for c in reversed(values)
    ]
    if len(candles) < 2:
        raise InsufficientDataError(
            f"Not enough historical data for '{symbol}' to run analysis."
        )

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

    vol = ta["volume_analysis"]
    sr = ta["support_resistance"]

    return {
        "symbol": symbol,
        "trend": ta["trend"],
        "rsi": ta["rsi"],
        "ema20": ta["ema20"],
        "ema50": ta["ema50"],
        "macd": ta["macd"],
        "macd_signal": ta["macd_signal"],
        "macd_histogram": ta["macd_histogram"],
        "support": sr["support"],
        "resistance": sr["resistance"],
        "latest_volume": vol["latest_volume"],
        "average_volume": vol["average_volume"],
        "volume_ratio": vol["volume_ratio"],
        "above_average_volume": vol["above_average"],
        "volatility_pct": volatility,
        "sentiment": {
            "label": sentiment["label"],
            "score": sentiment["sentiment_score"],
            "article_count": sentiment["article_count"],
            "headlines": sentiment["headlines"],
        },
        "confidence_score": confidence["confidence_score"],
        "risk_level": confidence["risk_level"],
        "reasoning": confidence["reasoning"],
    }