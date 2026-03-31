from fastapi import APIRouter, HTTPException, Query

from app.services.restaurant_discovery_service import search_restaurants, autocomplete_places
from app.services.travel_time_service import (
    get_route_matrix,
    attach_route_info_to_restaurants,
)

router = APIRouter(prefix="/discover", tags=["discovery"])


@router.get("/restaurants")
def discover_restaurants(
    query: str = Query(..., min_length=1),
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_meters: int = Query(3000, gt=0),
    travel_mode: str = Query("DRIVE"),
    max_travel_time_minutes: float | None = Query(None, ge=0),
):
    restaurants = search_restaurants(
        query=query,
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
    )

    if not restaurants:
        return []

    valid_restaurants = [
        restaurant
        for restaurant in restaurants
        if restaurant.get("latitude") is not None
        and restaurant.get("longitude") is not None
    ]

    if not valid_restaurants:
        raise HTTPException(status_code=404, detail="No valid restaurant locations found")

    destinations = [
        {
            "latitude": restaurant["latitude"],
            "longitude": restaurant["longitude"],
        }
        for restaurant in valid_restaurants
    ]

    route_matrix = get_route_matrix(
        origin_lat=latitude,
        origin_lng=longitude,
        destinations=destinations,
        travel_mode=travel_mode,
    )

    enriched_restaurants = attach_route_info_to_restaurants(valid_restaurants, route_matrix)

    if max_travel_time_minutes is not None:
        enriched_restaurants = [
            restaurant
            for restaurant in enriched_restaurants
            if restaurant.get("travel_time_minutes") is not None
            and restaurant["travel_time_minutes"] <= max_travel_time_minutes
        ]

    enriched_restaurants = [
        restaurant
        for restaurant in enriched_restaurants
        if restaurant.get("is_open") is True
    ]

    return enriched_restaurants


@router.get("/places/autocomplete")
def get_places_autocomplete(query: str = Query(..., min_length=2)):
    return autocomplete_places(query)