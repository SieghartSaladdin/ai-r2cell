import sqlite3
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from src.core.database import get_db_connection
from src.core.event_bus import send_graph_event

@tool
def query_products(query: str = None, brand: str = None, model: str = None, grade: str = None, config: RunnableConfig = None) -> str:
    """
    Queries the database and lists matching phone specifications, grades, pricing, and stock levels.
    Use this tool when a customer asks about stock levels, phone grades, pricing, or specifications.
    
    Args:
        query (str, optional): General keyword to search in brand, model, storage, or grade.
        brand (str, optional): Brand filter (e.g., Apple, Samsung, Google, Xiaomi, Poco).
        model (str, optional): Model filter (e.g., iPhone 15, Galaxy S24, Pixel 8).
        grade (str, optional): Grade filter (Like New, Grade A, Grade B, Grade C+).
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown") if config else "unknown"
    send_graph_event("tools", "running", thread_id)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        sql = "SELECT brand, model, storage, grade, price, stock FROM products WHERE 1=1"
        params = []
        
        if brand:
            sql += " AND brand LIKE ?"
            params.append(f"%{brand}%")
        if model:
            sql += " AND model LIKE ?"
            params.append(f"%{model}%")
        if grade:
            sql += " AND grade = ?"
            params.append(grade)
        if query:
            sql += " AND (brand LIKE ? OR model LIKE ? OR storage LIKE ? OR grade LIKE ?)"
            q_param = f"%{query}%"
            params.extend([q_param, q_param, q_param, q_param])
            
        sql += " ORDER BY brand, model, storage, grade"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return "No matching products found in the inventory."
            
        formatted_list = []
        for row in rows:
            r = dict(row)
            # Formatting exactly for LLM visibility
            formatted_list.append(
                f"- Brand: {r['brand']}, Model: {r['model']}, Storage: {r['storage']}, Grade: {r['grade']}, Price: *${r['price']}*, Stock: {r['stock']} units"
            )
        return "\n".join(formatted_list)
        
    except Exception as e:
        return f"Error querying product database: {str(e)}"
    finally:
        send_graph_event("tools", "completed", thread_id)

@tool
def book_cod_appointment(
    customer_name: str, 
    customer_phone: str, 
    model: str, 
    storage: str, 
    grade: str, 
    date: str, 
    time: str, 
    config: RunnableConfig = None
) -> str:
    """
    Creates a Cash-on-Delivery (COD) appointment booking in the database.
    This tool automatically checks stock availability, calculates the price, and decrements stock on success.
    
    Args:
        customer_name (str): Full name of the customer.
        customer_phone (str): Phone number of the customer.
        model (str): Smartphone model name (e.g., iPhone 15 Pro Max, Galaxy S24 Ultra).
        storage (str): Storage capacity (e.g., 128 GB, 256 GB, 512 GB).
        grade (str): Cosmetic grade (Like New, Grade A, Grade B, Grade C+).
        date (str): Appointment date (e.g., YYYY-MM-DD or readable format).
        time (str): Appointment time (e.g., HH:MM or readable format).
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown") if config else "unknown"
    send_graph_event("tools", "running", thread_id)
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Look for matching product
        # Make search flexible using LIKE for model to support partial name match
        cursor.execute(
            "SELECT id, price, stock, brand, model, storage, grade FROM products WHERE model LIKE ? AND storage = ? AND grade = ?",
            (f"%{model}%", storage, grade)
        )
        product = cursor.fetchone()
        
        if not product:
            # Let's try exact match without LIKE just in case
            cursor.execute(
                "SELECT id, price, stock, brand, model, storage, grade FROM products WHERE model = ? AND storage = ? AND grade = ?",
                (model, storage, grade)
            )
            product = cursor.fetchone()
            
        if not product:
            conn.close()
            return f"Error: No product found matching Model: '{model}', Storage: '{storage}', Grade: '{grade}' in our database. Please double-check availability using query_products first."
            
        product_dict = dict(product)
        product_id = product_dict["id"]
        price = product_dict["price"]
        stock = product_dict["stock"]
        full_model_name = product_dict["model"]
        
        if stock <= 0:
            conn.close()
            return f"Error: '{full_model_name} {storage} ({grade})' is currently out of stock."
            
        # Create booking description
        model_storage_grade = f"{full_model_name} {storage} ({grade})"
        location = "R2Cell Bandung Central Hub (Jl. Asia Afrika No. 140, Bandung)"
        status = "Pending"
        
        # Insert booking record
        cursor.execute("""
            INSERT INTO bookings (customer_name, customer_phone, model_storage_grade, price, appointment_date, appointment_time, location, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, customer_phone, model_storage_grade, price, date, time, location, status))
        
        # Decrement stock by 1
        cursor.execute("UPDATE products SET stock = stock - 1 WHERE id = ?", (product_id,))
        
        conn.commit()
        conn.close()
        
        return (
            f"Success! Booking created successfully.\n"
            f"- *Booking ID*: [auto-assigned]\n"
            f"- *Customer Name*: {customer_name}\n"
            f"- *Customer Phone*: {customer_phone}\n"
            f"- *Device*: {model_storage_grade}\n"
            f"- *Price*: *${price}*\n"
            f"- *Date*: {date}\n"
            f"- *Time*: {time}\n"
            f"- *Meetup Location*: {location}\n"
            f"Please share this information with the customer and provide the Google Maps link: https://maps.google.com/?q=-6.917464,107.619122"
        )
        
    except Exception as e:
        return f"Error creating booking: {str(e)}"
    finally:
        send_graph_event("tools", "completed", thread_id)

@tool
def get_bandung_gmaps_location(config: RunnableConfig = None) -> str:
    """
    Returns the R2Cell Bandung office coordinates and Google Maps pin link.
    Use this tool whenever a customer asks for the meetup location, address, office location, or Google Maps pin.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown") if config else "unknown"
    send_graph_event("tools", "running", thread_id)
    try:
        return (
            "Meetup Location: *R2Cell Bandung Central Hub*\n"
            "Address: Jl. Asia Afrika No. 140, Bandung\n"
            "Google Maps Link: https://maps.google.com/?q=-6.917464,107.619122"
        )
    finally:
        send_graph_event("tools", "completed", thread_id)
