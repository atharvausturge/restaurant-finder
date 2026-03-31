import dotenv
import os
import requests

dotenv.load_dotenv()

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
GOOGLE_PLACES_BASE_URL = "https://places.googleapis.com/v1"

if not GOOGLE_PLACES_API_KEY:
    raise ValueError("GOOGLE_PLACES_API_KEY is not set")

def search_restaurants(query, latitude, longitude, radius_meters=None):
    url = f"{GOOGLE_PLACES_BASE_URL}/places:searchText"
    
    if radius_meters is None:
        radius_meters = 5000
        
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join([
            "places.id",
            "places.displayName",
            "places.formattedAddress",
            "places.location",
            "places.rating",
            "places.priceLevel",
            "places.primaryType",
            "places.types",
            "places.currentOpeningHours.openNow",
        ]),
    }
    
    payload = {
        "textQuery": query,
        "locationBias": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": radius_meters,
            }
        }
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    
    data = response.json()
    return [normalize_google_place(place) for place in data.get("places", [])]
        

def autocomplete_places(query):
    url = f"{GOOGLE_PLACES_BASE_URL}/places:searchText"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": "places.id,places.displayName,places.formattedAddress",
    }
    
    payload = {
        "textQuery": query
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    
    if not response.ok:
        return {"places": []}
    
    return response.json()


def get_restaurant_details(place_id):
    url = f"{GOOGLE_PLACES_BASE_URL}/places/{place_id}"
    
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_PLACES_API_KEY,
        "X-Goog-FieldMask": ",".join([
            "id",
            "displayName",
            "formattedAddress",
            "location",
            "rating",
            "priceLevel",
            "primaryType",
            "types",
            "currentOpeningHours.openNow",
            "nationalPhoneNumber",
            "websiteUri",
        ]),
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    data = response.json()
    return normalize_google_place(data)

def generate_restaurant_short_summary(cuisine_type, rating, price_level):
    parts = []

    if price_level is not None:
        if price_level == "cheap":
            parts.append("Budget-friendly")
        elif price_level == "moderate":
            parts.append("Moderately priced")
        elif price_level == "expensive":
            parts.append("Higher-end")

    if cuisine_type and cuisine_type != "Restaurant":
        parts.append(cuisine_type)
    else:
        parts.append("Restaurant")

    summary = " ".join(parts)

    if rating is not None:
        summary += f" rated {rating} stars"

    return summary

def normalize_google_place(details):
    place_id = details.get("id")
    name = details.get("displayName", {}).get("text", "")
    raw_cuisine_type = details.get("primaryType", "")
    formatted_address = details.get("formattedAddress")
    phone_number = details.get("nationalPhoneNumber")

    cuisine_type = raw_cuisine_type.replace("_restaurant", "").replace("_", " ").title()
    if not cuisine_type:
        cuisine_type = "Restaurant"

    rating = details.get("rating")

    raw_price_level = details.get("priceLevel")
    if raw_price_level == "PRICE_LEVEL_INEXPENSIVE":
        price_level = "cheap"
    elif raw_price_level == "PRICE_LEVEL_MODERATE":
        price_level = "moderate"
    elif raw_price_level in ["PRICE_LEVEL_EXPENSIVE", "PRICE_LEVEL_VERY_EXPENSIVE"]:
        price_level = "expensive"
    else:
        price_level = None

    is_open = details.get("currentOpeningHours", {}).get("openNow", None)
    menu_available = False
    dietary_options = []
    short_summary = generate_restaurant_short_summary(cuisine_type, rating, price_level)
    
    location = details.get("location", {})
    latitude = location.get("latitude")
    longitude = location.get("longitude")
    
    website_uri = details.get("websiteUri", None)

    return {
        "id": place_id,
        "name": name,
        "cuisine_type": cuisine_type,
        "rating": rating,
        "price_level": price_level,
        "is_open": is_open,
        "menu_available": menu_available,
        "dietary_options": dietary_options,
        "short_summary": short_summary,
        "formatted_address": formatted_address,
        "phone_number": phone_number,
        "latitude": latitude,
        "longitude": longitude,
        "website_url": website_uri,
    }
