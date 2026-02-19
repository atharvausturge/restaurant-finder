import os
from dotenv import load_dotenv
import googlemaps
import sys
import re
from html import unescape


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

    start = input("Enter origin address: ")
    end = input("Enter destination address: ")
    mode = input("Mode (driving/walking/bicycling/transit)")

    print()
    print_directions(gmaps, start, end, mode=mode)


if __name__ == "__main__":
    main()