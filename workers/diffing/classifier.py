from __future__ import annotations
import re
from typing import Any, Dict, List, Tuple
from bs4 import BeautifulSoup

PRICING_KEYWORDS = {
    'price', 'pricing', 'plan', 'plans', 'cost', 'tier', 'subscription',
    'monthly', 'annually', 'billed', 'discount', 'free trial', 'checkout',
    'per month', 'per user', 'starting at', '$', '€', '£', '₹'
}

class ChangeClassifier:
    """
    Classifies website diffs into actionable business intelligence categories
    (pricing changes, messaging pivots, layout overhauls, SEO shifts, minor copy).
    """

    @classmethod
    def classify(
        cls,
        old_html: str,
        new_html: str,
        comparison_res: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Returns (change_type, human_readable_summary).
        """
        similarity = comparison_res.get('similarity_ratio', 1.0)
        diff_chunks = comparison_res.get('diff_chunks', [])
        total_changes = comparison_res.get('total_changes', 0)

        if total_changes == 0 or similarity >= 0.999:
            return "no_change", "Content is identical across both snapshot versions."

        # Parse titles and H1s
        soup_old = BeautifulSoup(old_html, 'lxml') if old_html else None
        soup_new = BeautifulSoup(new_html, 'lxml') if new_html else None

        title_old = soup_old.title.string.strip() if soup_old and soup_old.title and soup_old.title.string else ""
        title_new = soup_new.title.string.strip() if soup_new and soup_new.title and soup_new.title.string else ""

        h1_old = soup_old.h1.get_text(strip=True) if soup_old and soup_old.h1 else ""
        h1_new = soup_new.h1.get_text(strip=True) if soup_new and soup_new.h1 else ""

        # Collect changed text
        changed_snippets: List[str] = []
        for chunk in diff_chunks:
            if chunk['type'] in ('added', 'removed'):
                changed_snippets.append(chunk['content'].lower())
            elif chunk['type'] == 'modified':
                changed_snippets.append(chunk.get('old_content', '').lower())
                changed_snippets.append(chunk.get('new_content', '').lower())

        changed_text_joined = " ".join(changed_snippets)

        # 1. Check for Pricing Changes
        has_price_keyword = any(k in changed_text_joined for k in PRICING_KEYWORDS)
        has_currency_regex = bool(re.search(r'[\$€£₹]\s*\d+', changed_text_joined))
        if has_currency_regex or (has_price_keyword and ('pricing' in title_new.lower() or 'pricing' in h1_new.lower())):
            pct_change = round((1.0 - similarity) * 100, 1)
            return "pricing_change", f"Pricing information adjusted with {pct_change}% content change detected."

        # 2. Check for Messaging Pivot (H1 or Title changed significantly)
        if (h1_old and h1_new and h1_old != h1_new) or (title_old and title_new and title_old != title_new):
            if h1_old != h1_new:
                summary = f"Primary headline pivoted from '{h1_old[:60]}' to '{h1_new[:60]}'."
            else:
                summary = f"Page title updated from '{title_old[:60]}' to '{title_new[:60]}'."
            return "messaging_pivot", summary

        # 3. Check for Major Layout Overhaul
        if similarity < 0.60:
            pct_mod = round((1.0 - similarity) * 100, 1)
            return "layout_overhaul", f"Comprehensive page redesign detected with {pct_mod}% structural variance."

        # 4. Check for SEO Meta Changes
        meta_desc_old = (soup_old.find('meta', attrs={'name': 'description'}) or {}).get('content', '') if soup_old else ""
        meta_desc_new = (soup_new.find('meta', attrs={'name': 'description'}) or {}).get('content', '') if soup_new else ""
        if meta_desc_old and meta_desc_new and meta_desc_old != meta_desc_new:
            return "seo_change", f"SEO meta description revised: '{meta_desc_new[:80]}...'."

        # 5. Minor Copy vs General Content Update
        if similarity >= 0.85 or total_changes <= 2:
            return "minor_copy", f"Subtle copy revisions across {total_changes} text blocks ({round((1.0 - similarity) * 100, 1)}% variance)."

        return "content_update", f"General body copy updated across {total_changes} sections ({round((1.0 - similarity) * 100, 1)}% variance)."
