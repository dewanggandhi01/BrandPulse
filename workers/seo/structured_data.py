from __future__ import annotations
from bs4 import BeautifulSoup
from typing import Any, Dict, List
import json

def audit_structured_data(soup: BeautifulSoup) -> Dict[str, Any]:
    issues: List[Dict[str, Any]] = []
    points = 100
    details: Dict[str, Any] = {}

    json_ld_scripts = soup.find_all('script', attrs={'type': 'application/ld+json'})
    details['json_ld_count'] = len(json_ld_scripts)

    schemas_found: List[str] = []
    parse_errors: List[str] = []

    for idx, script in enumerate(json_ld_scripts):
        content = script.string
        if not content:
            continue
        try:
            data = json.loads(content.strip())
            # Extract @type
            if isinstance(data, dict):
                stype = data.get('@type')
                if stype:
                    schemas_found.append(str(stype))
                # Check for @graph
                graph = data.get('@graph')
                if isinstance(graph, list):
                    for item in graph:
                        if isinstance(item, dict) and '@type' in item:
                            schemas_found.append(str(item['@type']))
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and '@type' in item:
                        schemas_found.append(str(item['@type']))
        except Exception as err:
            parse_errors.append(f'Block {idx+1}: {str(err)}')

    details['schemas_detected'] = list(set(schemas_found))
    details['parse_errors'] = parse_errors

    # Microdata check
    microdata_items = soup.find_all(attrs={'itemscope': True})
    details['microdata_count'] = len(microdata_items)
    
    # Specific Schema Detection (Breadcrumb, FAQ, Product)
    details['has_breadcrumb'] = any('BreadcrumbList' in str(s) for s in schemas_found)
    details['has_faq'] = any('FAQPage' in str(s) for s in schemas_found)
    details['has_product'] = any('Product' in str(s) for s in schemas_found)

    has_structured_data = len(json_ld_scripts) > 0 or len(microdata_items) > 0

    if not has_structured_data:
        points -= 60
        issues.append({
            'id': 'struct_missing_schema',
            'pillar': 'structured_data',
            'severity': 'critical',
            'title': 'No Structured Data (Schema.org / JSON-LD) Found',
            'description': 'The page does not provide any JSON-LD or Microdata markup.',
            'recommendation': 'Add Schema.org JSON-LD (e.g., Organization, WebSite, Product, BreadcrumbList) for rich SERP snippets.'
        })
    else:
        if parse_errors:
            points -= 40
            issues.append({
                'id': 'struct_json_syntax_error',
                'pillar': 'structured_data',
                'severity': 'critical',
                'title': 'Malformed JSON-LD Syntax',
                'description': f'Encountered JSON parsing errors in structured data block: {", ".join(parse_errors[:2])}',
                'recommendation': 'Validate JSON-LD syntax using Google Rich Results Test to fix invalid tokens.'
            })
        elif len(schemas_found) == 0 and len(microdata_items) == 0:
            points -= 20
            issues.append({
                'id': 'struct_empty_schema',
                'pillar': 'structured_data',
                'severity': 'warning',
                'title': 'Empty or Unrecognized Schema Type',
                'description': 'JSON-LD blocks were detected but no standard Schema.org @type entities were identified.',
                'recommendation': 'Specify formal Schema.org types like Organization, WebSite, Product, or Article.'
            })

    score = max(0, min(100, points))
    return {
        'score': score,
        'details': details,
        'issues': issues
    }
