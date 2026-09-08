from __future__ import annotations
import pytest
from decimal import Decimal
from workers.extraction.product_extractor import ProductExtractor

JSONLD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "Acme Wireless Noise-Canceling Headphones",
      "image": [
        "https://example.com/photos/1x1/photo.jpg"
       ],
      "description": "High performance noise cancelling over-ear headphones.",
      "sku": "ACME-WH-1000",
      "mpn": "925872",
      "brand": {
        "@type": "Brand",
        "name": "Acme"
      },
      "offers": {
        "@type": "Offer",
        "url": "https://example.com/product/acme-headphones",
        "priceCurrency": "USD",
        "price": "299.99",
        "priceValidUntil": "2026-11-20",
        "itemCondition": "https://schema.org/NewCondition",
        "availability": "https://schema.org/InStock"
      }
    }
    </script>
</head>
<body>
    <h1>Acme Headphones</h1>
</body>
</html>
"""

NEXT_DATA_HTML = """
<!DOCTYPE html>
<html>
<head></head>
<body>
    <div id="__next">Content</div>
    <script id="__NEXT_DATA__" type="application/json">
    {
      "props": {
        "pageProps": {
          "product": {
            "title": "Ergonomic Mechanical Keyboard",
            "price": 149.50,
            "currency": "EUR",
            "sku": "KEYB-MECH-01",
            "availability": "InStock",
            "image": "https://example.com/keyboard.png",
            "description": "Custom mechanical switch keyboard"
          }
        }
      }
    }
    </script>
</body>
</html>
"""

DOM_FALLBACK_HTML = """
<!DOCTYPE html>
<html>
<head>
    <meta property="og:title" content="UltraLight Running Shoes">
    <meta property="og:image" content="https://example.com/shoes.jpg">
</head>
<body>
    <h1 class="product-title">UltraLight Running Shoes</h1>
    <span class="price">$120.00</span>
    <div class="availability in-stock">In Stock</div>
</body>
</html>
"""

def test_extract_jsonld():
    products = ProductExtractor.extract(JSONLD_HTML, "https://example.com/product/1")
    assert len(products) == 1
    p = products[0]
    assert p["name"] == "Acme Wireless Noise-Canceling Headphones"
    assert p["sku"] == "ACME-WH-1000"
    assert p["current_price"] == Decimal("299.99")
    assert p["currency"] == "USD"
    assert p["availability"] == "InStock"
    assert p["data_source_tag"] == "scraped_jsonld"
    assert p["image_url"] == "https://example.com/photos/1x1/photo.jpg"

def test_extract_hydration():
    products = ProductExtractor.extract(NEXT_DATA_HTML, "https://example.com/shop/item")
    assert len(products) == 1
    p = products[0]
    assert p["name"] == "Ergonomic Mechanical Keyboard"
    assert p["sku"] == "KEYB-MECH-01"
    assert p["current_price"] == Decimal("149.50")
    assert p["currency"] == "EUR"
    assert p["data_source_tag"] == "scraped_hydration"

def test_extract_dom_fallback():
    products = ProductExtractor.extract(DOM_FALLBACK_HTML, "https://example.com/shoes")
    assert len(products) == 1
    p = products[0]
    assert p["name"] == "UltraLight Running Shoes"
    assert p["current_price"] == Decimal("120.00")
    assert p["currency"] == "USD"
    assert p["availability"] == "InStock"
    assert p["data_source_tag"] == "scraped_dom"

def test_clean_price_variations():
    assert ProductExtractor.clean_price("$199.99") == Decimal("199.99")
    assert ProductExtractor.clean_price("€ 49,99") == Decimal("49.99")
    assert ProductExtractor.clean_price("₹ 1,499.00") == Decimal("1499.00")
    assert ProductExtractor.clean_price("99") == Decimal("99.00")
    assert ProductExtractor.clean_price("Free") is None
    assert ProductExtractor.clean_price(None) is None
    assert ProductExtractor.clean_price("") is None

def test_detect_price_anomaly():
    # 10% change is normal
    is_anomaly, pct = ProductExtractor.detect_price_anomaly(Decimal("100.00"), Decimal("110.00"))
    assert not is_anomaly
    assert pct == 10.0

    # 60% drop is an anomaly
    is_anomaly, pct = ProductExtractor.detect_price_anomaly(Decimal("100.00"), Decimal("40.00"))
    assert is_anomaly
    assert pct == 60.0

def test_extract_empty_or_non_product():
    assert ProductExtractor.extract("", "https://example.com") == []
    assert ProductExtractor.extract("<html><body><p>Just an about page</p></body></html>", "https://example.com") == []
