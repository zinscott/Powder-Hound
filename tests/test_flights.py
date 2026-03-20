import sys
import time
sys.path.insert(0, "src")

from flights import search_flights, get_flight_details, departure_cache

# --- Test 1: Flight search ---
print("=== 1. Search: SFO to DEN (tomorrow) ===\n")

flights = search_flights("SFO", "DEN")
print(f"Found {len(flights)} operating flights (codeshares removed)\n")

for f in flights[:5]:
    print(f"  {f.airline} {f.flight_number}")
    print(f"    {f.departure_airport} -> {f.arrival_airport}")
    print(f"    Departs: {f.departure_time}")
    print(f"    Status: {f.status}")
    print()

# --- Test 2: Departure cache ---
print("=== 2. Cache: SFO to SLC (should reuse cached departures) ===\n")

start = time.time()
flights2 = search_flights("SFO", "SLC")
elapsed = time.time() - start
print(f"Found {len(flights2)} flights in {elapsed:.3f}s (expected near 0s)")
for f in flights2:
    print(f"  {f.flight_number} ({f.airline}) dep={f.departure_time}")
print(f"\nCache entries: {len(departure_cache)}")
print()

# --- Test 3: Flight details with arrival time ---
if flights:
    first = flights[0]
    print(f"=== 3. Details: {first.flight_number} ===\n")

    time.sleep(2)

    details = get_flight_details(first.flight_number)
    if details:
        print(f"  {details.airline} {details.flight_number}")
        print(f"    {details.departure_airport} -> {details.arrival_airport}")
        print(f"    Departs: {details.departure_time}")
        print(f"    Arrives: {details.arrival_time}")
        print(f"    Status: {details.status}")
        assert details.arrival_time != "N/A", "Arrival time should be populated"
        print("\n  Arrival time populated: PASSED")

# --- Test 4: Case insensitive airport codes ---
print("\n=== 4. Case insensitive: sfo to den ===\n")

time.sleep(2)
flights3 = search_flights("sfo", "den")
print(f"Found {len(flights3)} flights (same as test 1: {len(flights)})")
assert len(flights3) == len(flights), "Lowercase codes should return same results"
print("Case insensitive: PASSED")
