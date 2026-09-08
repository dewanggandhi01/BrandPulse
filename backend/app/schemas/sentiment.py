from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from uuid import UUID

class SentimentBase(BaseModel):
    label: str = Field(..., description="Sentiment classification: positive, negative, or neutral")
    positive_score: float = Field(..., ge=0.0, le=1.0)
    negative_score: float = Field(..., ge=0.0, le=1.0)
    neutral_score: float = Field(..., ge=0.0, le=1.0)
    compound_score: float | None = Field(default=None, ge=-1.0, le=1.0)
    model_version: str | None = "lexicon-vader-v1"

class SentimentRead(SentimentBase):
    id: UUID
    mention_id: UUID
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class MentionBase(BaseModel):
    source: str = Field(..., description="Platform or source: twitter, reddit, g2, trustpilot, news, blog, web")
    source_url: str | None = None
    content: str = Field(..., min_length=1, description="Raw text of the mention, tweet, review, or comment")
    author: str | None = None
    published_at: datetime | None = None

class MentionCreate(MentionBase):
    pass

class MentionBatchCreate(BaseModel):
    mentions: list[MentionCreate] = Field(..., min_length=1)

class MentionRead(MentionBase):
    id: UUID
    brand_id: UUID
    created_at: datetime | None = None
    sentiment: SentimentRead | None = None

    model_config = ConfigDict(from_attributes=True)

class MentionListResponse(BaseModel):
    items: list[MentionRead]
    total: int
    page: int
    size: int
    pages: int

class TopicStat(BaseModel):
    topic: str
    frequency: int
    sentiment_label: str
    average_compound: float

class SourceStat(BaseModel):
    source: str
    count: int
    positive: int
    negative: int
    neutral: int
    avg_compound: float

class ReputationAnalyticsResponse(BaseModel):
    brand_id: UUID
    total_mentions: int
    net_sentiment_score: float = Field(..., description="Net Sentiment Score (-100 to +100)")
    positive_count: int
    negative_count: int
    neutral_count: int
    positive_pct: float
    negative_pct: float
    neutral_pct: float
    sources_breakdown: list[SourceStat]
    top_topics: list[TopicStat]

class AnalyzeTextRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text string to evaluate for sentiment")

class AnalyzeTextResponse(BaseModel):
    text: str
    label: str
    positive_score: float
    negative_score: float
    neutral_score: float
    compound_score: float
    model_version: str
