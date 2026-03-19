"""
Dynamic ski resort database.

Fetches resort data from OpenStreetMap via Overpass API and matches
each resort to its nearest major airport using bundled OurAirports
data with haversine distance calculation.
"""

import csv
import json
import math
import os
import time
import httpx
import geopip
from models import Resort

# Cache the built resort database to avoid hitting Overpass on every startup
CACHE_FILE = os.path.join(os.path.dirname(__file__), "data", "resorts_cache.json")
CACHE_MAX_AGE_SECONDS = 604800  # refresh weekly


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Query OSM for named, non-abandoned ski resort areas with bounding boxes
OVERPASS_QUERY = (
    "[out:json][timeout:60];"
    '( way["landuse"="winter_sports"]["name"]["abandoned"!="yes"];'
    '  relation["landuse"="winter_sports"]["name"]["abandoned"!="yes"]; );'
    "out center bb;"
)

# Minimum bounding box area to filter out tubing hills, sledding areas, etc.
MIN_AREA_KM2 = 0.5

RESORTS: list[Resort] = []


def load_resorts(force_refresh: bool = False) -> list[Resort]:
    # Load resort database from cache, or fetch from Overpass if stale/missing
    global RESORTS

    if not force_refresh and cache_is_valid():
        RESORTS = load_cache()
    else:
        RESORTS = build_resort_database()
        save_cache(RESORTS)

    return RESORTS


def get_resort(name: str) -> Resort | None:
    # Case-insensitive lookup — matches if query is contained in the resort name
    name_lower = name.lower()
    for resort in RESORTS:
        if name_lower in resort.name.lower():
            return resort
    return None


def get_resorts_by_region(region: str) -> list[Resort]:
    # Filter resorts by region (case-insensitive partial match)
    region_lower = region.lower()
    return [r for r in RESORTS if region_lower in r.region.lower()]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    # Great-circle distance between two GPS points in kilometers
    r = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return r * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def load_airports(csv_path: str | None = None) -> list[dict]:
    # Load major airports from bundled OurAirports CSV (pre-filtered to large only)
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "data", "airports.csv")
        
    airports = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            airports.append({
                "name": row["name"],
                "city": row["municipality"] or "",
                "country": row["iso_country"],
                "iata": row["iata_code"],
                "latitude": float(row["latitude_deg"]),
                "longitude": float(row["longitude_deg"]),
            })
    return airports


def find_nearest_airport(lat: float, lon: float, airports: list[dict]) -> dict | None:
    # Find the closest airport to a given point using haversine distance
    best = None
    best_dist = float("inf")
    for airport in airports:
        dist = haversine_km(lat, lon, airport["latitude"], airport["longitude"])
        if dist < best_dist:
            best_dist = dist
            best = airport
    return best


def bbox_area_km2(bounds: dict) -> float:
    # Calculate rough area of a bounding box in km²
    lat_mid = math.radians((bounds["minlat"] + bounds["maxlat"]) / 2)
    width_km = (bounds["maxlon"] - bounds["minlon"]) * 111.32 * math.cos(lat_mid)
    height_km = (bounds["maxlat"] - bounds["minlat"]) * 111.32
    return abs(width_km * height_km)


def fetch_resorts_from_overpass() -> list[dict]:
    # Query OpenStreetMap for ski resorts via the Overpass API
    resp = httpx.post(OVERPASS_URL, data={"data": OVERPASS_QUERY}, timeout=60.0)
    resp.raise_for_status()
    data = resp.json()

    resorts = []
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        # Prefer English name for searchability, fall back to default name
        name = tags.get("name:en") or tags.get("name")
        if not name:
            continue

        # Skip small areas (tubing hills, sledding parks, etc.)
        bounds = element.get("bounds")
        if not bounds:
            continue
        area = round(bbox_area_km2(bounds), 2)
        if area < MIN_AREA_KM2:
            continue

        # Calculate center from bounding box
        lat = (bounds["minlat"] + bounds["maxlat"]) / 2
        lon = (bounds["minlon"] + bounds["maxlon"]) / 2
        resorts.append({"name": name, "latitude": lat, "longitude": lon, "area_km2": area})
    return resorts


def cache_is_valid() -> bool:
    # Check if the local cache file exists and is fresh enough
    if not os.path.exists(CACHE_FILE):
        return False
    age = time.time() - os.path.getmtime(CACHE_FILE)
    return age < CACHE_MAX_AGE_SECONDS


def save_cache(resorts: list[Resort]) -> None:
    # Write resort list to local JSON cache
    data = [r.model_dump() for r in resorts]
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_cache() -> list[Resort]:
    # Read resort list from local JSON cache
    with open(CACHE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    return [Resort(**entry) for entry in data]


def build_resort_database() -> list[Resort]:
    # Fetch resorts from Overpass, match each to its nearest airport
    raw_resorts = fetch_resorts_from_overpass()
    airports = load_airports()

    resorts = []
    for raw in raw_resorts:
        nearest = find_nearest_airport(raw["latitude"], raw["longitude"], airports)
        if nearest is None:
            continue

        # Get country code from actual country boundaries
        geo = geopip.search(lng=raw["longitude"], lat=raw["latitude"])
        region = geo.get("ISO2", "XX") if geo else "XX"

        resorts.append(Resort(
            name=raw["name"],
            region=region,
            latitude=raw["latitude"],
            longitude=raw["longitude"],
            elevation_m=0,
            area_km2=raw["area_km2"],
            nearest_airport=nearest["iata"],
            airport_name=nearest["name"],
        ))
    return resorts
