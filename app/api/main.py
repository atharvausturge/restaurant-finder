import json
import os
import re
from html import unescape
from pathlib import Path
from typing import Any

import googlemaps
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, model_validator

from app.services.restaurant_finder import search_restaurants

BASE_DIR = Path(__file__).resolve().parent
APP_DIR = BASE_DIR.parent
CONFIG_DIR = APP_DIR / "config"
PROFILE_PATH = CONFIG_DIR / "user_profile.json"
LEGACY_PROFILE_PATH = BASE_DIR / "user_profile.json"
QUESTIONS_PATH = CONFIG_DIR / "questions.txt"
LEGACY_QUESTIONS_PATH = APP_DIR.parent / "ttsconfig" / "questions.txt"


class Coordinates(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


class RestaurantSearchRequest(BaseModel):
    location_query: str | None = None
    location_coords: Coordinates | None = None
    keyword: str | None = None
    min_rating: float = Field(0, ge=0, le=5)
    max_price: int = Field(4, ge=0, le=4)
    radius_meters: int = Field(8046, ge=100, le=50000)
    limit: int = Field(10, ge=1, le=60)

    @model_validator(mode="after")
    def validate_location(self):
        if not self.location_query and not self.location_coords:
            raise ValueError("Provide either location_query or location_coords")
        return self


class DirectionsRequest(BaseModel):
    origin_query: str | None = None
    origin_coords: Coordinates | None = None
    destination_query: str | None = None
    destination_coords: Coordinates | None = None
    mode: str = Field("driving", pattern="^(driving|walking|bicycling|transit)$")

    @model_validator(mode="after")
    def validate_locations(self):
        has_origin = self.origin_query or self.origin_coords
        has_destination = self.destination_query or self.destination_coords
        if not has_origin or not has_destination:
            raise ValueError(
                "Provide origin and destination, each as query or coordinates"
            )
        return self


class ProfileUpdateRequest(BaseModel):
    profile: dict[str, Any]


def _load_profile() -> dict[str, Any]:
    profile_path = PROFILE_PATH if PROFILE_PATH.exists() else LEGACY_PROFILE_PATH
    if not profile_path.exists():
        return {}
    with profile_path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _save_profile(profile: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with PROFILE_PATH.open("w", encoding="utf-8") as handle:
        json.dump(profile, handle, indent=2, ensure_ascii=False)


def _load_questions() -> list[dict[str, str]]:
    questions_path = (
        QUESTIONS_PATH if QUESTIONS_PATH.exists() else LEGACY_QUESTIONS_PATH
    )
    if not questions_path.exists():
        return []
    questions: list[dict[str, str]] = []
    with questions_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#") or "|" not in line:
                continue
            key, question = line.split("|", 1)
            questions.append({"key": key.strip(), "question": question.strip()})
    return questions


def _init_gmaps_client() -> googlemaps.Client:
    load_dotenv()
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("MAPS_API_KEY is not set")
    return googlemaps.Client(key=api_key)


def _normalize_restaurant(place: dict[str, Any]) -> dict[str, Any]:
    return {
        "place_id": place.get("place_id"),
        "name": place.get("name"),
        "rating": place.get("rating"),
        "user_ratings_total": place.get("user_ratings_total"),
        "price_level": place.get("price_level"),
        "address": place.get("vicinity") or place.get("formatted_address"),
        "location": place.get("geometry", {}).get("location"),
        "open_now": place.get("opening_hours", {}).get("open_now"),
        "types": place.get("types", []),
    }


def _step_html_to_text(html_instruction: str) -> str:
    return unescape(re.sub("<[^<]+?>", "", html_instruction or "")).strip()


def _normalize_directions_route(route: dict[str, Any]) -> dict[str, Any]:
    leg = route.get("legs", [{}])[0]
    steps = leg.get("steps", [])
    return {
        "start_address": leg.get("start_address"),
        "end_address": leg.get("end_address"),
        "distance": leg.get("distance", {}).get("text"),
        "duration": leg.get("duration", {}).get("text"),
        "steps": [
            {
                "instruction": _step_html_to_text(step.get("html_instructions", "")),
                "distance": step.get("distance", {}).get("text"),
                "duration": step.get("duration", {}).get("text"),
            }
            for step in steps
        ],
    }


app = FastAPI(title="Restaurant Finder API", version="1.0.0")

allowed_origins = [
    origin.strip() for origin in os.getenv("ALLOWED_ORIGINS", "*").split(",")
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/profile")
def get_profile() -> dict[str, Any]:
    return {"profile": _load_profile()}


@app.put("/profile")
def update_profile(payload: ProfileUpdateRequest) -> dict[str, Any]:
    _save_profile(payload.profile)
    return {"saved": True, "profile": payload.profile}


@app.get("/profile/questions")
def get_profile_questions() -> dict[str, Any]:
    return {"questions": _load_questions()}


@app.post("/restaurants/search")
def restaurants_search(payload: RestaurantSearchRequest) -> dict[str, Any]:
    try:
        gmaps = _init_gmaps_client()
        if payload.location_coords:
            location: str | tuple[float, float] = (
                payload.location_coords.lat,
                payload.location_coords.lng,
            )
        else:
            location = payload.location_query or ""

        restaurants = search_restaurants(
            gmaps=gmaps,
            location=location,
            keyword=payload.keyword,
            min_rating=payload.min_rating,
            max_price=payload.max_price,
            radius=payload.radius_meters,
        )

        restaurants = sorted(
            restaurants,
            key=lambda item: item.get("rating", 0),
            reverse=True,
        )[: payload.limit]

        return {
            "count": len(restaurants),
            "restaurants": [_normalize_restaurant(item) for item in restaurants],
        }
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Search failed: {error}"
        ) from error


@app.post("/directions")
def directions(payload: DirectionsRequest) -> dict[str, Any]:
    try:
        gmaps = _init_gmaps_client()

        origin: str | tuple[float, float]
        destination: str | tuple[float, float]

        if payload.origin_coords:
            origin = (payload.origin_coords.lat, payload.origin_coords.lng)
        else:
            origin = payload.origin_query or ""

        if payload.destination_coords:
            destination = (
                payload.destination_coords.lat,
                payload.destination_coords.lng,
            )
        else:
            destination = payload.destination_query or ""

        routes = gmaps.directions(origin, destination, mode=payload.mode)
        if not routes:
            raise HTTPException(status_code=404, detail="No routes found")

        return {"mode": payload.mode, "route": _normalize_directions_route(routes[0])}
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch directions: {error}"
        ) from error
