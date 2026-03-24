"""
Open-Meteo weather client for ski resort snow conditions.

Fetches historical snowfall + forecast data using regional weather models
matched to each resort's location for better mountain accuracy.
Open-Meteo is free with no API key required.
"""

import asyncio
import httpx
from models import DayForecast, SnowConditions, Resort

# Regional model endpoints — higher resolution than the default global model
REGION_MODELS = {
    "CA": "https://api.open-meteo.com/v1/gem",          # Canadian GEM 2.5km
    "US": "https://api.open-meteo.com/v1/gfs",          # GFS/HRRR 3km
    "JP": "https://api.open-meteo.com/v1/jma",          # JMA MSM 5km
    "FR": "https://api.open-meteo.com/v1/meteofrance",  # AROME 1.3km
    "DE": "https://api.open-meteo.com/v1/dwd-icon",     # ICON-D2 2km
    "AT": "https://api.open-meteo.com/v1/dwd-icon",     # ICON-D2 2km
    "CH": "https://api.open-meteo.com/v1/dwd-icon",     # ICON-D2 2km
    "IT": "https://api.open-meteo.com/v1/dwd-icon",     # ICON-D2 2km
}
DEFAULT_MODEL_URL = "https://api.open-meteo.com/v1/forecast"

# Average mid-station offset by region — Alps have much more vertical than Japan/NA
ALPINE_OFFSETS = {
    "FR": 1400,  # French Alps (Chamonix, Val d'Isère)
    "CH": 1300,  # Swiss Alps (Zermatt, Verbier)
    "AT": 1000,  # Austrian Alps (St. Anton, Kitzbühel)
    "IT": 1000,  # Italian Alps (Cortina, Livigno)
    "DE": 800,   # German Alps
    "US": 600,   # North America
    "CA": 700,   # Canada (Whistler, Revelstoke)
    "JP": 500,   # Japan (Niseko, Hakuba)
}
DEFAULT_ALPINE_OFFSET_M = 600

# Limit concurrent requests to be polite to the free API
MAX_CONCURRENT = 10


def get_model_url(region: str) -> str:
    # Pick the best regional weather model for a resort's country
    return REGION_MODELS.get(region, DEFAULT_MODEL_URL)


def get_alpine_elevation(resort: Resort) -> int:
    # Estimate mid-station elevation using region-specific offset
    offset = ALPINE_OFFSETS.get(resort.region, DEFAULT_ALPINE_OFFSET_M)
    return resort.elevation_m + offset


def build_params(resort: Resort, days_back: int, forecast_days: int) -> list[tuple]:
    # Build the Open-Meteo query parameters for a resort
    return [
        ("latitude", resort.latitude),
        ("longitude", resort.longitude),
        ("elevation", get_alpine_elevation(resort)),
        ("daily", "snowfall_sum"),
        ("daily", "temperature_2m_max"),
        ("daily", "temperature_2m_min"),
        ("daily", "wind_speed_10m_max"),
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

    # Build day-by-day details
    daily_details = []
    for i, d in enumerate(dates):
        daily_details.append(DayForecast(
            date=d,
            snowfall_cm=snowfall[i] or 0.0,
            temp_high_c=temp_max[i],
            temp_low_c=temp_min[i],
            wind_speed_max_kmh=wind_max[i] or 0.0,
        ))

    # Split into past (recent) and future (forecast) periods
    recent_snowfall = sum(snowfall[i] or 0.0 for i in range(days_back))
    forecast_snowfall = sum(snowfall[i] or 0.0 for i in range(days_back, len(snowfall)))

    return SnowConditions(
        resort_name=resort.name,
        region=resort.region,
        latitude=resort.latitude,
        longitude=resort.longitude,
        recent_snowfall_cm=recent_snowfall,
        forecast_snowfall_cm=forecast_snowfall,
        temp_high_c=max(t for t in temp_max if t is not None),
        temp_low_c=min(t for t in temp_min if t is not None),
        daily_details=daily_details,
    )


def fetch_resort_conditions(resort: Resort, days_back: int = 3, forecast_days: int = 7) -> SnowConditions:
    # Fetch snow and weather conditions for a single resort (sync)
    # Try regional model first, fall back to default if it returns incomplete data
    url = get_model_url(resort.region)
    params = build_params(resort, days_back, forecast_days)
    resp = httpx.get(url, params=params, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()

    # If regional model has None temps, pull temps from default model but keep regional snow
    if any(t is None for t in data["daily"]["temperature_2m_max"]):
        fallback = httpx.get(DEFAULT_MODEL_URL, params=params, timeout=30.0)
        fallback.raise_for_status()
        fb = fallback.json()
        data["daily"]["temperature_2m_max"] = fb["daily"]["temperature_2m_max"]
        data["daily"]["temperature_2m_min"] = fb["daily"]["temperature_2m_min"]

    return parse_conditions(resort, data, days_back)


async def fetch_all_conditions(resorts: list[Resort], days_back: int = 3, forecast_days: int = 7) -> list[SnowConditions]:
    # Fetch conditions for multiple resorts concurrently
    semaphore = asyncio.Semaphore(MAX_CONCURRENT)

    async def fetch_one(resort: Resort, client: httpx.AsyncClient) -> SnowConditions | None:
        url = get_model_url(resort.region)
        async with semaphore:
            # Retry up to 3 times on rate limit (429) with increasing backoff
            for attempt in range(3):
                try:
                    params = build_params(resort, days_back, forecast_days)
                    resp = await client.get(url, params=params, timeout=30.0)
                    resp.raise_for_status()
                    data = resp.json()

                    # If regional model has None temps, pull temps from default but keep regional snow
                    if any(t is None for t in data["daily"]["temperature_2m_max"]):
                        fallback = await client.get(DEFAULT_MODEL_URL, params=params, timeout=30.0)
                        fallback.raise_for_status()
                        fb = fallback.json()
                        data["daily"]["temperature_2m_max"] = fb["daily"]["temperature_2m_max"]
                        data["daily"]["temperature_2m_min"] = fb["daily"]["temperature_2m_min"]

                    return parse_conditions(resort, data, days_back)
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
