from app.core.database import engine, Base
from app.models.restaurant import Restaurant
from app.models.menu_item import MenuItem

if __name__ == "__main__": 
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully")