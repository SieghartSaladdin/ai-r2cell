from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from src.core.database import get_db_connection

router = APIRouter(tags=["bookings"])

class BookingUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    model_storage_grade: Optional[str] = None
    price: Optional[int] = None
    appointment_date: Optional[str] = None
    appointment_time: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None

@router.get("/api/bookings")
def list_bookings():
    """
    Retrieve all recorded COD bookings.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, customer_name, customer_phone, model_storage_grade, price, appointment_date, appointment_time, location, status FROM bookings ORDER BY id DESC")
        rows = cursor.fetchall()
        bookings = [dict(row) for row in rows]
        conn.close()
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.patch("/api/bookings/{booking_id}")
def update_booking(booking_id: int, booking: BookingUpdate):
    """
    Modify a booking's status or details.
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if booking exists
        cursor.execute("SELECT id FROM bookings WHERE id = ?", (booking_id,))
        row = cursor.fetchone()
        if not row:
            conn.close()
            raise HTTPException(status_code=404, detail="Booking not found")
        
        # Build dynamic update query
        update_data = booking.dict(exclude_unset=True)
        if not update_data:
            cursor.execute("SELECT id, customer_name, customer_phone, model_storage_grade, price, appointment_date, appointment_time, location, status FROM bookings WHERE id = ?", (booking_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row)
            
        fields = []
        values = []
        for key, value in update_data.items():
            fields.append(f"{key} = ?")
            values.append(value)
        values.append(booking_id)
        
        query = f"UPDATE bookings SET {', '.join(fields)} WHERE id = ?"
        cursor.execute(query, tuple(values))
        conn.commit()
        
        # Get updated row
        cursor.execute("SELECT id, customer_name, customer_phone, model_storage_grade, price, appointment_date, appointment_time, location, status FROM bookings WHERE id = ?", (booking_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
