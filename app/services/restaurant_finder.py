import os
from dotenv import load_dotenv
import googlemaps
import sys
import re
import time
import requests
from html import unescape


def get_current_location():    
    # Try ip-api.com first (no API key needed, 45 requests/minute)
    try:
        response = requests.get('http://ip-api.com/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                lat = data.get('lat')
                lng = data.get('lon')
                city = data.get('city', '')
                region = data.get('regionName', '')
                country = data.get('country', '')
                if lat and lng:
                    location_name = ', '.join(filter(None, [city, region, country]))
                    return (lat, lng), location_name
    except Exception:
        pass
    
    # Fallback to ipapi.co
    try:
        response = requests.get('https://ipapi.co/json/', timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get('city', '')
            region = data.get('region', '')
            country = data.get('country_name', '')
            lat = data.get('latitude')
            lng = data.get('longitude')
            
            if lat and lng:
                location_name = ', '.join(filter(None, [city, region, country]))
                return (lat, lng), location_name
    except Exception:
        pass
    
    # Fallback to ipinfo.io
    try:
        response = requests.get('https://ipinfo.io/json', timeout=5)
        if response.status_code == 200:
            data = response.json()
            loc = data.get('loc', '')
            if loc and ',' in loc:
                lat, lng = map(float, loc.split(','))
                city = data.get('city', '')
                region = data.get('region', '')
                country = data.get('country', '')
                location_name = ', '.join(filter(None, [city, region, country]))
                return (lat, lng), location_name
    except Exception:
        pass
    
    return None, None


def search_restaurants(gmaps, location, keyword=None, min_rating=0, max_price=4, radius=5000):
    if isinstance(location, str):
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            print(f"Could not find location: {location}")
            return []
        coords = geocode_result[0]['geometry']['location']
        location = (coords['lat'], coords['lng'])
    
    print(f"Searching within {radius / 1609.34:.1f} miles ({radius} meters)...")
    
    places_result = gmaps.places_nearby(
        location=location,
        radius=radius,
        type='restaurant',
        keyword=keyword
    )
    
    restaurants = places_result.get('results', [])
    
    # Get additional pages of results (up to 60 total)
    while 'next_page_token' in places_result and len(restaurants) < 60:
        time.sleep(2)  # Required delay before using next_page_token
        places_result = gmaps.places_nearby(page_token=places_result['next_page_token'])
        restaurants.extend(places_result.get('results', []))
    
    print(f"Found {len(restaurants)} total restaurants from API")
    
    filtered = []
    for r in restaurants:
        rating = r.get('rating', 0)
        price_level = r.get('price_level', 0)
        
        if rating >= min_rating and price_level <= max_price:
            filtered.append(r)
    
    return filtered


def print_restaurants(restaurants):
    """Print restaurant results in a formatted way."""
    if not restaurants:
        print("No restaurants found matching your criteria.")
        return
    
    # Sort by rating (highest first) and take top 5
    sorted_restaurants = sorted(restaurants, key=lambda r: r.get('rating', 0), reverse=True)[:5]
    
    print(f"\nTop {len(sorted_restaurants)} of {len(restaurants)} restaurant(s):\n")
    print("-" * 60)
    
    for i, r in enumerate(sorted_restaurants, 1):
        name = r.get('name', 'Unknown')
        rating = r.get('rating', 'N/A')
        total_ratings = r.get('user_ratings_total', 0)
        price_level = r.get('price_level', 0)
        price_str = '$' * price_level if price_level else 'N/A'
        address = r.get('vicinity', 'Unknown address')
        is_open = r.get('opening_hours', {}).get('open_now', None)
        open_str = '(Open now)' if is_open else '(Closed)' if is_open is False else ''
        
        print(f"{i}. {name}")
        print(f"   Rating: {rating}/5 ({total_ratings} reviews) | Price: {price_str}")
        print(f"   Address: {address} {open_str}")
        print()


def print_directions(gmaps, origin, destination, mode='driving'):
    try:
        routes = gmaps.directions(origin, destination, mode=mode)
    except Exception as e:
        print("Error:", e)
        return

    if not routes:
        print("No routes found")
        return

    route = routes[0]
    leg = route.get('legs', [])[0]

    print(f"From: {leg.get('start_address')}")
    print(f"To:   {leg.get('end_address')}")
    print(f"Distance: {leg.get('distance',{}).get('text')}, Duration: {leg.get('duration',{}).get('text')}\n")

    steps = leg.get('steps', [])
    for i, step in enumerate(steps, start=1):
        instr = step.get('html_instructions', '')
        number = unescape(re.sub('<[^<]+?>', '', instr))
        distance = step.get('distance', {}).get('text', '')
        time = step.get('duration', {}).get('text', '')
        print(f"{i}. {number} ({distance}, {time})")


def main():
    load_dotenv()
    api_key = os.getenv("MAPS_API_KEY")

    if not api_key:
        print("MAPS_API_KEY not found in environment. Put it in a .env file as MAPS_API_KEY=your_key")
        sys.exit(1)

    gmaps = googlemaps.Client(key=api_key)

    print("=== Restaurant Finder ===\n")
    
    # Auto-detect location or get from input
    print("Detecting your location...")
    coords, location_name = get_current_location()
    
    if coords:
        print(f"Detected location: {location_name}")
        use_detected = input("Use this location? [Y/n]: ").strip().lower()
        if use_detected in ('', 'y', 'yes'):
            location = coords
        else:
            location = input("Enter your location (address or city): ")
    else:
        print("Could not auto-detect location.")
        location = input("Enter your location (address or city): ")
    
    keyword = input("Search keyword (e.g., italian, sushi, pizza) [optional]: ").strip() or None
    
    min_rating_input = input("Minimum rating (0-5) [default: 0]: ").strip()
    min_rating = float(min_rating_input) if min_rating_input else 0
    
    print("Budget levels: 0=free, 1=cheap ($), 2=moderate ($$), 3=expensive ($$$), 4=very expensive ($$$$)")
    max_price_input = input("Maximum price level (0-4) [default: 4]: ").strip()
    max_price = int(max_price_input) if max_price_input else 4
    
    radius_input = input("Search radius in miles [default: 5]: ").strip()
    radius = int((float(radius_input) if radius_input else 5) * 1609.34)
    
    # Search for restaurants
    print("\nSearching for restaurants...")
    restaurants = search_restaurants(gmaps, location, keyword, min_rating, max_price, radius)
    
    # Sort by rating and take top 5
    top_restaurants = sorted(restaurants, key=lambda r: r.get('rating', 0), reverse=True)[:5]
    print_restaurants(restaurants)
    
    # Optionally get directions to a restaurant
    if top_restaurants:
        choice = input("Get directions to a restaurant? Enter number (or press Enter to skip): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(top_restaurants):
            selected = top_restaurants[int(choice) - 1]
            destination = selected.get('vicinity', selected.get('name'))
            mode = input("Mode (driving/walking/bicycling/transit) [default: driving]: ").strip() or 'driving'
            print()
            print_directions(gmaps, location, destination, mode=mode)


if __name__ == "__main__":
    main()