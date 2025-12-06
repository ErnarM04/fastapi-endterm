from typing import List

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, PositiveFloat, PositiveInt
from sqlalchemy import ForeignKey, String, or_
from sqlalchemy.orm import Mapped, Session, mapped_column, relationship

# Assuming your database.py is in the same folder
from .database import Base, engine, get_db

app = FastAPI(title="Store API", version="0.1.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- SQLAlchemy Models ---

class ProductORM(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str]
    description: Mapped[str | None]
    price: Mapped[float]
    discount_percentage: Mapped[float | None]
    rating: Mapped[float | None]
    stock: Mapped[int | None]
    brand: Mapped[str | None]
    category: Mapped[str | None]
    thumbnail: Mapped[str | None]
    images: Mapped[str | None] = mapped_column(String(length=1000), nullable=True)

    items: Mapped[List["CartItemORM"]] = relationship(
        back_populates="product", cascade="all, delete-orphan"
    )


class CartORM(Base):
    __tablename__ = "carts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    items: Mapped[List["CartItemORM"]] = relationship(
        back_populates="cart", cascade="all, delete-orphan"
    )


class CartItemORM(Base):
    __tablename__ = "cart_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    cart_id: Mapped[int] = mapped_column(ForeignKey("carts.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int]

    cart: Mapped[CartORM] = relationship(back_populates="items")
    product: Mapped[ProductORM] = relationship(back_populates="items")


class FavoriteORM(Base):
    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), unique=True)

    product: Mapped[ProductORM] = relationship()


# Create tables
Base.metadata.create_all(bind=engine)


# --- Pydantic Models ---

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    price: PositiveFloat
    discount_percentage: float | None = None
    rating: float | None = None
    stock: int | None = None
    brand: str | None = None
    category: str | None = None
    thumbnail: str | None = None
    images: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=500)
    price: PositiveFloat | None = None


class Product(ProductBase):
    id: int

    class Config:
        from_attributes = True


class CartItem(BaseModel):
    product_id: int
    quantity: PositiveInt = 1


class Cart(BaseModel):
    id: int
    items: List[CartItem]


class CartSummary(Cart):
    total: float = 0.0


class ProductPage(BaseModel):
    page: int
    pages: int
    limit: int
    total: int
    products: List[Product]


# --- Helper Function ---

def calculate_cart_total(cart_orm: CartORM) -> float:
    """
    Calculates total based on the ORM relationships.
    Accessing item.product triggers a lazy load from the DB.
    """
    total = 0.0
    for item in cart_orm.items:
        if item.product:
            total += item.product.price * item.quantity
    return round(total, 2)


# --- Endpoints ---

@app.get("/")
def root():
    return {
        "message": "Store API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "products": "/products",
            "carts": "/carts",
            "favorites": "/favorites",
        }
    }


@app.get("/products", response_model=ProductPage)
def list_products(
    q: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ProductPage:
    query = db.query(ProductORM)
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                ProductORM.name.ilike(search_term),
                ProductORM.description.ilike(search_term),
                ProductORM.brand.ilike(search_term),
                ProductORM.category.ilike(search_term),
            )
        )

    total = query.count()
    pages = (total + limit - 1) // limit if total else 0
    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()

    return ProductPage(
        page=page,
        pages=pages,
        limit=limit,
        total=total,
        products=[Product.model_validate(p) for p in products],
    )


