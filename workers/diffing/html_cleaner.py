from __future__ import annotations
import re
from bs4 import BeautifulSoup, Comment
from typing import List, Tuple

# Tags that typically contain dynamic, non-content noise or styling
NOISE_TAGS = {
    'script', 'style', 'noscript', 'svg', 'canvas', 'iframe',
    'form', 'input', 'button', 'select', 'textarea'
}

# Attributes that often change on every page load without real content changes
DYNAMIC_ATTRS = {
    'data-reactid', 'data-rh', 'data-nonce', 'nonce', 'csrf-token',
    'data-csrftoken', 'data-timestamp', 'aria-describedby', 'tabindex'
}

class HtmlCleaner:
    """
    Normalizes HTML snapshots by stripping ephemeral noise, scripts, dynamic tokens,
    and whitespace variance to enable deterministic, signal-rich visual and textual diffing.
    """

    @classmethod
    def clean(cls, raw_html: str) -> Tuple[str, List[str]]:
        """
        Cleans the input HTML and returns:
        1. Cleaned simplified HTML
        2. Normalized list of content text lines
        """
        if not raw_html or not raw_html.strip():
            return "", []

        soup = BeautifulSoup(raw_html, 'lxml')

        # 1. Remove all HTML comments
        for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
            comment.extract()

        # 2. Remove noise tags
        for tag in soup.find_all(NOISE_TAGS):
            tag.decompose()

        # 3. Strip dynamic / ephemeral attributes
        for tag in soup.find_all(True):
            for attr in list(tag.attrs.keys()):
                if attr.lower() in DYNAMIC_ATTRS or attr.lower().startswith('data-analytics'):
                    del tag.attrs[attr]

        # 4. Extract meaningful text lines
        # Target headings, paragraphs, list items, spans, table cells
        text_blocks: List[str] = []
        target_tags = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'td', 'th', 'a', 'span', 'blockquote'])

        for el in target_tags:
            t = el.get_text(strip=True)
            if t and len(t) > 2:
                # Collapse repeated whitespace
                t = re.sub(r'\s+', ' ', t)
                # Avoid duplicate exact lines back-to-back
                if not text_blocks or text_blocks[-1] != t:
                    text_blocks.append(t)

        # 5. Build clean simplified HTML representation
        # If body exists, format body, otherwise full soup
        target = soup.body or soup
        cleaned_html = str(target)
        # Collapse multiple newlines/spaces in HTML
        cleaned_html = re.sub(r'\n\s*\n', '\n', cleaned_html).strip()

        return cleaned_html, text_blocks
