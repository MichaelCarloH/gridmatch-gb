"""Deterministic half-hourly synthetic GB commercial and renewable portfolio."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmatch.data.manifests import SourceManifest

SEED = 20260725
START_UTC = "2025-01-01T00:00:00Z"
DAYS = 180

SITE_ROWS = [
    ("dem_office_london", "Civic Quarter Offices", "demand", "grid_supply", "office", 51.5074, -0.1278, 0.85),
    ("dem_office_bristol", "Harbourside Offices", "demand", "grid_supply", "office", 51.4545, -2.5879, 0.62),
    ("dem_warehouse_manchester", "Trafford Distribution", "demand", "grid_supply", "warehouse", 53.4808, -2.2426, 1.15),
    ("dem_warehouse_glasgow", "Clyde Logistics", "demand", "grid_supply", "warehouse", 55.8642, -4.2518, 0.95),
    ("dem_retail_birmingham", "Bullring Retail", "demand", "grid_supply", "retail", 52.4862, -1.8904, 0.72),
    ("dem_retail_cardiff", "Taff Retail Park", "demand", "grid_supply", "retail", 51.4816, -3.1791, 0.66),
    ("dem_hospitality_edinburgh", "Old Town Hotel", "demand", "grid_supply", "hospitality", 55.9533, -3.1883, 0.58),
    ("dem_manufacturing_sheffield", "Sheffield Works", "demand", "grid_supply", "manufacturing", 53.3811, -1.4701, 2.40),
    ("gen_solar_cambridge", "Fenland Solar", "generation", "solar", "renewable_generator", 52.2053, 0.1218, 4.20),
    ("gen_solar_cornwall", "Tamar Solar", "generation", "solar", "renewable_generator", 50.2660, -5.0527, 3.10),
    ("gen_wind_cumbria", "Solway Wind", "generation", "wind", "renewable_generator", 54.5772, -3.2340, 6.00),
    ("gen_wind_aberdeenshire", "Dee Wind", "generation", "wind", "renewable_generator", 57.1497, -2.0943, 7.50),
]

SITE_REGIONS = {
    "dem_office_london": "London",
    "dem_office_bristol": "South West England",
    "dem_warehouse_manchester": "North West England",
    "dem_warehouse_glasgow": "Scotland",
    "dem_retail_birmingham": "West Midlands",
    "dem_retail_cardiff": "Wales",
    "dem_hospitality_edinburgh": "Scotland",
    "dem_manufacturing_sheffield": "Yorkshire and the Humber",
    "gen_solar_cambridge": "East of England",
    "gen_solar_cornwall": "South West England",
    "gen_wind_cumbria": "North West England",
    "gen_wind_aberdeenshire": "Scotland",
}


def site_frame() -> pd.DataFrame:
    columns = ["site_id", "name", "site_role", "technology", "business_archetype", "latitude", "longitude", "installed_capacity_mw"]
    frame = pd.DataFrame(SITE_ROWS, columns=columns)
    frame["region"] = frame["site_id"].map(SITE_REGIONS)
    frame["data_origin"] = "simulated"
    return frame


def _weather(index: pd.DatetimeIndex, latitude: float, longitude: float, rng: np.random.Generator) -> dict[str, np.ndarray]:
    day = index.dayofyear.to_numpy()
    hour = index.hour.to_numpy() + index.minute.to_numpy() / 60
    latitude_adjustment = (52.0 - latitude) * 0.35
    temperature = 10.0 + latitude_adjustment + 7.0 * np.sin(2 * np.pi * (day - 172) / 365) + 2.2 * np.sin(2 * np.pi * (hour - 14) / 24) + rng.normal(0, 0.7, len(index))
    cloud = np.clip(58 + 25 * np.sin(2 * np.pi * day / 11 + longitude) + rng.normal(0, 12, len(index)), 3, 100)
    seasonal_daylight = 12 + 4 * np.sin(2 * np.pi * (day - 80) / 365) * np.cos(np.deg2rad(latitude - 51))
    sunrise = 12 - seasonal_daylight / 2
    sunset = 12 + seasonal_daylight / 2
    phase = np.clip((hour - sunrise) / np.maximum(seasonal_daylight, 1), 0, 1)
    daylight = (hour >= sunrise) & (hour <= sunset)
    sun_shape = np.where(daylight, np.sin(np.pi * phase), 0.0)
    clear_irradiance = 850 * sun_shape * (0.72 + 0.28 * np.sin(2 * np.pi * (day - 80) / 365))
    irradiance = np.clip(clear_irradiance * (1 - 0.0065 * cloud), 0, None)
    wind = np.clip(7.4 + 2.7 * np.sin(2 * np.pi * day / 6 + longitude) + 1.5 * np.sin(2 * np.pi * hour / 24) + rng.normal(0, 1.1, len(index)), 0, 32)
    wind_direction = np.mod(
        225
        + 38 * np.sin(2 * np.pi * day / 9 + longitude)
        + 24 * np.sin(2 * np.pi * hour / 24),
        360,
    )
    wind_gust = np.clip(
        wind + 2.4 + 0.8 * np.abs(np.sin(2 * np.pi * hour / 12)),
        wind,
        45,
    )
    surface_pressure = (
        1013
        + 11 * np.sin(2 * np.pi * day / 8 + longitude)
        + 1.8 * np.cos(2 * np.pi * hour / 24)
    )
    return {
        "temperature_c": temperature,
        "cloud_cover_pct": cloud,
        "irradiance_wm2": irradiance,
        "wind_speed_mps": wind,
        "wind_direction_deg": wind_direction,
        "wind_gust_mps": wind_gust,
        "surface_pressure_hpa": surface_pressure,
        "daylight": daylight,
    }


def _demand(archetype: str, capacity: float, index: pd.DatetimeIndex, weather: dict[str, np.ndarray], portfolio_factor: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    local = index.tz_convert("Europe/London")
    hour = local.hour.to_numpy() + local.minute.to_numpy() / 60
    weekday = local.dayofweek.to_numpy() < 5
    params = {
        "office": (0.15, 0.57, 8.0, 18.5, 0.32),
        "warehouse": (0.36, 0.43, 6.0, 22.0, 0.12),
        "retail": (0.20, 0.57, 9.0, 21.0, 0.18),
        "hospitality": (0.30, 0.45, 6.0, 23.5, 0.05),
        "manufacturing": (0.42, 0.42, 6.0, 19.0, 0.20),
    }
    base, daytime, open_hour, close_hour, weekend_drop = params[archetype]
    open_profile = ((hour >= open_hour) & (hour < close_hour)).astype(float)
    ramps = np.clip(np.minimum((hour - open_hour + 1.0), (close_hour - hour + 1.0)), 0, 1)
    calendar = daytime * open_profile * ramps * (1 - weekend_drop * (~weekday))
    if archetype == "hospitality":
        calendar += 0.16 * (np.exp(-((hour - 8) / 2.0) ** 2) + np.exp(-((hour - 19) / 2.8) ** 2))
    heat = np.clip(15 - weather["temperature_c"], 0, None) * (0.010 if archetype != "warehouse" else 0.006)
    cooling = np.clip(weather["temperature_c"] - 20, 0, None) * (0.014 if archetype in {"office", "retail", "hospitality"} else 0.006)
    target = capacity * (base + calendar + heat + cooling + portfolio_factor)
    observed = np.empty(len(index))
    observed[0] = target[0]
    for position in range(1, len(index)):
        observed[position] = 0.82 * target[position] + 0.18 * observed[position - 1] + rng.normal(0, capacity * 0.018)
    anomalies = rng.random(len(index)) < 0.0015
    observed[anomalies] *= rng.choice([0.45, 1.55], size=int(anomalies.sum()))
    return np.clip(observed, 0, capacity), anomalies


def _solar(capacity: float, index: pd.DatetimeIndex, weather: dict[str, np.ndarray], rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    temperature_adjustment = np.clip(1 - 0.004 * np.maximum(weather["temperature_c"] - 25, 0), 0.85, 1)
    power = capacity * (weather["irradiance_wm2"] / 1000) * temperature_adjustment
    power += rng.normal(0, capacity * 0.012, len(index)) * weather["daylight"]
    outages = np.zeros(len(index), dtype=bool)
    for start in rng.choice(np.arange(96, len(index) - 24), size=3, replace=False):
        outages[start : start + int(rng.integers(4, 18))] = True
    power[outages] = 0
    power[~weather["daylight"]] = 0
    return np.clip(power, 0, capacity), outages


def _wind(capacity: float, wind_speed: np.ndarray, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    cut_in, rated, cut_out = 3.0, 12.0, 25.0
    fraction = np.zeros_like(wind_speed)
    ramp = (wind_speed >= cut_in) & (wind_speed < rated)
    fraction[ramp] = ((wind_speed[ramp] - cut_in) / (rated - cut_in)) ** 3
    fraction[(wind_speed >= rated) & (wind_speed <= cut_out)] = 1.0
    power = capacity * fraction + rng.normal(0, capacity * 0.015, len(wind_speed)) * (fraction > 0)
    outages = np.zeros(len(wind_speed), dtype=bool)
    for start in rng.choice(np.arange(96, len(wind_speed) - 48), size=4, replace=False):
        outages[start : start + int(rng.integers(6, 30))] = True
    curtailment = (rng.random(len(wind_speed)) < 0.002) & (fraction > 0.7)
    power[curtailment] *= 0.45
    outages |= curtailment
    power[outages & ~curtailment] = 0
    return np.clip(power, 0, capacity), outages


def generate_portfolio(seed: int = SEED, days: int = DAYS) -> tuple[pd.DataFrame, pd.DataFrame]:
    sites = site_frame()
    periods = days * 48
    index = pd.date_range(START_UTC, periods=periods, freq="30min", tz="UTC")
    root_rng = np.random.default_rng(seed)
    portfolio_factor = np.zeros(periods)
    shocks = root_rng.normal(0, 0.009, periods)
    for position in range(1, periods):
        portfolio_factor[position] = 0.94 * portfolio_factor[position - 1] + shocks[position]
    frames: list[pd.DataFrame] = []
    for site_number, site in sites.iterrows():
        rng = np.random.default_rng(seed + site_number + 1)
        weather = _weather(index, float(site.latitude), float(site.longitude), rng)
        if site.site_role == "demand":
            power, anomaly = _demand(str(site.business_archetype), float(site.installed_capacity_mw), index, weather, portfolio_factor, rng)
            outage = np.zeros(periods, dtype=bool)
        elif site.technology == "solar":
            power, outage = _solar(float(site.installed_capacity_mw), index, weather, rng)
            anomaly = outage.copy()
        else:
            power, outage = _wind(float(site.installed_capacity_mw), weather["wind_speed_mps"], rng)
            anomaly = outage.copy()
        local = index.tz_convert("Europe/London")
        observations = pd.DataFrame({
            "timestamp_utc": index,
            "settlement_date": local.date.astype(str),
            "site_id": site.site_id,
            "site_role": site.site_role,
            "technology": site.technology,
            "observed_power_mw": np.round(power, 6),
            "energy_mwh": np.round(power * 0.5, 6),
            "temperature_c": np.round(weather["temperature_c"], 3),
            "irradiance_wm2": np.round(weather["irradiance_wm2"], 3),
            "wind_speed_mps": np.round(weather["wind_speed_mps"], 3),
            "wind_direction_deg": np.round(weather["wind_direction_deg"], 3),
            "wind_gust_mps": np.round(weather["wind_gust_mps"], 3),
            "surface_pressure_hpa": np.round(weather["surface_pressure_hpa"], 3),
            "cloud_cover_pct": np.round(weather["cloud_cover_pct"], 3),
            "is_daylight": weather["daylight"],
            "anomaly_flag": anomaly,
            "outage_or_curtailment_flag": outage,
            "data_origin": "simulated",
        })
        observations["settlement_period"] = observations.groupby("settlement_date").cumcount() + 1
        frames.append(observations)
    return sites, pd.concat(frames, ignore_index=True)


def write_demo_dataset(output_root: Path | str = "data/demo", seed: int = SEED, days: int = DAYS) -> dict[str, Path]:
    root = Path(output_root)
    root.mkdir(parents=True, exist_ok=True)
    sites, observations = generate_portfolio(seed=seed, days=days)
    sites_path = root / "sites.parquet"
    observations_path = root / "observations.parquet"
    metadata_path = root / "site_metadata.json"
    sites.to_parquet(sites_path, index=False)
    observations.to_parquet(observations_path, index=False)
    metadata = {"schema_version": "2", "seed": seed, "start_utc": START_UTC, "days": days, "site_count": len(sites), "observation_count": len(observations), "data_origin": "simulated", "units": {"observed_power_mw": "MW", "energy_mwh": "MWh", "temperature_c": "degrees Celsius", "irradiance_wm2": "W/m2", "wind_speed_mps": "m/s", "wind_direction_deg": "degrees", "wind_gust_mps": "m/s", "surface_pressure_hpa": "hPa"}, "sites": sites.to_dict(orient="records")}
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    retrieved_at = pd.Timestamp(START_UTC).isoformat()
    for dataset_name, processed_path in (("simulated_sites", sites_path), ("simulated_observations", observations_path)):
        SourceManifest(dataset_name, "generated:gridmatch.data.synthetic", retrieved_at, "", str(processed_path), "1", "simulated", "Synthetic demonstration data; no real customers", "generated").write()
    return {"sites": sites_path, "observations": observations_path, "metadata": metadata_path}
