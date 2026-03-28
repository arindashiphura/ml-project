"""
Climate intelligence core: Uganda-oriented rainfall forecast (ML demo) and risk scoring.

Trains on synthetic data that approximate bimodal rainfall (Mar–May, Sep–Nov).
Replace with ERA5 / station data + retrained models for production use.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
from sklearn.ensemble import RandomForestRegressor

# --- Uganda context (representative; refine with admin boundaries) ---
REGIONS = [
    {"id": "central", "name": "Central", "notes": "Lake Victoria influence, urban heat"},
    {"id": "eastern", "name": "Eastern", "notes": "Mt. Elgon rainfall gradient"},
    {"id": "western", "name": "Western", "notes": "Highlands, coffee/banana belt"},
    {"id": "northern", "name": "Northern", "notes": "Drier single peak, pastoral risk"},
]

REGION_INDEX = {r["id"]: i for i, r in enumerate(REGIONS)}


def _bimodal_rain_signal(month: int) -> float:
    """Rough Uganda-like seasonality (mm baseline contribution)."""
    m = (month - 1) / 12.0 * 2 * math.pi
    # Long rains ~MAM, short rains ~SON
    peak1 = math.exp(-0.5 * ((month - 4) / 1.8) ** 2) * 120
    peak2 = math.exp(-0.5 * ((month - 10) / 1.6) ** 2) * 90
    return peak1 + peak2


def _synthetic_dataset(n: int = 4000, seed: int = 42) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed)
    month = rng.integers(1, 13, size=n)
    region = rng.integers(0, len(REGIONS), size=n)
    temp_c = rng.normal(23.0, 3.5, size=n)
    humidity_pct = rng.uniform(45.0, 95.0, size=n)
    recent_rain_mm = rng.uniform(0.0, 180.0, size=n)

    baseline = np.array([_bimodal_rain_signal(int(m)) for m in month])
    regional = np.where(region == 3, -15.0, 0.0)  # Northern slightly drier
    regional = np.where(region == 2, 12.0, regional)  # Western wetter
    noise = rng.normal(0, 22.0, size=n)
    # Next-week total rainfall (target)
    next_week_mm = np.maximum(
        0.0,
        baseline * 0.35
        + recent_rain_mm * 0.15
        + (humidity_pct - 60) * 0.4
        + regional
        + noise,
    )
    X = np.column_stack(
        [month.astype(float), region.astype(float), temp_c, humidity_pct, recent_rain_mm]
    )
    return X, next_week_mm


_X, _y = _synthetic_dataset()
_MODEL = RandomForestRegressor(
    n_estimators=120,
    max_depth=14,
    min_samples_leaf=4,
    random_state=42,
    n_jobs=-1,
)
_MODEL.fit(_X, _y)


@dataclass(frozen=True)
class ForecastResult:
    region_id: str
    month: int
    next_week_rain_mm: float
    band: str
    summary: str


def forecast_next_week_rainfall(
    *,
    region_id: str,
    month: int,
    temp_c: float,
    humidity_pct: float,
    recent_rain_mm: float,
) -> ForecastResult:
    if region_id not in REGION_INDEX:
        raise ValueError("Unknown region")
    if not 1 <= month <= 12:
        raise ValueError("month must be 1–12")
    ri = float(REGION_INDEX[region_id])
    feats = np.array([[float(month), ri, temp_c, humidity_pct, recent_rain_mm]])
    mm = float(max(0.0, _MODEL.predict(feats)[0]))
    if mm < 15:
        band = "dry"
        summary = "Below typical weekly totals — monitor soil moisture and water storage."
    elif mm < 45:
        band = "moderate"
        summary = "Near typical weekly rainfall — favourable for most field operations."
    else:
        band = "wet"
        summary = "Elevated weekly rainfall — watch for runoff, pests, and access roads."
    return ForecastResult(
        region_id=region_id,
        month=month,
        next_week_rain_mm=round(mm, 1),
        band=band,
        summary=summary,
    )


@dataclass(frozen=True)
class RiskBreakdown:
    level: str  # low | moderate | high | severe
    score: float  # 0–100
    agriculture: str
    energy: str
    government: str
    drivers: list[str]


def assess_climate_risks(
    *,
    forecast_mm: float,
    month: int,
    recent_dry_spell_days: int,
    flood_events_30d: int,
) -> RiskBreakdown:
    """Rule-based composite on top of ML rainfall (transparent for policy use)."""
    drivers: list[str] = []
    score = 35.0

    if forecast_mm < 12:
        score += 18
        drivers.append("Low expected weekly rainfall")
    elif forecast_mm > 85:
        score += 14
        drivers.append("Very high expected weekly rainfall")

    if recent_dry_spell_days > 14:
        score += 20
        drivers.append(f"Prolonged dry spell ({recent_dry_spell_days} days)")
    elif recent_dry_spell_days > 7:
        score += 10
        drivers.append("Emerging dry spell")

    if flood_events_30d > 0:
        score += min(25, flood_events_30d * 12)
        drivers.append("Recent flood / heavy rain episodes in the last 30 days")

    # Seasonal stress (simplified)
    if month in (1, 2, 12) and forecast_mm < 20:
        score += 8
        drivers.append("Dry season conditions — elevated agricultural water stress")

    score = float(min(100, max(0, score)))

    if score < 35:
        level = "low"
    elif score < 55:
        level = "moderate"
    elif score < 75:
        level = "high"
    else:
        level = "severe"

    agriculture = (
        "Prioritise drought-tolerant varieties and flexible planting windows; verify soil moisture before costly inputs."
        if score >= 55
        else "Maintain regular extension checks; align fertiliser and planting with verified soil moisture."
    )
    energy = (
        "Expect hydro variability; stress-test grid planning and diesel backup for critical loads."
        if forecast_mm < 15 or forecast_mm > 80
        else "Hydro inflows likely stable short term — still monitor reservoir rule curves."
    )
    government = (
        "Activate early-warning comms with districts; coordinate WASH and transport resilience."
        if level in ("high", "severe")
        else "Continue routine monitoring; publish district-level advisories where score exceeds local thresholds."
    )

    return RiskBreakdown(
        level=level,
        score=round(score, 1),
        agriculture=agriculture,
        energy=energy,
        government=government,
        drivers=drivers or ["No acute drivers beyond baseline variability"],
    )
