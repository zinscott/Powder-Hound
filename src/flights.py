"""
AeroDataBox flight schedule client.

Fetches airport departures via AeroDataBox (RapidAPI) and filters
to flights heading to a specific destination airport.
Free tier: 150 requests/month, supports future dates.
"""

import os
import time
from datetime import datetime, timedelta
import httpx
from dotenv import load_dotenv
from models import FlightResult

load_dotenv()

API_KEY = os.environ.get("AERODATABOX_API_KEY")
AERODATABOX_URL = "https://aerodatabox.p.rapidapi.com"


def get_headers() -> dict:
    # Build the RapidAPI auth headers
    return {
        "X-RapidAPI-Key": API_KEY,
        "X-RapidAPI-Host": "aerodatabox.p.rapidapi.com",
    }


def parse_flight(flight: dict, dep_iata: str) -> FlightResult:
    # Map an AeroDataBox FIDS departure to our FlightResult model
    # Arrival time is not provided by the FIDS endpoint
    movement = flight.get("movement", {})
    arr_airport = movement.get("airport", {})
    scheduled = movement.get("scheduledTime", {})

    return FlightResult(
        airline=flight.get("airline", {}).get("name", "Unknown"),
        flight_number=flight.get("number", "N/A"),
        departure_airport=dep_iata,
        arrival_airport=arr_airport.get("iata", "N/A"),
        departure_time=scheduled.get("local", "N/A"),
        arrival_time="N/A",
        status=flight.get("status", "unknown"),
    )


def search_flights(dep_iata: str, arr_iata: str, flight_date: str | None = None) -> list[FlightResult]:
    # Get departures from dep_iata, filtered to arr_iata, codeshares removed
    if not API_KEY:
        raise ValueError("AERODATABOX_API_KEY not set in environment")

    # Default to tomorrow if no date provided
    if flight_date:
        day = datetime.strptime(flight_date, "%Y-%m-%d")
    else:
        day = datetime.now() + timedelta(days=1)

    # AeroDataBox max window is 12 hours, so split into two calls for full day
    ranges = [
        (day.strftime("%Y-%m-%dT00:00"), day.strftime("%Y-%m-%dT12:00")),
        (day.strftime("%Y-%m-%dT12:00"), day.strftime("%Y-%m-%dT23:59")),
    ]

    all_departures = []
    for i, (from_local, to_local) in enumerate(ranges):
        if i > 0:
            time.sleep(1)  # Rate limit: pause between consecutive requests
        url = f"{AERODATABOX_URL}/flights/airports/iata/{dep_iata}/{from_local}/{to_local}"
        resp = httpx.get(url, headers=get_headers(), timeout=30.0)
        resp.raise_for_status()
        all_departures.extend(resp.json().get("departures", []))

    if not all_departures:
        return []

    # Filter to destination airport, skip codeshares (only keep operating flights)
    filtered = []
    for flight in all_departures:
        arr_airport = flight.get("movement", {}).get("airport", {}).get("iata", "")
        codeshare = flight.get("codeshareStatus", "")
        if arr_airport == arr_iata and codeshare == "IsOperator":
            filtered.append(parse_flight(flight, dep_iata))

    return filtered


def get_flight_details(flight_number: str, flight_date: str | None = None) -> FlightResult | None:
    # Get full details for a specific flight including arrival time
    if not API_KEY:
        raise ValueError("AERODATABOX_API_KEY not set in environment")

    if not flight_date:
        flight_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    # Remove space from flight number if present (e.g. "UA 513" -> "UA513")
    flight_number = flight_number.replace(" ", "")

    url = f"{AERODATABOX_URL}/flights/number/{flight_number}/{flight_date}"
    resp = httpx.get(url, headers=get_headers(), timeout=30.0)
    resp.raise_for_status()

    data = resp.json()
    if not data:
        return None

    # API returns a list, take the first (operating) flight
    flight = data[0]
    departure = flight.get("departure", {})
    arrival = flight.get("arrival", {})

    return FlightResult(
        airline=flight.get("airline", {}).get("name", "Unknown"),
        flight_number=flight.get("number", "N/A"),
        departure_airport=departure.get("airport", {}).get("iata", "N/A"),
        arrival_airport=arrival.get("airport", {}).get("iata", "N/A"),
        departure_time=departure.get("scheduledTime", {}).get("local", "N/A"),
        arrival_time=arrival.get("scheduledTime", {}).get("local", "N/A"),
        status=flight.get("status", "unknown"),
    )
