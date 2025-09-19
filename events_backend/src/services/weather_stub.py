from datetime import datetime, timedelta
from typing import List

from src.schemas.models import WeatherSnapshot, ForecastItem


class WeatherServiceStub:
    """
    PUBLIC_INTERFACE
    Stub implementation of a weather service.

    Produces deterministic placeholder data. Replace with real provider integration.
    """

    def get_current(self, location: str) -> WeatherSnapshot:
        """
        PUBLIC_INTERFACE
        Return a synthetic WeatherSnapshot for a location.
        """
        # Deterministic pseudo values based on location length
        base = len(location) % 10
        return WeatherSnapshot(
            timestamp=datetime.utcnow(),
            temperature_c=20.0 + base,
            condition="Partly Cloudy",
            humidity=55.0,
            wind_kph=10.0 + base,
        )

    def get_forecast(self, location: str, hours: int = 24, step_hours: int = 6) -> List[ForecastItem]:
        """
        PUBLIC_INTERFACE
        Return a simple stepped forecast list.
        """
        now = datetime.utcnow()
        items: List[ForecastItem] = []
        for h in range(0, hours + 1, step_hours):
            t = now + timedelta(hours=h)
            items.append(
                ForecastItem(
                    timestamp=t,
                    temperature_c=18.0 + (h / 24.0) * 8.0,
                    condition="Clear" if h % 12 != 0 else "Clouds",
                    precipitation_mm=0.0 if h % 12 != 0 else 1.5,
                    probability_precip=0.1 if h % 12 != 0 else 0.5,
                )
            )
        return items


# Singleton instance
weather_service = WeatherServiceStub()
