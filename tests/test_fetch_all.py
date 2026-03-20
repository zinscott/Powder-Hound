"""Test fetch_all_conditions — concurrent weather fetching, sorting, and days_back."""

import sys
import time
import asyncio
sys.path.insert(0, "src")

from resorts import load_resorts, get_resorts_by_region
from weather import fetch_all_conditions

# Load resort database (from cache)
load_resorts()

us_resorts = get_resorts_by_region("US")
major = [r for r in us_resorts if r.area_km2 >= 10.0][:10]

# --- Test 1: Concurrent fetch with default days_back=3 ---
print("=== 1. Concurrent fetch (10 US resorts, days_back=3) ===\n")

start = time.time()
results = asyncio.run(fetch_all_conditions(major, days_back=3, forecast_days=7))
elapsed = time.time() - start

print(f"Got conditions for {len(results)}/{len(major)} resorts in {elapsed:.1f}s\n")

# --- Test 2: Sort by recent snowfall ---
print("=== 2. Sort by recent snowfall ===\n")
results.sort(key=lambda c: c.recent_snowfall_cm, reverse=True)
for c in results[:3]:
    print(f"  {c.resort_name}: {c.recent_snowfall_cm}cm recent")

# --- Test 3: Sort by forecast snowfall ---
print("\n=== 3. Sort by forecast snowfall ===\n")
results.sort(key=lambda c: c.forecast_snowfall_cm, reverse=True)
for c in results[:3]:
    print(f"  {c.resort_name}: {c.forecast_snowfall_cm}cm forecast")

# --- Test 4: Sort by total (recent + forecast) ---
print("\n=== 4. Sort by total snowfall ===\n")
results.sort(key=lambda c: c.recent_snowfall_cm + c.forecast_snowfall_cm, reverse=True)
for c in results[:3]:
    total = c.recent_snowfall_cm + c.forecast_snowfall_cm
    print(f"  {c.resort_name}: {total}cm total ({c.recent_snowfall_cm}cm recent + {c.forecast_snowfall_cm}cm forecast)")

# --- Test 5: days_back=7 returns more snow than days_back=3 ---
print("\n=== 5. days_back=7 vs days_back=3 ===\n")

results7 = asyncio.run(fetch_all_conditions(major, days_back=7, forecast_days=7))
results7.sort(key=lambda c: c.recent_snowfall_cm, reverse=True)

for c3, c7 in zip(
    sorted(results, key=lambda c: c.resort_name),
    sorted(results7, key=lambda c: c.resort_name),
):
    print(f"  {c3.resort_name}: 3-day={c3.recent_snowfall_cm}cm, 7-day={c7.recent_snowfall_cm}cm")
    assert c7.recent_snowfall_cm >= c3.recent_snowfall_cm, \
        f"7-day should be >= 3-day for {c3.resort_name}"

print("\n  7-day >= 3-day for all resorts: PASSED")
