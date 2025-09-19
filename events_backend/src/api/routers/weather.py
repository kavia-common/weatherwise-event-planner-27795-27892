from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query, status

from src.schemas.models import ForecastItem, WeatherSnapshot
from src.services.weather_client import GeoError, WeatherProviderError, nominatim_client, openmeteo_client

router = APIRouter()


@router.get(
    "/location/search",
    summary="Location search",
    description="Search for locations using OpenStreetMap Nominatim.",
    operation_id="search_location",
    tags=["Weather"],
)
async def search_location(
    q: str = Query(..., description="Free-form location query, e.g., 'San Francisco'"),
    limit: int = Query(5, ge=1, le=10, description="Maximum number of results"),
) -> List[Dict[str, Any]]:
    """
    PUBLIC_INTERFACE
    Search for locations using Nominatim. Returns raw Nominatim result items.

    Returns:
        A list of objects containing fields such as display_name, lat, lon, and address.
    """
    try:
        return await nominatim_client.search(q, limit=limit)
    except GeoError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e


@router.get(
    "/current",
    response_model=WeatherSnapshot,
    summary="Get current weather snapshot",
    description="Return current weather from Open-Meteo for a queried location using geocoding.",
    operation_id="get_current_weather",
)
async def get_current_weather(
    location: str = Query(..., description="City or location to query"),
) -> WeatherSnapshot:
    """
    PUBLIC_INTERFACE
    Get current weather snapshot for the given location by geocoding to coordinates and querying Open-Meteo.
    """
    try:
        lat, lon, _ = await nominatim_client.geocode_first(location)
        return await openmeteo_client.get_current(lat, lon)
    except GeoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Geocoding failed: {e}") from e
    except WeatherProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e


@router.get(
    "/forecast",
    response_model=List[ForecastItem],
    summary="Get forecast",
    description="Return a forecast from Open-Meteo for a location using geocoding.",
    operation_id="get_forecast",
)
async def get_forecast(
    location: str = Query(..., description="City or location to query"),
    hours: int = Query(24, ge=1, le=168, description="Forecast horizon in hours (max 168)"),
    step_hours: int = Query(6, ge=1, le=24, description="Sampling interval in hours"),
) -> List[ForecastItem]:
    """
    PUBLIC_INTERFACE
    Get forecast list for the given location and horizon by geocoding to coordinates and querying Open-Meteo.
    """
    try:
        lat, lon, _ = await nominatim_client.geocode_first(location)
        return await openmeteo_client.get_forecast(lat, lon, hours=hours, step_hours=step_hours)
    except GeoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Geocoding failed: {e}") from e
    except WeatherProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e
