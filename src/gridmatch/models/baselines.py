"""Leakage-safe baseline forecasts for demand, solar and wind sites."""

from __future__ import annotations

import numpy as np
import pandas as pd

BASELINE_DESCRIPTIONS = {
    "previous_day": "Actual energy at the forecast issue time, exactly 48 periods before valid time.",
    "previous_week": "Actual energy 336 periods before valid time.",
    "rolling_same_period": "Mean of the same UTC half-hour across the prior four weeks.",
    "persistence": "Latest generation available at the day-ahead issue time.",
    "physical_solar": "Capacity-scaled irradiance with a temperature derate and night-time zero.",
    "physical_wind": "Stylised cubic wind power curve with cut-in, rated and cut-out speeds.",
}


def _fill(values: np.ndarray, frame: pd.DataFrame) -> np.ndarray:
    fallback = frame["rolling_mean_48"].to_numpy(dtype=float)
    result = np.asarray(values, dtype=float).copy()
    result = np.where(np.isnan(result), fallback, result)
    median = float(np.nanmedian(frame["actual_mwh"]))
    return np.nan_to_num(result, nan=median)


def _physical_solar(frame: pd.DataFrame, capacity_mw: float) -> np.ndarray:
    temperature_derate = np.clip(
        1 - 0.004 * np.maximum(frame["temperature_c"].to_numpy() - 25, 0),
        0.85,
        1.0,
    )
    power_mw = (
        capacity_mw
        * frame["irradiance_wm2"].to_numpy(dtype=float)
        / 1000
        * temperature_derate
    )
    energy_mwh = power_mw * 0.5
    return np.where(frame["is_daylight"].to_numpy(dtype=bool), energy_mwh, 0.0)


def _physical_wind(frame: pd.DataFrame, capacity_mw: float) -> np.ndarray:
    speed = frame["wind_speed_mps"].to_numpy(dtype=float)
    fraction = np.zeros(len(frame))
    ramp = (speed >= 3.0) & (speed < 12.0)
    fraction[ramp] = ((speed[ramp] - 3.0) / 9.0) ** 3
    fraction[(speed >= 12.0) & (speed <= 25.0)] = 1.0
    return capacity_mw * fraction * 0.5


def baseline_predictions(
    frame: pd.DataFrame,
    site: pd.Series | dict,
) -> dict[str, np.ndarray]:
    """Return all baselines relevant to a site's role and technology."""
    metadata = dict(site)
    predictions = {
        "previous_day": _fill(frame["lag_48"].to_numpy(), frame),
        "previous_week": _fill(frame["lag_336"].to_numpy(), frame),
        "rolling_same_period": _fill(
            frame["rolling_same_period_mean"].to_numpy(),
            frame,
        ),
    }
    technology = str(metadata["technology"])
    capacity = float(metadata["installed_capacity_mw"])
    if str(metadata["site_role"]) == "generation":
        predictions["persistence"] = _fill(frame["lag_1"].to_numpy(), frame)
    if technology == "solar":
        predictions["physical_solar"] = _physical_solar(frame, capacity)
    if technology == "wind":
        predictions["physical_wind"] = _physical_wind(frame, capacity)
    return predictions


def canonical_baseline_name(site: pd.Series | dict) -> str:
    technology = str(dict(site)["technology"])
    if technology == "solar":
        return "physical_solar"
    if technology == "wind":
        return "physical_wind"
    return "rolling_same_period"
