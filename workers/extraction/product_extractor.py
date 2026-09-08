from __future__ import annotations
import json
import re
from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple

CURRENCY_SYMBOLS = {
    '$': 'USD',
    '€': 'EUR',
    '£': 'GBP',
    '₹': 'INR',
    '¥': 'JPY',
    'C$': 'CAD',
    'A$': 'AUD',
    'CHF': 'CHF',
}

AVAILABILITY_MAP = {
    'instock': 'InStock',
    'in_stock': 'InStock',
    'http://schema.org/instock': 'InStock',
    'https://schema.org/instock': 'InStock',
    'outofstock': 'OutOfStock',
    'out_of_stock': 'OutOfStock',
    'http://schema.org/outofstock': 'OutOfStock',
    'https://schema.org/outofstock': 'OutOfStock',
    'preorder': 'PreOrder',
    'pre_order': 'PreOrder',
    'http://schema.org/preorder': 'PreOrder',
    'https://schema.org/preorder': 'PreOrder',
    'backorder': 'BackOrder',
    'http://schema.org/backorder': 'BackOrder',
    'https://schema.org/backorder': 'BackOrder',
    'discontinued': 'Discontinued',
    'http://schema.org/discontinued': 'Discontinued',
    'https://schema.org/discontinued': 'Discontinued',
}

