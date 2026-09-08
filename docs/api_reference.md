# BrandPulse REST API Reference

Comprehensive specification of the BrandPulse REST API v1. All endpoints return RFC 9457 compliant error structures on non-2xx responses and standard JSON payloads.

Base URL Prefix: `/api/v1`

---

## Table of Contents
1. [System & Health](#1-system--health)
2. [Brand Management](#2-brand-management)
3. [Crawling & Snapshots](#3-crawling--snapshots)
4. [SEO Audit Engine](#4-seo-audit-engine)
5. [Products & Pricing Intelligence](#5-products--pricing-intelligence)
6. [Competitor Intelligence & Benchmarking](#6-competitor-intelligence--benchmarking)
7. [Website Change Detection & Diffing](#7-website-change-detection--diffing)
8. [Social Sentiment & Reputation](#8-social-sentiment--reputation)
9. [Ad Intelligence & Paid Media](#9-ad-intelligence--paid-media)
10. [Executive Reports & Insights](#10-executive-reports--insights)

---

## 1. System & Health

### `GET /api/v1/health`
Checks connectivity to PostgreSQL database and Redis caching/broker infrastructure.

**Response `200 OK`**:
```json
{
  "status": "healthy",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-09-05T14:30:00Z"
}
```

---

## 2. Brand Management

### `GET /api/v1/brands`
Retrieve paginated list of monitored brands.

**Query Parameters**:
- `page` (int, default: 1): Page number
- `size` (int, default: 20, max: 100): Page size

**Response `200 OK`**:
```json
[
  {
    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "ApexCloud",
    "domain": "apexcloud.com",
    "industry": "Cloud Infrastructure",
    "metadata": {},
    "created_at": "2026-09-05T12:00:00Z",
    "updated_at": "2026-09-05T12:00:00Z"
  }
]
```

### `POST /api/v1/brands`
Register a new brand for monitoring.

**Request Body**:
```json
{
  "name": "ApexCloud",
  "domain": "apexcloud.com",
  "industry": "Cloud Infrastructure",
  "metadata": {}
}
```

**Response `201 Created`**: Returns created `BrandRead` object.

### `GET /api/v1/brands/{id}`
Retrieve a specific brand by UUID.

### `DELETE /api/v1/brands/{id}`
Remove a brand and cascade associated audit history.

---

## 3. Crawling & Snapshots

### `POST /api/v1/scrape-jobs`
Submit a new scraping job into the Celery task queue.

**Request Body**:
```json
{
  "brand_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "target_url": "https://apexcloud.com",
  "job_type": "full_crawl",
  "config": {
    "tier": "tier1_http",
    "respect_robots": true,
    "max_depth": 2
  }
}
```

**Response `202 Accepted`**:
```json
{
  "job_id": "8fa85f64-5717-4562-b3fc-2c963f66afa6",
  "status": "pending",
  "message": "Scrape job submitted to scraping queue"
}
```

### `GET /api/v1/scrape-jobs/{job_id}`
Retrieve the status, progress metrics, and error state of a scrape job.

### `GET /api/v1/snapshots`
List stored HTML snapshots filtered by brand or scrape job.

---

## 4. SEO Audit Engine

### `POST /api/v1/seo/snapshot/{snapshot_id}/audit`
Trigger algorithmic 4-pillar SEO audit on a captured HTML snapshot.

**Response `201 Created`**:
```json
{
  "id": "7fa85f64-5717-4562-b3fc-2c963f66afa6",
  "snapshot_id": "6fa85f64-5717-4562-b3fc-2c963f66afa6",
  "total_score": 88,
  "technical_scores": { "score": 92, "meta_title": true, "meta_desc": true, "canonical": true },
  "content_scores": { "score": 85, "word_count": 1420, "heading_hierarchy": true },
  "structured_data_scores": { "score": 90, "json_ld_present": true, "schema_types": ["Product", "Organization"] },
  "link_scores": { "score": 85, "internal_links": 42, "external_links": 8 },
  "issues": [
    { "pillar": "content", "severity": "warning", "message": "Low image alt text coverage", "remediation": "Add alt tags to 3 images" }
  ],
  "audited_at": "2026-09-05T13:00:00Z"
}
```

### `GET /api/v1/seo/brand/{brand_id}/latest`
Get latest compiled SEO audit for a brand.

---

## 5. Products & Pricing Intelligence

### `POST /api/v1/products/extract/{snapshot_id}`
Execute multi-strategy extraction (JSON-LD -> Hydration -> DOM) on an HTML snapshot.

**Response `200 OK`**:
```json
{
  "extracted_count": 12,
  "data_source_tags": { "scraped_jsonld": 10, "scraped_dom": 2 },
  "products": [...]
}
```

### `GET /api/v1/products/brand/{brand_id}`
Query product catalog with pricing, stock availability, and time-series history.

**Query Parameters**:
- `availability` (optional): `in_stock`, `out_of_stock`, `preorder`
- `min_price` / `max_price` (optional): Price filters
- `search` (optional): Name / SKU text query

---

## 6. Competitor Intelligence & Benchmarking

### `POST /api/v1/competitors/{brand_id}/link/{competitor_brand_id}`
Link a rival brand to establish benchmarking relationship.

### `GET /api/v1/competitors/{brand_id}/matrix`
Retrieve multi-pillar comparison matrix comparing target brand with linked competitors.

**Response `200 OK`**:
```json
{
  "target_brand": { "brand_name": "ApexCloud", "seo_total_score": 88, "avg_price": 120.0, "product_count": 24 },
  "competitors": [
    { "brand_name": "CloudScale", "seo_total_score": 82, "avg_price": 135.0, "product_count": 19 }
  ],
  "price_index": 0.89,
  "radar_data": [
    { "pillar": "SEO Health", "ApexCloud": 88, "CloudScale": 82 },
    { "pillar": "Content Quality", "ApexCloud": 85, "CloudScale": 78 }
  ]
}
```

---

## 7. Website Change Detection & Diffing

### `POST /api/v1/changes/detect`
Compare two snapshots using DOM cleaner and SequenceMatcher comparator to classify revisions.

### `GET /api/v1/changes/brand/{brand_id}`
List categorized change events (`pricing_change`, `messaging_pivot`, `layout_overhaul`, `seo_change`, `minor_copy`).

### `GET /api/v1/changes/{change_id}`
Retrieve structured diff chunks and unified diff text.

---

## 8. Social Sentiment & Reputation

### `POST /api/v1/mentions`
Ingest social mention or customer review with automatic VADER-style sentiment classification.

**Request Body**:
```json
{
  "brand_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "source": "twitter",
  "source_url": "https://twitter.com/dev/status/123",
  "content": "Loving the new ApexCloud CLI, deployment speed is blazing fast! 🔥",
  "author": "dev_user"
}
```

### `GET /api/v1/mentions/brand/{brand_id}/analytics`
Returns Net Sentiment Score (NSS: -100 to +100), source breakdown, and extracted topic frequencies.

---

## 9. Ad Intelligence & Paid Media

### `POST /api/v1/ads`
Ingest ad creative metadata with automatic headline, CTA, and spend tier classification.

### `GET /api/v1/ads/brand/{brand_id}`
List paid ad creatives filtered by platform (`google`, `meta`, `linkedin`, `twitter`) and format (`search`, `display`, `video`).

### `GET /api/v1/ads/brand/{brand_id}/analytics`
Returns ad longevity breakdown (Pilot, Active, Scaling, Evergreen Winner) and estimated monthly spend ranges.

---

## 10. Executive Reports & Insights

### `POST /api/v1/reports/brand/{brand_id}/generate`
Synthesizes multi-pillar intelligence into an executive brief.

**Request Body**:
```json
{
  "report_type": "executive_brief"
}
```

**Response `201 Created`**:
```json
{
  "message": "Executive intelligence brief compiled successfully",
  "report": {
    "id": "2fa85f64-5717-4562-b3fc-2c963f66afa6",
    "brand_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "report_type": "executive_brief",
    "content": {
      "health_score": 82,
      "risk_level": "Low Risk",
      "pillar_scores": {
        "seo": 88,
        "pricing": 95,
        "sentiment": 80,
        "agility": 85,
        "advertising": 65
      },
      "kpi_highlights": {},
      "swot": [
        {
          "category": "strength",
          "title": "Robust Technical SEO Foundation",
          "description": "Composite SEO score exceeds 75% benchmark.",
          "impact": "high"
        }
      ],
      "recommendations": [
        "Sustain evergreen ad creatives to capitalize on stable customer acquisition."
      ]
    },
    "ai_narrative": "ApexCloud exhibits a strong competitive posture with an 82/100 Composite Health Score...",
    "generated_at": "2026-09-05T14:35:00Z"
  }
}
```

### `GET /api/v1/reports/brand/{brand_id}`
List historical executive briefs for a brand.

### `DELETE /api/v1/reports/{report_id}`
Delete an archived executive report.
