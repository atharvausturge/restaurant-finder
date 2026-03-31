from fastapi import APIRouter, HTTPException
from app.repositories import restaurant_repository
from app.schemas.restaurant import RestaurantSchema

router = APIRouter(prefix="/restaurants", tags=["restaurants"])


@router.get("/", response_model=list[RestaurantSchema])
def get_restaurants():
    return restaurant_repository.get_all_restaurants()


@router.get("/{restaurant_id}", response_model=RestaurantSchema)
def get_restaurant(restaurant_id: str):
    restaurant = restaurant_repository.get_restaurant_by_id(restaurant_id)
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    return restaurant