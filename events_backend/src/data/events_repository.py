from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, List, Optional

from src.schemas.models import EventRequest, EventResponse
import logging
from src.services.notifications import EmailMessage, get_email_service


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
        Provider-agnostic email trigger using the configured EmailService (console by default).
        """
        try:
            service = get_email_service()
            service.send(EmailMessage(to=to_email, subject=subject, body=body))
        except Exception as exc:
            # Fail-safe: log but do not break the main flow
            self._logger.warning("Email stub failed: %s", exc)

    def add(self, payload: EventRequest) -> EventResponse:
        """Create and store a new EventResponse from the request."""
        event_id = str(uuid.uuid4())
        now = datetime.utcnow()
        event = EventResponse(
            id=event_id,
            name=payload.name,
            email=payload.email,
            event_date=payload.event_date,
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
            body=f"Your event '{event.name}' scheduled for {event.event_date.isoformat()} at {event.location} has been received.",
        )
        self._send_email_stub(
            to_email="ops@example.com",
            subject="New event submission",
            body=f"New event submitted: {event.id} - {event.name} ({event.email}) on {event.event_date.isoformat()} @ {event.location}",
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
