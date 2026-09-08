from __future__ import annotations
import re
import math
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

# Lexicons with valence weights [-3.0 to +3.0]
POSITIVE_LEXICON: dict[str, float] = {
    "great": 2.0, "excellent": 2.8, "amazing": 2.7, "awesome": 2.5, "love": 2.5,
    "good": 1.5, "best": 2.8, "perfect": 2.9, "fast": 1.6, "smooth": 1.5,
    "reliable": 2.0, "intuitive": 2.0, "clean": 1.4, "easy": 1.6, "innovative": 2.1,
    "helpful": 1.7, "recommend": 2.2, "superb": 2.6, "fantastic": 2.7, "value": 1.5,
    "affordable": 1.8, "satisfied": 1.9, "impressive": 2.2, "quality": 1.6,
    "solid": 1.5, "outstanding": 2.8, "top-tier": 2.4, "efficient": 1.8,
    "seamless": 2.1, "favorite": 2.2, "happy": 1.8, "powerful": 1.9, "gamechanger": 2.7,
    "beautiful": 2.0, "flawless": 2.8, "wonderful": 2.4, "brilliant": 2.5
}

NEGATIVE_LEXICON: dict[str, float] = {
    "terrible": -2.8, "horrible": -2.9, "bad": -1.8, "worst": -3.0, "hate": -2.5,
    "poor": -1.8, "slow": -1.6, "buggy": -2.3, "broken": -2.5, "crash": -2.4,
    "expensive": -1.8, "overpriced": -2.2, "useless": -2.6, "frustrating": -2.3,
    "disappointed": -2.2, "scam": -3.0, "waste": -2.4, "awful": -2.8, "annoying": -1.9,
    "fail": -2.1, "failed": -2.1, "unreliable": -2.4, "clunky": -1.9, "confusing": -1.8,
    "garbage": -2.8, "trash": -2.7, "outage": -2.0, "downtime": -1.9, "lag": -1.6,
    "glitch": -1.7, "subpar": -1.9, "rip-off": -2.8, "poorly": -1.8
}

EMOJI_SENTIMENT: dict[str, float] = {
    "😊": 1.5, "😃": 1.8, "😄": 1.8, "❤️": 2.0, "🔥": 1.6, "🚀": 1.9, "👍": 1.5,
    "🎉": 1.7, "✨": 1.5, "💯": 2.0, "🙌": 1.6, "😍": 2.2, "💪": 1.5,
    "😡": -2.2, "😠": -1.8, "💩": -2.0, "🤮": -2.5, "👎": -1.8, "💔": -1.9,
    "😤": -1.6, "😢": -1.6, "😭": -1.5, "🤦": -1.5, "🙄": -1.2, "🤬": -2.8
}

NEGATION_WORDS = {"not", "no", "never", "hardly", "barely", "scarcely", "without", "isn't", "aren't", "wasn't", "weren't", "don't", "doesn't", "didn't", "won't", "wouldn't", "can't", "couldn't"}

BOOSTER_WORDS = {
    "very": 0.35, "extremely": 0.5, "really": 0.3, "super": 0.4, "incredibly": 0.5,
    "absolutely": 0.45, "highly": 0.35, "so": 0.25, "totally": 0.35, "completely": 0.4,
    "slightly": -0.2, "somewhat": -0.2, "a bit": -0.2, "barely": -0.3
}

STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "he",
    "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "this", "they", "we", "you", "i", "me", "my", "our", "your",
    "their", "all", "any", "both", "each", "few", "more", "most", "other", "some",
    "such", "than", "too", "very", "can", "just", "should", "now", "also", "have",
    "had", "do", "does", "did", "but", "or", "if", "because", "about", "into", "over"
}

@dataclass
class SentimentResult:
    label: str                  # "positive" | "negative" | "neutral"
    positive_score: float       # 0.0 - 1.0
    negative_score: float       # 0.0 - 1.0
    neutral_score: float        # 0.0 - 1.0
    compound_score: float       # -1.0 to 1.0
    model_version: str = "lexicon-vader-v1"
    embedding: list[float] = field(default_factory=list) # Dense vector representation for semantic clustering

