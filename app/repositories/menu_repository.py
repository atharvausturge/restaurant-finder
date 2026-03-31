from app.core.database import SessionLocal
from app.models import MenuItem, Restaurant

def get_all_menu_items():
    db = SessionLocal()
    try:
        return db.query(MenuItem).all()
    finally:
        db.close()

def get_menu_by_restaurant_id(restaurant_id):
    db = SessionLocal()
    try:
        return db.query(MenuItem).filter(MenuItem.restaurant_id == restaurant_id).all()
    finally:
        db.close()

def get_sections_by_restaurant_id(restaurant_id):
    db = SessionLocal()
    try:
        rows = (
            db.query(MenuItem.section_name)
            .filter(MenuItem.restaurant_id == restaurant_id)
            .distinct()
            .all()
        )
        return [row[0] for row in rows]
    finally:
        db.close()