from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.brand import Brand
from app.models.report import Report

@pytest.mark.asyncio
async def test_reports_api_endpoints():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_db.delete = AsyncMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # 1. Non-existent brand -> 404
        mock_db.get.return_value = None
        fake_id = uuid4()
        resp_404 = await client.post(
            f"/api/v1/reports/brand/{fake_id}/generate",
            json={"report_type": "executive_brief"}
        )
        assert resp_404.status_code == 404

        # 2. Valid brand -> Generate report -> 201 Created
        fake_brand = Brand(id=fake_id, name="ApexCloud", domain="apexcloud.com")
        mock_db.get.return_value = fake_brand

        # Mock query results for SEO, products, changes, mentions, ads
        mock_seo_exec = MagicMock()
        mock_seo_exec.scalar_one_or_none.return_value = None
        
        mock_prod_exec = MagicMock()
        mock_prod_exec.scalars.return_value.all.return_value = []

        mock_chg_exec = MagicMock()
        mock_chg_exec.scalars.return_value.all.return_value = []

        mock_ment_exec = MagicMock()
        mock_ment_exec.scalars.return_value.all.return_value = []

        mock_ad_exec = MagicMock()
        mock_ad_exec.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [
            mock_seo_exec,
            mock_prod_exec,
            mock_chg_exec,
            mock_ment_exec,
            mock_ad_exec
        ]

        resp_generate = await client.post(
            f"/api/v1/reports/brand/{fake_id}/generate",
            json={"report_type": "executive_brief"}
        )
        assert resp_generate.status_code == 201
        data_gen = resp_generate.json()
        assert "Executive intelligence brief" in data_gen["message"]
        assert data_gen["report"]["brand_id"] == str(fake_id)
        assert data_gen["report"]["content"]["health_score"] >= 0

        # 3. List reports for brand -> 200 OK
        report_id = uuid4()
        now = datetime.now(timezone.utc)
        rep_obj = Report(
            id=report_id,
            brand_id=fake_id,
            report_type="executive_brief",
            content={"health_score": 85, "risk_level": "Low Risk"},
            ai_narrative="Strong performance",
            generated_at=now,
            created_at=now
        )

        mock_count = MagicMock()
        mock_count.scalar_one.return_value = 1
        mock_items = MagicMock()
        mock_items.scalars.return_value.all.return_value = [rep_obj]
        mock_db.execute.side_effect = [mock_count, mock_items]

        resp_list = await client.get(f"/api/v1/reports/brand/{fake_id}?page=1&size=20")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert list_data["total"] == 1
        assert len(list_data["items"]) == 1

        # 4. Get specific report detail -> 200 OK
        mock_db.get.return_value = rep_obj
        resp_detail = await client.get(f"/api/v1/reports/{report_id}")
        assert resp_detail.status_code == 200
        assert resp_detail.json()["id"] == str(report_id)

        # 5. Delete report -> 204 No Content
        resp_del = await client.delete(f"/api/v1/reports/{report_id}")
        assert resp_del.status_code == 204
