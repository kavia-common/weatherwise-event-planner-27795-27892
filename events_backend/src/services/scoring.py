from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Sequence, Tuple

from src.schemas.models import ForecastItem, ScoredOption, WeatherSnapshot


@dataclass(frozen=True)
class ScoringWeights:
    """
    PUBLIC_INTERFACE
    Weights used to compute the weather suitability score.

    The score is computed as a weighted sum of the following sub-scores:
    - temperature_score: favors temperatures around a comfort range (default 18-26°C)
    - precipitation_score: penalizes precipitation and its probability
    - wind_score: penalizes high wind speeds (using current snapshot when available)
    - condition_bonus: small bonus for "Clear" and small penalty for "Thunderstorm"

    Final score is normalized to [0, 1].
    """
    temperature: float = 0.4
    precipitation_amount: float = 0.25
    precipitation_probability: float = 0.2
    wind: float = 0.1
    condition: float = 0.05


@dataclass(frozen=True)
class ComfortConfig:
    """Comfort ranges and limits for scoring."""
    ideal_min_temp_c: float = 18.0
    ideal_max_temp_c: float = 26.0
    # Linear decay up to these hard limits, after which temperature score is 0
    hard_min_temp_c: float = 5.0
    hard_max_temp_c: float = 35.0

    # Wind comfort thresholds (km/h)
    wind_ok_kph: float = 20.0
    wind_max_kph: float = 40.0

    # Precipitation thresholds
    precip_ok_mm: float = 0.0
    precip_bad_mm: float = 2.0  # >2mm is considered undesirable


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def temperature_score(temp_c: float, cfg: ComfortConfig) -> float:
    """
    PUBLIC_INTERFACE
    Score temperature based on comfort band:
    - 1.0 inside [ideal_min, ideal_max]
    - linearly decays to 0.0 at hard limits
    """
    if cfg.ideal_min_temp_c <= temp_c <= cfg.ideal_max_temp_c:
        return 1.0
    if temp_c < cfg.ideal_min_temp_c:
        # from hard_min to ideal_min: 0 -> 1
        if temp_c <= cfg.hard_min_temp_c:
            return 0.0
        return (temp_c - cfg.hard_min_temp_c) / (cfg.ideal_min_temp_c - cfg.hard_min_temp_c)
    # temp > ideal_max
    if temp_c >= cfg.hard_max_temp_c:
        return 0.0
    return (cfg.hard_max_temp_c - temp_c) / (cfg.hard_max_temp_c - cfg.ideal_max_temp_c)


def precipitation_amount_score(mm: Optional[float], cfg: ComfortConfig) -> float:
    """
    PUBLIC_INTERFACE
    Score precipitation amount:
    - 1.0 for 0mm
    - decays linearly to 0.0 at >= precip_bad_mm
    """
    if mm is None:
        # Unknown amount; be cautiously optimistic but not perfect
        return 0.7
    if mm <= cfg.precip_ok_mm:
        return 1.0
    if mm >= cfg.precip_bad_mm:
        return 0.0
    return 1.0 - (mm - cfg.precip_ok_mm) / (cfg.precip_bad_mm - cfg.precip_ok_mm)


def precipitation_probability_score(p: Optional[float]) -> float:
    """
    PUBLIC_INTERFACE
    Score precipitation probability (0..1):
    - 1.0 at 0%
    - 0.0 at >= 100%
    """
    if p is None:
        # Unknown probability; be neutral
        return 0.6
    return 1.0 - _clamp01(p)


def wind_score_kph(wind_kph: Optional[float], cfg: ComfortConfig) -> float:
    """
    PUBLIC_INTERFACE
    Score wind speed:
    - 1.0 for <= wind_ok_kph
    - 0.0 for >= wind_max_kph
    """
    if wind_kph is None:
        return 0.7
    if wind_kph <= cfg.wind_ok_kph:
        return 1.0
    if wind_kph >= cfg.wind_max_kph:
        return 0.0
    return 1.0 - (wind_kph - cfg.wind_ok_kph) / (cfg.wind_max_kph - cfg.wind_ok_kph)


