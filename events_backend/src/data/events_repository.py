from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from src.schemas.models import EventRequest, EventResponse


class InMemoryEventsRepository:
    """
    PUBLIC_INTERFACE
    Simple in-memory repository for events.

    This is a placeholder abstraction to be replaced by a database-backed repository later.
    """

    def __init__(self) -> None:
        self._events: Dict[str, EventResponse] = {}

    def add(self, payload: EventRequest) -> EventResponse:
        """Create and store a new EventResponse from the request."""
        event_id = str(uuid.uuid4())
        now = datetime.utcnow()
        event = EventResponse(
            id=event_id,
            name=payload.name,
            email=payload.email,
            date=payload.date,
            location=payload.location,
            created_at=now,
            status="received",
            weather_snapshot=None,
            forecast=None,
        )
        self._events[event_id] = event
        return event

    def get(self, event_id: str) -> Optional[EventResponse]:
        """Retrieve event by ID."""
        return self._events.get(event_id)

    def list(self) -> List[EventResponse]:
        """List all events."""
        return list(self._events.values())


# Singleton repository instance for app lifetime
repository = InMemoryEventsRepository()
