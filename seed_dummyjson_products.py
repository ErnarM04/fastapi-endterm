import sys
from typing import Any, Dict, List

import requests


API_BASE = "http://127.0.0.1:8000"
DUMMYJSON_URL = "https://dummyjson.com/products?limit=100"


def fetch_dummy_products() -> List[Dict[str, Any]]:
    resp = requests.get(DUMMYJSON_URL, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("products", [])


def to_payload(product: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": product.get("title") or "No title",
        "description": product.get("description") or "",
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
        "thumbnail": product.get("thumbnail"),
        "images": ", ".join(product.get("images", [])) if product.get("images") else None,
    }


def post_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = requests.post(f"{API_BASE}/products", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("Fetching products from dummyjson...")
    try:
        products = fetch_dummy_products()
    except Exception as exc:  # pragma: no cover - simple script
        print(f"Failed to fetch from dummyjson: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Fetched {len(products)} products, posting to {API_BASE}/products ...")

    created = 0
    for p in products:
        payload = to_payload(p)
        try:
            created_product = post_product(payload)
            created += 1
            print(f"Created product #{created}: {created_product['id']} - {created_product['name']}")
        except Exception as exc:  # pragma: no cover - simple script
            print(f"Failed to create product '{payload['name']}': {exc}", file=sys.stderr)

    print(f"Done. Successfully created {created} products.")


if __name__ == "__main__":
    main()


