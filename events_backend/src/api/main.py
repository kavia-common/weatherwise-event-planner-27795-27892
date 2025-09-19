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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ALLOW_ORIGINS,
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
