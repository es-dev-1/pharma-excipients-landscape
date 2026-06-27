"""
Fetch all product URLs and attributes from the pharmaexcipients.com WooCommerce shop.
Uses the public WooCommerce Store API (no auth needed).

Usage: python3 fetch-all-shop-products.py
Output: shop-products-complete.csv in the same directory
"""

import urllib.request
import json
import csv
import os
import ssl
import time

BASE_URL = "https://www.pharmaexcipients.com/wp-json/wc/store/v1/products"

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
PER_PAGE = 100
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "shop-products-complete.csv")

ATTRIBUTE_COLUMNS = [
    "manufacturer",
    "composition",
    "cas_number",
    "function",
    "dosage_form",
    "synonym",
    "quality",
    "einecs",
]

ATTR_KEY_MAP = {
    "manufacturer": "manufacturer",
    "composition": "composition",
    "cas-no": "cas_number",
    "cas number": "cas_number",
    "function": "function",
    "dosage form": "dosage_form",
    "dosage-form": "dosage_form",
    "synonym": "synonym",
    "quality": "quality",
    "einecs": "einecs",
}


def fetch_page(page_num, retries=3):
    url = f"{BASE_URL}?per_page={PER_PAGE}&page={page_num}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=60, context=ctx) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < retries - 1:
                wait = 3 * (attempt + 1)
                print(f"  Retry {attempt+1}/{retries} after {wait}s: {e}")
                time.sleep(wait)
            else:
                raise


def extract_attributes(product):
    attrs = {col: "" for col in ATTRIBUTE_COLUMNS}
    for attr in product.get("attributes", []):
        raw_name = attr.get("name", "").lower().strip()
        col = ATTR_KEY_MAP.get(raw_name)
        if col:
            terms = [t.get("name", "") for t in attr.get("terms", [])]
            attrs[col] = "; ".join(terms)
    return attrs


def main():
    all_products = []
    page = 1
    fieldnames = ["name", "slug", "url", "sku", "price", "categories"] + ATTRIBUTE_COLUMNS

    while True:
        print(f"Fetching page {page}...")
        try:
            products = fetch_page(page)
        except Exception as e:
            print(f"Error on page {page} after retries: {e}")
            break

        if not products:
            break

        for p in products:
            name = p.get("name", "")
            slug = p.get("slug", "")
            product_url = f"https://www.pharmaexcipients.com/product/{slug}/"
            sku = p.get("sku", "")
            price = p.get("prices", {}).get("price", "")
            categories = "; ".join(
                c.get("name", "") for c in p.get("categories", [])
            )
            attrs = extract_attributes(p)

            row = {
                "name": name,
                "slug": slug,
                "url": product_url,
                "sku": sku,
                "price": price,
                "categories": categories,
                **attrs,
            }
            all_products.append(row)

        print(f"  Got {len(products)} products (total: {len(all_products)})")

        if len(products) < PER_PAGE:
            break

        page += 1
        time.sleep(1)

    with open(OUTPUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_products)

    print(f"\nDone. {len(all_products)} products saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
