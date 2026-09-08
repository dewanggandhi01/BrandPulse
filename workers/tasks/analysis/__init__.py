from __future__ import annotations
from workers.celery_app import app
import structlog
from .sentiment_analyzer import analyze_brand_mentions
from .report_generator import generate_brand_report

logger = structlog.get_logger()

@app.task(name="workers.tasks.analysis.placeholder_analyze")
def placeholder_analyze(data: dict):
    logger.info("Analyzing placeholder data")
    return {"status": "analyzed"}

__all__ = ["analyze_brand_mentions", "generate_brand_report", "placeholder_analyze"]
