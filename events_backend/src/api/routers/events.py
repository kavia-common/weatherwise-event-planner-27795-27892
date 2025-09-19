from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, status, Query

from src.api.deps import get_events_repo
from src.data.events_repository import InMemoryEventsRepository
import logging
from src.schemas.models import (
    EventRequest,
    EventResponse,
    RecommendationRequest,
    RecommendationResponse,
    ScoreRequest,
    ScoreResponse,
    ScoredOption,
)
from src.services.scoring import build_time_windows_for_day, score_windows_from_forecast
from src.services.weather_client import GeoError, WeatherProviderError, nominatim_client, openmeteo_client
from src.services.notifications import get_email_service, EmailMessage

router = APIRouter()

# Ensure basic logging is configured for email stub visibility (safe if configured elsewhere)
logging.basicConfig(level=logging.INFO)


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create event",
    description=(
        "Create an event plan request. Stores the event in an in-memory repository for now. "
        "On success, triggers email notification stubs that log to the console."
    ),
    operation_id="create_event",
)
def create_event(payload: EventRequest, repo: InMemoryEventsRepository = Depends(get_events_repo)) -> EventResponse:
    """
    PUBLIC_INTERFACE
    Create a new event.

    Parameters:
        payload: EventRequest body with event details (supports optional user_id and notes).

    Returns:
        EventResponse representing the created event record.

    Side effects:
        Logs 'email' notifications to console via stub hooks.
    """
    return repo.add(payload)


@router.get(
    "",
    response_model=List[EventResponse],
    summary="List events",
    description="List events stored in the repository. Optionally filter by userId.",
    operation_id="list_events",
)
def list_events(
    userId: Optional[str] = Query(default=None, description="Filter events by associated user ID"),
    repo: InMemoryEventsRepository = Depends(get_events_repo),
) -> List[EventResponse]:
    """
    PUBLIC_INTERFACE
    List events currently in the in-memory store. If userId is provided,
    only events associated with that user are returned.
    """
    if userId:
        return repo.list_by_user(userId)
    return repo.list()


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event",
    description="Retrieve a single event by ID. Returns 404 if not found.",
    operation_id="get_event",
)
def get_event(
    event_id: str = Path(..., description="Event identifier"),
    repo: InMemoryEventsRepository = Depends(get_events_repo),
) -> EventResponse:
    """
    PUBLIC_INTERFACE
    Get a single event by its ID.

    Raises:
        HTTPException 404 if not found.
    """
    event = repo.get(event_id)
    if not event:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")
    return event


@router.get(
    "/{event_id}/recommendations",
    response_model=RecommendationResponse,
    summary="Get recommendations for event",
    description="Return placeholder weather-aware recommendations for the specified event.",
    operation_id="get_event_recommendations",
)
def get_recommendations(
    event_id: str = Path(..., description="Event identifier"),
    repo: InMemoryEventsRepository = Depends(get_events_repo),
) -> RecommendationResponse:
    """
    PUBLIC_INTERFACE
    Generate placeholder recommendations with mock-scored options.
    """
    event = repo.get(event_id)
    if not event:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Event not found")

    options = [
        ScoredOption(label="Morning window", score=0.78),
        ScoredOption(label="Afternoon window", score=0.66),
        ScoredOption(label="Evening window", score=0.52),
    ]
    response = RecommendationResponse(
        event_id=event.id,
        options=options,
        generated_at=datetime.utcnow(),
        notes="Scores are illustrative placeholders. Real scoring to be integrated.",
    )

    # Notify user (stub) that recommendations were generated
    try:
        email_service = get_email_service()
        best = options[0] if options else None
        subject = f"Recommendations ready for '{event.name}'"
        best_str = f" Top option: {best.label} (score {best.score:.2f})." if best else ""
        body = (
            f"We generated recommendations for your event on {event.date.isoformat()} at {event.location}."
            f"{best_str}"
        )
        email_service.send(EmailMessage(to=event.email, subject=subject, body=body))
    except Exception as exc:
        logging.getLogger("events.notifications").warning("Recommendation email stub failed: %s", exc)

    return response


@router.post(
    "/score",
    response_model=ScoreResponse,
    summary="Score weather suitability for a date",
    description=(
        "Scores suitability of time windows for a given target date and location using forecast from Open-Meteo. "
        "It builds several windows across the day and averages scores of forecast points within each window."
    ),
    operation_id="score_event_date",
)
async def score_event_date(payload: ScoreRequest) -> ScoreResponse:
    """
    PUBLIC_INTERFACE
    Score time windows for the provided location and date.

    Parameters:
        payload: ScoreRequest with location, target_date, forecast parameters and window size.

    Returns:
        ScoreResponse with sorted ScoredOptions and metadata.

    Error handling:
        - 400 for geocoding failure
        - 502 for weather provider failure
    """
    try:
        lat, lon, _ = await nominatim_client.geocode_first(payload.location)
        snapshot = await openmeteo_client.get_current(lat, lon)
        forecast = await openmeteo_client.get_forecast(lat, lon, hours=payload.hours, step_hours=payload.step_hours)
    except GeoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Geocoding failed: {e}") from e
    except WeatherProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    windows = build_time_windows_for_day(payload.target_date, window_hours=payload.window_hours, step_hours=payload.step_hours)
    options = score_windows_from_forecast(windows, forecast, snapshot=snapshot)
    notes = (
        "Score computed using temperature comfort band (18-26°C), precipitation amount and probability penalties, "
        "wind penalty, and small condition adjustment. Scores normalized to 0..1."
    )
    return ScoreResponse(options=options, generated_at=datetime.utcnow(), notes=notes)


@router.post(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Generate recommendations for an ad-hoc event",
    description=(
        "Generates ranked time-window recommendations for a new event using live geocoding and forecast. "
        "This does not persist the event; use POST /api/events to create records."
    ),
    operation_id="post_event_recommendations",
)
async def post_recommendations(payload: RecommendationRequest) -> RecommendationResponse:
    """
    PUBLIC_INTERFACE
    Generate weather-aware recommendations for a new event request.

    Parameters:
        payload: RecommendationRequest with event and scoring parameters.

    Returns:
        RecommendationResponse with ranked ScoredOptions.
    """
    try:
        lat, lon, _ = await nominatim_client.geocode_first(payload.location)
        snapshot = await openmeteo_client.get_current(lat, lon)
        # Forecast window from now through hours ahead should cover the target date windows near-term.
        forecast = await openmeteo_client.get_forecast(lat, lon, hours=payload.hours, step_hours=payload.step_hours)
    except GeoError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Geocoding failed: {e}") from e
    except WeatherProviderError as e:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e)) from e

    windows = build_time_windows_for_day(payload.date, window_hours=payload.window_hours, step_hours=payload.step_hours)
    options = score_windows_from_forecast(windows, forecast, snapshot=snapshot)

    response = RecommendationResponse(
        event_id="ad-hoc",
        options=options,
        generated_at=datetime.utcnow(),
        notes="Recommendations generated via suitability scoring. Not persisted.",
    )

    # Notify requester (stub) about recommendations
    try:
        email_service = get_email_service()
        best = options[0] if options else None
        subject = f"Your weather-aware recommendations for '{payload.name}'"
        best_str = f" Best option: {best.label} (score {best.score:.2f})." if best else ""
        body = (
            f"We prepared recommendations for {payload.date.isoformat()} at {payload.location}."
            f"{best_str}"
        )
        email_service.send(EmailMessage(to=payload.email, subject=subject, body=body))
    except Exception as exc:
        logging.getLogger("events.notifications").warning("Ad-hoc recommendation email stub failed: %s", exc)

    return response
