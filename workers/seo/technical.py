from __future__ import annotations
from bs4 import BeautifulSoup
from typing import Any, Dict, List
from urllib.parse import urlparse

def audit_technical_seo(soup: BeautifulSoup, url: str) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    points = 100
    details: Dict[str, Any] = {}

    # 1. Title tag
    title_tag = soup.find('title')
    title_text = title_tag.get_text().strip() if title_tag else ''
    details['title'] = title_text
    details['title_length'] = len(title_text)

    if not title_text:
        points -= 25
        issues.append({
            'id': 'tech_missing_title',
            'pillar': 'technical',
            'severity': 'critical',
            'title': 'Missing Page Title Tag',
            'description': 'The page does not contain a <title> tag in the head.',
            'recommendation': 'Add a unique, descriptive <title> tag between 30 and 60 characters.'
        })
    elif len(title_text) < 30:
        points -= 8
        issues.append({
            'id': 'tech_short_title',
            'pillar': 'technical',
            'severity': 'warning',
            'title': 'Title Tag Too Short',
            'description': f'Title is {len(title_text)} characters, which is under the recommended 30 characters.',
            'recommendation': 'Expand title to 30-60 characters incorporating primary target keywords.'
        })
    elif len(title_text) > 65:
        points -= 5
        issues.append({
            'id': 'tech_long_title',
            'pillar': 'technical',
            'severity': 'warning',
            'title': 'Title Tag May Be Truncated in SERP',
            'description': f'Title is {len(title_text)} characters, exceeding search engine display limits (~60 chars).',
            'recommendation': 'Shorten title tag to under 60 characters to avoid truncation.'
        })

    # 2. Meta description
    meta_desc = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'description'})
    desc_text = meta_desc.get('content', '').strip() if meta_desc else ''
    details['meta_description'] = desc_text
    details['meta_description_length'] = len(desc_text)

    if not desc_text:
        points -= 20
        issues.append({
            'id': 'tech_missing_description',
            'pillar': 'technical',
            'severity': 'critical',
            'title': 'Missing Meta Description',
            'description': 'The page lacks a meta description tag.',
            'recommendation': 'Add an enticing meta description between 120 and 160 characters.'
        })
    elif len(desc_text) < 70:
        points -= 6
        issues.append({
            'id': 'tech_short_description',
            'pillar': 'technical',
            'severity': 'warning',
            'title': 'Meta Description Too Short',
            'description': f'Meta description is only {len(desc_text)} characters long.',
            'recommendation': 'Elaborate on page benefits to reach 120-160 characters.'
        })
    elif len(desc_text) > 165:
        points -= 4
        issues.append({
            'id': 'tech_long_description',
            'pillar': 'technical',
            'severity': 'warning',
            'title': 'Meta Description Exceeds SERP Snippet',
            'description': f'Meta description is {len(desc_text)} characters long.',
            'recommendation': 'Trim description to under 160 characters to fit search results snippets.'
        })

    # 3. Canonical URL
    canonical_tag = soup.find('link', attrs={'rel': lambda x: x and 'canonical' in x})
    canonical_url = canonical_tag.get('href', '').strip() if canonical_tag else ''
    details['canonical_url'] = canonical_url

    if not canonical_url:
        points -= 10
        issues.append({
            'id': 'tech_missing_canonical',
            'pillar': 'technical',
            'severity': 'warning',
            'title': 'Missing Canonical Link Element',
            'description': 'No rel="canonical" link tag was found.',
            'recommendation': 'Add a rel="canonical" tag pointing to the authoritative page URL.'
        })

    # 4. Viewport meta tag (Mobile friendliness)
    viewport_meta = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'viewport'})
    details['has_viewport'] = bool(viewport_meta)
    if not viewport_meta:
        points -= 15
        issues.append({
            'id': 'tech_missing_viewport',
            'pillar': 'technical',
            'severity': 'critical',
            'title': 'Missing Mobile Viewport Meta Tag',
            'description': 'No <meta name="viewport"> tag detected, impairing mobile rendering.',
            'recommendation': 'Add <meta name="viewport" content="width=device-width, initial-scale=1.0">.'
        })

    # 5. Open Graph tags
    og_title = soup.find('meta', property='og:title')
    og_desc = soup.find('meta', property='og:description')
    og_image = soup.find('meta', property='og:image')
    details['open_graph'] = {
        'has_title': bool(og_title),
        'has_description': bool(og_desc),
        'has_image': bool(og_image)
    }

    if not (og_title and og_desc and og_image):
        points -= 8
        issues.append({
            'id': 'tech_incomplete_opengraph',
            'pillar': 'technical',
            'severity': 'warning',
            'title': 'Incomplete Open Graph Metadata',
            'description': 'Page is missing og:title, og:description, or og:image social share tags.',
            'recommendation': 'Add complete Open Graph and Twitter card tags for enhanced social preview.'
        })

    # 6. HTTPS verification
    parsed_url = urlparse(url)
    details['is_https'] = parsed_url.scheme == 'https'
    if parsed_url.scheme != 'https':
        points -= 15
        issues.append({
            'id': 'tech_not_https',
            'pillar': 'technical',
            'severity': 'critical',
            'title': 'Insecure HTTP Connection',
            'description': 'Target URL is served over unencrypted HTTP.',
            'recommendation': 'Enforce HTTPS and install a valid SSL/TLS certificate.'
        })

    # 7. Robots meta tag
    robots_meta = soup.find('meta', attrs={'name': lambda x: x and x.lower() == 'robots'})
    robots_content = robots_meta.get('content', '').lower() if robots_meta else ''
    details['robots_meta'] = robots_content
    if 'noindex' in robots_content:
        points -= 20
        issues.append({
            'id': 'tech_robots_noindex',
            'pillar': 'technical',
            'severity': 'critical',
            'title': 'Page Blocked from Indexing (noindex)',
            'description': 'The robots meta tag contains "noindex", preventing search indexing.',
            'recommendation': 'Remove "noindex" directive if you want this page to rank on Google.'
        })

    # 8. Hreflang tags
    hreflang_tags = soup.find_all('link', attrs={'rel': lambda x: x and 'alternate' in x, 'hreflang': True})
    details['hreflang_count'] = len(hreflang_tags)
    if not hreflang_tags:
        # Not strictly an error, but worth noting if missing on large sites.
        details['has_hreflang'] = False
    else:
        details['has_hreflang'] = True

    score = max(0, min(100, points))
    return {
        'score': score,
        'details': details,
        'issues': issues
    }
