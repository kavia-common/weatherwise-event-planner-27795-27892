from typing import List

from fastapi import APIRouter, Query

from src.schemas.models import WeatherSnapshot, ForecastItem
from src.services.weather_stub import weather_service

router = APIRouter()


@router.get(
    "/current",
    response_model=WeatherSnapshot,
    summary="Get current weather snapshot",
    description="Return a stubbed current weather snapshot for a location.",
    operation_id="get_current_weather",
)
def get_current_weather(
    location: str = Query(..., description="City or location to query")
) -> WeatherSnapshot:
    """
    PUBLIC_INTERFACE
    Get a stubbed current weather snapshot for the given location.
    """
    return weather_service.get_current(location)


@router.get(
    "/forecast",
    response_model=List[ForecastItem],
    summary="Get forecast",
    description="Return a stubbed forecast for a location.",
    operation_id="get_forecast",
)
def get_forecast(
    location: str = Query(..., description="City or location to query"),
    hours: int = Query(24, ge=1, le=120, description="Forecast horizon in hours"),
    step_hours: int = Query(6, ge=1, le=24, description="Sampling interval in hours"),
) -> List[ForecastItem]:
    """
    PUBLIC_INTERFACE
    Get a stubbed forecast list for the given location and horizon.
    """
    return weather_service.get_forecast(location, hours=hours, step_hours=step_hours)
