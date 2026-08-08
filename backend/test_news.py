from app.services.news_service import analyze_sentiment

result = analyze_sentiment("AAPL")
print(f"Sentiment: {result['label']} ({result['sentiment_score']})")
print(f"Based on {result['article_count']} articles\n")
for h in result["headlines"]:
    print(f"  - {h['headline']}")