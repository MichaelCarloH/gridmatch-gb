"""Leakage-aware aggregate features for direct portfolio forecasting."""

from __future__ import annotations

import holidays
import numpy as np
import pandas as pd

PORTFOLIO_FEATURE_VERSION = "portfolio-features-v1"

PORTFOLIO_FEATURE_COLUMNS = [
    "settlement_period",
    "horizon_periods",
    "period_sin",
    "period_cos",
    "weekday",
    "weekend",
    "bank_holiday",
    "day_of_year_sin",
    "day_of_year_cos",
    "demand_temperature_c",
    "demand_cloud_cover_pct",
    "solar_irradiance_wm2",
    "solar_cloud_cover_pct",
    "wind_speed_mps",
    "wind_speed_squared",
    "wind_speed_cubed",
    "wind_gust_mps",
    "surface_pressure_hpa",
    "demand_lag_48",
    "demand_lag_96",
    "demand_lag_336",
    "generation_lag_48",
    "generation_lag_96",
    "generation_lag_336",
    "net_lag_48",
    "net_lag_96",
    "net_lag_336",
    "demand_rolling_mean_48",
    "demand_rolling_std_48",
    "generation_rolling_mean_48",
    "generation_rolling_std_48",
    "net_rolling_mean_48",
    "net_rolling_std_48",
    "demand_site_count",
    "generation_site_count",
    "demand_capacity_mw",
    "generation_capacity_mw",
    "solar_capacity_mw",
    "wind_capacity_mw",
]


def _mean_by_time(
    observations: pd.DataFrame,
    mask: pd.Series,
    column: str,
) -> pd.Series:
    return observations.loc[mask].groupby("timestamp_utc")[column].mean()


def build_portfolio_features(
    observations: pd.DataFrame,
    sites: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate site observations and construct issue-time-safe features."""
    data = observations.copy()
    data["timestamp_utc"] = pd.to_datetime(data["timestamp_utc"], utc=True)
    timestamps = (
        data.groupby("timestamp_utc", as_index=False)
        .agg(
            settlement_date=("settlement_date", "first"),
            settlement_period=("settlement_period", "first"),
        )
        .sort_values("timestamp_utc")
        .reset_index(drop=True)
    )
    demand = (
        data[data["site_role"] == "demand"]
        .groupby("timestamp_utc")["energy_mwh"]
        .sum()
    )
    generation = (
        data[data["site_role"] == "generation"]
        .groupby("timestamp_utc")["energy_mwh"]
        .sum()
    )
    frame = timestamps.rename(columns={"timestamp_utc": "valid_time_utc"})
    frame["actual_demand_mwh"] = frame["valid_time_utc"].map(demand)
    frame["actual_generation_mwh"] = frame["valid_time_utc"].map(generation)
    frame["actual_net_mwh"] = (
        frame["actual_demand_mwh"] - frame["actual_generation_mwh"]
    )
    frame["settlement_date"] = pd.to_datetime(frame["settlement_date"]).dt.date
    frame["issue_time_utc"] = frame["valid_time_utc"] - pd.Timedelta(hours=24)
    frame["horizon_periods"] = 48

    local = frame["valid_time_utc"].dt.tz_convert("Europe/London")
    hour = local.dt.hour.to_numpy() + local.dt.minute.to_numpy() / 60
    angle = 2 * np.pi * (hour * 2) / 48
    day_of_year = local.dt.dayofyear.to_numpy()
    frame["period_sin"] = np.sin(angle)
    frame["period_cos"] = np.cos(angle)
    frame["weekday"] = local.dt.dayofweek.astype(int)
    frame["weekend"] = (local.dt.dayofweek >= 5).astype(int)
    gb_holidays = holidays.UnitedKingdom(
        years=sorted(set(local.dt.year.astype(int)))
    )
    frame["bank_holiday"] = local.dt.date.map(
        lambda value: int(value in gb_holidays)
    )
    frame["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    frame["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)

    demand_mask = data["site_role"] == "demand"
    solar_mask = data["technology"] == "solar"
    wind_mask = data["technology"] == "wind"
    weather_series = {
        "demand_temperature_c": _mean_by_time(
            data,
            demand_mask,
            "temperature_c",
        ),
        "demand_cloud_cover_pct": _mean_by_time(
            data,
            demand_mask,
            "cloud_cover_pct",
        ),
        "solar_irradiance_wm2": _mean_by_time(
            data,
            solar_mask,
            "irradiance_wm2",
        ),
        "solar_cloud_cover_pct": _mean_by_time(
            data,
            solar_mask,
            "cloud_cover_pct",
        ),
        "wind_speed_mps": _mean_by_time(data, wind_mask, "wind_speed_mps"),
        "wind_gust_mps": _mean_by_time(data, wind_mask, "wind_gust_mps"),
        "surface_pressure_hpa": _mean_by_time(
            data,
            wind_mask,
            "surface_pressure_hpa",
        ),
    }
    for column, values in weather_series.items():
        frame[column] = frame["valid_time_utc"].map(values)
    frame["wind_speed_squared"] = frame["wind_speed_mps"] ** 2
    frame["wind_speed_cubed"] = frame["wind_speed_mps"] ** 3

    for prefix in ("demand", "generation", "net"):
        target = frame[f"actual_{prefix}_mwh"]
        for lag in (48, 96, 336):
            frame[f"{prefix}_lag_{lag}"] = target.shift(lag)
        frame[f"{prefix}_rolling_mean_48"] = target.rolling(48).mean().shift(48)
        frame[f"{prefix}_rolling_std_48"] = (
            target.rolling(48).std(ddof=0).shift(48)
        )

    frame["demand_site_count"] = int(sites["site_role"].eq("demand").sum())
    frame["generation_site_count"] = int(
        sites["site_role"].eq("generation").sum()
    )
    frame["demand_capacity_mw"] = float(
        sites.loc[
            sites["site_role"] == "demand",
            "installed_capacity_mw",
        ].sum()
    )
    frame["generation_capacity_mw"] = float(
        sites.loc[
            sites["site_role"] == "generation",
            "installed_capacity_mw",
        ].sum()
    )
    frame["solar_capacity_mw"] = float(
        sites.loc[sites["technology"] == "solar", "installed_capacity_mw"].sum()
    )
    frame["wind_capacity_mw"] = float(
        sites.loc[sites["technology"] == "wind", "installed_capacity_mw"].sum()
    )
    frame["data_origin"] = "simulated"
    return frame
