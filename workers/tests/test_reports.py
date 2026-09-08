from __future__ import annotations
import pytest
from workers.reports.generator import ExecutiveReportGenerator

def test_executive_report_generator_composite_health():
    generator = ExecutiveReportGenerator()
    
    # 1. Strong brand posture
    brief_strong = generator.generate_brief(
        brand_name="ApexCloud",
        brand_domain="apexcloud.com",
        seo_data={"total_score": 88},
        product_data={"total_products": 40, "in_stock_count": 38},
        change_data={"total_changes": 8},
        sentiment_data={"net_sentiment_score": 45.0},
        ad_data={"total_ads": 15, "evergreen_count": 4, "estimated_monthly_spend_range": "$25,000+"}
    )
    assert brief_strong.health_score >= 75
    assert brief_strong.risk_level == "Low Risk"
    assert brief_strong.pillar_scores["seo"] == 88

    # 2. Vulnerable brand posture
    brief_weak = generator.generate_brief(
        brand_name="SlowCorp",
        brand_domain="slowcorp.com",
        seo_data={"total_score": 42},
        product_data={"total_products": 2, "in_stock_count": 0},
        change_data={"total_changes": 35},
        sentiment_data={"net_sentiment_score": -35.0},
        ad_data={"total_ads": 0, "evergreen_count": 0, "estimated_monthly_spend_range": "$0"}
    )
    assert brief_weak.health_score < 50
    assert brief_weak.risk_level == "High Threat"

def test_executive_report_generator_swot():
    generator = ExecutiveReportGenerator()
    brief = generator.generate_brief(
        brand_name="TechPro",
        brand_domain="techpro.io",
        seo_data={"total_score": 92},
        product_data={"total_products": 10, "in_stock_count": 10},
        change_data={"total_changes": 12},
        sentiment_data={"net_sentiment_score": 25.0},
        ad_data={"total_ads": 6, "evergreen_count": 2, "platform_distribution": [{"platform": "google", "count": 6}]}
    )
    categories = {s["category"] for s in brief.swot}
    assert "strength" in categories
    assert "opportunity" in categories
    assert "threat" in categories
    assert len(brief.recommendations) >= 3
    assert "TechPro" in brief.ai_narrative
