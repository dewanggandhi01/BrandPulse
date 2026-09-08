from __future__ import annotations
import pytest
from datetime import date, timedelta
from workers.ads.parser import AdCreativeParser
from workers.ads.estimator import AdSpendEstimator

def test_ad_creative_parser_headline_and_cta():
    parser = AdCreativeParser()
    sample_text = "Revolutionize Your Workflow - The #1 AI Project Manager\nAutomate your sprint tracking and deploy faster. Sign up today for free."
    
    parsed = parser.parse_ad(sample_text, target_url="https://saascorp.com/signup?utm_source=google&utm_campaign=brand_q3")
    assert parsed.headline == "Revolutionize Your Workflow"
    assert "Automate your sprint tracking" in parsed.body_copy
    assert parsed.cta == "Sign Up"
    assert parsed.landing_page_domain == "saascorp.com"
    assert parsed.utm_parameters.get("utm_source") == "google"
    assert parsed.utm_parameters.get("utm_campaign") == "brand_q3"

def test_ad_creative_parser_formats():
    parser = AdCreativeParser()
    # Search ad
    res_search = parser.parse_ad("Cloud CRM Software. 14-day free trial. Compare plans now.")
    assert res_search.detected_format == "search"
    assert res_search.cta == "Free Trial"

    # Video ad
    res_video = parser.parse_ad("Watch our 2-minute demo video to see how fast our pipeline builds.")
    assert res_video.detected_format == "video"

def test_ad_longevity_and_tiers():
    today = date.today()

    # 1. Pilot (<= 3 days)
    tier_pilot = AdSpendEstimator.calculate_longevity_and_tier(today - timedelta(days=2), today)
    assert tier_pilot.longevity_days == 3
    assert tier_pilot.tier_label == "Testing / Pilot"
    assert tier_pilot.is_evergreen is False

    # 2. Active (4 - 14 days)
    tier_active = AdSpendEstimator.calculate_longevity_and_tier(today - timedelta(days=9), today)
    assert tier_active.longevity_days == 10
    assert tier_active.tier_label == "Active Campaign"
    assert tier_active.is_evergreen is False

    # 3. Scaling (15 - 45 days)
    tier_scaling = AdSpendEstimator.calculate_longevity_and_tier(today - timedelta(days=29), today)
    assert tier_scaling.longevity_days == 30
    assert tier_scaling.tier_label == "Scaling Campaign"
    assert tier_scaling.is_evergreen is False

    # 4. Evergreen (> 45 days)
    tier_evergreen = AdSpendEstimator.calculate_longevity_and_tier(today - timedelta(days=64), today)
    assert tier_evergreen.longevity_days == 65
    assert tier_evergreen.tier_label == "Evergreen Winner"
    assert tier_evergreen.is_evergreen is True

def test_aggregate_brand_ad_intelligence():
    today = date.today()
    mock_ads = [
        {
            "platform": "google",
            "ad_format": "search",
            "first_seen": today - timedelta(days=60),
            "last_seen": today,
            "targeting_info": {"cta": "Get Started", "landing_page_domain": "brand.com"}
        },
        {
            "platform": "google",
            "ad_format": "search",
            "first_seen": today - timedelta(days=10),
            "last_seen": today,
            "targeting_info": {"cta": "Get Started", "landing_page_domain": "brand.com"}
        },
        {
            "platform": "meta",
            "ad_format": "sponsored_feed",
            "first_seen": today - timedelta(days=2),
            "last_seen": today,
            "targeting_info": {"cta": "Learn More", "landing_page_domain": "brand.com"}
        }
    ]

    agg = AdSpendEstimator.aggregate_brand_ad_intelligence(mock_ads)
    assert agg["total_ads"] == 3
    assert agg["evergreen_count"] == 1
    assert len(agg["platform_distribution"]) == 2
    assert agg["platform_distribution"][0]["platform"] == "google"
    assert agg["platform_distribution"][0]["count"] == 2
    assert agg["top_ctas"][0]["cta"] == "Get Started"
    assert agg["top_ctas"][0]["count"] == 2
