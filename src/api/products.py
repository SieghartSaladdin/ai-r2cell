from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.core.database import get_db_connection

router = APIRouter(tags=["products"])

class ProductCreate(BaseModel):
    brand: str
    model: str
    storage: str
    grade: str
    price: int
    stock: int

@router.get("/api/products")
def list_products():
    """
    Retrieve all products in the database inventory.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, brand, model, storage, grade, price, stock FROM products ORDER BY brand, model, storage, grade")
        rows = cursor.fetchall()
        products = [dict(row) for row in rows]
        conn.close()
        return products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.post("/api/products")
def upsert_product(product: ProductCreate):
    """
    Add a new product or update pricing/stock levels for an existing one.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # SQLite UPSERT syntax
        cursor.execute("""
            INSERT INTO products (brand, model, storage, grade, price, stock)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(brand, model, storage, grade)
            DO UPDATE SET
                price = excluded.price,
                stock = excluded.stock
        """, (product.brand, product.model, product.storage, product.grade, product.price, product.stock))
        
        conn.commit()
        
        # Retrieve the upserted row
        cursor.execute("""
            SELECT id, brand, model, storage, grade, price, stock 
            FROM products 
            WHERE brand = ? AND model = ? AND storage = ? AND grade = ?
        """, (product.brand, product.model, product.storage, product.grade))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
