"""
Powder Hound MCP Server.

Exposes ski resort snow conditions and flight search tools
via the Model Context Protocol (MCP).
"""

from mcp.server.fastmcp import FastMCP
import resorts as resort_db
from resorts import load_resorts, get_resort, get_resorts_by_region
from weather import fetch_resort_conditions, fetch_all_conditions

mcp = FastMCP("Powder Hound")

# Load the resort database on startup
load_resorts()


@mcp.tool()
def get_resort_conditions(resort_name: str) -> dict:
    # Get detailed snow and weather conditions for a specific ski resort
    resort = get_resort(resort_name)
    if not resort:
        return {"error": f"Resort '{resort_name}' not found"}

    conditions = fetch_resort_conditions(resort)
    return conditions.model_dump()


@mcp.tool()
async def find_best_snow(region: str | None = None, top_n: int = 10, min_area_km2: float = 10.0) -> list[dict]:
    # Rank resorts by recent snowfall, optionally filtered by region and size
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


if __name__ == "__main__":
    mcp.run()
