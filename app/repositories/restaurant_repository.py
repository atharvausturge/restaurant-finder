from app.core.database import SessionLocal
from app.models import MenuItem, Restaurant

def get_all_restaurants():
    db = SessionLocal()
    try:
        return db.query(Restaurant).all()
    finally:
        db.close()
        
def get_restaurant_by_id(restaurant_id):
    db = SessionLocal()
    try:
        return db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()
    finally:
        db.close()