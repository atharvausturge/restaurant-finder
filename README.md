# Tavio - Restaurant Finder

Tavio is a FastAPI-based backend for Tavio an app for blind individuals to help with restaurant discovery, menu management, and preference-based recommendations,. 

It combines:
- Restaurant and menu storage in PostgreSQL
- Discovery via Google Places API
- Travel-time enrichment via Google Routes API
- Recommendation scoring based on cuisine, dietary restrictions, allergens, spice level, price, and travel time

## Requirements

- Python 3.10+
- PostgreSQL
- Google Places API key (also used for route matrix calls in current code)

# Setup

### 1. Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/restaurant_finder
GOOGLE_PLACES_API_KEY=your_google_api_key
```


### 4. Create database tables

```bash
python -m app.utils.create_tables
```

### 5. Run the API server

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Restaurants

- `GET /restaurants/`
	- Returns all restaurants.

- `GET /restaurants/{restaurant_id}`
	- Returns one restaurant by ID.
	- Returns `404` if not found.

### Menus

- `POST /restaurants/menus/bulk?restaurant_name=My%20Restaurant`
	- Creates menu items in bulk.
	- If the restaurant ID does not exist, it is created automatically with cuisine type `General`.

Example request body:

```json
[
	{
		"id": "item_001",
		"restaurant_id": "rest_001",
		"section_name": "Main Course",
		"name": "Chicken Biryani",
		"description": "Aromatic basmati rice with chicken",
		"price": 12.5,
		"dietary_info": ["halal"],
		"allergens": ["dairy"],
		"spice_level": "medium",
		"tags": ["rice", "high protein"],
		"is_available": true,
		"short_summary": "Classic biryani, medium spice"
	}
]
```

- `GET /restaurants/{restaurant_id}/menu`
	- Returns grouped menu items by section.
	- Returns `404` if no menu items are found for the restaurant.

### Recommendations

- `POST /recommendations/`
	- Returns top 3 restaurant recommendations based on preferences.

Example request body:

```json
{
	"cuisine_preferences": ["Indian", "Middle Eastern"],
	"dietary_restrictions": ["halal"],
	"allergen_exclusions": ["peanuts"],
	"spice_preference": "medium",
	"price_preference": "moderate",
	"max_travel_time_minutes": 20,
	"preferred_tags": ["high protein", "rice"]
}
```

### Discovery

- `GET /discover/restaurants`
	- Discovers restaurants from Google Places and enriches with route metrics.
	- Filters to restaurants that are currently open.
	- Optional max travel-time filter supported.

Query parameters:
- `query` (required)
- `latitude` (required)
- `longitude` (required)
- `radius_meters` (default `3000`)
- `travel_mode` (default `DRIVE`)
- `max_travel_time_minutes` (optional)

Example:

```bash
curl "http://localhost:8000/discover/restaurants?query=indian%20food&latitude=3.1390&longitude=101.6869&radius_meters=3000&travel_mode=DRIVE&max_travel_time_minutes=20"
```

- `GET /discover/places/autocomplete?query=...`
	- Returns place suggestions used by the menu builder UI.

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Google Places API
- Google Routes API
