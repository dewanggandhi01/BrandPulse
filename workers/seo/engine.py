from __future__ import annotations
from bs4 import BeautifulSoup
from typing import Any, Dict, List
import time

from .technical import audit_technical_seo
from .content import audit_content_quality
from .structured_data import audit_structured_data
from .links import audit_link_architecture

class SeoAuditEngine:
    """
    4-Pillar SEO Scoring Engine.
    Weights:
    - Technical SEO: 30%
    - Content Quality: 35%
    - Structured Data: 15%
    - Link Architecture: 20%
    """
    WEIGHTS = {
        'technical': 0.30,
        'content': 0.35,
        'structured_data': 0.15,
        'links': 0.20
    }

    @classmethod
    def audit(cls, html: str, url: str) -> Dict[str, Any]:
        t0 = time.perf_counter()
        soup = BeautifulSoup(html or '', 'lxml')

        tech = audit_technical_seo(soup, url)
        content = audit_content_quality(soup, html or '')
        struct = audit_structured_data(soup)
        links = audit_link_architecture(soup, url)

        # Calculate weighted total score
        total_score = (
            tech['score'] * cls.WEIGHTS['technical'] +
            content['score'] * cls.WEIGHTS['content'] +
            struct['score'] * cls.WEIGHTS['structured_data'] +
            links['score'] * cls.WEIGHTS['links']
        )
        total_score_int = int(round(max(0.0, min(100.0, total_score))))

        all_issues = (
            tech['issues'] +
            content['issues'] +
            struct['issues'] +
            links['issues']
        )

        # Sort issues: critical first, then warning, then info
        severity_order = {'critical': 0, 'warning': 1, 'info': 2}
        all_issues.sort(key=lambda x: severity_order.get(x.get('severity', 'info'), 3))

        critical_count = sum(1 for i in all_issues if i.get('severity') == 'critical')
        warning_count = sum(1 for i in all_issues if i.get('severity') == 'warning')

        elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)

        return {
            'total_score': total_score_int,
            'technical_scores': {
                'score': tech['score'],
                'details': tech['details']
            },
            'content_scores': {
                'score': content['score'],
                'details': content['details']
            },
            'structured_data_scores': {
                'score': struct['score'],
                'details': struct['details']
            },
            'link_scores': {
                'score': links['score'],
                'details': links['details']
            },
            'issues': all_issues,
            'summary': {
                'total_issues': len(all_issues),
                'critical_count': critical_count,
                'warning_count': warning_count,
                'passed_pillars': sum(
                    1 for s in [tech['score'], content['score'], struct['score'], links['score']] if s >= 80
                ),
                'elapsed_ms': elapsed_ms
            }
        }
