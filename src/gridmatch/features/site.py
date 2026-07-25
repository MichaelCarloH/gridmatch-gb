"""Day-ahead, issue-time-safe site feature construction."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import holidays
import numpy as np
import pandas as pd

FEATURE_VERSION = "site-features-v1"

FEATURE_COLUMNS = [
    "settlement_period",
    "horizon_periods",
    "period_sin",
    "period_cos",
    "weekday",
    "weekend",
    "bank_holiday",
    "day_of_year_sin",
    "day_of_year_cos",
    "temperature_c",
    "heating_degree_c",
    "cooling_degree_c",
    "irradiance_wm2",
    "cloud_cover_pct",
    "wind_speed_mps",
    "wind_speed_squared",
    "wind_speed_cubed",
    "wind_direction_sin",
    "wind_direction_cos",
    "wind_gust_mps",
    "surface_pressure_hpa",
    "sun_elevation_deg",
    "is_daylight",
    "lag_1",
    "lag_2",
    "lag_48",
    "lag_96",
    "lag_336",
    "rolling_mean_48",
    "rolling_std_48",
    "rolling_same_period_mean",
    "recent_residual",
    "installed_capacity_mw",
    "latitude",
    "longitude",
    "archetype_code",
    "technology_code",
    "is_open",
    "is_generation",
    "is_solar",
    "is_wind",
]

ARCHETYPE_CODES = {
    "office": 1,
    "warehouse": 2,
    "retail": 3,
    "hospitality": 4,
    "manufacturing": 5,
    "renewable_generator": 6,
}
TECHNOLOGY_CODES = {"grid_supply": 0, "solar": 1, "wind": 2}


@dataclass(frozen=True)
class RollingOriginSplit:
    fold: int
    training_cutoff: pd.Timestamp
    test_start: pd.Timestamp
    test_end: pd.Timestamp
    train_mask: pd.Series
    test_mask: pd.Series


def _sun_elevation(
    local_time: pd.Series,
    latitude: float,
) -> np.ndarray:
    day = local_time.dt.dayofyear.to_numpy(dtype=float)
    hour = (
        local_time.dt.hour.to_numpy(dtype=float)
        + local_time.dt.minute.to_numpy(dtype=float) / 60
    )
    declination = np.deg2rad(23.44 * np.sin(2 * np.pi * (284 + day) / 365))
    latitude_rad = np.deg2rad(latitude)
    hour_angle = np.deg2rad(15 * (hour - 12))
    sine_elevation = (
        np.sin(latitude_rad) * np.sin(declination)
        + np.cos(latitude_rad) * np.cos(declination) * np.cos(hour_angle)
    )
    return np.rad2deg(np.arcsin(np.clip(sine_elevation, -1, 1)))


def _operating_schedule(archetype: str, hour: np.ndarray) -> np.ndarray:
    windows = {
        "office": (8.0, 18.5),
        "warehouse": (6.0, 22.0),
        "retail": (9.0, 21.0),
        "hospitality": (6.0, 23.5),
        "manufacturing": (6.0, 19.0),
    }
    if archetype not in windows:
        return np.ones(len(hour), dtype=float)
    start, end = windows[archetype]
    return ((hour >= start) & (hour < end)).astype(float)


def _safe_lookup(
    target_by_time: pd.Series,
    source_times: pd.Series,
    issue_times: pd.Series,
) -> np.ndarray:
    values = target_by_time.reindex(pd.DatetimeIndex(source_times)).to_numpy(
        dtype=float,
        copy=True,
    )
    known = source_times.to_numpy() <= issue_times.to_numpy()
    values[~known] = np.nan
    return values


def build_site_features(
    observations: pd.DataFrame,
    site: pd.Series | dict,
) -> pd.DataFrame:
    """Build features using only meter values known by each forecast issue time.

    Weather fields are treated as forecast-weather inputs for methodology testing.
    The current demo values are simulated realised weather and this limitation must
    remain disclosed in model metadata and cards.
    """
    metadata = dict(site)
    frame = observations.sort_values("timestamp_utc").reset_index(drop=True).copy()
    frame["valid_time_utc"] = pd.to_datetime(frame["timestamp_utc"], utc=True)
    frame["settlement_date"] = pd.to_datetime(frame["settlement_date"]).dt.date
    frame["actual_mwh"] = frame["energy_mwh"].astype(float)

    frame["issue_time_utc"] = frame["valid_time_utc"] - pd.Timedelta(hours=24)
    frame["horizon_periods"] = (
        (frame["valid_time_utc"] - frame["issue_time_utc"])
        / pd.Timedelta(minutes=30)
    ).astype(int)

    local_time = frame["valid_time_utc"].dt.tz_convert("Europe/London")
    hour = local_time.dt.hour.to_numpy() + local_time.dt.minute.to_numpy() / 60
    day_of_year = local_time.dt.dayofyear.to_numpy()
    angle = 2 * np.pi * (hour * 2) / 48
    frame["period_sin"] = np.sin(angle)
    frame["period_cos"] = np.cos(angle)
    frame["weekday"] = local_time.dt.dayofweek.astype(int)
    frame["weekend"] = (local_time.dt.dayofweek >= 5).astype(int)
    gb_holidays = holidays.UnitedKingdom(
        years=sorted(set(local_time.dt.year.astype(int)))
    )
    frame["bank_holiday"] = local_time.dt.date.map(
        lambda value: int(value in gb_holidays)
    )
    frame["day_of_year_sin"] = np.sin(2 * np.pi * day_of_year / 365.25)
    frame["day_of_year_cos"] = np.cos(2 * np.pi * day_of_year / 365.25)

    frame["heating_degree_c"] = np.clip(15 - frame["temperature_c"], 0, None)
    frame["cooling_degree_c"] = np.clip(frame["temperature_c"] - 20, 0, None)
    frame["wind_speed_squared"] = frame["wind_speed_mps"] ** 2
    frame["wind_speed_cubed"] = frame["wind_speed_mps"] ** 3
    direction = np.deg2rad(frame["wind_direction_deg"])
    frame["wind_direction_sin"] = np.sin(direction)
    frame["wind_direction_cos"] = np.cos(direction)
    frame["sun_elevation_deg"] = _sun_elevation(
        local_time,
        float(metadata["latitude"]),
    )
    frame["is_daylight"] = frame["is_daylight"].astype(int)

    target_by_time = frame.set_index("valid_time_utc")["actual_mwh"]
    issue_times = frame["issue_time_utc"]
    issue_lag_1_time = issue_times
    issue_lag_2_time = issue_times - pd.Timedelta(minutes=30)
    frame["lag_1"] = _safe_lookup(target_by_time, issue_lag_1_time, issue_times)
    frame["lag_2"] = _safe_lookup(target_by_time, issue_lag_2_time, issue_times)
    for periods in (48, 96, 336):
        source_times = frame["valid_time_utc"] - pd.Timedelta(minutes=30 * periods)
        frame[f"lag_{periods}"] = _safe_lookup(
            target_by_time,
            source_times,
            issue_times,
        )

    frame["rolling_mean_48"] = frame["actual_mwh"].rolling(48).mean().shift(48)
    frame["rolling_std_48"] = (
        frame["actual_mwh"].rolling(48).std(ddof=0).shift(48)
    )
    frame["recent_residual"] = frame["lag_1"] - frame["lag_96"]

    same_period_values = []
    for row in frame.itertuples():
        candidates = [
            target_by_time.get(row.valid_time_utc - pd.Timedelta(days=7 * week), np.nan)
            for week in range(1, 5)
            if row.valid_time_utc - pd.Timedelta(days=7 * week) <= row.issue_time_utc
        ]
        available = [float(value) for value in candidates if pd.notna(value)]
        same_period_values.append(float(np.mean(available)) if available else np.nan)
    frame["rolling_same_period_mean"] = same_period_values

    archetype = str(metadata["business_archetype"])
    technology = str(metadata["technology"])
    frame["installed_capacity_mw"] = float(metadata["installed_capacity_mw"])
    frame["latitude"] = float(metadata["latitude"])
    frame["longitude"] = float(metadata["longitude"])
    frame["archetype_code"] = ARCHETYPE_CODES[archetype]
    frame["technology_code"] = TECHNOLOGY_CODES[technology]
    frame["is_open"] = _operating_schedule(archetype, hour)
    frame["is_generation"] = int(metadata["site_role"] == "generation")
    frame["is_solar"] = int(technology == "solar")
    frame["is_wind"] = int(technology == "wind")

    frame["site_id"] = str(metadata["site_id"])
    frame["site_role"] = str(metadata["site_role"])
    frame["technology"] = technology
    frame["business_archetype"] = archetype
    frame["data_origin"] = str(metadata["data_origin"])
    return frame


def rolling_origin_splits(
    frame: pd.DataFrame,
    folds: int = 2,
    test_days: int = 7,
    min_train_days: int = 90,
) -> list[RollingOriginSplit]:
    """Return expanding-window splits over complete settlement dates."""
    dates = sorted(frame["settlement_date"].unique())
    required = min_train_days + folds * test_days
    if len(dates) < required:
        raise ValueError(
            f"need at least {required} settlement days, received {len(dates)}"
        )
    first_test_position = len(dates) - folds * test_days
    splits = []
    for fold in range(folds):
        start_position = first_test_position + fold * test_days
        test_dates = dates[start_position : start_position + test_days]
        test_start_date, test_end_date = test_dates[0], test_dates[-1]
        test_mask = frame["settlement_date"].isin(test_dates)
        earliest_issue_time = frame.loc[test_mask, "issue_time_utc"].min()
        train_mask = frame["valid_time_utc"] <= earliest_issue_time
        training_cutoff = frame.loc[train_mask, "valid_time_utc"].max()
        splits.append(
            RollingOriginSplit(
                fold=fold + 1,
                training_cutoff=pd.Timestamp(training_cutoff),
                test_start=pd.Timestamp(test_start_date),
                test_end=pd.Timestamp(test_end_date),
                train_mask=train_mask,
                test_mask=test_mask,
            )
        )
    return splits
