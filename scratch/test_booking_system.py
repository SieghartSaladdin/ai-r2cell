import os
import sys
import sqlite3

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.booking import query_products, book_cod_appointment, get_bandung_gmaps_location
from src.core.database import get_db_connection

def test_get_location():
    print("Testing get_bandung_gmaps_location...")
    res = get_bandung_gmaps_location.invoke({})
    assert "maps.google.com" in res, "Should contain maps URL"
    assert "-6.917464,107.619122" in res, "Should contain correct coordinates"
    print("[PASS] get_bandung_gmaps_location test passed!")

def test_query_products():
    print("Testing query_products...")
    
    # Test brand filter
    apple_res = query_products.invoke({"brand": "Apple"})
    assert "iPhone 15" in apple_res, "Should contain iPhone 15"
    assert "Galaxy" not in apple_res, "Should not contain Galaxy"
    
    # Test model filter
    s24_res = query_products.invoke({"model": "Galaxy S24 Ultra"})
    assert "Galaxy S24 Ultra" in s24_res, "Should contain Galaxy S24 Ultra"
    assert "iPhone" not in s24_res, "Should not contain iPhone"
    
    # Test grade filter
    grade_res = query_products.invoke({"grade": "Like New"})
    assert "Grade: Like New" in grade_res, "Should match grade filter"
    assert "Grade: Grade A" not in grade_res, "Should not contain Grade A"
    
    # Test no results
    empty_res = query_products.invoke({"brand": "NonExistentBrand"})
    assert "No matching products found" in empty_res, "Should handle empty results"
    
    print("[PASS] query_products test passed!")

def test_book_cod_appointment():
    print("Testing book_cod_appointment...")
    
    # Get initial stock of Apple iPhone 15 Pro Max 512 GB Like New
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, stock, price FROM products WHERE brand = 'Apple' AND model = 'iPhone 15 Pro Max' AND storage = '512 GB' AND grade = 'Like New'"
    )
    product = cursor.fetchone()
    assert product is not None, "Product should exist in seeded DB"
    initial_stock = product["stock"]
    price = product["price"]
    product_id = product["id"]
    conn.close()
    
    # Book appointment
    booking_params = {
        "customer_name": "Test Customer",
        "customer_phone": "+628123456789",
        "model": "iPhone 15 Pro Max",
        "storage": "512 GB",
        "grade": "Like New",
        "date": "2026-06-30",
        "time": "14:00"
    }
    
    booking_res = book_cod_appointment.invoke(booking_params)
    assert "Success! Booking created successfully." in booking_res, "Booking should be successful"
    assert f"${price}" in booking_res, "Booking confirmation should contain the price"
    
    # Verify stock decremented
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT stock FROM products WHERE id = ?", (product_id,))
    updated_stock = cursor.fetchone()["stock"]
    
    assert updated_stock == initial_stock - 1, f"Stock should decrement by 1. Expected {initial_stock - 1}, got {updated_stock}"
    
    # Verify booking record in DB
    cursor.execute(
        "SELECT id, customer_name, customer_phone, model_storage_grade, price, appointment_date, appointment_time, location, status FROM bookings WHERE customer_name = 'Test Customer'"
    )
    booking = cursor.fetchone()
    assert booking is not None, "Booking record should be inserted in DB"
    assert booking["customer_phone"] == "+628123456789"
    assert booking["model_storage_grade"] == "iPhone 15 Pro Max 512 GB (Like New)"
    assert booking["price"] == price
    assert booking["appointment_date"] == "2026-06-30"
    assert booking["appointment_time"] == "14:00"
    assert booking["status"] == "Pending"
    
    # Cleanup (Restore stock and delete test booking)
    cursor.execute("UPDATE products SET stock = ? WHERE id = ?", (initial_stock, product_id))
    cursor.execute("DELETE FROM bookings WHERE id = ?", (booking["id"],))
    conn.commit()
    conn.close()
    
    print("[PASS] book_cod_appointment test passed!")

if __name__ == "__main__":
    print("=== Running Booking System Tool Tests ===")
    test_get_location()
    test_query_products()
    test_book_cod_appointment()
    print("=== All Tests Completed Successfully ===")
