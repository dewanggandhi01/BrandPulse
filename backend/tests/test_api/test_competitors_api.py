from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.brand import Brand
from app.models.competitor import Competitor

@pytest.mark.asyncio
async def test_competitors_api():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        brand1_id = uuid4()
        brand2_id = uuid4()
        link_id = uuid4()

        brand1 = Brand(id=brand1_id, name="Target Brand", domain="target.com")
        brand2 = Brand(id=brand2_id, name="Rival Corp", domain="rival.com")

        # 1. Self-link rejected -> 400 Bad Request
        resp_self = await client.post(
            f"/api/v1/competitors/brand/{brand1_id}/link",
            json={"competitor_brand_id": str(brand1_id)}
        )
        assert resp_self.status_code == 400

        # 2. Link competitor brand -> 201 Created
        def mock_get(model, item_id):
            if item_id == brand1_id:
                return brand1
            if item_id == brand2_id:
                return brand2
            return None

        mock_db.get.side_effect = mock_get
        mock_exec_exist = MagicMock()
        mock_exec_exist.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_exec_exist

        resp_link = await client.post(
            f"/api/v1/competitors/brand/{brand1_id}/link",
            json={"competitor_brand_id": str(brand2_id)}
        )
        assert resp_link.status_code == 201
        data = resp_link.json()
        assert data["competitor_name"] == "Rival Corp"
        assert data["competitor_domain"] == "rival.com"

        # 3. List linked competitors -> 200 OK
        comp_obj = Competitor(
            id=link_id,
            brand_id=brand1_id,
            competitor_brand_id=brand2_id,
            created_at=datetime.now(timezone.utc)
        )
        mock_exec_list = MagicMock()
        mock_exec_list.all.return_value = [(comp_obj, brand2)]
        mock_db.execute.return_value = mock_exec_list

        resp_list = await client.get(f"/api/v1/competitors/brand/{brand1_id}")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert len(list_data) == 1
        assert list_data[0]["competitor_name"] == "Rival Corp"

        # 4. Compare matrix -> 200 OK
        mock_exec_compare = MagicMock()
        # Mocking queries inside _get_brand_profile:
        # 1st execute for SEO audit: scalar_one_or_none
        mock_exec_compare.scalar_one_or_none.return_value = None
        # 2nd execute for products: first -> (10, 150.0, 50.0, 300.0)
        mock_exec_compare.first.return_value = (10, 150.0, 50.0, 300.0)
        # 3rd execute for in-stock count: scalar -> 8
        mock_exec_compare.scalar.return_value = 8
        # Competitor IDs query: scalars -> [brand2_id]
        mock_exec_compare.scalars.return_value.all.return_value = [brand2_id]

        mock_db.execute.return_value = mock_exec_compare

        resp_matrix = await client.get(f"/api/v1/competitors/brand/{brand1_id}/compare")
        assert resp_matrix.status_code == 200
        matrix_data = resp_matrix.json()
        assert "target_brand" in matrix_data
        assert "competitors" in matrix_data
        assert "radar_data" in matrix_data
        assert len(matrix_data["radar_data"]) == 4  # 4 SEO pillars

        # 5. Unlink competitor -> 204 No Content
        mock_db.get.side_effect = None
        mock_db.get.return_value = comp_obj
        resp_del = await client.delete(f"/api/v1/competitors/{link_id}")
        assert resp_del.status_code == 204
