from __future__ import annotations
import pytest

@pytest.fixture
def sample_robots_txt() -> str:
    return """
User-agent: *
Disallow: /admin/
Disallow: /private/
Crawl-delay: 5

User-agent: BadBot
Disallow: /
"""
