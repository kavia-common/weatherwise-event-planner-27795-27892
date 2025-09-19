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
        "retrieve weather-informed recommendations, and serve current/forecast "
        "weather data. This foundation is prepared for plugging in real weather "
        "providers, scoring logic, and notification services."
    )
