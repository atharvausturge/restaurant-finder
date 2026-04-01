from fastapi import APIRouter, HTTPException, Depends
from typing import List
from app.services.menu_service import get_restaurant_menu
from app.schemas.menu import MenuSchema
from app.core.database import SessionLocal


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


from sqlalchemy.orm import Session
from app.models.menu_item import MenuItem
from app.models.restaurant import Restaurant

from app.services.restaurant_discovery_service import get_restaurant_details

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.post("/menus/bulk", status_code=201)
def create_menus(
    menus: List[MenuSchema],
    restaurant_name: str = "New Restaurant",
    db: Session = Depends(get_db),
):
    if not menus:
        return {"message": "No menus to create", "count": 0}

    restaurant_id = menus[0].restaurant_id
    restaurant = db.query(Restaurant).filter(Restaurant.id == restaurant_id).first()

    if not restaurant:
        try:
            details = get_restaurant_details(restaurant_id)
            restaurant = Restaurant(
                id=restaurant_id,
                name=details.get("name") or restaurant_name,
                cuisine_type=details.get("cuisine_type") or "General",
                rating=details.get("rating"),
                price_level=details.get("price_level"),
                is_open=(
                    details.get("is_open")
                    if details.get("is_open") is not None
                    else True
                ),
                menu_available=True,
                dietary_options=[],
                short_summary=details.get("short_summary"),
            )
        except Exception as e:
            print(f"Failed to fetch from Google Places: {e}")
            restaurant = Restaurant(
                id=restaurant_id,
                name=restaurant_name,
                cuisine_type="General",
                menu_available=True,
            )
        db.add(restaurant)
        db.commit()

    db_items = []
    for menu in menus:
        db_item = MenuItem(
            id=menu.id,
            restaurant_id=menu.restaurant_id,
            section_name=menu.section_name,
            name=menu.name,
            description=menu.description,
            price=menu.price,
            dietary_info=menu.dietary_info,
            allergens=menu.allergens,
            spice_level=menu.spice_level,
            tags=menu.tags,
            is_available=menu.is_available,
            short_summary=menu.short_summary,
        )
        db_items.append(db_item)
        db.add(db_item)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    return {"message": "Menus created successfully", "count": len(db_items)}


@router.get("/{restaurant_id}/menu")
def get_menu(restaurant_id: str):
    result = get_restaurant_menu(restaurant_id)
    if not result["menu"]:
        raise HTTPException(
            status_code=404, detail="Menu not found for this restaurant"
        )
    return result
