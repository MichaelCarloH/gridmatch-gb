"""Weather availability and leakage-methodology helpers, not model features."""

from __future__ import annotations

from math import asin, cos, radians, sin, sqrt
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from gridmatch.research.common import FIGURE_ROOT, research_style, save_table


def distance_km(latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float) -> float:
    dlat, dlon = radians(latitude_b - latitude_a), radians(longitude_b - longitude_a)
    value = sin(dlat / 2) ** 2 + cos(radians(latitude_a)) * cos(radians(latitude_b)) * sin(dlon / 2) ** 2
    return 6371.0 * 2 * asin(sqrt(value))


def weather_availability(weather: pd.DataFrame) -> pd.DataFrame:
    groups = {
        "demand": ["temperature_2m", "cloud_cover"],
        "solar": ["shortwave_radiation", "cloud_cover", "temperature_2m"],
        "wind": ["wind_speed_10m", "wind_direction_10m", "surface_pressure"],
    }
    rows = []
    for use_case, variables in groups.items():
        for variable in variables:
            rows.append({"use_case": use_case, "variable": variable, "available": variable in weather, "missing_rate": float(weather[variable].isna().mean()) if variable in weather else 1.0, "available_at_forecast_time": "only when supplied by a forecast vintage issued before valid_time"})
    return pd.DataFrame(rows)


def example_weather_tables(weather: pd.DataFrame, sites: pd.DataFrame) -> dict[str, pd.DataFrame]:
    weather_latitude = float(weather["latitude"].iloc[0])
    weather_longitude = float(weather["longitude"].iloc[0])
    selectors = {
        "demand": sites[sites["site_role"] == "demand"].iloc[0],
        "solar": sites[sites["technology"] == "solar"].iloc[0],
        "wind": sites[sites["technology"] == "wind"].iloc[0],
    }
    variables = {
        "demand": ["temperature_2m", "cloud_cover"],
        "solar": ["temperature_2m", "cloud_cover", "shortwave_radiation"],
        "wind": ["wind_speed_10m", "wind_direction_10m", "surface_pressure"],
    }
    tables = {}
    for use_case, site in selectors.items():
        columns = ["issue_time", "valid_time", *variables[use_case], "weather_model", "data_origin"]
        table = weather[columns].head(8).copy()
        table.insert(0, "site_id", site["site_id"])
        table["site_latitude"] = site["latitude"]
        table["site_longitude"] = site["longitude"]
        table["weather_grid_distance_km"] = round(distance_km(float(site["latitude"]), float(site["longitude"]), weather_latitude, weather_longitude), 2)
        tables[use_case] = table
    return tables


def save_weather_artifacts(weather: pd.DataFrame, sites: pd.DataFrame) -> dict[str, Path]:
    research_style()
    availability = weather_availability(weather)
    tables = example_weather_tables(weather, sites)
    paths = {"availability_table": save_table(availability, "03_weather_availability")}
    for name, table in tables.items():
        paths[f"{name}_table"] = save_table(table, f"03_{name}_weather_example")
    missing = weather.isna().mean().rename("missing_rate").reset_index().rename(columns={"index": "column"})
    paths["missingness_table"] = save_table(missing, "03_weather_missingness")
    figure, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)
    valid_time = pd.to_datetime(weather["valid_time"], utc=True)
    axes[0].plot(valid_time, weather["temperature_2m"], color="#2f73d9")
    axes[0].set_ylabel("Temperature °C")
    axes[1].plot(valid_time, weather["shortwave_radiation"], color="#d99a2b")
    axes[1].set_ylabel("Radiation W/m²")
    axes[2].plot(valid_time, weather["wind_speed_10m"], color="#4ca855")
    axes[2].set_ylabel("Wind km/h")
    axes[2].set_xlabel("Valid time (UTC)")
    figure.suptitle("Compact Open-Meteo historical weather artifact")
    figure.tight_layout()
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    paths["weather_figure"] = FIGURE_ROOT / "03_weather_driver_overview.png"
    figure.savefig(paths["weather_figure"], bbox_inches="tight")
    plt.close(figure)
    return paths
