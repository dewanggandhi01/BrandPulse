from __future__ import annotations
from bs4 import BeautifulSoup
from typing import Any, Dict, List
import re

def estimate_flesch_reading_ease(text: str) -> float:
    """Approximate Flesch Reading Ease score without external dictionary dependencies."""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    num_sentences = max(1, len(sentences))
    
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    num_words = max(1, len(words))

    # Syllables estimation
    def count_syllables(word: str) -> int:
        word = word.lower()
        count = len(re.findall(r'[aeiouy]+', word))
        if word.endswith('e') and not word.endswith('le') and count > 1:
            count -= 1
        return max(1, count)

    num_syllables = sum(count_syllables(w) for w in words)

    # Standard Flesch Reading Ease formula
    score = 206.835 - (1.015 * (num_words / num_sentences)) - (84.6 * (num_syllables / num_words))
    return round(max(0.0, min(100.0, score)), 1)

def audit_content_quality(soup: BeautifulSoup, raw_html: str) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    points = 100
    details: Dict[str, Any] = {}

    # 1. Clean Body Text & Word Count
    # Remove script and style elements
    clean_soup = BeautifulSoup(str(soup), 'lxml')
    for script_or_style in clean_soup(['script', 'style', 'noscript', 'svg']):
        script_or_style.decompose()

    body_text = clean_soup.get_text(separator=' ', strip=True)
    words = re.findall(r'\b[\w-]+\b', body_text)
    word_count = len(words)
    details['word_count'] = word_count

    if word_count < 100:
        points -= 25
        issues.append({
            'id': 'content_thin_critical',
            'pillar': 'content',
            'severity': 'critical',
            'title': 'Thin Content Detected (<100 Words)',
            'description': f'Page contains only {word_count} words of visible content.',
            'recommendation': 'Substantially enrich the page content with valuable body text and information.'
        })
    elif word_count < 300:
        points -= 15
        issues.append({
            'id': 'content_thin_warning',
            'pillar': 'content',
            'severity': 'warning',
            'title': 'Low Content Volume (<300 Words)',
            'description': f'Page has {word_count} words, which may struggle to rank against comprehensive competitor pages.',
            'recommendation': 'Aim for at least 500-800 words of thorough, authoritative content.'
        })

    # 2. Heading Structure (H1-H6)
    h1_tags = soup.find_all('h1')
    h1_texts = [h.get_text().strip() for h in h1_tags if h.get_text().strip()]
    details['h1_count'] = len(h1_texts)
    details['h1_texts'] = h1_texts[:3]

    if len(h1_texts) == 0:
        points -= 25
        issues.append({
            'id': 'content_missing_h1',
            'pillar': 'content',
            'severity': 'critical',
            'title': 'Missing Top-Level Heading (H1)',
            'description': 'The page does not have a primary <h1> heading.',
            'recommendation': 'Add a single, prominent <h1> heading matching the target search intent.'
        })
    elif len(h1_texts) > 1:
        points -= 10
        issues.append({
            'id': 'content_multiple_h1',
            'pillar': 'content',
            'severity': 'warning',
            'title': 'Multiple H1 Headings Detected',
            'description': f'Found {len(h1_texts)} <h1> tags. Multiple H1 tags can dilute thematic focus.',
            'recommendation': 'Consolidate to a single <h1> heading, converting secondary headings to <h2>.'
        })

    # Check H2 and H3 presence
    h2_count = len(soup.find_all('h2'))
    h3_count = len(soup.find_all('h3'))
    details['h2_count'] = h2_count
    details['h3_count'] = h3_count

    if word_count > 300 and h2_count == 0:
        points -= 10
        issues.append({
            'id': 'content_missing_h2',
            'pillar': 'content',
            'severity': 'warning',
            'title': 'Missing Sub-Headings (H2)',
            'description': 'Page has substantial text but lacks <h2> sub-headings to break up sections.',
            'recommendation': 'Organize paragraphs with descriptive <h2> and <h3> sub-headings.'
        })

    # 3. Image Alt Text Audit
    images = soup.find_all('img')
    total_images = len(images)
    missing_alt = 0
    for img in images:
        alt = img.get('alt')
        if alt is None or not str(alt).strip():
            missing_alt += 1

    details['total_images'] = total_images
    details['images_missing_alt'] = missing_alt
    alt_coverage = ((total_images - missing_alt) / total_images * 100) if total_images > 0 else 100.0
    details['alt_coverage_pct'] = round(alt_coverage, 1)

    if total_images > 0 and missing_alt > 0:
        if alt_coverage < 50.0:
            points -= 15
            issues.append({
                'id': 'content_missing_alt_critical',
                'pillar': 'content',
                'severity': 'critical',
                'title': 'Over 50% Images Missing Alt Text',
                'description': f'{missing_alt} of {total_images} images lack descriptive alt tags.',
                'recommendation': 'Add descriptive, accessible alt text to all informational images.'
            })
        else:
            points -= 8
            issues.append({
                'id': 'content_missing_alt_warning',
                'pillar': 'content',
                'severity': 'warning',
                'title': 'Some Images Missing Alt Attributes',
                'description': f'{missing_alt} image(s) do not specify an alt attribute.',
                'recommendation': 'Ensure all product and editorial images have descriptive alt attributes.'
            })

    # 4. Text-to-HTML Ratio
    raw_html_len = max(1, len(raw_html))
    text_len = len(body_text)
    ratio = round((text_len / raw_html_len) * 100, 1)
    details['text_to_html_ratio'] = ratio

    if ratio < 5.0 and word_count > 50:
        points -= 10
        issues.append({
            'id': 'content_low_text_ratio',
            'pillar': 'content',
            'severity': 'warning',
            'title': 'Excessive Code Bloat (Low Text-to-HTML Ratio)',
            'description': f'Text constitutes only {ratio}% of the total page size.',
            'recommendation': 'Minify DOM structure, inline styles, and unneeded scripts to reduce HTML bloat.'
        })

    # 5. Readability
    readability = estimate_flesch_reading_ease(body_text) if word_count >= 50 else 50.0
    details['flesch_reading_ease'] = readability

    # 6. Keyword Density
    # Simple unigram density
    lower_words = [w.lower() for w in words if len(w) > 3]
    word_freq = {}
    for w in lower_words:
        word_freq[w] = word_freq.get(w, 0) + 1
    
    top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    details['top_keywords'] = [{'keyword': k, 'count': v, 'density': round((v / max(1, len(lower_words))) * 100, 2)} for k, v in top_keywords]

    # 7. Content Freshness
    time_tag = soup.find('time')
    meta_published = soup.find('meta', property='article:published_time') or soup.find('meta', property='og:updated_time')
    
    has_freshness = bool(time_tag or meta_published)
    details['has_freshness_signals'] = has_freshness
    
    if not has_freshness and word_count > 300:
        points -= 5
        issues.append({
            'id': 'content_missing_freshness',
            'pillar': 'content',
            'severity': 'warning',
            'title': 'Missing Publish/Update Dates',
            'description': 'Could not detect an article:published_time meta tag or HTML <time> element.',
            'recommendation': 'For articles or blog posts, include explicit published and updated timestamps.'
        })

    score = max(0, min(100, points))
    return {
        'score': score,
        'details': details,
        'issues': issues
    }
