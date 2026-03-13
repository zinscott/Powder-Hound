r"""Test the dynamic resort database step by step."""

import sys
sys.path.insert(0, "src")

from resorts import (
    load_airports, find_nearest_airport, fetch_resorts_from_overpass,
    haversine_km, load_resorts, get_resort, get_resorts_by_region,
)

# --- Step 1: Test airport loading ---
print("Loading airports...")
airports = load_airports()
print(f"Loaded {len(airports)} major airports with IATA codes")

# --- Step 2: Test haversine calculation ---
# Denver to SLC should be ~590 km
dist = haversine_km(39.8561, -104.6737, 40.7899, -111.9791)
print(f"Denver to SLC: {dist:.0f} km (expected ~590)")

# --- Step 3: Test nearest airport lookup ---
# Vail, CO (39.64, -106.37) — should find a Colorado airport
nearest = find_nearest_airport(39.64, -106.37, airports)
print(f"Nearest airport to Vail: {nearest['iata']} - {nearest['name']} ({nearest['city']})")

# --- Step 4: Test Overpass API fetch ---
print("\nFetching resorts from Overpass API...")
raw_resorts = fetch_resorts_from_overpass()
print(f"Found {len(raw_resorts)} ski resorts from OpenStreetMap")

# Show a sample of what we got
print("\nFirst 10 resorts:")
for r in raw_resorts[:10]:
    print(f"  {r['name']} ({r['latitude']:.2f}, {r['longitude']:.2f})")

# --- Step 5: Test full build_resort_database pipeline via load_resorts ---
print("\nBuilding full resort database (resorts + airport matching)...")
resorts = load_resorts()
print(f"Built {len(resorts)} resorts with airport assignments")

# Show some well-known resorts to verify airport matching
print("\nSample resorts with their nearest major airport:")
for name in ["Vail", "Whistler", "Chamonix", "Niseko", "Killington"]:
    r = get_resort(name)
    if r:
        print(f"  {r.name} ({r.region}) -> {r.nearest_airport} ({r.airport_name})")
    else:
        print(f"  {name}: not found in database")

# --- Step 6: Test region filter ---
us_resorts = get_resorts_by_region("US")
print(f"\nUS resorts: {len(us_resorts)}")

jp_resorts = get_resorts_by_region("JP")
print(f"Japan resorts: {len(jp_resorts)}")
