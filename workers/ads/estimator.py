from __future__ import annotations
from datetime import date, datetime
from collections import Counter
from dataclasses import dataclass
from typing import Any

@dataclass
class AdLongevityTier:
    longevity_days: int
    tier_label: str             # "Testing / Pilot", "Active Campaign", "Scaling Campaign", "Evergreen Winner"
    estimated_spend_range: str  # "$100 - $1,000", etc.
    is_evergreen: bool

class AdSpendEstimator:
    """
    Longevity-based ad spend and campaign efficacy estimator.
    In digital advertising (Google/Meta/LinkedIn), advertisers ruthlessly turn off
    unprofitable ad creatives within 3-7 days. Ads that remain active for 30-90+ days
    are top-performing 'evergreen' revenue drivers with significant continuous ad spend.
    """

    @staticmethod
    def calculate_longevity_and_tier(
        first_seen: date | datetime | None,
        last_seen: date | datetime | None
    ) -> AdLongevityTier:
        if not first_seen:
            return AdLongevityTier(
                longevity_days=1,
                tier_label="Testing / Pilot",
                estimated_spend_range="$100 - $1,000",
                is_evergreen=False
            )

        f_date = first_seen.date() if isinstance(first_seen, datetime) else first_seen
        l_date = (last_seen.date() if isinstance(last_seen, datetime) else last_seen) if last_seen else date.today()

        days = max(1, (l_date - f_date).days + 1)

        if days <= 3:
            return AdLongevityTier(
                longevity_days=days,
                tier_label="Testing / Pilot",
                estimated_spend_range="$100 - $1,000",
                is_evergreen=False
            )
        elif days <= 14:
            return AdLongevityTier(
                longevity_days=days,
                tier_label="Active Campaign",
                estimated_spend_range="$1,000 - $5,000",
                is_evergreen=False
            )
        elif days <= 45:
            return AdLongevityTier(
                longevity_days=days,
                tier_label="Scaling Campaign",
                estimated_spend_range="$5,000 - $25,000",
                is_evergreen=False
            )
        else:
            return AdLongevityTier(
                longevity_days=days,
                tier_label="Evergreen Winner",
                estimated_spend_range="$25,000+",
                is_evergreen=True
            )

    @classmethod
    def aggregate_brand_ad_intelligence(
        cls,
        ads: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Compute high-level ad media mix, spend tier breakdown, and campaign insights.
        """
        total = len(ads)
        if total == 0:
            return {
                "total_ads": 0,
                "evergreen_count": 0,
                "platform_distribution": [],
                "format_distribution": [],
                "spend_tier_distribution": [],
                "top_ctas": [],
                "top_landing_domains": [],
                "estimated_monthly_spend_range": "$0"
            }

        platforms_counter: Counter[str] = Counter()
        formats_counter: Counter[str] = Counter()
        tiers_counter: Counter[str] = Counter()
        ctas_counter: Counter[str] = Counter()
        domains_counter: Counter[str] = Counter()
        evergreen_count = 0

        for ad in ads:
            platform = (ad.get("platform") or "unknown").lower()
            platforms_counter[platform] += 1

            fmt = (ad.get("ad_format") or "search").lower()
            formats_counter[fmt] += 1

            f_seen = ad.get("first_seen")
            l_seen = ad.get("last_seen")
            tier_info = cls.calculate_longevity_and_tier(f_seen, l_seen)
            tiers_counter[tier_info.tier_label] += 1
            if tier_info.is_evergreen:
                evergreen_count += 1

            targeting = ad.get("targeting_info") or {}
            cta = targeting.get("cta")
            if cta:
                ctas_counter[cta] += 1

            domain = targeting.get("landing_page_domain")
            if domain:
                domains_counter[domain] += 1

        # Platform distribution with percentages
        platform_dist = [
            {
                "platform": p,
                "count": count,
                "percentage": round((count / total) * 100, 1)
            }
            for p, count in platforms_counter.most_common()
        ]

        # Format distribution with percentages
        format_dist = [
            {
                "format": f,
                "count": count,
                "percentage": round((count / total) * 100, 1)
            }
            for f, count in formats_counter.most_common()
        ]

        # Tier distribution
        tier_dist = [
            {
                "tier": t,
                "count": count,
                "percentage": round((count / total) * 100, 1)
            }
            for t, count in tiers_counter.most_common()
        ]

        # Top CTAs
        top_ctas = [
            {"cta": c, "count": count}
            for c, count in ctas_counter.most_common(5)
        ]

        # Top Landing Domains
        top_domains = [
            {"domain": d, "count": count}
            for d, count in domains_counter.most_common(5)
        ]

        # Overall estimated monthly spend range heuristic
        if evergreen_count >= 5 or total >= 20:
            est_monthly = "$25,000 - $100,000+"
        elif evergreen_count >= 2 or total >= 10:
            est_monthly = "$10,000 - $25,000"
        elif total >= 3:
            est_monthly = "$2,500 - $10,000"
        else:
            est_monthly = "$500 - $2,500"

        return {
            "total_ads": total,
            "evergreen_count": evergreen_count,
            "platform_distribution": platform_dist,
            "format_distribution": format_dist,
            "spend_tier_distribution": tier_dist,
            "top_ctas": top_ctas,
            "top_landing_domains": top_domains,
            "estimated_monthly_spend_range": est_monthly
        }
