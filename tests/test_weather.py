"""Test weather.py — fetch conditions for a single resort."""

import sys
sys.path.insert(0, "src")

from resorts import load_resorts, get_resort
from weather import fetch_resort_conditions

# Load resort database (from cache)
load_resorts()

# Test with Vail
resort = get_resort("Vail")
print(f"Fetching conditions for {resort.name}...\n")

conditions = fetch_resort_conditions(resort, days_back=3, forecast_days=7)

print(f"Resort: {conditions.resort_name} ({conditions.region})")
print(f"Recent snowfall (last 3 days): {conditions.recent_snowfall_cm} cm")
print(f"Snow depth: {conditions.snow_depth_m} m")
print(f"Forecast snowfall (next 7 days): {conditions.forecast_snowfall_cm} cm")
print(f"Temp range: {conditions.temp_low_c}°C to {conditions.temp_high_c}°C")
print(f"\nDaily breakdown:")
for day in conditions.daily_details:
    depth = f"{day.snow_depth_m}m" if day.snow_depth_m is not None else "N/A"
    print(f"  {day.date}: snow={day.snowfall_cm}cm, depth={depth}, "
          f"temp={day.temp_low_c}°C/{day.temp_high_c}°C, wind={day.wind_speed_max_kmh}km/h")
