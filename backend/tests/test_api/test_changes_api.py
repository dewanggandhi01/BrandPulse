from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.snapshot import Snapshot
from app.models.change_event import ChangeEvent

SNAP_HTML_1 = "<html><body><h1>Original Headline</h1><p>Our solution costs $50/mo.</p></body></html>"
SNAP_HTML_2 = "<html><body><h1>New Revolutionary Headline</h1><p>Our solution costs $79/mo.</p></body></html>"

@pytest.mark.asyncio
async def test_changes_api_endpoints():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        brand_id = uuid4()
        snap1_id = uuid4()
        snap2_id = uuid4()
        change_id = uuid4()

        fake_event = ChangeEvent(
            id=change_id,
            snapshot_id=snap2_id,
            previous_snapshot_id=snap1_id,
            change_type="messaging_pivot",
            similarity_ratio=0.75,
            diff_details={"additions_count": 2, "deletions_count": 2, "total_changes": 4, "diff_chunks": []},
            ai_summary="Primary headline pivoted from 'Original Headline' to 'New Revolutionary Headline'.",
            created_at=datetime.now(timezone.utc)
        )

        # 1. List brand changes -> 200 OK
        mock_exec_list = MagicMock()
        mock_exec_list.scalar.return_value = 1
        mock_exec_list.scalars.return_value.all.return_value = [fake_event]
        mock_db.execute.return_value = mock_exec_list

        resp_list = await client.get(f"/api/v1/changes/brand/{brand_id}")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert list_data["total"] == 1
        assert list_data["items"][0]["change_type"] == "messaging_pivot"

        # 2. Get change detail -> 200 OK
        mock_db.get.return_value = fake_event
        resp_detail = await client.get(f"/api/v1/changes/{change_id}")
        assert resp_detail.status_code == 200
        detail_data = resp_detail.json()
        assert detail_data["id"] == str(change_id)
        assert "diff_details" in detail_data

        # 3. Analytics summary -> 200 OK
        mock_exec_agg = MagicMock()
        mock_exec_agg.all.return_value = [("messaging_pivot", 1, 0.75)]
        mock_db.execute.return_value = mock_exec_agg

        resp_analytics = await client.get(f"/api/v1/changes/brand/{brand_id}/analytics")
        assert resp_analytics.status_code == 200
        analytics_data = resp_analytics.json()
        assert analytics_data["total_changes"] == 1
        assert analytics_data["messaging_pivots_count"] == 1

        # 4. Compare on-demand -> 201 Created
        snap1 = Snapshot(
            id=snap1_id,
            content_hash="hash1",
            html_size=100,
            status_code=200,
            html_path=SNAP_HTML_1,
            captured_at=datetime.now(timezone.utc)
        )
        snap2 = Snapshot(
            id=snap2_id,
            content_hash="hash2",
            html_size=110,
            status_code=200,
            html_path=SNAP_HTML_2,
            captured_at=datetime.now(timezone.utc)
        )

        def mock_get_snapshot(model, target_id):
            if target_id == snap1_id:
                return snap1
            if target_id == snap2_id:
                return snap2
            return fake_event

        mock_db.get.side_effect = mock_get_snapshot

        resp_comp = await client.post("/api/v1/changes/compare", json={
            "snapshot_id": str(snap2_id),
            "previous_snapshot_id": str(snap1_id)
        })
        assert resp_comp.status_code == 201
        comp_data = resp_comp.json()
        assert comp_data["change_type"] in ["messaging_pivot", "pricing_change"]
        assert "diff_details" in comp_data
