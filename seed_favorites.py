from app.database import SessionLocal
from app.main import FavoriteORM, ProductORM


def seed_favorites() -> None:
    db = SessionLocal()
    try:
        # Get some products from the database
        products = db.query(ProductORM).limit(20).all()
        
        if not products:
            print("No products found in database. Please seed products first using seed_dummyjson_products.py")
            return
        
        print(f"Found {len(products)} products. Adding favorites for multiple users...")
        
        # Define favorites: user_id -> list of product indices to favorite
        favorites_map = {
            1: [0, 1, 2, 3, 4],  # User 1 favorites first 5 products
            2: [5, 6, 7, 8],      # User 2 favorites next 4 products
            3: [0, 5, 10, 15],    # User 3 favorites some scattered products
            4: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],  # User 4 favorites many products
        }
        
        created = 0
        skipped = 0
        
        for user_id, product_indices in favorites_map.items():
            for idx in product_indices:
                if idx >= len(products):
                    continue
                
                product = products[idx]
                
                # Check if favorite already exists
                existing = (
                    db.query(FavoriteORM)
                    .filter(
                        FavoriteORM.user_id == user_id,
                        FavoriteORM.product_id == product.id
                    )
                    .first()
                )
                
                if existing:
                    skipped += 1
                    continue
                
                favorite = FavoriteORM(user_id=user_id, product_id=product.id)
                db.add(favorite)
                created += 1
                print(f"Added favorite: User {user_id} -> Product {product.id} ({product.name[:50]}...)")
        
        db.commit()
        print(f"\nDone! Created {created} favorites, skipped {skipped} duplicates.")
        print("\nFavorites summary:")
        for user_id in favorites_map.keys():
            count = db.query(FavoriteORM).filter(FavoriteORM.user_id == user_id).count()
            print(f"  User {user_id}: {count} favorites")
    
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_favorites()

