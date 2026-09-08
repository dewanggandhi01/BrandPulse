import asyncio
import json
import re
from decimal import Decimal
from uuid import UUID
from app.database import async_session_maker
from app.models.snapshot import Snapshot

def extract_shopify_meta(html: str):
    products = []
    # Find currency
    curr_match = re.search(r"ShopifyAnalytics\.meta\.currency\s*=\s*['\"]([A-Z]{3})['\"]", html)
    currency = curr_match.group(1) if curr_match else "INR"

    # Match var meta = {"products": ...}
    for m in re.finditer(r'var\s+meta\s*=\s*(\{.*?"products"\s*:\s*\[.*?\]\s*\});', html, re.DOTALL):
        try:
            data = json.loads(m.group(1))
            raw_products = data.get("products", [])
            for p in raw_products:
                name = p.get("name") or p.get("title")
                vendor = p.get("vendor")
                for v in p.get("variants", []):
                    v_name = v.get("name") or name
                    v_sku = v.get("sku")
                    raw_price = v.get("price")
                    if raw_price is not None:
                        # Shopify prices in variants are typically integer cents (e.g. 119900 = 1199.00)
                        if isinstance(raw_price, (int, float)) and raw_price > 1000:
                            price = Decimal(str(raw_price)) / 100
                        else:
                            price = Decimal(str(raw_price))
                        products.append({
                            "name": v_name,
                            "sku": v_sku,
                            "current_price": price,
                            "currency": currency,
                            "availability": "InStock",
                            "data_source_tag": "scraped_shopify"
                        })
        except Exception as e:
            pass
    return products

async def main():
    async with async_session_maker() as session:
        # Fraganote
        s = await session.get(Snapshot, UUID("67556100-f1cc-4309-806a-4c141c756e5a"))
        prods = extract_shopify_meta(s.html_path or "")
        print(f"Fraganote products found: {len(prods)}")
        for p in prods[:5]:
            print(f" - {p['name']} | Price: {p['current_price']} {p['currency']} | SKU: {p['sku']}")

if __name__ == "__main__":
    asyncio.run(main())
