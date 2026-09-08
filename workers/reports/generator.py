from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

@dataclass
class SwotEntry:
    category: str  # "strength" | "weakness" | "opportunity" | "threat"
    title: str
    description: str
    impact: str    # "high" | "medium" | "low"

@dataclass
class ExecutiveBriefData:
    health_score: int               # 0 - 100
    risk_level: str                 # "Low Risk" | "Moderate Attention" | "High Threat"
    pillar_scores: dict[str, int]   # "seo", "pricing", "sentiment", "agility", "advertising"
    kpi_highlights: dict[str, Any]
    swot: list[dict[str, Any]]
    recommendations: list[str]
    ai_narrative: str
    confidence_score: float         # 0.0 - 100.0 (Data density confidence)

class ExecutiveReportGenerator:
    """
    Multi-source intelligence aggregator and executive synthesis engine.
    Correlates SEO performance, catalog pricing parity, website change frequency,
    social reputation sentiment, and paid ad spend velocity into a unified executive brief.
    """

    def generate_brief(
        self,
        brand_name: str,
        brand_domain: str,
        seo_data: dict[str, Any] | None = None,
        product_data: dict[str, Any] | None = None,
        change_data: dict[str, Any] | None = None,
        sentiment_data: dict[str, Any] | None = None,
        ad_data: dict[str, Any] | None = None
    ) -> ExecutiveBriefData:
        # Default fallbacks
        seo = seo_data or {}
        prod = product_data or {}
        chg = change_data or {}
        sent = sentiment_data or {}
        ads = ad_data or {}

        # 1. Compute Individual Pillar Performance (0 - 100 scale)
        # Pillar 1: SEO
        seo_score = int(seo.get("total_score") or 65)

        # Pillar 2: Pricing & Catalog Parity
        in_stock_pct = 100.0
        tot_products = prod.get("total_products", 0)
        if tot_products > 0:
            in_stock_pct = (prod.get("in_stock_count", 0) / tot_products) * 100.0
        pricing_score = min(100, int(in_stock_pct * 0.7 + (30 if tot_products > 0 else 15)))

        # Pillar 3: Sentiment & Reputation
        nss = sent.get("net_sentiment_score", 0.0)  # -100 to +100
        # Map -100..+100 to 0..100
        sentiment_score = max(0, min(100, int((nss + 100) / 2)))

        # Pillar 4: Change & Market Agility
        tot_changes = chg.get("total_changes", 0)
        # Moderate change is healthy agility (e.g. 5-20 changes = 85+)
        if 3 <= tot_changes <= 25:
            agility_score = 85
        elif tot_changes > 25:
            agility_score = 70
        else:
            agility_score = 50

        # Pillar 5: Advertising Footprint
        tot_ads = ads.get("total_ads", 0)
        evergreen_count = ads.get("evergreen_count", 0)
        ad_score = min(100, int((tot_ads * 4) + (evergreen_count * 12) + (30 if tot_ads > 0 else 0)))

        # 2. Composite Health Score (Weighted Multi-Pillar Blend)
        composite_health = int(
            (seo_score * 0.25) +
            (pricing_score * 0.20) +
            (sentiment_score * 0.25) +
            (agility_score * 0.15) +
            (ad_score * 0.15)
        )
        composite_health = max(0, min(100, composite_health))

        # Risk level determination
        if composite_health >= 75:
            risk_level = "Low Risk"
        elif composite_health >= 50:
            risk_level = "Moderate Attention"
        else:
            risk_level = "High Threat"

        # 3. Dynamic SWOT Matrix Generation
        swot_entries: list[SwotEntry] = []

        # Strengths
        if seo_score >= 75:
            swot_entries.append(SwotEntry(
                category="strength",
                title="Strong Technical & Content SEO Foundation",
                description=f"Overall SEO audit score is high ({seo_score}/100), ensuring robust organic discoverability.",
                impact="high"
            ))
        if nss >= 15:
            swot_entries.append(SwotEntry(
                category="strength",
                title="Favorable Consumer Net Sentiment",
                description=f"Net Sentiment Score is positive (+{nss}), indicating strong customer loyalty and word-of-mouth.",
                impact="high"
            ))
        if evergreen_count >= 1:
            swot_entries.append(SwotEntry(
                category="strength",
                title="Proven Evergreen Ad Campaigns",
                description=f"Brand operates {evergreen_count} high-converting evergreen ad campaigns active for over 45 days.",
                impact="medium"
            ))
        if not swot_entries:
            swot_entries.append(SwotEntry(
                category="strength",
                title="Established Digital Footprint",
                description=f"Active online presence indexed at {brand_domain}.",
                impact="medium"
            ))

        # Weaknesses
        if seo_score < 60:
            swot_entries.append(SwotEntry(
                category="weakness",
                title="Sub-Optimal Search Architecture",
                description=f"SEO score ({seo_score}/100) indicates underlying technical issues or missing schema markup.",
                impact="high"
            ))
        if nss < 0:
            swot_entries.append(SwotEntry(
                category="weakness",
                title="Negative Brand Sentiment Headwinds",
                description=f"Net sentiment is negative ({nss}), reflecting consumer friction around service or product quality.",
                impact="high"
            ))
        if tot_ads == 0:
            swot_entries.append(SwotEntry(
                category="weakness",
                title="Absence of Paid Advertising Footprint",
                description="Zero observed paid search or social media ad campaigns, yielding traffic share to rivals.",
                impact="medium"
            ))
        if not any(s.category == "weakness" for s in swot_entries):
            swot_entries.append(SwotEntry(
                category="weakness",
                title="Catalog Visibility Gaps",
                description="Opportunities remain to expand structured product markup and review syndication.",
                impact="low"
            ))

        # Opportunities
        if ads.get("platform_distribution") and len(ads.get("platform_distribution", [])) == 1:
            swot_entries.append(SwotEntry(
                category="opportunity",
                title="Multi-Channel Paid Media Diversification",
                description="Currently concentrated in one ad network; expanding to Meta or LinkedIn can unlock net-new customer segments.",
                impact="high"
            ))
        if tot_changes > 0:
            swot_entries.append(SwotEntry(
                category="opportunity",
                title="Agile Value Proposition Iteration",
                description="Recent messaging adjustments provide testing opportunities to optimize landing page conversion rates.",
                impact="medium"
            ))
        swot_entries.append(SwotEntry(
                category="opportunity",
                title="Reputation-Driven Marketing Copy",
                description="Incorporate positive customer quotes directly into digital ad creatives to accelerate social proof.",
                impact="medium"
        ))

        # Threats
        if tot_changes >= 10:
            swot_entries.append(SwotEntry(
                category="threat",
                title="Aggressive Competitor Market Repositioning",
                description="High velocity of competitor website and pricing shifts signals imminent rival campaign pushes.",
                impact="high"
            ))
        if ads.get("evergreen_count", 0) >= 3:
            swot_entries.append(SwotEntry(
                category="threat",
                title="Entrenched Competitor Paid Domination",
                description="Competitors maintain seasoned evergreen ads with high budget velocity.",
                impact="high"
            ))
        if not any(s.category == "threat" for s in swot_entries):
            swot_entries.append(SwotEntry(
                category="threat",
                title="Fluctuating Paid Auction Costs",
                description="Rising cost-per-click across Google and Meta ad auctions demands disciplined bid management.",
                impact="medium"
            ))

        # 4. Actionable Strategic Recommendations
        recommendations = [
            f"Address top technical SEO warnings on {brand_domain} to elevate organic ranking velocity.",
            "A/B test top-performing competitor Call-to-Actions ('Free Trial' / 'Book A Demo') on core landing pages.",
            "Leverage positive sentiment themes in upcoming paid acquisition campaigns to lower customer acquisition costs (CAC).",
            "Monitor rival pricing changes weekly to maintain price index parity across key product lines."
        ]

        # 5. Compute Confidence Score (based on data density)
        data_points = (1 if seo_score else 0) + (1 if tot_products > 0 else 0) + (1 if nss != 0.0 else 0) + (1 if tot_changes > 0 else 0) + (1 if tot_ads > 0 else 0)
        confidence_score = round((data_points / 5.0) * 100.0, 1)

        # 6. Executive AI Narrative (Data -> Analysis -> Insights -> Recommendations)
        ai_narrative = (
            f"### Data\n"
            f"- **SEO**: {seo_score}/100 total score.\n"
            f"- **Catalog**: {tot_products} products ({in_stock_pct:.1f}% in-stock).\n"
            f"- **Sentiment**: Net Sentiment Score {nss:+0.1f}.\n"
            f"- **Ads**: {tot_ads} active ad creatives ({evergreen_count} evergreen).\n\n"
            
            f"### Analysis\n"
            f"{brand_name} achieves a Composite Health Score of **{composite_health}/100** ({risk_level}). "
            f"Performance across the 5 pillars indicates a {'strong' if composite_health >= 75 else 'moderate' if composite_health >= 50 else 'weak'} market posture. "
            f"Analytical confidence is {confidence_score}% based on cross-module data density.\n\n"
            
            f"### Insights\n"
            f"Key strengths lie in {'SEO and brand awareness' if seo_score >= 75 else 'product catalog depth'} while primary threats "
            f"emerge from {'competitor ad spend' if tot_ads == 0 else 'shifting search algorithms'}. "
            f"The current operating risk is assessed as {risk_level}.\n\n"
            
            f"### Recommendations\n"
        )
        for rec in recommendations:
            ai_narrative += f"- {rec}\n"

        return ExecutiveBriefData(
            health_score=composite_health,
            risk_level=risk_level,
            pillar_scores={
                "seo": seo_score,
                "pricing": pricing_score,
                "sentiment": sentiment_score,
                "agility": agility_score,
                "advertising": ad_score
            },
            kpi_highlights={
                "seo_score": seo_score,
                "net_sentiment_score": nss,
                "total_products": tot_products,
                "total_changes": tot_changes,
                "total_ads": tot_ads,
                "evergreen_ads": evergreen_count,
                "estimated_monthly_spend": ads.get("estimated_monthly_spend_range", "$0")
            },
            swot=[
                {
                    "category": s.category,
                    "title": s.title,
                    "description": s.description,
                    "impact": s.impact
                }
                for s in swot_entries
            ],
            recommendations=recommendations,
            ai_narrative=ai_narrative,
            confidence_score=confidence_score
        )
