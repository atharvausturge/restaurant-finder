from app.core.database import SessionLocal
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem

db = SessionLocal()

try:
    db.query(MenuItem).delete()
    db.query(Restaurant).delete()
    db.commit()
finally:
    db.close()