import argparse
import os
import re
import sys
from collections import Counter

import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv
import googlemaps

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.services import restaurant_finder as finder


def TTS(text):
    engine = pyttsx3.init()
    voices = engine.getProperty("voices")
    if voices:
        engine.setProperty("voice", voices[min(4, len(voices) - 1)].id)
    rate = engine.getProperty("rate")
    engine.setProperty("rate", rate - 75)
    engine.say(text)
    engine.runAndWait()


def _recognize_audio(recognizer, audio):
    try:
        text = recognizer.recognize_google(audio)
        print("You said: " + text)
        return text
    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""
    except sr.RequestError as e:
        print("Could not request results; {0}".format(e))
        return ""


def STT(timeout=10, phrase_time_limit=8):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Speak your food preference or cuisine...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(
            source,
            timeout=timeout,
            phrase_time_limit=phrase_time_limit,
        )
    return _recognize_audio(recognizer, audio)


def extract_keywords(text, top_n=5):
    stopwords = {
        "a",
        "an",
        "and",
        "are",
        "at",
        "be",
        "but",
        "by",
        "for",
        "from",
        "i",
        "in",
        "is",
        "it",
        "me",
        "my",
        "near",
        "of",
        "on",
        "or",
        "please",
        "restaurant",
        "restaurants",
        "show",
        "that",
        "the",
        "to",
        "want",
        "with",
        "find",
        "looking",
        "place",
        "places",
    }
    words = re.findall(r"[a-zA-Z]+", text.lower())
    filtered = [w for w in words if len(w) > 2 and w not in stopwords]
    counts = Counter(filtered)
    return [word for word, _ in counts.most_common(top_n)]


def run_finder_with_keywords(keywords, radius_miles=5, min_rating=0, max_price=4):
    load_dotenv(os.path.join(PROJECT_ROOT, ".env"))
    api_key = os.getenv("MAPS_API_KEY")
    if not api_key:
        raise RuntimeError("MAPS_API_KEY not found in .env")

    gmaps = googlemaps.Client(key=api_key)

    coords, location_name = finder.get_current_location()
    if not coords:
        raise RuntimeError("Could not auto-detect location")

    keyword_query = " ".join(keywords).strip() or None
    radius = int(radius_miles * 1609.34)

    restaurants = finder.search_restaurants(
        gmaps=gmaps,
        location=coords,
        keyword=keyword_query,
        min_rating=min_rating,
        max_price=max_price,
        radius=radius,
    )

    top_restaurants = sorted(
        restaurants,
        key=lambda r: r.get("rating", 0),
        reverse=True,
    )[:3]

    if not top_restaurants:
        return f"I could not find matching restaurants near {location_name}."

    lines = [f"I found {len(restaurants)} options near {location_name}. Top picks are:"]
    for i, r in enumerate(top_restaurants, start=1):
        name = r.get("name", "Unknown")
        rating = r.get("rating", "N/A")
        address = r.get("vicinity", "Unknown address")
        lines.append(f"{i}. {name}, rated {rating}, at {address}.")
    return " ".join(lines)


def execute_pipeline(raw_text=None):
    TTS("Tell me what kind of restaurant you want.")

    transcript = raw_text.strip() if raw_text else STT()
    if not transcript:
        TTS("I could not capture your request. Please try again.")
        return

    keywords = extract_keywords(transcript)
    print("Extracted keywords:", keywords)

    if not keywords:
        TTS("I could not extract keywords from your request. Please try again.")
        return

    summary = run_finder_with_keywords(keywords)
    print("Finder output:", summary)
    TTS(summary)


def main():
    parser = argparse.ArgumentParser(
        description="STT to keyword to finder to TTS pipeline"
    )
    parser.add_argument(
        "--text", default="", help="Optional text to bypass STT for testing"
    )
    args = parser.parse_args()

    execute_pipeline(raw_text=args.text)


if __name__ == "__main__":
    main()
