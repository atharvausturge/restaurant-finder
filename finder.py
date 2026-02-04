import os
from dotenv import load_dotenv
import googlemaps

def main():
    load_dotenv()
    api_key = os.getenv("MAPS_API_KEY")
    gmaps = googlemaps.Client(key=api_key)

    address = input("Enter an address to geocode: ")
    
    geocode_result = gmaps.geocode(address)

    print(geocode_result)



if __name__ == "__main__":
    main()