@app.get("/products/{product_id}", response_model=Product)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(ProductORM, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return Product.model_validate(product)


@app.post("/products", response_model=Product, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)) -> Product:
    product = ProductORM(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return Product.model_validate(product)


@app.put("/products/{product_id}", response_model=Product)
def update_product(
    product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)
) -> Product:
    product = db.get(ProductORM, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return Product.model_validate(product)


@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    product = db.get(ProductORM, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return None


@app.get("/carts", response_model=List[CartSummary])
def list_carts(db: Session = Depends(get_db)) -> List[CartSummary]:
    carts_orm = db.query(CartORM).all()
    result: List[CartSummary] = []
    
    for cart in carts_orm:
        # Calculate total using ORM relationship
        total = calculate_cart_total(cart)
        
        # Convert ORM items to Pydantic items
        pydantic_items = [
            CartItem(product_id=item.product_id, quantity=item.quantity)
            for item in cart.items
        ]
        
        result.append(CartSummary(id=cart.id, items=pydantic_items, total=total))
    
    return result


@app.post("/carts", response_model=Cart, status_code=201)
def create_cart(db: Session = Depends(get_db)) -> Cart:
    cart_orm = CartORM()
    db.add(cart_orm)
    db.commit()
    db.refresh(cart_orm)
    return Cart(id=cart_orm.id, items=[])


@app.get("/carts/{cart_id}", response_model=CartSummary)
def get_cart(cart_id: int, db: Session = Depends(get_db)) -> CartSummary:
    cart = db.get(CartORM, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    total = calculate_cart_total(cart)
    
    items = [
        CartItem(product_id=item.product_id, quantity=item.quantity)
        for item in cart.items
    ]
    return CartSummary(id=cart.id, items=items, total=total)


@app.post("/carts/{cart_id}/items", response_model=CartSummary)
def add_cart_item(
    cart_id: int, item: CartItem, db: Session = Depends(get_db)
) -> CartSummary:
    cart = db.get(CartORM, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    
    product = db.get(ProductORM, item.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Check if item exists in cart using ORM relationship
    existing = next(
        (ci for ci in cart.items if ci.product_id == item.product_id), None
    )
    
    if existing:
        existing.quantity += item.quantity
    else:
        cart_item = CartItemORM(
            cart_id=cart.id, product_id=item.product_id, quantity=item.quantity
        )
        db.add(cart_item)

    db.commit()
    db.refresh(cart) # Refreshes relationships too

    items = [
        CartItem(product_id=ci.product_id, quantity=ci.quantity) for ci in cart.items
    ]
    total = calculate_cart_total(cart)
    
    return CartSummary(id=cart.id, items=items, total=total)


@app.delete("/carts/{cart_id}/items/{product_id}", response_model=CartSummary)
def remove_cart_item(
    cart_id: int, product_id: int, db: Session = Depends(get_db)
) -> CartSummary:
    cart = db.get(CartORM, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    item = next((ci for ci in cart.items if ci.product_id == product_id), None)
    
    if item:
        db.delete(item)
        db.commit()
        db.refresh(cart)

    items = [
        CartItem(product_id=ci.product_id, quantity=ci.quantity) for ci in cart.items
    ]
    total = calculate_cart_total(cart)
    
    return CartSummary(id=cart.id, items=items, total=total)


@app.delete("/carts/{cart_id}", status_code=204)
def delete_cart(cart_id: int, db: Session = Depends(get_db)) -> None:
    cart = db.get(CartORM, cart_id)
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    db.delete(cart)
    db.commit()
    return None


# Favorites
@app.get("/favorites", response_model=List[Product])
def list_favorites(db: Session = Depends(get_db)) -> List[Product]:
    favorites = db.query(FavoriteORM).join(ProductORM).all()
    return [Product.model_validate(f.product) for f in favorites if f.product]


@app.post("/favorites/{product_id}", response_model=Product, status_code=201)
def add_favorite(product_id: int, db: Session = Depends(get_db)) -> Product:
    product = db.get(ProductORM, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    existing = (
        db.query(FavoriteORM).filter(FavoriteORM.product_id == product_id).first()
    )
    if existing:
        return Product.model_validate(product)
    favorite = FavoriteORM(product_id=product_id)
    db.add(favorite)
    db.commit()
    return Product.model_validate(product)


@app.delete("/favorites/{product_id}", status_code=204)
def remove_favorite(product_id: int, db: Session = Depends(get_db)) -> None:
    favorite = (
        db.query(FavoriteORM).filter(FavoriteORM.product_id == product_id).first()
    )
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")
    db.delete(favorite)
    db.commit()
    return None
    