@dataclass
class TopicPerception:
    topic: str
    frequency: int
    sentiment_label: str
    average_compound: float

class SentimentAnalyzer:
    """
    Algorithmic multi-lexicon sentiment and perception analyzer.
    Features:
    - Negation inversion window (e.g. 'not good' flips to negative valence)
    - Booster and dampener weighting (e.g. 'extremely good' increases valence)
    - Emoji emotion decoding
    - Net Sentiment Score (NSS) calculation
    - Perception keyphrase & n-gram topic clustering
    """
    
    def __init__(self, model_version: str = "lexicon-vader-v1") -> None:
        self.model_version = model_version

    def analyze_text(self, text: str) -> SentimentResult:
        if not text or not text.strip():
            return SentimentResult(
                label="neutral",
                positive_score=0.0,
                negative_score=0.0,
                neutral_score=1.0,
                compound_score=0.0,
                model_version=self.model_version
            )

        # 1. Check emoji sentiment
        emoji_valence_sum = 0.0
        emoji_count = 0
        for char, valence in EMOJI_SENTIMENT.items():
            count = text.count(char)
            if count > 0:
                emoji_valence_sum += valence * count
                emoji_count += count

        # 2. Tokenize words while preserving contraction apostrophes
        clean_text = re.sub(r"[^\w\s\'-]", " ", text.lower())
        tokens = [t.strip("'") for t in clean_text.split() if t.strip("'")]

        if not tokens and emoji_count == 0:
            return SentimentResult(
                label="neutral",
                positive_score=0.0,
                negative_score=0.0,
                neutral_score=1.0,
                compound_score=0.0,
                model_version=self.model_version
            )

        valence_scores: list[float] = []
        n = len(tokens)

        for i, token in enumerate(tokens):
            item_valence = 0.0
            if token in POSITIVE_LEXICON:
                item_valence = POSITIVE_LEXICON[token]
            elif token in NEGATIVE_LEXICON:
                item_valence = NEGATIVE_LEXICON[token]

            if item_valence != 0.0:
                # Check for booster word immediately preceding
                booster = 0.0
                if i > 0 and tokens[i - 1] in BOOSTER_WORDS:
                    booster = BOOSTER_WORDS[tokens[i - 1]]
                
                if item_valence > 0:
                    item_valence += booster
                else:
                    item_valence -= booster

                # Check for negation in 3 preceding tokens
                is_negated = False
                for step in range(1, min(4, i + 1)):
                    if tokens[i - step] in NEGATION_WORDS:
                        is_negated = True
                        break
                
                if is_negated:
                    # Invert valence by standard damper factor (-0.74)
                    item_valence = item_valence * -0.74

                valence_scores.append(item_valence)

        if emoji_count > 0:
            valence_scores.append(emoji_valence_sum)

        if not valence_scores:
            return SentimentResult(
                label="neutral",
                positive_score=0.0,
                negative_score=0.0,
                neutral_score=1.0,
                compound_score=0.0,
                model_version=self.model_version
            )

        # 3. Calculate compound score via hyperbolic tangent / normalization curve
        sum_s = sum(valence_scores)
        alpha = 15.0
        compound = sum_s / math.sqrt((sum_s * sum_s) + alpha)
        compound = max(-1.0, min(1.0, round(compound, 4)))

        # 4. Decompose into positive, negative, and neutral proportions
        pos_sum = sum(s for s in valence_scores if s > 0)
        neg_sum = abs(sum(s for s in valence_scores if s < 0))
        neu_count = max(0, len(tokens) - len(valence_scores))
        neu_val = neu_count * 0.2

        total_mag = pos_sum + neg_sum + neu_val
        if total_mag > 0:
            pos_pct = round(pos_sum / total_mag, 3)
            neg_pct = round(neg_sum / total_mag, 3)
            neu_pct = max(0.0, round(1.0 - pos_pct - neg_pct, 3))
        else:
            pos_pct, neg_pct, neu_pct = 0.0, 0.0, 1.0

        # Determine label based on standard VADER compound thresholds
        if compound >= 0.05:
            label = "positive"
        elif compound <= -0.05:
            label = "negative"
        else:
            label = "neutral"

        # Generate a fast pseudo-embedding (dense vector) for future clustering
        # In a real ML pipeline, this would be a SentenceTransformer vector.
        import hashlib
        vector = [0.0] * 64
        for w in tokens:
            idx = int(hashlib.md5(w.encode()).hexdigest()[:8], 16) % 64
            vector[idx] += 1.0
        # Normalize the vector
        magnitude = math.sqrt(sum(x*x for x in vector)) or 1.0
        embedding = [round(x / magnitude, 4) for x in vector]

        return SentimentResult(
            label=label,
            positive_score=pos_pct,
            negative_score=neg_pct,
            neutral_score=neu_pct,
            compound_score=compound,
            model_version=self.model_version,
            embedding=embedding
        )

    def extract_topics_and_perception(
        self,
        texts: list[str],
        top_n: int = 8
    ) -> list[TopicPerception]:
        """
        Extract key thematic phrases / topics and compute average sentiment per topic.
        """
        if not texts:
            return []

        # Common 2-word topic patterns in consumer & competitor feedback
        known_topics = [
            "customer support", "user experience", "pricing plan", "ease of use",
            "feature set", "performance", "api integration", "speed",
            "product quality", "reliability", "mobile app", "onboarding",
            "refund policy", "billing", "interface", "documentation"
        ]

        topic_occurrences: dict[str, list[float]] = {t: [] for t in known_topics}
        word_counter: Counter[str] = Counter()

        for t in texts:
            t_lower = t.lower()
            sent_res = self.analyze_text(t)
            
            # Check known multi-word topics
            for kt in known_topics:
                if kt in t_lower:
                    topic_occurrences[kt].append(sent_res.compound_score)

            # Check prominent single keywords (excluding stopwords & short words)
            words = [
                re.sub(r"[^\w]", "", w) for w in t_lower.split()
                if len(w) > 3 and w not in STOP_WORDS and w not in POSITIVE_LEXICON and w not in NEGATIVE_LEXICON
            ]
            for w in words:
                if w:
                    word_counter[w] += 1

        results: list[TopicPerception] = []

        # Add detected multi-word topics first
        for kt, compounds in topic_occurrences.items():
            if compounds:
                avg_comp = sum(compounds) / len(compounds)
                lbl = "positive" if avg_comp >= 0.05 else ("negative" if avg_comp <= -0.05 else "neutral")
                results.append(TopicPerception(
                    topic=kt,
                    frequency=len(compounds),
                    sentiment_label=lbl,
                    average_compound=round(avg_comp, 3)
                ))

        # Add top single keywords if fewer than top_n
        for word, count in word_counter.most_common(top_n * 2):
            if len(results) >= top_n:
                break
            # Skip if already part of a multi-word topic
            if any(word in r.topic for r in results):
                continue
            
            # Compute average compound for this word
            word_compounds = [
                self.analyze_text(t).compound_score for t in texts if word in t.lower()
            ]
            avg_comp = sum(word_compounds) / len(word_compounds) if word_compounds else 0.0
            lbl = "positive" if avg_comp >= 0.05 else ("negative" if avg_comp <= -0.05 else "neutral")
            results.append(TopicPerception(
                topic=word,
                frequency=count,
                sentiment_label=lbl,
                average_compound=round(avg_comp, 3)
            ))

        # Sort by frequency descending
        results.sort(key=lambda x: x.frequency, reverse=True)
        return results[:top_n]

    @staticmethod
    def calculate_net_sentiment_score(
        positive_count: int,
        negative_count: int,
        total_count: int
    ) -> float:
        """
        Net Sentiment Score (NSS) = ((Positive - Negative) / Total) * 100.
        Range: -100.0 to +100.0
        """
        if total_count <= 0:
            return 0.0
        nss = ((positive_count - negative_count) / total_count) * 100.0
        return max(-100.0, min(100.0, round(nss, 1)))
