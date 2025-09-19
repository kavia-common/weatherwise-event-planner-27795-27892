from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from src.schemas.models import EventRequest, EventResponse
import logging


class InMemoryEventsRepository:
    """
    PUBLIC_INTERFACE
    Simple in-memory repository for events.

    This is a placeholder abstraction to be replaced by a database-backed repository later.
    """

    def __init__(self) -> None:
        self._events: Dict[str, EventResponse] = {}
        self._logger = logging.getLogger("events.repository")

    def _send_email_stub(self, to_email: str, subject: str, body: str) -> None:
        """
        PUBLIC_INTERFACE
        Stub for email sending which just logs the intent.
        """
        self._logger.info("[EMAIL_STUB] To=%s | Subject=%s | Body=%s", to_email, subject, body)

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
            user_id=payload.user_id,
            notes=payload.notes,
        )
        self._events[event_id] = event

        # Email notification stub hooks
        self._send_email_stub(
            to_email=event.email,
            subject="Event received",
            body=f"Your event '{event.name}' scheduled for {event.date.isoformat()} at {event.location} has been received.",
        )
        self._send_email_stub(
            to_email="ops@example.com",
            subject="New event submission",
            body=f"New event submitted: {event.id} - {event.name} ({event.email}) on {event.date.isoformat()} @ {event.location}",
        )

        return event

    def get(self, event_id: str) -> Optional[EventResponse]:
        """Retrieve event by ID."""
        return self._events.get(event_id)

    def list(self) -> List[EventResponse]:
        """List all events."""
        return list(self._events.values())

    def list_by_user(self, user_id: str) -> List[EventResponse]:
        """List events filtered by user_id."""
        return [e for e in self._events.values() if e.user_id == user_id]


# Singleton repository instance for app lifetime
repository = InMemoryEventsRepository()
