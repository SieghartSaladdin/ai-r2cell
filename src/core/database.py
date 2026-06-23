import os
import sqlite3

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# CURRENT_DIR is project_root/src/core
WORKSPACE_ROOT = os.path.dirname(os.path.dirname(CURRENT_DIR))
CHECKPOINTS_DB_PATH = os.path.join(WORKSPACE_ROOT, "checkpoints.db")

def get_db_connection():
    conn = sqlite3.connect(CHECKPOINTS_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        brand TEXT NOT NULL,
        model TEXT NOT NULL,
        storage TEXT NOT NULL,
        grade TEXT NOT NULL,
        price INTEGER NOT NULL,
        stock INTEGER NOT NULL,
        UNIQUE(brand, model, storage, grade)
    )
    """)
    
    # Create bookings table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS bookings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_name TEXT NOT NULL,
        customer_phone TEXT NOT NULL,
        model_storage_grade TEXT NOT NULL,
        price INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        location TEXT NOT NULL,
        status TEXT NOT NULL
    )
    """)
    
    # Check if products is empty to decide whether to seed
    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Seed products
        # List of tuple: (brand, model, storage, grades_prices)
        # where grades_prices is a dict of {grade: price}
        seed_data = [
            # iPhones
            ("Apple", "iPhone 15 Pro Max", "512 GB", {"Like New": 1149, "Grade A": 1049, "Grade B": 949, "Grade C+": 829}),
            ("Apple", "iPhone 15 Pro Max", "256 GB", {"Like New": 1029, "Grade A": 939, "Grade B": 849, "Grade C+": 739}),
            ("Apple", "iPhone 15 Pro", "256 GB", {"Like New": 919, "Grade A": 829, "Grade B": 749, "Grade C+": 649}),
            ("Apple", "iPhone 15 Pro", "128 GB", {"Like New": 829, "Grade A": 749, "Grade B": 679, "Grade C+": 589}),
            ("Apple", "iPhone 15", "256 GB", {"Like New": 719, "Grade A": 649, "Grade B": 579, "Grade C+": 499}),
            ("Apple", "iPhone 15", "128 GB", {"Like New": 629, "Grade A": 569, "Grade B": 499, "Grade C+": 429}),
            ("Apple", "iPhone 14 Pro Max", "256 GB", {"Like New": 829, "Grade A": 749, "Grade B": 679, "Grade C+": 589}),
            ("Apple", "iPhone 14 Pro", "128 GB", {"Like New": 729, "Grade A": 659, "Grade B": 599, "Grade C+": 519}),
            ("Apple", "iPhone 13", "128 GB", {"Like New": 479, "Grade A": 429, "Grade B": 379, "Grade C+": 319}),
            # Samsung Galaxy
            ("Samsung", "Galaxy S24 Ultra", "256 GB", {"Like New": 979, "Grade A": 879, "Grade B": 789, "Grade C+": 689}),
            ("Samsung", "Galaxy S24+", "256 GB", {"Like New": 799, "Grade A": 719, "Grade B": 649, "Grade C+": 559}),
            ("Samsung", "Galaxy S24", "128 GB", {"Like New": 619, "Grade A": 559, "Grade B": 499, "Grade C+": 419}),
            ("Samsung", "Galaxy S23 Ultra", "256 GB", {"Like New": 799, "Grade A": 719, "Grade B": 649, "Grade C+": 559}),
            ("Samsung", "Galaxy S23", "128 GB", {"Like New": 499, "Grade A": 449, "Grade B": 399, "Grade C+": 339}),
            ("Samsung", "Galaxy S22", "128 GB", {"Like New": 359, "Grade A": 319, "Grade B": 279, "Grade C+": 229}),
            ("Samsung", "Galaxy A55 5G", "128 GB", {"Like New": 369, "Grade A": 329, "Grade B": 289, "Grade C+": 239}),
            ("Samsung", "Galaxy A35 5G", "128 GB", {"Like New": 279, "Grade A": 249, "Grade B": 219, "Grade C+": 179}),
            # Google Pixel
            ("Google", "Pixel 8 Pro", "256 GB", {"Like New": 699, "Grade A": 629, "Grade B": 559, "Grade C+": 479}),
            ("Google", "Pixel 8", "128 GB", {"Like New": 499, "Grade A": 449, "Grade B": 399, "Grade C+": 339}),
            ("Google", "Pixel 7a", "128 GB", {"Like New": 299, "Grade A": 269, "Grade B": 239, "Grade C+": 199}),
            # Xiaomi / Redmi / Poco
            ("Xiaomi", "Xiaomi 14 Ultra", "512 GB", {"Like New": 949, "Grade A": 849, "Grade B": 759, "Grade C+": 659}),
            ("Xiaomi", "Xiaomi 14", "256 GB", {"Like New": 629, "Grade A": 559, "Grade B": 499, "Grade C+": 429}),
            ("Xiaomi", "Redmi Note 13 Pro+", "256 GB", {"Like New": 319, "Grade A": 289, "Grade B": 249, "Grade C+": 209}),
            ("Xiaomi", "Redmi Note 13 Pro", "256 GB", {"Like New": 239, "Grade A": 209, "Grade B": 179, "Grade C+": 149}),
            ("Poco", "Poco F6 Pro", "256 GB", {"Like New": 419, "Grade A": 379, "Grade B": 339, "Grade C+": 289}),
            ("Xiaomi", "Redmi 13C", "128 GB", {"Like New": 99, "Grade A": 89, "Grade B": 79, "Grade C+": 65}),
        ]
        
        for brand, model, storage, grades_prices in seed_data:
            for grade, price in grades_prices.items():
                cursor.execute(
                    "INSERT INTO products (brand, model, storage, grade, price, stock) VALUES (?, ?, ?, ?, ?, ?)",
                    (brand, model, storage, grade, price, 10) # Seed with default stock of 10
                )
        conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database tables initialized and seeded successfully.")