def condition_bonus(condition: str) -> float:
    """
    PUBLIC_INTERFACE
    Provide a small bonus or penalty based on condition string.
    Returns in range [-1, 1] which will later be scaled by weights.condition.
    """
    cond = (condition or "").lower()
    if "thunder" in cond:
        return -1.0
    if "snow" in cond:
        return -0.6
    if "rain" in cond:
        return -0.5
    if "fog" in cond:
        return -0.3
    if "cloud" in cond:
        return 0.0
    if "clear" in cond or "sun" in cond:
        return 1.0
    return 0.0


# PUBLIC_INTERFACE
def score_forecast_item(
    item: ForecastItem,
    snapshot: Optional[WeatherSnapshot] = None,
    weights: ScoringWeights = ScoringWeights(),
    cfg: ComfortConfig = ComfortConfig(),
) -> float:
    """
    Compute a normalized suitability score [0,1] for a single ForecastItem.

    Inputs:
        item: ForecastItem with temperature, precipitation, probability, condition.
        snapshot: optional current WeatherSnapshot to estimate wind (if item lacks it).
        weights: ScoringWeights to adjust importance of subscores.
        cfg: ComfortConfig with comfort ranges and thresholds.

    Returns:
        float in [0, 1] representing suitability.
    """
    t_score = temperature_score(item.temperature_c, cfg)
    p_amt_score = precipitation_amount_score(item.precipitation_mm, cfg)
    p_prob_score = precipitation_probability_score(item.probability_precip)
    w_score = wind_score_kph(snapshot.wind_kph if snapshot else None, cfg)
    cond_adj = condition_bonus(item.condition)

    # Weighted sum with small condition adjustment
    raw = (
        t_score * weights.temperature
        + p_amt_score * weights.precipitation_amount
        + p_prob_score * weights.precipitation_probability
        + w_score * weights.wind
        + cond_adj * weights.condition
    )
    # Scale by total positive weights (excluding signed condition magnitude) to keep roughly within 0..1
    total_pos = max(1e-6, weights.temperature + weights.precipitation_amount + weights.precipitation_probability + weights.wind)
    normalized = raw / (total_pos + abs(weights.condition))  # include condition influence
    return _clamp01(normalized)


# PUBLIC_INTERFACE
def build_time_windows_for_day(
    day: date,
    window_hours: int = 3,
    step_hours: int = 3,
    tz: timezone = timezone.utc,
) -> List[Tuple[datetime, datetime, str]]:
    """
    Build labeled time windows for a given day.

    Returns:
        List of tuples: (start_dt, end_dt, label)
    """
    start_of_day = datetime(day.year, day.month, day.day, 0, 0, tzinfo=tz)
    windows: List[Tuple[datetime, datetime, str]] = []
    label_map = {
        (6, 9): "Morning window",
        (12, 15): "Afternoon window",
        (17, 20): "Evening window",
    }
    for hour in range(6, 21, step_hours):
        start = start_of_day + timedelta(hours=hour)
        end = start + timedelta(hours=window_hours)
        # Pick a friendly label if available; else generic
        label = next((v for (h1, h2), v in label_map.items() if h1 == hour or h2 == hour), f"Window {hour:02d}:00")
        windows.append((start, end, label))
    return windows


# PUBLIC_INTERFACE
def score_windows_from_forecast(
    windows: Sequence[Tuple[datetime, datetime, str]],
    forecast: Sequence[ForecastItem],
    snapshot: Optional[WeatherSnapshot] = None,
) -> List[ScoredOption]:
    """
    Compute a ScoredOption per time window by averaging the scores of items within each window.

    If a window has no items, it will be omitted.
    """
    results: List[ScoredOption] = []
    for start, end, label in windows:
        items = [f for f in forecast if start <= f.timestamp <= end]
        if not items:
            continue
        scores = [score_forecast_item(it, snapshot=snapshot) for it in items]
        avg_score = sum(scores) / len(scores)
        notes = f"Avg of {len(items)} forecast points between {start.isoformat()} and {end.isoformat()}."
        results.append(ScoredOption(label=label, score=avg_score, start=start, end=end, notes=notes))
    # Sort by score descending
    results.sort(key=lambda x: x.score, reverse=True)
    return results
