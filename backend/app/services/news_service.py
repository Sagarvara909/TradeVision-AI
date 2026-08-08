from datetime import datetime, timedelta
import requests

from app.core.config import settings

BASE_URL = "https://finnhub.io/api/v1"

POSITIVE_WORDS = {
    "surge", "soar", "jump", "gain", "rise", "rally", "beat", "outperform",
    "upgrade", "strong", "growth", "profit", "record", "boost", "bullish",
    "exceed", "positive", "recover", "climb", "high",
}
NEGATIVE_WORDS = {
    "fall", "drop", "plunge", "decline", "loss", "miss", "downgrade", "weak",
    "cut", "concern", "risk", "bearish", "sell-off", "selloff", "warn",
    "negative", "slump", "crash", "low", "lawsuit", "investigation",
}


def get_company_news(symbol: str, days_back: int = 7) -> list[dict]:
    """Fetch recent company news headlines."""
    today = datetime.utcnow().date()
    from_date = today - timedelta(days=days_back)

    response = requests.get(
        f"{BASE_URL}/company-news",
        params={
            "symbol": symbol,
            "from": from_date.isoformat(),
            "to": today.isoformat(),
            "token": settings.finnhub_api_key,
        },
        timeout=10,
    )
    data = response.json()

    if not isinstance(data, list):
        return []

    return data[:20]  # cap to most recent 20 articles


def score_headline(text: str) -> int:
    """
    Simple keyword-based sentiment score for one piece of text.
    Returns: positive count - negative count (can be negative, zero, or positive).
    """
    words = set(text.lower().split())
    positive_hits = sum(1 for w in POSITIVE_WORDS if w in text.lower())
    negative_hits = sum(1 for w in NEGATIVE_WORDS if w in text.lower())
    return positive_hits - negative_hits


def analyze_sentiment(symbol: str) -> dict:
    """
    Aggregate sentiment across recent news for a symbol.
    Returns a normalized score from -1 (very negative) to +1 (very positive),
    plus the raw article count and a human-readable label.
    """
    articles = get_company_news(symbol)

    if not articles:
        return {
            "sentiment_score": 0.0,
            "label": "no_data",
            "article_count": 0,
            "headlines": [],
        }

    scores = []
    headlines = []
    for article in articles:
        headline = article.get("headline", "")
        summary = article.get("summary", "")
        combined_text = f"{headline} {summary}"
        scores.append(score_headline(combined_text))
        headlines.append({
            "headline": headline,
            "source": article.get("source"),
            "url": article.get("url"),
            "datetime": article.get("datetime"),
        })

    raw_avg = sum(scores) / len(scores)
    # Normalize to roughly -1..1 range (clip extreme values)
    normalized = max(-1.0, min(1.0, raw_avg / 3))

    if normalized > 0.15:
        label = "positive"
    elif normalized < -0.15:
        label = "negative"
    else:
        label = "neutral"

    return {
        "sentiment_score": round(normalized, 3),
        "label": label,
        "article_count": len(articles),
        "headlines": headlines[:5],  # top 5 for display
    }