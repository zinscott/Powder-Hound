"""
Pydantic data models for Powder Hound.

Defines the core data structures used across the application for
resorts, weather conditions, flights, and recommendations.
"""

from pydantic import BaseModel


# Represents a ski resort entry in the static database
class Resort(BaseModel):
    name: str
    region: str
    latitude: float
    longitude: float
    elevation_m: int
    nearest_airport: str  # IATA code (e.g. "DEN")
    airport_name: str


# Weather data for a single day at a resort
class DayForecast(BaseModel):
    date: str
    snowfall_cm: float
    snow_depth_m: float | None
    temp_high_c: float
    temp_low_c: float


# Aggregated snow/weather conditions for a resort over a time range
class SnowConditions(BaseModel):
    resort_name: str
    region: str
    latitude: float
    longitude: float
    recent_snowfall_cm: float  # total over lookback period
    snow_depth_m: float | None
    forecast_snowfall_cm: float  # total over next 7 days
    temp_high_c: float
    temp_low_c: float
    daily_details: list[DayForecast]


# A single flight from Aviation Stack (no pricing — schedules only)
class FlightResult(BaseModel):
    airline: str
    flight_number: str
    departure_airport: str
    arrival_airport: str
    departure_time: str
    arrival_time: str
    status: str


# Combined snow conditions + optional flights for a resort recommendation
class ResortRecommendation(BaseModel):
    resort: str
    region: str
    recent_snowfall_cm: float
    snow_depth_m: float | None
    forecast_snowfall_cm: float
    conditions_summary: str  # human-readable summary
    flights: list[FlightResult] | None
