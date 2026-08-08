"""
Risk and Confidence Score engine.

Combines technical analysis output and news sentiment into a single
confidence score (0-100) with an accompanying risk level. This is the
project's core explainable-AI contribution — every input to the score
is traceable back to a concrete number, not a black-box model.
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