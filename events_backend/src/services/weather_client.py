from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

from src.schemas.models import ForecastItem, WeatherSnapshot
from src.services.cache import TTLCache


class GeoError(Exception):
    """Raised when geocoding fails."""


class WeatherProviderError(Exception):
    """Raised when weather provider calls fail."""


class NominatimClient:
    """
    PUBLIC_INTERFACE
    Minimal client for location search and geocoding via OpenStreetMap Nominatim.
    """

    def __init__(self, user_agent: str = "weatherwise-events/0.1.0") -> None:
        self._base_url = "https://nominatim.openstreetmap.org"
        self._user_agent = user_agent
        # Cache location queries for 12 hours
        self._cache: TTLCache[str, List[Dict[str, Any]]] = TTLCache(ttl_seconds=60 * 60 * 12, maxsize=1000)

    async def search(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        key = f"{query}:{limit}".lower().strip()

        cached = self._cache.get(key)
        if cached is not None:
            return cached

        headers = {"User-Agent": self._user_agent, "Accept": "application/json"}
        params = {"q": query, "format": "json", "addressdetails": 1, "limit": limit}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            resp = await client.get(f"{self._base_url}/search", params=params)
            if resp.status_code != 200:
                raise GeoError(f"Nominatim search failed: {resp.status_code}")
            data = resp.json()
            # Important: Respect Nominatim usage policy by caching and providing UA.
            self._cache.set(key, data)
            return data

    async def geocode_first(self, query: str) -> Tuple[float, float, str]:
        """
        PUBLIC_INTERFACE
        Geocode a string and return (lat, lon, display_name). Raises GeoError if no results.
        """
        results = await self.search(query, limit=1)
        if not results:
            raise GeoError("No results from geocoding")
        item = results[0]
        return float(item["lat"]), float(item["lon"]), item.get("display_name", query)


class OpenMeteoClient:
    """
    PUBLIC_INTERFACE
    Client for fetching weather data from Open-Meteo.
    """

    def __init__(self) -> None:
        # Cache current snapshots for 2 minutes, forecasts for 30 minutes
        self._cache_current: TTLCache[str, WeatherSnapshot] = TTLCache(ttl_seconds=120, maxsize=1000)
        self._cache_forecast: TTLCache[str, List[ForecastItem]] = TTLCache(ttl_seconds=1800, maxsize=1000)

    @staticmethod
    def _kmh_from_ms(ms: Optional[float]) -> Optional[float]:
        if ms is None:
            return None
        return ms * 3.6

    def _map_current(self, payload: Dict[str, Any], as_of: datetime) -> WeatherSnapshot:
        current = payload.get("current", {})
        temperature = current.get("temperature_2m")
        wind_ms = current.get("wind_speed_10m")
        humidity = current.get("relative_humidity_2m")
        condition = "Unknown"
        # Open-Meteo returns weather_code; we can map some basic codes
        code = current.get("weather_code")
        if code is not None:
            # Simplified mapping
            if code == 0:
                condition = "Clear"
            elif code in (1, 2, 3):
                condition = "Partly Cloudy"
            elif code in (45, 48):
                condition = "Fog"
            elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
                condition = "Rain"
            elif code in (71, 73, 75, 77, 85, 86):
                condition = "Snow"
            elif code in (95, 96, 99):
                condition = "Thunderstorm"
            else:
                condition = "Clouds"

        return WeatherSnapshot(
            timestamp=as_of,
            temperature_c=float(temperature) if temperature is not None else 0.0,
            condition=condition,
            humidity=float(humidity) if humidity is not None else None,
            wind_kph=self._kmh_from_ms(wind_ms),
        )

    def _map_forecast(self, payload: Dict[str, Any]) -> List[ForecastItem]:
        hourly = payload.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        precip = hourly.get("precipitation", [])
        prob = hourly.get("precipitation_probability", [])
        codes = hourly.get("weather_code", [])

        items: List[ForecastItem] = []
        for i, ts in enumerate(times):
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(timezone.utc)
            except Exception:
                # Fallback parsing
                dt = datetime.strptime(ts, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc)

            code = codes[i] if i < len(codes) else None
            condition = "Clouds"
            if code is not None:
                if code == 0:
                    condition = "Clear"
                elif code in (1, 2, 3):
                    condition = "Partly Cloudy"
                elif code in (45, 48):
                    condition = "Fog"
                elif code in (51, 53, 55, 61, 63, 65, 80, 81, 82):
                    condition = "Rain"
                elif code in (71, 73, 75, 77, 85, 86):
                    condition = "Snow"
                elif code in (95, 96, 99):
                    condition = "Thunderstorm"
                else:
                    condition = "Clouds"

            items.append(
                ForecastItem(
                    timestamp=dt,
                    temperature_c=float(temps[i]) if i < len(temps) else 0.0,
                    condition=condition,
                    precipitation_mm=float(precip[i]) if i < len(precip) and precip[i] is not None else None,
                    probability_precip=float(prob[i]) / 100.0 if i < len(prob) and prob[i] is not None else None,
                )
            )
        return items

    async def get_current(self, lat: float, lon: float) -> WeatherSnapshot:
        key = f"current:{lat:.4f},{lon:.4f}"
        cached = self._cache_current.get(key)
        if cached is not None:
            return cached

        params = {
            "latitude": lat,
            "longitude": lon,
            "current": ["temperature_2m", "relative_humidity_2m", "wind_speed_10m", "weather_code"],
            "timezone": "UTC",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            if resp.status_code != 200:
                raise WeatherProviderError(f"Open-Meteo current failed: {resp.status_code}")
            data = resp.json()
        snapshot = self._map_current(data, as_of=datetime.now(tz=timezone.utc))
        self._cache_current.set(key, snapshot)
        return snapshot

    async def get_forecast(self, lat: float, lon: float, hours: int = 24, step_hours: int = 6) -> List[ForecastItem]:
        hours = max(1, min(hours, 168))  # max 7 days window
        step_hours = max(1, min(step_hours, 24))
        key = f"forecast:{lat:.4f},{lon:.4f}:{hours}:{step_hours}"
        cached = self._cache_forecast.get(key)
        if cached is not None:
            return cached

        now = datetime.now(tz=timezone.utc)
        end = now + timedelta(hours=hours)
        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": ["temperature_2m", "precipitation", "precipitation_probability", "weather_code"],
            "start_hour": now.strftime("%Y-%m-%dT%H:00"),
            "end_hour": end.strftime("%Y-%m-%dT%H:00"),
            "timezone": "UTC",
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get("https://api.open-meteo.com/v1/forecast", params=params)
            if resp.status_code != 200:
                raise WeatherProviderError(f"Open-Meteo forecast failed: {resp.status_code}")
            data = resp.json()

        # Map to ForecastItem list then downsample by step_hours
        all_items = self._map_forecast(data)
        if step_hours > 1:
            # keep every Nth hour
            filtered = [item for idx, item in enumerate(all_items) if idx % step_hours == 0]
        else:
            filtered = all_items

        self._cache_forecast.set(key, filtered)
        return filtered


# Singleton clients
nominatim_client = NominatimClient()
openmeteo_client = OpenMeteoClient()
