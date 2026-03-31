import dotenv
import os
import requests
import app.services.restaurant_discovery_service

dotenv.load_dotenv()

GOOGLE_ROUTES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

def get_route_matrix(origin_lat, origin_lng, destinations, travel_mode="DRIVE"):
    if not GOOGLE_ROUTES_API_KEY:
        raise ValueError("GOOGLE_ROUTES_API_KEY is not set")

    url = "https://routes.googleapis.com/distanceMatrix/v2:computeRouteMatrix"

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_ROUTES_API_KEY,
        "X-Goog-FieldMask": "originIndex,destinationIndex,status,condition,distanceMeters,duration,staticDuration",
    }

    payload = {
        "origins": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": origin_lat,
                            "longitude": origin_lng,
                        }
                    }
                }
            }
        ],
        "destinations": [
            {
                "waypoint": {
                    "location": {
                        "latLng": {
                            "latitude": dest["latitude"],
                            "longitude": dest["longitude"],
                        }
                    }
                }
            }
            for dest in destinations
        ],
        "travelMode": travel_mode,
        "routingPreference": "TRAFFIC_AWARE",
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()

    return response.json()


def parse_duration_seconds(duration_value):
    if not duration_value:
        return None
    if isinstance(duration_value, str) and duration_value.endswith("s"):
        try:
            return int(float(duration_value[:-1]))
        except ValueError:
            return None
    return None


def attach_route_info_to_restaurants(restaurants, route_matrix):
    for restaurant in restaurants:
        restaurant["travel_time_seconds"] = None
        restaurant["travel_time_minutes"] = None
        restaurant["static_travel_time_seconds"] = None
        restaurant["distance_meters"] = None

    for element in route_matrix:
        destination_index = element.get("destinationIndex")

        if destination_index is None or destination_index >= len(restaurants):
            continue

        restaurant = restaurants[destination_index]

        if element.get("condition") == "ROUTE_EXISTS":
            travel_time_seconds = parse_duration_seconds(element.get("duration"))
            static_travel_time_seconds = parse_duration_seconds(element.get("staticDuration"))

            restaurant["distance_meters"] = element.get("distanceMeters")
            restaurant["travel_time_seconds"] = travel_time_seconds
            restaurant["travel_time_minutes"] = (
                round(travel_time_seconds / 60, 1) if travel_time_seconds is not None else None
            )
            restaurant["static_travel_time_seconds"] = static_travel_time_seconds

    return restaurants