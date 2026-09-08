from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import date, timedelta, datetime, timezone

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.brand import Brand
from app.models.ad_intel import AdIntel

@pytest.mark.asyncio
async def test_ads_api_endpoints():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Test parse-preview endpoint
        resp_preview = await client.post(
            "/api/v1/ads/parse-preview",
            json={
                "raw_text": "Scale Your Team - The Leading DevOps Platform. Try for free today.",
                "target_url": "https://devops.io/trial?utm_source=meta&utm_medium=paid_social"
            }
        )
        assert resp_preview.status_code == 200
        data_preview = resp_preview.json()
        assert data_preview["headline"] == "Scale Your Team"
        assert data_preview["cta"] == "Try For Free"
        assert data_preview["landing_page_domain"] == "devops.io"
        assert data_preview["utm_parameters"].get("utm_source") == "meta"

        # 2. Ingest ad for non-existent brand -> 404
        mock_db.get.return_value = None
        fake_id = uuid4()
        resp_404 = await client.post(
            f"/api/v1/ads/brand/{fake_id}",
            json={
                "platform": "google",
                "ad_text": "Buy Widget X - 20% off today",
                "ad_format": "search"
            }
        )
        assert resp_404.status_code == 404

        # 3. Ingest ad for valid brand -> 201 Created
        fake_brand = Brand(id=fake_id, name="AdCo", domain="adco.com")
        mock_db.get.return_value = fake_brand

        today = date.today()
        first_date = today - timedelta(days=60)

        resp_create = await client.post(
            f"/api/v1/ads/brand/{fake_id}",
            json={
                "platform": "google",
                "ad_text": "Enterprise Data Hub\nUnify all company metrics. Book a demo today.",
                "ad_format": "search",
                "first_seen": first_date.isoformat(),
                "last_seen": today.isoformat(),
                "target_url": "https://adco.com/demo"
            }
        )
        assert resp_create.status_code == 201
        created_ad = resp_create.json()
        assert created_ad["platform"] == "google"
        assert created_ad["headline"] == "Enterprise Data Hub"
        assert created_ad["cta"] == "Book A Demo"
        assert created_ad["is_evergreen"] is True
        assert created_ad["spend_tier"] == "Evergreen Winner"

        # 4. List ads for brand -> 200 OK
        ad_obj = AdIntel(
            id=uuid4(),
            brand_id=fake_id,
            platform="google",
            ad_text="Enterprise Data Hub\nUnify metrics.",
            ad_format="search",
            target_url="https://adco.com/demo",
            first_seen=first_date,
            last_seen=today,
            targeting_info={"headline": "Enterprise Data Hub", "cta": "Book A Demo"},
            data_source_tag="manual_ingest",
            created_at=datetime.now(timezone.utc)
        )

        mock_exec_count = MagicMock()
        mock_exec_count.scalar_one.return_value = 1
        mock_exec_items = MagicMock()
        mock_exec_items.scalars.return_value.all.return_value = [ad_obj]
        mock_db.execute.side_effect = [mock_exec_count, mock_exec_items]

        resp_list = await client.get(f"/api/v1/ads/brand/{fake_id}?page=1&size=20")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert list_data["total"] == 1
        assert len(list_data["items"]) == 1
        assert list_data["items"][0]["platform"] == "google"

        # 5. Get ad intelligence analytics -> 200 OK
        mock_db.execute.side_effect = None
        mock_exec_all = MagicMock()
        mock_exec_all.scalars.return_value.all.return_value = [ad_obj]
        mock_db.execute.return_value = mock_exec_all

        resp_analytics = await client.get(f"/api/v1/ads/brand/{fake_id}/analytics")
        assert resp_analytics.status_code == 200
        analytics = resp_analytics.json()
        assert analytics["total_ads"] == 1
        assert analytics["evergreen_count"] == 1
        assert len(analytics["platform_distribution"]) == 1
        assert analytics["platform_distribution"][0]["platform"] == "google"
