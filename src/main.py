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
async def find_best_snow(region: str | None = None, top_n: int = 10, min_area_km2: float = 10.0, sort_by: str = "recent") -> list[dict]:
    """Rank resorts by snowfall. sort_by: 'recent' for last 3 days of snowfall (default), 'forecast' for upcoming 7-day snowfall, or 'total' for both combined. Use region to filter by country code (e.g. 'US', 'JP', 'FR'). min_area_km2 filters by resort size — default 10 returns only major resorts, set to 0 to include small local hills."""
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

    # Sort by selected snowfall metric (most snow first)
    if sort_by == "forecast":
        conditions.sort(key=lambda c: c.forecast_snowfall_cm, reverse=True)
    elif sort_by == "total":
        conditions.sort(key=lambda c: c.recent_snowfall_cm + c.forecast_snowfall_cm, reverse=True)
    else:
        conditions.sort(key=lambda c: c.recent_snowfall_cm, reverse=True)

    # Return top N as dicts
    return [c.model_dump() for c in conditions[:top_n]]


@mcp.tool()
def search_flights(departure_airport: str, arrival_airport: str, flight_date: str | None = None) -> list[dict]:
    """Search for flights between two airports. Each resort has a nearest_airport field you can use as the arrival airport. Ask the user for a specific travel date before calling — each search uses 2 API calls from a limited monthly quota. flight_date format: YYYY-MM-DD."""
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
