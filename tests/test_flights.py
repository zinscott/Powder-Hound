import sys
sys.path.insert(0, "src")

from flights import search_flights, get_flight_details

print("=== Search: SFO to DEN (tomorrow) ===\n")

flights = search_flights("SFO", "DEN")
print(f"Found {len(flights)} operating flights (codeshares removed)\n")

for f in flights[:5]:
    print(f"  {f.airline} {f.flight_number}")
    print(f"    {f.departure_airport} -> {f.arrival_airport}")
    print(f"    Departs: {f.departure_time}")
    print(f"    Status: {f.status}")
    print()

if flights:
    first = flights[0]
    print(f"=== Details: {first.flight_number} ===\n")

    import time
    time.sleep(1)

    details = get_flight_details(first.flight_number)
    if details:
        print(f"  {details.airline} {details.flight_number}")
        print(f"    {details.departure_airport} -> {details.arrival_airport}")
        print(f"    Departs: {details.departure_time}")
        print(f"    Arrives: {details.arrival_time}")
        print(f"    Status: {details.status}")
