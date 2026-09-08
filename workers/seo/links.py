from __future__ import annotations
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from urllib.parse import urlparse

GENERIC_ANCHOR_TERMS = {
    'click here', 'here', 'read more', 'learn more', 'link', 'website',
    'more', 'this', 'this link', 'go', 'view', 'details'
}

def audit_link_architecture(soup: BeautifulSoup, page_url: str) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    points = 100
    details: Dict[str, Any] = {}

    page_netloc = urlparse(page_url).netloc.lower()

    links = soup.find_all('a', href=True)
    internal_links: List[str] = []
    external_links: List[str] = []
    generic_anchors: List[str] = []
    malformed_links: List[str] = []
    nofollow_count = 0

    for a in links:
        href = a['href'].strip()
        anchor_text = a.get_text().strip().lower()

        # Skip telephone, mailto
        if href.startswith(('mailto:', 'tel:')):
            continue
            
        if not href or href == '#' or href.startswith('javascript:'):
            malformed_links.append(href)
            continue

        # Check for malformed syntax
        if ' ' in href or not (href.startswith('/') or href.startswith(('http://', 'https://'))):
            malformed_links.append(href[:50])
        else:
            # Categorize internal vs external
            parsed = urlparse(href)
            if not parsed.netloc or parsed.netloc.lower() == page_netloc:
                internal_links.append(href)
            else:
                external_links.append(href)

        # Check rel attribute
        rel = a.get('rel', [])
        if isinstance(rel, str):
            rel = [rel]
        if any('nofollow' in r.lower() for r in rel):
            nofollow_count += 1

        # Check generic anchor text
        if anchor_text in GENERIC_ANCHOR_TERMS:
            generic_anchors.append(anchor_text)

    details['total_links'] = len(internal_links) + len(external_links)
    details['internal_links_count'] = len(internal_links)
    details['external_links_count'] = len(external_links)
    details['nofollow_count'] = nofollow_count
    details['generic_anchors_count'] = len(generic_anchors)
    details['malformed_links_count'] = len(malformed_links)

    # Scoring checks
    if len(internal_links) == 0:
        points -= 30
        issues.append({
            'id': 'link_orphan_or_no_internal',
            'pillar': 'links',
            'severity': 'critical',
            'title': 'No Internal Navigation Links Detected',
            'description': 'Page does not link to any other internal pages on your domain.',
            'recommendation': 'Add navigation, breadcrumbs, and contextual links to relevant internal pages.'
        })

    if len(generic_anchors) > 2:
        points -= 15
        issues.append({
            'id': 'link_generic_anchors',
            'pillar': 'links',
            'severity': 'warning',
            'title': 'Generic Anchor Text Detected',
            'description': f'Found {len(generic_anchors)} links using non-descriptive anchor text like "click here" or "read more".',
            'recommendation': 'Replace generic anchors with keyword-rich, descriptive anchor text explaining the destination page.'
        })

    if len(malformed_links) > 0:
        points -= 20
        issues.append({
            'id': 'link_malformed_urls',
            'pillar': 'links',
            'severity': 'critical',
            'title': 'Malformed Link Target URLs',
            'description': f'{len(malformed_links)} link(s) have invalid formatting or spaces in the URL.',
            'recommendation': 'Review and sanitize link href attributes to ensure RFC compliance.'
        })

    score = max(0, min(100, points))
    return {
        'score': score,
        'details': details,
        'issues': issues
    }
