from __future__ import annotations
import pytest
from workers.diffing.html_cleaner import HtmlCleaner
from workers.diffing.comparator import SnapshotComparator
from workers.diffing.classifier import ChangeClassifier

HTML_V1 = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme Inc - The Future of Project Management</title>
    <meta name="description" content="AI-driven project management for modern teams.">
</head>
<body>
    <script>const csrf = "12345";</script>
    <!-- Some developer comment -->
    <header><h1>The Future of Project Management</h1></header>
    <p>Acme helps distributed engineering teams ship software 10x faster with AI roadmaps.</p>
    <div class="pricing">
        <span class="plan">Starter Plan: $29/mo</span>
        <span class="plan">Pro Plan: $99/mo</span>
    </div>
</body>
</html>
"""

HTML_V2_MESSAGING = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme Inc - Autonomous Workflow Intelligence</title>
    <meta name="description" content="AI-driven project management for modern teams.">
</head>
<body>
    <header><h1>Autonomous Workflow Intelligence</h1></header>
    <p>Acme helps distributed engineering teams ship software 10x faster with AI roadmaps.</p>
    <div class="pricing">
        <span class="plan">Starter Plan: $29/mo</span>
        <span class="plan">Pro Plan: $99/mo</span>
    </div>
</body>
</html>
"""

HTML_V2_PRICING = """
<!DOCTYPE html>
<html>
<head>
    <title>Acme Inc - The Future of Project Management</title>
    <meta name="description" content="AI-driven project management for modern teams.">
</head>
<body>
    <header><h1>The Future of Project Management</h1></header>
    <p>Acme helps distributed engineering teams ship software 10x faster with AI roadmaps.</p>
    <div class="pricing">
        <span class="plan">Starter Plan: $49/mo</span>
        <span class="plan">Enterprise Tier: $199/mo</span>
    </div>
</body>
</html>
"""

def test_html_cleaner():
    clean_html, blocks = HtmlCleaner.clean(HTML_V1)
    # Ensure script and comment removed
    assert "12345" not in clean_html
    assert "developer comment" not in clean_html
    assert len(blocks) >= 3
    assert any("The Future of Project Management" in b for b in blocks)

def test_comparator_identical():
    _, blocks1 = HtmlCleaner.clean(HTML_V1)
    res = SnapshotComparator.compare(blocks1, blocks1)
    assert res["is_identical"] is True
    assert res["similarity_ratio"] == 1.0
    assert res["additions_count"] == 0
    assert res["deletions_count"] == 0

def test_comparator_with_differences():
    _, blocks1 = HtmlCleaner.clean(HTML_V1)
    _, blocks2 = HtmlCleaner.clean(HTML_V2_PRICING)
    res = SnapshotComparator.compare(blocks1, blocks2)
    assert res["is_identical"] is False
    assert 0.4 <= res["similarity_ratio"] < 1.0
    assert res["total_changes"] > 0
    assert len(res["diff_chunks"]) > 0

def test_classifier_messaging_pivot():
    _, blocks1 = HtmlCleaner.clean(HTML_V1)
    _, blocks2 = HtmlCleaner.clean(HTML_V2_MESSAGING)
    comp = SnapshotComparator.compare(blocks1, blocks2)
    change_type, summary = ChangeClassifier.classify(HTML_V1, HTML_V2_MESSAGING, comp)
    assert change_type == "messaging_pivot"
    assert "pivoted from" in summary or "updated from" in summary

def test_classifier_pricing_change():
    _, blocks1 = HtmlCleaner.clean(HTML_V1)
    _, blocks2 = HtmlCleaner.clean(HTML_V2_PRICING)
    comp = SnapshotComparator.compare(blocks1, blocks2)
    change_type, summary = ChangeClassifier.classify(HTML_V1, HTML_V2_PRICING, comp)
    assert change_type == "pricing_change"
    assert "Pricing" in summary

def test_classifier_minor_copy():
    # Only change one word in a paragraph
    html_minor = HTML_V1.replace("10x faster", "5x faster")
    _, b1 = HtmlCleaner.clean(HTML_V1)
    _, b2 = HtmlCleaner.clean(html_minor)
    comp = SnapshotComparator.compare(b1, b2)
    change_type, _ = ChangeClassifier.classify(HTML_V1, html_minor, comp)
    assert change_type == "minor_copy"
