import sys
from typing import Any, Dict, List

import requests


API_BASE = "http://127.0.0.1:8000"
RENDER_API_BASE = "https://fastapi-endterm.onrender.com"


def fetch_all_products() -> List[Dict[str, Any]]:
    """Fetch all products from Render API with pagination."""
    all_products = []
    page = 1
    
    while True:
        url = f"{RENDER_API_BASE}/products?page={page}&limit=100"
        print(f"Fetching page {page} from {url}...")
        
        try:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            print(f"Failed to fetch page {page}: {exc}", file=sys.stderr)
            break
        
        products = data.get("products", [])
        if not products:
            break
        
        all_products.extend(products)
        print(f"Fetched {len(products)} products from page {page}")
        
        # Check if there are more pages
        total_pages = data.get("pages", 0)
        if page >= total_pages:
            break
        
        page += 1
    
    return all_products


def to_payload(product: Dict[str, Any]) -> Dict[str, Any]:
    """Convert product from Render API format to local API format."""
    return {
        "name": product.get("name") or "No name",
        "name_ru": product.get("name_ru") or product.get("name") or "Без названия",
        "description": product.get("description"),
        "description_ru": product.get("description_ru") or product.get("description") or "Нет описания",
        "price": float(product.get("price", 0)),
        "discount_percentage": float(product.get("discount_percentage", 0))
        if product.get("discount_percentage") is not None
        else None,
        "rating": float(product.get("rating", 0))
        if product.get("rating") is not None
        else None,
        "stock": int(product.get("stock", 0))
        if product.get("stock") is not None
        else None,
        "brand": product.get("brand"),
        "category": product.get("category"),
        "category_ru": product.get("category_ru") or product.get("category") or "Без категории",
        "thumbnail": product.get("thumbnail"),
        "images": product.get("images"),
    }


def post_product(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Post product to local API."""
    resp = requests.post(f"{API_BASE}/products", json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    print("Fetching products from Render API...")
    try:
        products = fetch_all_products()
    except Exception as exc:
        print(f"Failed to fetch products: {exc}", file=sys.stderr)
        sys.exit(1)
    
    if not products:
        print("No products found to import.")
        return
    
    print(f"\nFetched {len(products)} products total, posting to {API_BASE}/products ...\n")
    
    created = 0
    skipped = 0
    
    for p in products:
        payload = to_payload(p)
        try:
            created_product = post_product(payload)
            created += 1
            print(f"Created product #{created}: {created_product['id']} - {created_product['name']}")
        except requests.exceptions.HTTPError as exc:
            if exc.response and exc.response.status_code == 422:
                print(f"Skipped product '{payload['name']}': Validation error - {exc.response.text}", file=sys.stderr)
            else:
                print(f"Failed to create product '{payload['name']}': {exc}", file=sys.stderr)
            skipped += 1
        except Exception as exc:
            print(f"Failed to create product '{payload['name']}': {exc}", file=sys.stderr)
            skipped += 1
    
    print(f"\nDone! Successfully created {created} products, skipped {skipped}.")


if __name__ == "__main__":
    main()