class ProductExtractor:
    """
    Multi-strategy Product & Pricing Extractor following the Strategy Selection Protocol:
    1. Schema.org JSON-LD (Product / Offer)
    2. Embedded Hydration Data (__NEXT_DATA__)
    3. DOM CSS Selectors, Microdata, and Meta fallback
    """

    @classmethod
    def clean_price(cls, raw: Any) -> Optional[Decimal]:
        if raw is None:
            return None
        text = str(raw).strip()
        if not text:
            return None
            
        # Remove currency symbols and non-numeric characters except dots and commas
        cleaned = re.sub(r'[^\d.,]', '', text)
        if not cleaned:
            return None
            
        # Format commas and dots (e.g. European 49,99 or standard 1,499.99)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            parts = cleaned.split(',')
            if len(parts[-1]) == 2:
                cleaned = cleaned.replace(',', '.')
            else:
                cleaned = cleaned.replace(',', '')
                
        try:
            val = Decimal(cleaned).quantize(Decimal('0.01'))
            if val < 0 or val > Decimal('10000000.00'):
                return None
            return val
        except (InvalidOperation, ValueError):
            return None

    @classmethod
    def clean_currency(cls, raw_curr: Optional[str], raw_text: str = '') -> str:
        if raw_curr:
            curr = raw_curr.strip().upper()
            if len(curr) == 3:
                return curr
        for sym, code in CURRENCY_SYMBOLS.items():
            if sym in raw_text:
                return code
        return 'USD'

    @classmethod
    def clean_availability(cls, raw_avail: Optional[str]) -> str:
        if not raw_avail:
            return 'InStock'
        key = str(raw_avail).strip().lower()
        return AVAILABILITY_MAP.get(key, 'InStock')

    @classmethod
    def detect_price_anomaly(cls, old_price: Optional[Decimal], new_price: Optional[Decimal], threshold: float = 0.50) -> Tuple[bool, float]:
        """Detects if a price change exceeds the anomaly threshold (default 50%)."""
        if not old_price or not new_price or old_price <= 0:
            return False, 0.0
        diff = abs(new_price - old_price)
        ratio = float(diff / old_price)
        return ratio >= threshold, round(ratio * 100, 2)

    @classmethod
    def extract(cls, html: str, page_url: str = '') -> List[Dict[str, Any]]:
        """Extracts products from HTML using cascading multi-platform strategies."""
        if not html or not html.strip():
            return []

        soup = BeautifulSoup(html, 'lxml')
        all_products: List[Dict[str, Any]] = []

        # 1. Strategy 1: Schema.org JSON-LD (Product, ProductGroup, ItemList)
        jsonld_prods = cls._extract_from_jsonld(soup)
        all_products.extend(jsonld_prods)

        # 2. Strategy 2: Shopify & Platform Store State
        shopify_prods = cls._extract_from_shopify(html, soup)
        all_products.extend(shopify_prods)

        # 3. Strategy 3: Embedded Next.js / Nuxt.js hydration data
        hydration_prods = cls._extract_from_hydration(soup)
        all_products.extend(hydration_prods)

        # 4. Strategy 4: DOM CSS Selectors, Multi-Card Grids, Microdata & Meta fallback
        if not all_products:
            dom_prods = cls._extract_from_dom(soup, page_url)
            all_products.extend(dom_prods)

        # Deduplicate products by normalized name and SKU
        unique: Dict[str, Dict[str, Any]] = {}
        for p in all_products:
            name = (p.get("name") or "").strip()
            sku = (p.get("sku") or "").strip()
            if not name or p.get("current_price") is None:
                continue
            key = f"{name.lower()}:::{sku.lower()}"
            if key not in unique:
                unique[key] = p

        return list(unique.values())

    @classmethod
    def _extract_from_jsonld(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        scripts = soup.find_all('script', type='application/ld+json')

        for s in scripts:
            text = s.string or s.get_text() or ''
            if not text.strip():
                continue
            try:
                data = json.loads(text)
            except Exception:
                # Handle possible truncation by attempting balanced extraction
                continue

            items: List[Any] = []
            if isinstance(data, dict):
                if '@graph' in data and isinstance(data['@graph'], list):
                    items = data['@graph']
                else:
                    items = [data]
            elif isinstance(data, list):
                items = data

            for item in items:
                if not isinstance(item, dict):
                    continue

                item_type = str(item.get('@type', ''))

                # Case A: ProductGroup with hasVariant (e.g. Samsung, Nike, Apple)
                if 'ProductGroup' in item_type and 'hasVariant' in item:
                    group_name = item.get('name', '')
                    group_brand = item.get('brand')
                    variants = item.get('hasVariant', [])
                    if isinstance(variants, dict):
                        variants = [variants]
                    for v in variants:
                        if not isinstance(v, dict):
                            continue
                        if not v.get('name') and group_name:
                            v['name'] = f"{group_name} {v.get('sku', '')}".strip()
                        if 'brand' not in v and group_brand:
                            v['brand'] = group_brand
                        prod = cls._parse_jsonld_product(v)
                        if prod and prod.get('name') and prod.get('current_price') is not None:
                            results.append(prod)

                # Case B: ItemList containing product list elements (e.g. Catalog / Category pages)
                elif 'ItemList' in item_type and 'itemListElement' in item:
                    elements = item.get('itemListElement', [])
                    if isinstance(elements, dict):
                        elements = [elements]
                    for elem in elements:
                        if not isinstance(elem, dict):
                            continue
                        target = elem.get('item', elem)
                        if isinstance(target, dict):
                            prod = cls._parse_jsonld_product(target)
                            if prod and prod.get('name') and prod.get('current_price') is not None:
                                results.append(prod)

                # Case C: Standard Product / IndividualProduct
                elif any(k in item_type for k in ['Product', 'IndividualProduct']):
                    prod = cls._parse_jsonld_product(item)
                    if prod and prod.get('name') and prod.get('current_price') is not None:
                        results.append(prod)

        return results

    @classmethod
    def _parse_jsonld_product(cls, item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        name = item.get('name')
        if not name or not isinstance(name, str):
            return None

        sku = item.get('sku') or item.get('productID') or item.get('mpn')
        image = item.get('image')
        if isinstance(image, list) and image:
            image = image[0]
        elif isinstance(image, dict):
            image = image.get('url')

        offers = item.get('offers', {})
        if isinstance(offers, list) and offers:
            offers = offers[0]
        elif not isinstance(offers, dict):
            offers = {}

        raw_price = (
            offers.get('price') or
            offers.get('lowPrice') or
            offers.get('highPrice') or
            item.get('price')
        )
        price = cls.clean_price(raw_price)
        currency = cls.clean_currency(offers.get('priceCurrency') or item.get('currency'), str(raw_price))
        availability = cls.clean_availability(offers.get('availability'))

        brand_val = item.get('brand', {})
        brand_name = brand_val.get('name') if isinstance(brand_val, dict) else brand_val

        attributes = {
            'description': str(item.get('description', ''))[:500] if item.get('description') else None,
            'brand': str(brand_name) if brand_name else None,
            'rating': item.get('aggregateRating', {}).get('ratingValue') if isinstance(item.get('aggregateRating'), dict) else None,
            'review_count': item.get('aggregateRating', {}).get('reviewCount') if isinstance(item.get('aggregateRating'), dict) else None,
        }

        return {
            'name': name.strip()[:255],
            'sku': str(sku).strip()[:100] if sku else None,
            'current_price': price,
            'currency': currency,
            'availability': availability,
            'image_url': str(image)[:2048] if image else None,
            'attributes': attributes,
            'data_source_tag': 'scraped_jsonld'
        }

    @classmethod
    def _extract_from_shopify(cls, html: str, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extracts products from Shopify store metadata (var meta = {"products": [...]})."""
        results: List[Dict[str, Any]] = []

        # 1. Resolve currency from Shopify metadata
        currency = "USD"
        curr_match = re.search(r"ShopifyAnalytics\.meta\.currency\s*=\s*['\"]([A-Z]{3})['\"]", html)
        if curr_match:
            currency = curr_match.group(1).upper()
        else:
            curr_match2 = re.search(r"Shopify\.currency\.active\s*=\s*['\"]([A-Z]{3})['\"]", html)
            if curr_match2:
                currency = curr_match2.group(1).upper()
            else:
                curr_match3 = re.search(r'["\']currency["\']\s*:\s*["\']([A-Z]{3})["\']', html)
                if curr_match3:
                    currency = curr_match3.group(1).upper()

        # 2. Extract var meta = {"products": ...}
        pos = html.find('var meta = ')
        if pos != -1:
            start_brace = html.find('{', pos)
            end_semi = html.find('};', start_brace)
            if start_brace != -1 and end_semi != -1:
                json_str = html[start_brace:end_semi + 1]
                try:
                    meta_data = json.loads(json_str)
                    raw_prods = meta_data.get('products', [])
                    for p in raw_prods:
                        variants = p.get('variants', [])
                        vendor = p.get('vendor')
                        handle = p.get('handle')
                        fallback_title = p.get('name') or p.get('title')
                        if not fallback_title and variants:
                            fallback_title = variants[0].get('name')
                        if not fallback_title and handle:
                            fallback_title = handle.replace('-', ' ').title()

                        if not fallback_title and not variants:
                            continue

                        if variants:
                            for v in variants:
                                v_name = v.get('name') or fallback_title
                                if not v_name:
                                    continue
                                v_sku = v.get('sku') or str(v.get('id', ''))
                                raw_price = v.get('price')
                                if raw_price is not None:
                                    # In Shopify, prices are recorded as integer cents (e.g. 119900 = 1199.00)
                                    if isinstance(raw_price, (int, float)) and raw_price > 1000:
                                        price = Decimal(str(raw_price)) / 100
                                    else:
                                        price = Decimal(str(raw_price))
                                    
                                    # Extract image if available
                                    v_img = v.get('featured_image')
                                    img_url = None
                                    if isinstance(v_img, dict):
                                        img_url = v_img.get('src')
                                    elif isinstance(v_img, str):
                                        img_url = v_img
                                    if img_url and img_url.startswith('//'):
                                        img_url = 'https:' + img_url

                                    results.append({
                                        'name': str(v_name).strip()[:255],
                                        'sku': str(v_sku).strip()[:100] if v_sku else None,
                                        'current_price': price.quantize(Decimal('0.01')),
                                        'currency': currency,
                                        'availability': 'InStock',
                                        'image_url': str(img_url)[:2048] if img_url else None,
                                        'attributes': {'vendor': vendor, 'handle': handle},
                                        'data_source_tag': 'scraped_shopify'
                                    })
                        else:
                            raw_price = p.get('price')
                            if raw_price is not None:
                                price = (Decimal(str(raw_price)) / 100 if isinstance(raw_price, (int, float)) and raw_price > 1000 else Decimal(str(raw_price))).quantize(Decimal('0.01'))
                                results.append({
                                    'name': str(fallback_title).strip()[:255],
                                    'sku': str(p.get('id', '')),
                                    'current_price': price,
                                    'currency': currency,
                                    'availability': 'InStock',
                                    'image_url': None,
                                    'attributes': {'vendor': vendor, 'handle': handle},
                                    'data_source_tag': 'scraped_shopify'
                                })
                except Exception:
                    pass

        # 3. Check for standalone product JSON in <script id="ProductJson-...">
        for script in soup.find_all('script', attrs={'type': 'application/json'}):
            s_id = script.get('id', '')
            if 'product' in s_id.lower() or script.get('data-product-json') is not None:
                try:
                    p_data = json.loads(script.string or '')
                    p_title = p_data.get('title') or p_data.get('name')
                    if p_title:
                        for v in p_data.get('variants', [{}]):
                            v_price = v.get('price') or p_data.get('price')
                            if v_price is not None:
                                price = Decimal(str(v_price)) / 100 if isinstance(v_price, (int, float)) and v_price > 1000 else Decimal(str(v_price))
                                results.append({
                                    'name': str(v.get('name') or p_title).strip()[:255],
                                    'sku': str(v.get('sku') or v.get('id') or '')[:100] or None,
                                    'current_price': price.quantize(Decimal('0.01')),
                                    'currency': currency,
                                    'availability': 'InStock',
                                    'image_url': str(p_data.get('featured_image'))[:2048] if p_data.get('featured_image') else None,
                                    'attributes': {'vendor': p_data.get('vendor')},
                                    'data_source_tag': 'scraped_shopify'
                                })
                except Exception:
                    pass

        return results

    @classmethod
    def _extract_from_hydration(cls, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        next_data = soup.find('script', id='__NEXT_DATA__')
        if not next_data or not next_data.string:
            return results

        try:
            payload = json.loads(next_data.string)
            page_props = payload.get('props', {}).get('pageProps', {})
            
            # Check single product
            candidate = page_props.get('product') or page_props.get('initialProduct') or page_props.get('item')
            candidates = [candidate] if isinstance(candidate, dict) else []

            # Check list of products
            prod_list = page_props.get('products') or page_props.get('items') or page_props.get('catalog')
            if isinstance(prod_list, list):
                candidates.extend([p for p in prod_list if isinstance(p, dict)])

            for c in candidates:
                name = c.get('title') or c.get('name')
                raw_price = c.get('price') or c.get('amount')
                price = cls.clean_price(raw_price)
                if name and price is not None:
                    sku = c.get('sku') or c.get('id')
                    image = c.get('image') or c.get('featured_image')
                    results.append({
                        'name': str(name).strip()[:255],
                        'sku': str(sku).strip()[:100] if sku else None,
                        'current_price': price,
                        'currency': cls.clean_currency(c.get('currency'), str(raw_price)),
                        'availability': cls.clean_availability(c.get('availability') or c.get('status')),
                        'image_url': str(image)[:2048] if image else None,
                        'attributes': {'description': str(c.get('description', ''))[:500]},
                        'data_source_tag': 'scraped_hydration'
                    })
        except Exception:
            pass

        return results

    @classmethod
    def _extract_from_dom(cls, soup: BeautifulSoup, page_url: str = '') -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []

        # 1. Multi-Card Catalog / Category Grid Extraction
        card_selectors = [
            '.product-card', '.product-item', '.product-tile',
            '.grid-product', '.product', 'article.product', 'li.product'
        ]
        cards = []
        for sel in card_selectors:
            found = soup.select(sel)
            if len(found) >= 2:
                cards = found
                break

        if cards:
            for card in cards[:40]:  # Up to 40 cards per page
                # Title
                title_el = card.select_one('h2, h3, h4, .product-title, .title, a.product-card__title, [class*="product-title"]')
                name = title_el.get_text().strip() if title_el else None

                # Price
                price_el = card.select_one('.price, .money, .product-price, [data-price], .amount, [class*="price"]')
                price = None
                currency = 'USD'
                if price_el:
                    txt = price_el.get_text().strip()
                    price = cls.clean_price(txt)
                    currency = cls.clean_currency('', txt)

                # Image
                img_el = card.select_one('img[src], img[data-src]')
                image_url = img_el.get('src') or img_el.get('data-src') if img_el else None

                if name and price is not None:
                    results.append({
                        'name': name[:255],
                        'sku': None,
                        'current_price': price,
                        'currency': currency,
                        'availability': 'InStock',
                        'image_url': image_url[:2048] if image_url else None,
                        'attributes': {'source_url': page_url},
                        'data_source_tag': 'scraped_dom_card'
                    })

            if results:
                return results

        # 2. Single Detail Page Fallback (OpenGraph + H1 + Main Price)
        og_title = soup.find('meta', property='og:title')
        meta_price = (
            soup.find('meta', property='product:price:amount') or
            soup.find('meta', property='price') or
            soup.find('meta', attrs={'name': 'twitter:data1'})
        )
        meta_currency = soup.find('meta', property='product:price:currency')
        og_image = soup.find('meta', property='og:image')

        name = None
        if og_title and og_title.get('content'):
            name = og_title['content'].strip()
        elif soup.find('h1'):
            name = soup.find('h1').get_text().strip()

        price = None
        currency = 'USD'
        if meta_price and meta_price.get('content'):
            price = cls.clean_price(meta_price['content'])
            curr_str = meta_currency.get('content') if meta_currency else ''
            currency = cls.clean_currency(curr_str, meta_price.get('content', ''))

        if price is None:
            price_selectors = [
                '.price', '.current-price', '.product-price', '[data-product-price]',
                '.offer-price', '.sale-price', '.product__price', '.woocommerce-Price-amount'
            ]
            for sel in price_selectors:
                el = soup.select_one(sel)
                if el:
                    txt = el.get_text().strip()
                    parsed_p = cls.clean_price(txt)
                    if parsed_p is not None:
                        price = parsed_p
                        currency = cls.clean_currency('', txt)
                        break

        if not name or price is None:
            return []

        image_url = None
        if og_image and og_image.get('content'):
            image_url = og_image['content'].strip()
        else:
            main_img = soup.select_one('.product-image img, .gallery img, img.main-image')
            if main_img and (main_img.get('src') or main_img.get('data-src')):
                image_url = main_img.get('src') or main_img.get('data-src')

        stock_text = ''
        stock_el = soup.select_one('.stock, .availability, [data-stock-status], .in-stock, .out-of-stock')
        if stock_el:
            stock_text = stock_el.get_text().strip()

        return [{
            'name': name[:255],
            'sku': None,
            'current_price': price,
            'currency': currency,
            'availability': cls.clean_availability(stock_text),
            'image_url': image_url[:2048] if image_url else None,
            'attributes': {'source_url': page_url},
            'data_source_tag': 'scraped_dom'
        }]
