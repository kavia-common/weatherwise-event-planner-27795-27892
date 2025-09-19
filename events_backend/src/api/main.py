from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import get_settings
from src.core.docs import openapi_tags, get_app_description
from src.api.routers.health import router as health_router
from src.api.routers.events import router as events_router
from src.api.routers.weather import router as weather_router


def create_app() -> FastAPI:
    """
    Factory to create and configure the FastAPI application.
    Loads settings, configures CORS, routers, and OpenAPI metadata.

    OpenAPI/Docs:
    - Title, description, version, tags are set for rich documentation.
    - Routers are registered with explicit prefixes and tags so that the schema
      includes: Health, Events (create/list/get/recommendations/score),
      Weather (search/current/forecast).

    CORS:
    - Allows the configured origins in .env (CORS_ALLOW_ORIGINS), and always includes
      http://localhost:3000 to enable local frontend development.
    """
    settings = get_settings()

    app = FastAPI(
        title="WeatherWise Events API",
        description=get_app_description(),
        version="0.1.0",
        openapi_tags=openapi_tags,
        contact={
            "name": "WeatherWise Events",
            "url": "https://example.com",
        },
        license_info={
            "name": "Proprietary",
        },
    )

    # Ensure localhost:3000 is allowed for frontend development
    configured_origins = [o.strip() for o in (settings.CORS_ALLOW_ORIGINS or []) if o.strip()]
    if "http://localhost:3000" not in configured_origins and "*" not in configured_origins:
        configured_origins.append("http://localhost:3000")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=configured_origins if configured_origins else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(health_router, prefix="", tags=["Health"])
    app.include_router(events_router, prefix="/api/events", tags=["Events"])
    app.include_router(weather_router, prefix="/api/weather", tags=["Weather"])

    return app


app = create_app()
