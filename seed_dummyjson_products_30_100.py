import sys
from typing import Any, Dict, List

import requests


API_BASE = "http://127.0.0.1:8000"
DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def fetch_dummy_products() -> List[Dict[str, Any]]:
    """Fetch products from dummyjson."""
    resp = requests.get(DUMMYJSON_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("products", [])


def to_payload(product: Dict[str, Any]) -> Dict[str, Any]:
    """Convert product from dummyjson format to local API format.
    Uses original English values for Russian fields.
    """
    return {
        "name": product.get("title") or "No title",
        "name_ru": product.get("title") or "No title",  # Original English value
        "description": product.get("description") or "",
        "description_ru": product.get("description") or "",  # Original English value
        "price": float(product.get("price", 0)),
        "discount_percentage": float(product.get("discountPercentage", 0))
        if product.get("discountPercentage") is not None
        else None,
        "rating": float(product.get("rating", 0))
        if product.get("rating") is not None
        else None,
        "stock": int(product.get("stock", 0))
        if product.get("stock") is not None
        else None,
        "brand": product.get("brand"),
        "category": product.get("category"),
        "category_ru": product.get("category") or "",  # Original English value
        "thumbnail": product.get("thumbnail"),
        "images": ", ".join(product.get("images", [])) if product.get("images") else None,
    }


def post_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Post product to local API."""
    resp = requests.post(f"{API_BASE}/products", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("Fetching products from dummyjson...")
    try:
        all_products = fetch_dummy_products()
    except Exception as exc:
        print(f"Failed to fetch from dummyjson: {exc}", file=sys.stderr)
        sys.exit(1)
    
    # Get products starting from 31st (index 30) to 100th (index 99)
    # Note: dummyjson returns products in an array, so we use 0-based indexing
    # Products 31-100 means indices 30-99 (70 products total)
    # This ensures no overlap if original script posts products 1-30
    products = all_products[30:100]  # Slice from index 30 to 99
    
    if not products:
        print("No products found in range 30-100.")
        return
    
    print(f"Fetched {len(products)} products (31st to 100th), posting to {API_BASE}/products ...")
    
    created = 0
    skipped = 0
    
    for idx, p in enumerate(products, start=31):
        payload = to_payload(p)
        try:
            created_product = post_product(payload)
            created += 1
            print(f"Created product #{created} (original #{idx}): {created_product['id']} - {created_product['name']}")
        except requests.exceptions.HTTPError as exc:
            if exc.response and exc.response.status_code == 422:
                print(f"Skipped product #{idx} '{payload['name']}': Validation error - {exc.response.text}", file=sys.stderr)
            else:
                print(f"Failed to create product #{idx} '{payload['name']}': {exc}", file=sys.stderr)
            skipped += 1
        except Exception as exc:
            print(f"Failed to create product #{idx} '{payload['name']}': {exc}", file=sys.stderr)
            skipped += 1
    
    print(f"\nDone! Successfully created {created} products, skipped {skipped}.")


if __name__ == "__main__":
    main()

