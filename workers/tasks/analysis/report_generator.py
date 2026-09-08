from __future__ import annotations
import uuid
import structlog
from datetime import datetime, timezone
from workers.celery_app import app
from workers.reports.generator import ExecutiveReportGenerator

logger = structlog.get_logger()

@app.task(name="workers.tasks.analysis.generate_brand_report", bind=True)
def generate_brand_report(
    self,
    brand_id: str,
    brand_name: str,
    brand_domain: str,
    intelligence_bundle: dict
) -> dict:
    """
    Celery task to compile and synthesize a comprehensive multi-source executive report.
    """
    log = logger.bind(brand_id=brand_id, brand_name=brand_name, task_id=self.request.id)
    log.info("Generating executive intelligence report")

    generator = ExecutiveReportGenerator()
    brief = generator.generate_brief(
        brand_name=brand_name,
        brand_domain=brand_domain,
        seo_data=intelligence_bundle.get("seo"),
        product_data=intelligence_bundle.get("products"),
        change_data=intelligence_bundle.get("changes"),
        sentiment_data=intelligence_bundle.get("sentiment"),
        ad_data=intelligence_bundle.get("ads")
    )

    log.info(
        "Executive report compiled successfully",
        health_score=brief.health_score,
        risk_level=brief.risk_level,
        swot_count=len(brief.swot)
    )

    return {
        "brand_id": brand_id,
        "brand_name": brand_name,
        "brand_domain": brand_domain,
        "health_score": brief.health_score,
        "risk_level": brief.risk_level,
        "pillar_scores": brief.pillar_scores,
        "kpi_highlights": brief.kpi_highlights,
        "swot": brief.swot,
        "recommendations": brief.recommendations,
        "ai_narrative": brief.ai_narrative,
        "generated_at": datetime.now(timezone.utc).isoformat()
    }
