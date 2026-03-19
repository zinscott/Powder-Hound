"""
Open-Meteo weather client for ski resort snow conditions.

Fetches historical snowfall + forecast data for resort coordinates.
Open-Meteo is free with no API key required.
"""

from datetime import date

import asyncio

import httpx
from models import DayForecast, SnowConditions, Resort

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Limit concurrent requests to be polite to the free API
MAX_CONCURRENT = 10


def build_params(resort: Resort, days_back: int, forecast_days: int) -> list[tuple]:
    # Build the Open-Meteo query parameters for a resort
    return [
        ("latitude", resort.latitude),
        ("longitude", resort.longitude),
        ("daily", "snowfall_sum"),
        ("daily", "temperature_2m_max"),
        ("daily", "temperature_2m_min"),
        ("daily", "wind_speed_10m_max"),
        ("hourly", "snow_depth"),
        ("past_days", days_back),
        ("forecast_days", forecast_days),
        ("timezone", "auto"),
    ]


def parse_conditions(resort: Resort, data: dict, days_back: int) -> SnowConditions:
    # Parse an Open-Meteo response into a SnowConditions object
    daily = data["daily"]
    dates = daily["time"]
    snowfall = daily["snowfall_sum"]
    temp_max = daily["temperature_2m_max"]
    temp_min = daily["temperature_2m_min"]
    wind_max = daily["wind_speed_10m_max"]

    hourly_depth = data["hourly"]["snow_depth"]
    today_str = date.today().isoformat()

    # Snow depth per day: end-of-day for past, current hour for today, daily avg for future
    daily_snow_depth = []
    for i, d in enumerate(dates):
        day_hours = hourly_depth[i * 24:(i + 1) * 24]
        valid_hours = [h for h in day_hours if h is not None]

        if d < today_str:
            # Past day — end of day (hour 23)
            daily_snow_depth.append(day_hours[23] if day_hours[23] is not None else (valid_hours[-1] if valid_hours else None))
        elif d == today_str:
            # Today — most recent non-None reading
            depth = None
            for h in reversed(valid_hours):
                depth = h
                break
            daily_snow_depth.append(depth)
        else:
            # Future day — daily average, rounded
            daily_snow_depth.append(round(sum(valid_hours) / len(valid_hours), 2) if valid_hours else None)

    # Build day-by-day details
    daily_details = []
    for i, d in enumerate(dates):
        daily_details.append(DayForecast(
            date=d,
            snowfall_cm=snowfall[i] or 0.0,
            snow_depth_m=daily_snow_depth[i],
            temp_high_c=temp_max[i],
            temp_low_c=temp_min[i],
            wind_speed_max_kmh=wind_max[i] or 0.0,
        ))

    # Split into past (recent) and future (forecast) periods
    recent_snowfall = sum(snowfall[i] or 0.0 for i in range(days_back))
    forecast_snowfall = sum(snowfall[i] or 0.0 for i in range(days_back, len(snowfall)))

    # Current snow depth — most recent non-None hourly reading
    latest_depth = None
    for d in reversed(hourly_depth):
        if d is not None:
            latest_depth = d
            break

    return SnowConditions(
        resort_name=resort.name,
        region=resort.region,
        latitude=resort.latitude,
        longitude=resort.longitude,
        recent_snowfall_cm=recent_snowfall,
        snow_depth_m=latest_depth,
        forecast_snowfall_cm=forecast_snowfall,
        temp_high_c=max(t for t in temp_max if t is not None),
        temp_low_c=min(t for t in temp_min if t is not None),
        daily_details=daily_details,
    )


def fetch_resort_conditions(resort: Resort, days_back: int = 3, forecast_days: int = 7) -> SnowConditions:
    # Fetch snow and weather conditions for a single resort (sync)
    params = build_params(resort, days_back, forecast_days)
    resp = httpx.get(OPEN_METEO_URL, params=params, timeout=30.0)
    resp.raise_for_status()
    return parse_conditions(resort, resp.json(), days_back)


async def fetch_all_conditions(resorts: list[Resort], days_back: int = 3, forecast_days: int = 7) -> list[SnowConditions]:
    # Fetch conditions for multiple resorts concurrently
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def fetch_one(resort: Resort, client: httpx.AsyncClient) -> SnowConditions | None:
        async with semaphore:
            # Retry up to 3 times on rate limit (429) with increasing backoff
            for attempt in range(3):
                try:
                    params = build_params(resort, days_back, forecast_days)
                    resp = await client.get(OPEN_METEO_URL, params=params, timeout=30.0)
                    resp.raise_for_status()
                    return parse_conditions(resort, resp.json(), days_back)
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 429 and attempt < 2:
                        await asyncio.sleep(1 * (attempt + 1))
                        continue
                    print(f"Warning: failed to fetch conditions for {resort.name}: {e}")
                    return None
                except Exception as e:
                    print(f"Warning: failed to fetch conditions for {resort.name}: {e}")
                    return None

    async with httpx.AsyncClient() as client:
        tasks = [fetch_one(r, client) for r in resorts]
        results = await asyncio.gather(*tasks)

    return [r for r in results if r is not None]
