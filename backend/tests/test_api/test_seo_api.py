from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.brand import Brand, BrandUrl
from app.models.snapshot import Snapshot
from app.models.seo_audit import SeoAudit

@pytest.mark.asyncio
async def test_seo_audit_api():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        brand_id = uuid4()
        fake_brand = Brand(id=brand_id, name="Acme Corp", domain="acme.com")
        mock_db.get.return_value = fake_brand

        # 1. Run audit when brand has empty domain -> 400 Bad Request
        mock_db.get.return_value = Brand(id=brand_id, name="Acme Corp", domain="")
        mock_exec = MagicMock()
        mock_exec.first.return_value = None
        mock_db.execute.return_value = mock_exec

        resp = await client.post(f"/api/v1/seo/brands/{brand_id}/seo-audit/run")
        assert resp.status_code == 400

        # 2. Run audit when snapshot exists -> 201 Created
        mock_db.get.return_value = fake_brand
        fake_url = BrandUrl(id=uuid4(), brand_id=brand_id, url="https://acme.com")
        fake_snap = Snapshot(
            id=uuid4(),
            brand_url_id=fake_url.id,
            content_hash="abc",
            html_size=120,
            status_code=200,
            html_path="<html><head><title>Acme Corp Official</title></head><body><h1>Welcome</h1></body></html>",
            captured_at=datetime.now(timezone.utc)
        )
        mock_exec2 = MagicMock()
        mock_exec2.first.return_value = (fake_snap, fake_url)
        mock_db.execute.return_value = mock_exec2

        resp2 = await client.post(f"/api/v1/seo/brands/{brand_id}/seo-audit/run")
        assert resp2.status_code == 201
        data = resp2.json()
        assert "total_score" in data
        assert "technical_scores" in data
        assert "content_scores" in data

        # 3. Get latest audit
        mock_exec_latest = MagicMock()
        fake_audit = SeoAudit(
            id=uuid4(),
            snapshot_id=fake_snap.id,
            total_score=85,
            technical_scores={"score": 90},
            content_scores={"score": 85},
            structured_data_scores={"score": 75},
            link_scores={"score": 80},
            issues=[],
            audited_at=datetime.now(timezone.utc)
        )
        mock_exec_latest.scalar_one_or_none.return_value = fake_audit
        mock_db.execute.return_value = mock_exec_latest

        resp3 = await client.get(f"/api/v1/seo/brands/{brand_id}/seo-audit/latest")
        assert resp3.status_code == 200
        assert resp3.json()["total_score"] == 85
