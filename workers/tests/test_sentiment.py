from __future__ import annotations
import pytest
from workers.sentiment.analyzer import SentimentAnalyzer

def test_sentiment_positive():
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze_text("We absolutely love this platform! The user experience is outstanding and fast 🚀")
    assert res.label == "positive"
    assert res.positive_score > res.negative_score
    assert res.compound_score >= 0.5

def test_sentiment_negative():
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze_text("Terrible service. It is completely broken, buggy, and crashes constantly 😡")
    assert res.label == "negative"
    assert res.negative_score > res.positive_score
    assert res.compound_score <= -0.5

def test_sentiment_neutral():
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze_text("The software package was updated to version 3.2 on Wednesday.")
    assert res.label == "neutral"
    assert -0.05 <= res.compound_score <= 0.05

def test_sentiment_negation_inversion():
    analyzer = SentimentAnalyzer()
    # 'great' is positive, but 'not great' should invert valence
    res_pos = analyzer.analyze_text("This feature is great.")
    res_neg = analyzer.analyze_text("This feature is not great at all.")
    assert res_pos.compound_score > 0
    assert res_neg.compound_score < res_pos.compound_score

def test_sentiment_boosters():
    analyzer = SentimentAnalyzer()
    res_normal = analyzer.analyze_text("The product is good.")
    res_boosted = analyzer.analyze_text("The product is extremely good.")
    assert res_boosted.compound_score > res_normal.compound_score

def test_sentiment_empty_input():
    analyzer = SentimentAnalyzer()
    res = analyzer.analyze_text("   ")
    assert res.label == "neutral"
    assert res.compound_score == 0.0
    assert res.neutral_score == 1.0

def test_extract_topics_and_perception():
    analyzer = SentimentAnalyzer()
    feed = [
        "The customer support was helpful and resolved my billing issue.",
        "Terrible customer support, waited 3 hours with no answer.",
        "The pricing plan is affordable and offers great value.",
        "I love the ease of use and clean interface."
    ]
    topics = analyzer.extract_topics_and_perception(feed, top_n=5)
    assert len(topics) > 0
    topic_names = [t.topic for t in topics]
    assert "customer support" in topic_names
    assert "pricing plan" in topic_names or "ease of use" in topic_names

def test_calculate_net_sentiment_score():
    analyzer = SentimentAnalyzer()
    # 8 positive, 2 negative out of 10 -> (8-2)/10 * 100 = 60.0
    assert analyzer.calculate_net_sentiment_score(8, 2, 10) == 60.0
    # 2 positive, 8 negative out of 10 -> -60.0
    assert analyzer.calculate_net_sentiment_score(2, 8, 10) == -60.0
    # 5 positive, 5 negative out of 10 -> 0.0
    assert analyzer.calculate_net_sentiment_score(5, 5, 10) == 0.0
    # 0 total -> 0.0
    assert analyzer.calculate_net_sentiment_score(0, 0, 0) == 0.0
