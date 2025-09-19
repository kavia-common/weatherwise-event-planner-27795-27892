openapi_tags = [
    {
        "name": "Health",
        "description": "Service status and operations monitoring endpoints.",
    },
    {
        "name": "Events",
        "description": "Submit, list, and manage event plans; score suitability; generate recommendations.",
    },
    {
        "name": "Weather",
        "description": "Live weather snapshot and forecast via Open-Meteo and location search via Nominatim.",
    },
]


def get_app_description() -> str:
    """
    PUBLIC_INTERFACE
    Build the API description for OpenAPI docs.
    """
    return (
        "WeatherWise Events API provides endpoints to manage event planning, "
        "retrieve weather-informed recommendations (including scoring endpoints), "
        "and serve current/forecast weather data. The API includes detailed schemas "
        "for events, scoring, weather, and email-notification stubs to demonstrate "
        "end-to-end flows. All endpoints are documented with summaries and "
        "descriptions, grouped under Health, Events, and Weather tags."
    )
