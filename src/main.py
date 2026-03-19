"""
Powder Hound MCP Server.

Exposes ski resort snow conditions and flight search tools
via the Model Context Protocol (MCP).
"""

from mcp.server.fastmcp import FastMCP
import resorts as resort_db
from resorts import load_resorts, get_resort, get_resorts_by_region
from weather import fetch_resort_conditions, fetch_all_conditions
from flights import search_flights as flight_search, get_flight_details

mcp = FastMCP("Powder Hound")

# Load the resort database on startup
load_resorts()


@mcp.tool()
def get_resort_conditions(resort_name: str) -> dict:
    """Get detailed snow and weather conditions for a specific ski resort. Returns 3 days of recent snowfall and a 7-day forecast including snow depth, temperatures, and wind speed."""
    resort = get_resort(resort_name)
    if not resort:
        return {"error": f"Resort '{resort_name}' not found"}

    conditions = fetch_resort_conditions(resort)
    return conditions.model_dump()


@mcp.tool()
async def find_best_snow(region: str | None = None, top_n: int = 10, min_area_km2: float = 10.0) -> list[dict]:
    """Rank resorts by recent snowfall. Use region to filter by country code (e.g. 'US', 'JP', 'FR'). Set min_area_km2 to 0 to include smaller resorts, or keep the default (10) for major resorts only."""
    if region:
        resorts = get_resorts_by_region(region)
        if not resorts:
            return [{"error": f"No resorts found in region '{region}'"}]
    else:
        resorts = resort_db.RESORTS

    # Filter by minimum area if specified
    if min_area_km2 > 0:
        resorts = [r for r in resorts if r.area_km2 >= min_area_km2]

    # Fetch conditions for all resorts concurrently
    conditions = await fetch_all_conditions(resorts)

    # Sort by recent snowfall (most snow first)
    conditions.sort(key=lambda c: c.recent_snowfall_cm, reverse=True)

    # Return top N as dicts
    return [c.model_dump() for c in conditions[:top_n]]


@mcp.tool()
def search_flights(departure_airport: str, arrival_airport: str, flight_date: str | None = None) -> list[dict]:
    """Search for flights between two airports. Ask the user for a specific travel date before calling — each search uses 2 API calls from a limited monthly quota. flight_date format: YYYY-MM-DD."""
    flights = flight_search(departure_airport, arrival_airport, flight_date)
    return [f.model_dump() for f in flights]


@mcp.tool()
def flight_info(flight_number: str, flight_date: str | None = None) -> dict:
    """Get full details for a specific flight including arrival time. Use a flight number from search_flights results. flight_date format: YYYY-MM-DD."""
    details = get_flight_details(flight_number, flight_date)
    if not details:
        return {"error": f"Flight '{flight_number}' not found"}
    return details.model_dump()


if __name__ == "__main__":
    mcp.run()
