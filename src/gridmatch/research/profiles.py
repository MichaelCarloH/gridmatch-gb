"""Site-profile and quality summaries using Phase 3/4 artifacts."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from gridmatch.research.common import FIGURE_ROOT, research_style, save_table


def profile_summaries(sites: pd.DataFrame, observations: pd.DataFrame, readiness: pd.DataFrame, annotated: pd.DataFrame) -> dict[str, pd.DataFrame]:
    data = observations.copy()
    local = pd.to_datetime(data["timestamp_utc"], utc=True).dt.tz_convert("Europe/London")
    data["day_type"] = local.dt.dayofweek.map(lambda value: "weekday" if value < 5 else "weekend")
    archetypes = sites.groupby(["site_role", "business_archetype", "technology"], dropna=False).size().rename("site_count").reset_index()
    half_hour = data.groupby(["site_id", "day_type", "settlement_period"], as_index=False)["energy_mwh"].mean().rename(columns={"energy_mwh": "mean_energy_mwh"})
    generation = data[data["site_role"] == "generation"].groupby("site_id").agg(total_generation_mwh=("energy_mwh", "sum"), observed_periods=("energy_mwh", "size")).reset_index().merge(sites[["site_id", "installed_capacity_mw"]], on="site_id")
    generation["capacity_factor"] = generation["total_generation_mwh"] / (generation["installed_capacity_mw"] * 0.5 * generation["observed_periods"])
    missing = observations.isna().mean().rename("missing_rate").reset_index().rename(columns={"index": "column"})
    flags = annotated.loc[annotated["quality_flag"] != "valid", ["quality_flag"]].assign(quality_flag=lambda frame: frame["quality_flag"].str.split("|")).explode("quality_flag").value_counts("quality_flag").rename("flagged_rows").reset_index()
    scores = readiness["quality_score"]
    score_distribution = pd.DataFrame([{
        "site_count": int(scores.count()),
        "minimum": float(scores.min()),
        "p25": float(scores.quantile(0.25)),
        "median": float(scores.median()),
        "p75": float(scores.quantile(0.75)),
        "maximum": float(scores.max()),
        "ready_sites": int(readiness["site_readiness"].eq("ready").sum()),
    }])
    return {
        "archetypes": archetypes,
        "half_hour_profiles": half_hour,
        "capacity_factors": generation,
        "missingness": missing,
        "quality_flags": flags,
        "quality_score_distribution": score_distribution,
        "readiness": readiness.copy(),
    }


def save_profile_figure(observations: pd.DataFrame, site_id: str, label: str) -> Path:
    research_style()
    site = observations[observations["site_id"] == site_id].copy()
    local = pd.to_datetime(site["timestamp_utc"], utc=True).dt.tz_convert("Europe/London")
    site["day_type"] = local.dt.dayofweek.map(lambda value: "weekday" if value < 5 else "weekend")
    profile = site.groupby(["day_type", "settlement_period"])["energy_mwh"].mean().reset_index()
    figure, axis = plt.subplots(figsize=(9, 4.8))
    for day_type, color in (("weekday", "#2f73d9"), ("weekend", "#4ca855")):
        subset = profile[profile["day_type"] == day_type]
        axis.plot(subset["settlement_period"], subset["energy_mwh"], color=color, linewidth=2, label=day_type.title())
    axis.set_xlabel("GB settlement period")
    axis.set_ylabel("Mean half-hour energy (MWh)")
    axis.set_title(f"Half-hourly profile — {label}")
    axis.legend(frameon=False)
    figure.tight_layout()
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    path = FIGURE_ROOT / f"02_profile_{site_id}.png"
    figure.savefig(path, bbox_inches="tight")
    plt.close(figure)
    return path


def save_profile_artifacts(sites: pd.DataFrame, observations: pd.DataFrame, readiness: pd.DataFrame, annotated: pd.DataFrame) -> dict[str, Path]:
    summaries = profile_summaries(sites, observations, readiness, annotated)
    paths = {f"{name}_table": save_table(frame, f"02_{name}") for name, frame in summaries.items()}
    selections = [
        ("dem_office_london", "Civic Quarter Offices"),
        ("dem_manufacturing_sheffield", "Sheffield Works"),
        ("gen_solar_cambridge", "Fenland Solar"),
        ("gen_wind_cumbria", "Solway Wind"),
    ]
    for site_id, label in selections:
        paths[f"profile_{site_id}"] = save_profile_figure(observations, site_id, label)
    return paths
