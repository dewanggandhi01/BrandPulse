from __future__ import annotations
import re
from urllib.parse import urlparse, parse_qs
from dataclasses import dataclass
from typing import Any

COMMON_CTAS = [
    "sign up", "get started", "learn more", "try for free", "free trial",
    "book a demo", "request demo", "shop now", "buy now", "contact us",
    "download now", "start free trial", "claim offer", "subscribe",
    "apply now", "schedule call", "see pricing", "explore"
]

@dataclass
class ParsedAdCreative:
    headline: str | None
    body_copy: str
    cta: str | None
    detected_format: str       # "search", "display", "video", "sponsored_feed"
    landing_page_domain: str | None
    utm_parameters: dict[str, str]

class AdCreativeParser:
    """
    Parser for competitor digital ad copy, creative headlines, call-to-actions (CTAs),
    and landing page campaign parameters.
    """

    def parse_ad(
        self,
        raw_text: str,
        target_url: str | None = None,
        suggested_format: str | None = None
    ) -> ParsedAdCreative:
        body = raw_text.strip() if raw_text else ""
        
        # 1. Extract headline if text contains multi-line structure or delimiters
        headline = None
        if "\n" in body:
            lines = [line.strip() for line in body.split("\n") if line.strip()]
            if lines:
                first_line = lines[0]
                if " - " in first_line:
                    headline = first_line.split(" - ", 1)[0].strip()
                elif " | " in first_line:
                    headline = first_line.split(" | ", 1)[0].strip()
                else:
                    headline = first_line
                body_copy = "\n".join(lines[1:]) if len(lines) > 1 else lines[0]
            else:
                body_copy = body
        elif " - " in body:
            parts = body.split(" - ", 1)
            headline = parts[0].strip()
            body_copy = parts[1].strip()
        elif " | " in body:
            parts = body.split(" | ", 1)
            headline = parts[0].strip()
            body_copy = parts[1].strip()
        else:
            # First sentence or up to 60 characters as headline if long
            if len(body) > 70:
                sentences = re.split(r"[.!?]\s+", body, 1)
                headline = sentences[0].strip()
                body_copy = body
            else:
                headline = body
                body_copy = body

        # 2. Extract Call-To-Action (CTA)
        found_cta = None
        lower_body = body.lower()
        for cta in COMMON_CTAS:
            pattern = rf"\b{re.escape(cta)}\b"
            if re.search(pattern, lower_body):
                found_cta = cta.title()
                break

        # 3. Detect format heuristic if not explicitly supplied
        detected_format = suggested_format.lower() if suggested_format else "search"
        if not suggested_format or suggested_format.lower() in ("auto", "unknown"):
            if "video" in lower_body or "watch" in lower_body:
                detected_format = "video"
            elif len(body) > 180 or "#" in body:
                detected_format = "sponsored_feed"
            elif len(body) <= 90:
                detected_format = "search"
            else:
                detected_format = "display"

        # 4. Extract target landing page and UTM campaign tags
        landing_domain = None
        utm_params: dict[str, str] = {}
        if target_url:
            try:
                parsed_url = urlparse(target_url)
                landing_domain = parsed_url.netloc or None
                query_params = parse_qs(parsed_url.query)
                for k, v in query_params.items():
                    if k.startswith("utm_") and v:
                        utm_params[k] = v[0]
            except Exception:
                pass

        return ParsedAdCreative(
            headline=headline,
            body_copy=body_copy,
            cta=found_cta,
            detected_format=detected_format,
            landing_page_domain=landing_domain,
            utm_parameters=utm_params
        )
