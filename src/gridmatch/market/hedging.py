"""Lightweight asymmetric hedge-cost and scenario calculations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

import numpy as np
from scipy.stats import norm

from gridmatch.market.prices import PriceAssumptions

MIN_QUANTILE = 0.1
MAX_QUANTILE = 0.9
NORMAL_Q90 = float(norm.ppf(0.9))


@dataclass(frozen=True)
class HedgeCostResult:
    """Cost decomposition for one signed net-demand hedge."""

    realised_net_demand_mwh: float
    hedged_volume_mwh: float
    short_exposure_mwh: float
    long_exposure_mwh: float
    day_ahead_cost_gbp: float
    imbalance_cost_gbp: float
    total_cost_gbp: float


def interpolate_forecast_quantile(
    q10: float | np.ndarray,
    q50: float | np.ndarray,
    q90: float | np.ndarray,
    quantile: float,
) -> np.ndarray:
    """Interpolate a quantile between the supplied q10, q50 and q90."""
    tau = float(np.clip(quantile, MIN_QUANTILE, MAX_QUANTILE))
    lower = np.asarray(q10, dtype=float)
    median = np.asarray(q50, dtype=float)
    upper = np.asarray(q90, dtype=float)
    if tau <= 0.5:
        weight = (tau - 0.1) / 0.4
        return lower + weight * (median - lower)
    weight = (tau - 0.5) / 0.4
    return median + weight * (upper - median)


def evaluate_hedge_cost(
    realised_net_demand_mwh: float,
    hedged_volume_mwh: float,
    market_reference_price_gbp_mwh: float,
    short_price_gbp_mwh: float,
    long_price_gbp_mwh: float,
) -> HedgeCostResult:
    """Apply the documented signed-volume prototype cost convention."""
    if short_price_gbp_mwh < market_reference_price_gbp_mwh:
        raise ValueError("Short price cannot be below the market reference")
    if long_price_gbp_mwh > market_reference_price_gbp_mwh:
        raise ValueError("Long recovery cannot exceed the market reference")
    imbalance = realised_net_demand_mwh - hedged_volume_mwh
    short_exposure = max(imbalance, 0.0)
    long_exposure = max(-imbalance, 0.0)
    day_ahead_cost = (
        hedged_volume_mwh * market_reference_price_gbp_mwh
    )
    imbalance_cost = (
        short_exposure * short_price_gbp_mwh
        - long_exposure * long_price_gbp_mwh
    )
    return HedgeCostResult(
        realised_net_demand_mwh=float(realised_net_demand_mwh),
        hedged_volume_mwh=float(hedged_volume_mwh),
        short_exposure_mwh=float(short_exposure),
        long_exposure_mwh=float(long_exposure),
        day_ahead_cost_gbp=float(day_ahead_cost),
        imbalance_cost_gbp=float(imbalance_cost),
        total_cost_gbp=float(day_ahead_cost + imbalance_cost),
    )


def implied_optimal_quantile(
    market_reference_price_gbp_mwh: float,
    short_price_gbp_mwh: float,
    long_price_gbp_mwh: float,
) -> float:
    """Return the asymmetric-cost newsvendor quantile."""
    denominator = short_price_gbp_mwh - long_price_gbp_mwh
    if denominator <= 0:
        raise ValueError("Short price must exceed long recovery price")
    quantile = (
        short_price_gbp_mwh - market_reference_price_gbp_mwh
    ) / denominator
    return float(np.clip(quantile, MIN_QUANTILE, MAX_QUANTILE))


def forecast_distribution_samples(
    q10: float,
    q50: float,
    q90: float,
    *,
    sample_count: int = 399,
) -> np.ndarray:
    """Deterministically approximate a split-normal forecast distribution."""
    if not q10 <= q50 <= q90:
        raise ValueError("Forecast quantiles must be ordered")
    probabilities = (
        np.arange(sample_count, dtype=float) + 0.5
    ) / sample_count
    z_scores = norm.ppf(probabilities)
    lower_scale = max((q50 - q10) / NORMAL_Q90, 1e-9)
    upper_scale = max((q90 - q50) / NORMAL_Q90, 1e-9)
    return np.where(
        z_scores < 0,
        q50 + z_scores * lower_scale,
        q50 + z_scores * upper_scale,
    )


def expected_exposures(
    q10: float,
    q50: float,
    q90: float,
    hedged_volume_mwh: float,
) -> tuple[float, float]:
    """Estimate expected short and long exposure from fixed quantile samples."""
    samples = forecast_distribution_samples(q10, q50, q90)
    imbalance = samples - hedged_volume_mwh
    return (
        float(np.maximum(imbalance, 0).mean()),
        float(np.maximum(-imbalance, 0).mean()),
    )


def _forecast_quantiles(
    forecast: Mapping[str, Any],
    forecast_model: str,
) -> tuple[float, float, float]:
    prefix = f"{forecast_model}_net"
    keys = (
        f"{prefix}_q10_mwh",
        f"{prefix}_q50_mwh",
        f"{prefix}_q90_mwh",
    )
    try:
        values = tuple(float(forecast[key]) for key in keys)
    except KeyError as error:
        raise ValueError(
            f"Forecast model '{forecast_model}' lacks net quantiles"
        ) from error
    if not values[0] <= values[1] <= values[2]:
        raise ValueError("Forecast quantiles must be ordered")
    return values


def scenario_recommendation(
    forecast: Mapping[str, Any],
    *,
    market_reference_price_gbp_mwh: float,
    public_system_price_gbp_mwh: float,
    short_cost_multiplier: float = 1.35,
    long_value_multiplier: float = 0.65,
    risk_preference: float = 0.0,
    forecast_model: str = "bottom_up",
) -> dict[str, float | str]:
    """Recompute a single lightweight hedge recommendation for a future API."""
    assumptions = PriceAssumptions(
        short_cost_multiplier=short_cost_multiplier,
        long_value_multiplier=long_value_multiplier,
    )
    if not 0 <= risk_preference <= 1:
        raise ValueError("Risk preference must be between 0 and 1")
    short_price = max(
        public_system_price_gbp_mwh,
        market_reference_price_gbp_mwh
        * assumptions.short_cost_multiplier,
    )
    long_price = min(
        public_system_price_gbp_mwh,
        market_reference_price_gbp_mwh
        * assumptions.long_value_multiplier,
    )
    cost_quantile = implied_optimal_quantile(
        market_reference_price_gbp_mwh,
        short_price,
        long_price,
    )
    selected_quantile = cost_quantile + risk_preference * (
        MAX_QUANTILE - cost_quantile
    )
    q10, q50, q90 = _forecast_quantiles(forecast, forecast_model)
    recommended = interpolate_forecast_quantile(
        q10,
        q50,
        q90,
        selected_quantile,
    )
    recommended_value = float(recommended.item())
    expected_short, expected_long = expected_exposures(
        q10,
        q50,
        q90,
        recommended_value,
    )
    return {
        "forecast_model": forecast_model,
        "recommended_quantile": float(selected_quantile),
        "recommended_mwh": recommended_value,
        "expected_short_exposure_mwh": expected_short,
        "expected_long_exposure_mwh": expected_long,
        "market_reference_price_gbp_mwh": float(
            market_reference_price_gbp_mwh
        ),
        "public_system_price_gbp_mwh": float(
            public_system_price_gbp_mwh
        ),
        "short_price_gbp_mwh": float(short_price),
        "long_price_gbp_mwh": float(long_price),
        "short_cost_multiplier": short_cost_multiplier,
        "long_value_multiplier": long_value_multiplier,
        "risk_preference": risk_preference,
    }
