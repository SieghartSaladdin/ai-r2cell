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
        
        # Storage and grade are matched exactly (ignoring case and spaces, so "256GB" == "256 GB").
        base_sql = (
            "SELECT id, price, stock, brand, model, storage, grade FROM products "
            "WHERE REPLACE(storage, ' ', '') = REPLACE(?, ' ', '') COLLATE NOCASE "
            "AND grade = ? COLLATE NOCASE "
        )

        # 1. Exact model match first ("iPhone 15" must never resolve to "iPhone 15 Pro Max").
        cursor.execute(
            base_sql + "AND (model = ? COLLATE NOCASE OR brand || ' ' || model = ? COLLATE NOCASE)",
            (storage, grade, model.strip(), model.strip())
        )
        matches = cursor.fetchall()

        # 2. Fall back to partial match, but only accept it when it is unambiguous.
        if not matches:
            cursor.execute(base_sql + "AND model LIKE ?", (storage, grade, f"%{model.strip()}%"))
            matches = cursor.fetchall()
            candidates = sorted({row["model"] for row in matches})
            if len(candidates) > 1:
                conn.close()
                return (
                    f"Error: Model '{model}' is ambiguous for {storage} ({grade}). "
                    f"Matching models: {', '.join(candidates)}. "
                    f"Ask the customer which exact model they want, then retry."
                )

        if not matches:
            conn.close()
            return f"Error: No product found matching Model: '{model}', Storage: '{storage}', Grade: '{grade}' in our database. Please double-check availability using query_products first."

        product_dict = dict(matches[0])
        product_id = product_dict["id"]
        price = product_dict["price"]
        stock = product_dict["stock"]
        full_model_name = product_dict["model"]
        storage = product_dict["storage"]
        grade = product_dict["grade"]

        if stock <= 0:
            conn.close()
            return f"Error: '{full_model_name} {storage} ({grade})' is currently out of stock."

        # Create booking description
        model_storage_grade = f"{full_model_name} {storage} ({grade})"
        location = "R2Cell Bandung Central Hub (Jl. Asia Afrika No. 140, Bandung)"
        status = "Pending"
        
        # Decrement stock first, atomically, so concurrent bookings can't oversell the last unit
        cursor.execute("UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0", (product_id,))
        if cursor.rowcount == 0:
            conn.rollback()
            conn.close()
            return f"Error: '{model_storage_grade}' is currently out of stock."

        # Insert booking record
        cursor.execute("""
            INSERT INTO bookings (customer_name, customer_phone, model_storage_grade, price, appointment_date, appointment_time, location, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (customer_name, customer_phone, model_storage_grade, price, date, time, location, status))
        booking_id = cursor.lastrowid

        conn.commit()
        conn.close()

        return (
            f"Success! Booking created successfully.\n"
            f"- *Booking ID*: {booking_id}\n"
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
