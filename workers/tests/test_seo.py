from __future__ import annotations
import pytest
from bs4 import BeautifulSoup
from workers.seo.technical import audit_technical_seo
from workers.seo.content import audit_content_quality
from workers.seo.structured_data import audit_structured_data
from workers.seo.links import audit_link_architecture
from workers.seo.engine import SeoAuditEngine

OPTIMAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>BrandPulse - Competitive Intelligence & Brand Tracking</title>
    <meta name="description" content="Discover actionable competitor intelligence and track brand sentiment with BrandPulse real-time scraping and NLP auditing platform.">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="canonical" href="https://brandpulse.io/">
    <meta property="og:title" content="BrandPulse - Competitive Intelligence">
    <meta property="og:description" content="Actionable competitor intelligence and brand tracking.">
    <meta property="og:image" content="https://brandpulse.io/logo.png">
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Organization",
      "name": "BrandPulse",
      "url": "https://brandpulse.io"
    }
    </script>
</head>
<body>
    <header>
        <nav>
            <a href="https://brandpulse.io/features">Features Overview</a>
            <a href="https://brandpulse.io/pricing">Pricing Plans</a>
            <a href="https://brandpulse.io/contact">Contact Us</a>
            <a href="https://external.com/partner" rel="nofollow">Partner Site</a>
        </nav>
    </header>
    <main>
        <h1>Next Generation Brand Analysis & Competitor Tracking</h1>
        <h2>Comprehensive Scraping and NLP Auditing</h2>
        <p>BrandPulse monitors competitor websites, prices, advertisements, and brand sentiment with precision. Our 4-pillar SEO audit evaluates technical stability, content quality, schema compliance, and link architecture.</p>
        <p>Modern businesses require automated intelligence pipelines to maintain a competitive advantage across retail, technology, and service sectors.</p>
        <h2>Actionable Intelligence Reporting</h2>
        <p>Gain unprecedented visibility into price shifts, product catalogue changes, and search visibility across all major search and social platforms.</p>
        <p>With real-time alerts and time-series price tracking, BrandPulse empowers marketing and product teams to react rapidly to competitor strategies.</p>
        <img src="https://brandpulse.io/dashboard.png" alt="BrandPulse Intelligence Dashboard Screenshot">
        <img src="https://brandpulse.io/chart.png" alt="SEO Pillar Radar Chart Comparison">
    </main>
</body>
</html>
"""

POOR_HTML = """
<html>
<body>
    <img src="test.jpg">
    <a href="click here">click here</a>
</body>
</html>
"""

def test_technical_seo_optimal():
    soup = BeautifulSoup(OPTIMAL_HTML, "lxml")
    res = audit_technical_seo(soup, "https://brandpulse.io/")
    assert res["score"] >= 90
    assert res["details"]["has_viewport"] is True
    assert res["details"]["is_https"] is True
    critical_issues = [i for i in res["issues"] if i["severity"] == "critical"]
    assert len(critical_issues) == 0

def test_technical_seo_poor():
    soup = BeautifulSoup(POOR_HTML, "lxml")
    res = audit_technical_seo(soup, "http://insecure-site.com")
    assert res["score"] < 50
    # Missing title, missing description, not https, missing viewport
    issue_ids = [i["id"] for i in res["issues"]]
    assert "tech_missing_title" in issue_ids
    assert "tech_missing_description" in issue_ids
    assert "tech_not_https" in issue_ids
    assert "tech_missing_viewport" in issue_ids

def test_content_quality():
    soup_opt = BeautifulSoup(OPTIMAL_HTML, "lxml")
    res_opt = audit_content_quality(soup_opt, OPTIMAL_HTML)
    assert res_opt["score"] >= 80
    assert res_opt["details"]["h1_count"] == 1
    assert res_opt["details"]["images_missing_alt"] == 0

    soup_poor = BeautifulSoup(POOR_HTML, "lxml")
    res_poor = audit_content_quality(soup_poor, POOR_HTML)
    assert res_poor["score"] < 50
    poor_ids = [i["id"] for i in res_poor["issues"]]
    assert "content_missing_h1" in poor_ids
    assert "content_thin_critical" in poor_ids

def test_structured_data():
    soup_opt = BeautifulSoup(OPTIMAL_HTML, "lxml")
    res_opt = audit_structured_data(soup_opt)
    assert res_opt["score"] == 100
    assert "Organization" in res_opt["details"]["schemas_detected"]

    soup_poor = BeautifulSoup(POOR_HTML, "lxml")
    res_poor = audit_structured_data(soup_poor)
    assert res_poor["score"] < 50
    assert res_poor["issues"][0]["id"] == "struct_missing_schema"

def test_link_architecture():
    soup_opt = BeautifulSoup(OPTIMAL_HTML, "lxml")
    res_opt = audit_link_architecture(soup_opt, "https://brandpulse.io/")
    assert res_opt["score"] >= 90
    assert res_opt["details"]["internal_links_count"] >= 3

    soup_poor = BeautifulSoup(POOR_HTML, "lxml")
    res_poor = audit_link_architecture(soup_poor, "https://poor.com/")
    poor_ids = [i["id"] for i in res_poor["issues"]]
    assert "link_orphan_or_no_internal" in poor_ids

def test_seo_audit_engine_overall():
    audit_opt = SeoAuditEngine.audit(OPTIMAL_HTML, "https://brandpulse.io/")
    assert audit_opt["total_score"] >= 85
    assert "technical_scores" in audit_opt
    assert "content_scores" in audit_opt
    assert "structured_data_scores" in audit_opt
    assert "link_scores" in audit_opt
    assert audit_opt["summary"]["critical_count"] == 0

    # Boundary Value Analysis: Empty HTML
    audit_empty = SeoAuditEngine.audit("", "http://empty.com")
    assert audit_empty["total_score"] <= 40
    assert audit_empty["summary"]["critical_count"] > 0
