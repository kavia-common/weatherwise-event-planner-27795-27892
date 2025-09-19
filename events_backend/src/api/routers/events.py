from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.api.deps import get_events_repo
from src.data.events_repository import InMemoryEventsRepository
from src.schemas.models import EventRequest, EventResponse, RecommendationResponse, ScoredOption

router = APIRouter()


@router.post(
    "",
    response_model=EventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create event",
    description="Create an event plan request. Stores the event in an in-memory repository for now.",
    operation_id="create_event",
)
def create_event(payload: EventRequest, repo: InMemoryEventsRepository = Depends(get_events_repo)) -> EventResponse:
    """
    PUBLIC_INTERFACE
    Create a new event.

    Parameters:
        payload: EventRequest body with event details.

    Returns:
        EventResponse representing the created event record.
    """
    return repo.add(payload)


@router.get(
    "",
    response_model=List[EventResponse],
    summary="List events",
    description="List all events stored in the repository.",
    operation_id="list_events",
)
def list_events(repo: InMemoryEventsRepository = Depends(get_events_repo)) -> List[EventResponse]:
    """
    PUBLIC_INTERFACE
    List all events currently in the in-memory store.
    """
    return repo.list()


@router.get(
    "/{event_id}",
    response_model=EventResponse,
    summary="Get event",
    description="Retrieve a single event by ID.",
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
    return RecommendationResponse(
        event_id=event.id,
        options=options,
        generated_at=datetime.utcnow(),
        notes="Scores are illustrative placeholders. Real scoring to be integrated.",
    )
