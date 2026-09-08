from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.brand import Brand
from app.models.mention import Mention
from app.models.sentiment import Sentiment

@pytest.mark.asyncio
async def test_mentions_api_endpoints():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Quick ad-hoc text analysis
        resp_adhoc = await client.post(
            "/api/v1/mentions/analyze-text",
            json={"text": "Outstanding platform with great customer support and fast response!"}
        )
        assert resp_adhoc.status_code == 200
        data_adhoc = resp_adhoc.json()
        assert data_adhoc["label"] == "positive"
        assert data_adhoc["compound_score"] > 0.4

        # 2. Ingest mention for non-existent brand -> 404
        mock_db.get.return_value = None
        fake_id = uuid4()
        resp_404 = await client.post(
            f"/api/v1/mentions/brand/{fake_id}",
            json={
                "source": "twitter",
                "content": "Terrible downtime and slow app today!",
                "author": "@tech_user"
            }
        )
        assert resp_404.status_code == 404

        # 3. Ingest mention for valid brand -> 201 Created
        fake_brand = Brand(id=fake_id, name="TestCo", domain="testco.com")
        mock_db.get.return_value = fake_brand

        resp_create = await client.post(
            f"/api/v1/mentions/brand/{fake_id}",
            json={
                "source": "twitter",
                "content": "Terrible downtime and slow app today! Crashes constantly.",
                "author": "@tech_user"
            }
        )
        assert resp_create.status_code == 201
        created_mention = resp_create.json()
        assert created_mention["source"] == "twitter"
        assert created_mention["sentiment"]["label"] == "negative"

        # 4. List mentions for brand -> 200 OK
        mention_id = uuid4()
        test_m = Mention(
            id=mention_id,
            brand_id=fake_id,
            source="twitter",
            source_url="https://twitter.com/post/1",
            content="Great product!",
            author="@fan",
            published_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc)
        )
        test_s = Sentiment(
            id=uuid4(),
            mention_id=mention_id,
            label="positive",
            positive_score=0.8,
            negative_score=0.0,
            neutral_score=0.2,
            model_version="lexicon-vader-v1",
            created_at=datetime.now(timezone.utc)
        )
        test_m.sentiment = test_s

        mock_exec_count = MagicMock()
        mock_exec_count.scalar_one.return_value = 1
        mock_exec_items = MagicMock()
        mock_exec_items.scalars.return_value.all.return_value = [test_m]
        mock_db.execute.side_effect = [mock_exec_count, mock_exec_items]

        resp_list = await client.get(f"/api/v1/mentions/brand/{fake_id}?page=1&size=20")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert list_data["total"] == 1
        assert len(list_data["items"]) == 1
        assert list_data["items"][0]["sentiment"]["label"] == "positive"

        # 5. Get reputation analytics -> 200 OK
        mock_db.execute.side_effect = None
        mock_exec_all = MagicMock()
        mock_exec_all.scalars.return_value.all.return_value = [test_m]
        mock_db.execute.return_value = mock_exec_all

        resp_analytics = await client.get(f"/api/v1/mentions/brand/{fake_id}/analytics")
        assert resp_analytics.status_code == 200
        analytics = resp_analytics.json()
        assert analytics["total_mentions"] == 1
        assert analytics["positive_count"] == 1
        assert analytics["net_sentiment_score"] == 100.0
        assert len(analytics["sources_breakdown"]) >= 1

        # 6. Seed mentions for brand -> 201 Created
        resp_seed = await client.post(f"/api/v1/mentions/brand/{fake_id}/seed")
        assert resp_seed.status_code == 201
        seed_data = resp_seed.json()
        assert seed_data["status"] == "success"
        assert seed_data["count"] >= 15
        assert seed_data["brand_id"] == str(fake_id)
