from __future__ import annotations
import uuid
import structlog
from datetime import datetime, date, timezone
from workers.celery_app import app
from workers.ads.parser import AdCreativeParser
from workers.ads.estimator import AdSpendEstimator

logger = structlog.get_logger()

@app.task(name="workers.tasks.scraping.ingest_brand_ads", bind=True)
def ingest_brand_ads(self, brand_id: str, ads_data: list[dict]) -> dict:
    """
    Celery task to ingest, parse, and analyze competitor paid ads
    from ad libraries (Meta Ad Library, Google Ads Transparency, LinkedIn).
    """
    log = logger.bind(brand_id=brand_id, ads_count=len(ads_data), task_id=self.request.id)
    log.info("Starting competitor ads ingestion and creative analysis")

    parser = AdCreativeParser()
    processed_ads = []

    for item in ads_data:
        raw_text = item.get("ad_text", "")
        target_url = item.get("target_url")
        sug_format = item.get("ad_format")
        
        parsed = parser.parse_ad(raw_text, target_url, sug_format)
        
        f_seen = item.get("first_seen")
        l_seen = item.get("last_seen")
        tier_info = AdSpendEstimator.calculate_longevity_and_tier(f_seen, l_seen)

        targeting_info = item.get("targeting_info") or {}
        targeting_info.update({
            "headline": parsed.headline,
            "cta": parsed.cta,
            "landing_page_domain": parsed.landing_page_domain,
            "utm_parameters": parsed.utm_parameters,
            "longevity_days": tier_info.longevity_days,
            "spend_tier": tier_info.tier_label,
            "is_evergreen": tier_info.is_evergreen
        })

        processed_ads.append({
            "platform": item.get("platform", "google").lower(),
            "ad_text": raw_text,
            "ad_format": parsed.detected_format,
            "target_url": target_url,
            "first_seen": f_seen,
            "last_seen": l_seen,
            "targeting_info": targeting_info,
            "data_source_tag": item.get("data_source_tag", "ad_transparency")
        })

    analytics = AdSpendEstimator.aggregate_brand_ad_intelligence(processed_ads)

    log.info(
        "Ad intelligence analysis completed",
        total_ads=analytics["total_ads"],
        evergreen=analytics["evergreen_count"],
        spend_range=analytics["estimated_monthly_spend_range"]
    )

    return {
        "brand_id": brand_id,
        "total_processed": len(processed_ads),
        "analytics": analytics,
        "ads": processed_ads
    }
