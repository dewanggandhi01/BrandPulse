from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone
from workers.celery_app import app
from workers.sentiment.analyzer import SentimentAnalyzer

logger = structlog.get_logger()

@app.task(name="workers.tasks.analysis.analyze_brand_mentions", bind=True)
def analyze_brand_mentions(self, brand_id: str, mentions_data: list[dict]) -> dict:
    """
    Celery task to run sentiment analysis and perception theme extraction
    on ingested brand mentions.
    """
    log = logger.bind(brand_id=brand_id, mentions_count=len(mentions_data), task_id=self.request.id)
    log.info("Starting brand mentions sentiment analysis")

    analyzer = SentimentAnalyzer()
    processed_mentions = []
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    all_texts = []

    for item in mentions_data:
        text = item.get("content", "")
        all_texts.append(text)
        
        sent = analyzer.analyze_text(text)
        if sent.label == "positive":
            positive_count += 1
        elif sent.label == "negative":
            negative_count += 1
        else:
            neutral_count += 1

        processed_mentions.append({
            "source": item.get("source", "web"),
            "source_url": item.get("source_url"),
            "author": item.get("author"),
            "content": text,
            "published_at": item.get("published_at"),
            "sentiment": {
                "label": sent.label,
                "positive_score": sent.positive_score,
                "negative_score": sent.negative_score,
                "neutral_score": sent.neutral_score,
                "compound_score": sent.compound_score,
                "model_version": sent.model_version
            }
        })

    # Extract perception themes / topics
    topics_data = analyzer.extract_topics_and_perception(all_texts, top_n=8)
    topics = [
        {
            "topic": t.topic,
            "frequency": t.frequency,
            "sentiment_label": t.sentiment_label,
            "average_compound": t.average_compound
        }
        for t in topics_data
    ]

    total = len(mentions_data)
    nss = analyzer.calculate_net_sentiment_score(positive_count, negative_count, total)

    log.info(
        "Sentiment analysis completed",
        total=total,
        nss=nss,
        positive=positive_count,
        negative=negative_count,
        neutral=neutral_count
    )

    return {
        "brand_id": brand_id,
        "total_processed": total,
        "positive_count": positive_count,
        "negative_count": negative_count,
        "neutral_count": neutral_count,
        "net_sentiment_score": nss,
        "topics": topics,
        "mentions": processed_mentions
    }
