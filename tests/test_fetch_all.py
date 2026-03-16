"""Test fetch_all_conditions — concurrent weather fetching for multiple resorts."""

import sys
import time
import asyncio
sys.path.insert(0, "src")

from resorts import load_resorts, get_resorts_by_region
from weather import fetch_all_conditions

# Load resort database (from cache)
load_resorts()

# Test with JP resorts (smaller set than US)
jp_resorts = get_resorts_by_region("JP")
print(f"Fetching conditions for {len(jp_resorts)} Japan resorts...\n")

start = time.time()
results = asyncio.run(fetch_all_conditions(jp_resorts[:20], days_back=3, forecast_days=3))
elapsed = time.time() - start

print(f"Got conditions for {len(results)}/{min(20, len(jp_resorts))} resorts in {elapsed:.1f}s\n")

# Show top 5 by recent snowfall
results.sort(key=lambda r: r.recent_snowfall_cm, reverse=True)
print("Top 5 by recent snowfall:")
for r in results[:5]:
    depth = f"{r.snow_depth_m}m" if r.snow_depth_m is not None else "N/A"
    print(f"  {r.resort_name}: {r.recent_snowfall_cm}cm snow, depth={depth}")
