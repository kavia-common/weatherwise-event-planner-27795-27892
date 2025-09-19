from datetime import datetime, date
from typing import List, Optional

from pydantic import BaseModel, Field, EmailStr


# --- Weather Schemas ---

class WeatherSnapshot(BaseModel):
    """Current weather conditions snapshot."""
    timestamp: datetime = Field(..., description="UTC timestamp of the snapshot")
    temperature_c: float = Field(..., description="Temperature in Celsius")
    condition: str = Field(..., description="Weather condition description")
    humidity: Optional[float] = Field(None, description="Relative humidity percentage")
    wind_kph: Optional[float] = Field(None, description="Wind speed in km/h")


class ForecastItem(BaseModel):
    """Forecast data point for a future time."""
    timestamp: datetime = Field(..., description="UTC timestamp for the forecast item")
    temperature_c: float = Field(..., description="Forecasted temperature in Celsius")
    condition: str = Field(..., description="Forecasted weather condition")
    precipitation_mm: Optional[float] = Field(None, description="Expected precipitation in millimeters")
    probability_precip: Optional[float] = Field(None, description="Probability of precipitation (0-1)")


# --- Scoring Schema ---

class ScoredOption(BaseModel):
    """An option or time window with an associated suitability score."""
    label: str = Field(..., description="Human-readable option label (e.g., 'Morning window')")
    score: float = Field(..., ge=0.0, le=1.0, description="Normalized suitability score from 0 to 1")
    start: Optional[datetime] = Field(None, description="Optional start time for the option")
    end: Optional[datetime] = Field(None, description="Optional end time for the option")
    notes: Optional[str] = Field(None, description="Reasoning or notes about the score")


# --- Event Schemas ---

class EventRequest(BaseModel):
    """
    PUBLIC_INTERFACE
    Request payload to create or evaluate an event plan.
    """
    name: str = Field(..., description="Event name")
    email: EmailStr = Field(..., description="Requester email")
    date: date = Field(..., description="Target event date")
    location: str = Field(..., description="Location or city for the event")
    flexibility_days: int = Field(0, ge=0, le=30, description="Flexibility window in days around the target date")
    preferences: Optional[List[str]] = Field(
        default=None,
        description="Optional list of preferences (e.g., 'outdoor', 'shade', 'low-wind')",
    )


class EventResponse(BaseModel):
    """
    PUBLIC_INTERFACE
    Response body after creating or evaluating an event.
    """
    id: str = Field(..., description="Event identifier")
    name: str = Field(..., description="Event name")
    email: EmailStr = Field(..., description="Requester email")
    date: date = Field(..., description="Target event date")
    location: str = Field(..., description="Location or city for the event")
    created_at: datetime = Field(..., description="Creation timestamp")
    status: str = Field(..., description="Event status (e.g., 'received', 'scheduled')")
    weather_snapshot: Optional[WeatherSnapshot] = Field(None, description="Current weather at location")
    forecast: Optional[List[ForecastItem]] = Field(None, description="Forecast around event date")


class RecommendationResponse(BaseModel):
    """
    PUBLIC_INTERFACE
    Weather-aware recommendations for an event.
    """
    event_id: str = Field(..., description="Associated event ID")
    options: List[ScoredOption] = Field(..., description="Ranked options with scores")
    generated_at: datetime = Field(..., description="Recommendation generation time")
    notes: Optional[str] = Field(None, description="General notes for the recommendation")


# --- Request/Response models for scoring endpoints ---

class ScoreRequest(BaseModel):
    """
    PUBLIC_INTERFACE
    Request body to score forecast items for a specific day and location.
    """
    location: str = Field(..., description="Location or city used to obtain weather data")
    target_date: date = Field(..., description="Day for which to evaluate time windows")
    hours: int = Field(24, ge=1, le=168, description="Forecast lookahead hours")
    step_hours: int = Field(3, ge=1, le=24, description="Forecast sampling step in hours")
    window_hours: int = Field(3, ge=1, le=12, description="Time window span used for scoring")


class ScoreResponse(BaseModel):
    """
    PUBLIC_INTERFACE
    Response for POST /events/score containing scored windows and metadata.
    """
    options: List[ScoredOption] = Field(..., description="Scored time windows sorted by score desc")
    generated_at: datetime = Field(..., description="UTC generation timestamp")
    notes: Optional[str] = Field(None, description="Notes about scoring method and parameters")


class RecommendationRequest(BaseModel):
    """
    PUBLIC_INTERFACE
    Request body to generate recommendations for a new ad-hoc event.
    """
    name: str = Field(..., description="Event name")
    email: EmailStr = Field(..., description="Requester email")
    date: date = Field(..., description="Preferred date")
    location: str = Field(..., description="Location or city for the event")
    hours: int = Field(48, ge=1, le=168, description="Forecast horizon in hours")
    step_hours: int = Field(3, ge=1, le=24, description="Forecast sampling step in hours")
    window_hours: int = Field(3, ge=1, le=12, description="Time window span used for scoring")
