# FastAPI Store API

Simple FastAPI application that exposes in-memory products and carts.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn app.main:app --reload
```

## API overview

- `GET /products` – list products
- `POST /products` – create product
- `PUT /products/{id}` – update product
- `DELETE /products/{id}` – remove product and clean carts
- `GET /carts` – list carts with totals
- `POST /carts` – create empty cart
- `POST /carts/{id}/items` – add/update cart item
- `DELETE /carts/{id}/items/{product_id}` – remove item
- `DELETE /carts/{id}` – delete cart

