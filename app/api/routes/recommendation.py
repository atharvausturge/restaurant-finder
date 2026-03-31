from fastapi import APIRouter
from app.repositories import restaurant_repository, menu_repository
from app.schemas.preferences import PreferencesSchema
from app.schemas.recommendation import RecommendationSchema
from app.services.recommendation_service import get_recommendations

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.post("/", response_model=list[RecommendationSchema])
def recommend_restaurants(preferences: PreferencesSchema):
    restaurants = restaurant_repository.get_all_restaurants()
    menu_items = menu_repository.get_all_menu_items()
    return get_recommendations(restaurants, menu_items, preferences)