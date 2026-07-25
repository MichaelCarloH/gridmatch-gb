"""REPD public-asset summaries and figures."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from gridmatch.research.common import FIGURE_ROOT, research_style, save_table


def asset_summaries(repd: pd.DataFrame) -> dict[str, pd.DataFrame]:
    technology = repd.groupby("technology", dropna=False).agg(project_count=("project_name", "count"), installed_capacity_mw=("installed_capacity_mw", "sum"), median_project_mw=("installed_capacity_mw", "median")).reset_index().sort_values("installed_capacity_mw", ascending=False)
    capacity = repd.groupby("technology", dropna=False)["installed_capacity_mw"].quantile([0.25, 0.5, 0.75, 0.9]).unstack().reset_index().rename(columns={0.25: "p25_mw", 0.5: "p50_mw", 0.75: "p75_mw", 0.9: "p90_mw"})
    region = repd.groupby("region", dropna=False).agg(project_count=("project_name", "count"), installed_capacity_mw=("installed_capacity_mw", "sum")).reset_index().sort_values("installed_capacity_mw", ascending=False)
    map_ready = pd.DataFrame([{"total_operational_projects": len(repd), "valid_coordinates": int(repd["coordinate_valid"].sum()), "invalid_coordinates": int((~repd["coordinate_valid"]).sum()), "valid_coordinate_rate": float(repd["coordinate_valid"].mean())}])
    return {"technology": technology, "capacity": capacity, "region": region, "map_ready": map_ready}


def save_asset_artifacts(repd: pd.DataFrame) -> dict[str, Path]:
    research_style()
    summaries = asset_summaries(repd)
    paths = {f"{name}_table": save_table(frame, f"01_repd_{name}_summary") for name, frame in summaries.items()}
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    top = summaries["technology"].head(12).sort_values("installed_capacity_mw")
    figure, axis = plt.subplots(figsize=(10, 6))
    axis.barh(top["technology"], top["installed_capacity_mw"], color="#4ca855")
    axis.set_xlabel("Operational installed capacity (MW)")
    axis.set_title("REPD operational capacity by technology — top 12")
    figure.tight_layout()
    paths["technology_figure"] = FIGURE_ROOT / "01_repd_capacity_by_technology.png"
    figure.savefig(paths["technology_figure"], bbox_inches="tight")
    plt.close(figure)

    valid = repd[repd["coordinate_valid"]].copy()
    focus = valid[valid["technology"].astype(str).str.contains("solar|wind", case=False, regex=True)]
    figure, axis = plt.subplots(figsize=(7.2, 8))
    axis.scatter(valid["longitude"], valid["latitude"], s=5, alpha=0.18, color="#737b83", label="Other operational")
    for technology, color in (("Solar", "#d99a2b"), ("Wind", "#4ca855")):
        subset = focus[focus["technology"].astype(str).str.contains(technology, case=False)]
        axis.scatter(subset["longitude"], subset["latitude"], s=10, alpha=0.55, color=color, label=technology)
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.set_title("Map-ready operational REPD sites")
    axis.legend(frameon=False)
    figure.tight_layout()
    paths["geography_figure"] = FIGURE_ROOT / "01_repd_operational_geography.png"
    figure.savefig(paths["geography_figure"], bbox_inches="tight")
    plt.close(figure)
    return paths
