from typing import Generator

from src.core.config import get_settings, Settings
from src.data.events_repository import repository, InMemoryEventsRepository


# PUBLIC_INTERFACE
def get_settings_dep() -> Settings:
    """Dependency to access application settings."""
    return get_settings()


# PUBLIC_INTERFACE
def get_events_repo() -> Generator[InMemoryEventsRepository, None, None]:
    """Dependency that yields the events repository."""
    yield repository
