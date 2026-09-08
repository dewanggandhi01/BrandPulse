from __future__ import annotations
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime, timezone
from decimal import Decimal

from app.main import create_app
from app.api.deps import get_db, get_redis
from app.models.brand import Brand, BrandUrl
from app.models.snapshot import Snapshot
from app.models.product import Product
from app.models.price_history import PriceHistory

HTML_SAMPLE = """
<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "CloudPro Enterprise Suite",
      "sku": "CP-ENT-99",
      "offers": {
        "@type": "Offer",
        "price": "499.00",
        "priceCurrency": "USD",
        "availability": "https://schema.org/InStock"
      }
    }
    </script>
</head>
<body><h1>CloudPro</h1></body>
</html>
"""

@pytest.mark.asyncio
async def test_products_api_extract_and_query():
    app = create_app()
    mock_db = AsyncMock()
    mock_db.add = MagicMock()
    mock_redis = AsyncMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_redis] = lambda: mock_redis

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        brand_id = uuid4()
        fake_brand = Brand(id=brand_id, name="CloudPro", domain="cloudpro.com")
        mock_db.get.return_value = fake_brand

        # 1. Extract products when snapshot exists -> 201 Created
        fake_url = BrandUrl(id=uuid4(), brand_id=brand_id, url="https://cloudpro.com/pricing")
        fake_snap = Snapshot(
            id=uuid4(),
            brand_url_id=fake_url.id,
            content_hash="h123",
            html_size=500,
            status_code=200,
            html_path=HTML_SAMPLE,
            captured_at=datetime.now(timezone.utc)
        )

        mock_exec = MagicMock()
        mock_exec.first.return_value = (fake_snap, fake_url)
        # scalar_one_or_none for existing product check -> None (new product)
        mock_exec.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_exec

        resp = await client.post(f"/api/v1/products/brands/{brand_id}/products/extract")
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "completed"
        assert data["total_extracted"] == 1
        assert data["new_products"] == 1

        # 2. List products -> 200 OK
        prod_id = uuid4()
        fake_prod = Product(
            id=prod_id,
            brand_id=brand_id,
            name="CloudPro Enterprise Suite",
            sku="CP-ENT-99",
            current_price=Decimal("499.00"),
            currency="USD",
            availability="InStock"
        )
        mock_exec_list = MagicMock()
        # Count subquery
        mock_exec_list.scalar.return_value = 1
        # Item scalars
        mock_exec_list.scalars.return_value.all.return_value = [fake_prod]
        mock_db.execute.return_value = mock_exec_list

        resp_list = await client.get(f"/api/v1/products/brands/{brand_id}/products")
        assert resp_list.status_code == 200
        list_data = resp_list.json()
        assert list_data["total"] == 1
        assert len(list_data["items"]) == 1
        assert list_data["items"][0]["name"] == "CloudPro Enterprise Suite"

        # 3. Product detail with price history -> 200 OK
        mock_db.get.return_value = fake_prod
        p_hist = PriceHistory(
            id=uuid4(),
            product_id=prod_id,
            price=Decimal("499.00"),
            currency="USD",
            captured_at=datetime.now(timezone.utc)
        )
        mock_exec_hist = MagicMock()
        mock_exec_hist.scalars.return_value.all.return_value = [p_hist]
        mock_db.execute.return_value = mock_exec_hist

        resp_detail = await client.get(f"/api/v1/products/products/{prod_id}")
        assert resp_detail.status_code == 200
        detail_data = resp_detail.json()
        assert detail_data["name"] == "CloudPro Enterprise Suite"
        assert len(detail_data["price_history"]) == 1

        # 4. Product analytics summary -> 200 OK
        mock_exec_agg = MagicMock()
        mock_exec_agg.first.return_value = (1, 499.0, 499.0, 499.0)
        mock_exec_agg.scalar.return_value = 1
        mock_db.execute.return_value = mock_exec_agg

        resp_analytics = await client.get(f"/api/v1/products/brands/{brand_id}/products/analytics")
        assert resp_analytics.status_code == 200
        agg_data = resp_analytics.json()
        assert agg_data["total_products"] == 1
        assert agg_data["avg_price"] == 499.0
