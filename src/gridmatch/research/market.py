"""Worked GB settlement and imbalance examples for the market primer."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from gridmatch.data.settlements import expected_period_count, settlement_period_to_timestamp, to_london
from gridmatch.research.common import FIGURE_ROOT, research_style, save_table


def settlement_day_examples() -> pd.DataFrame:
    examples = [
        (date(2025, 1, 15), "normal"),
        (date(2025, 3, 30), "spring clock change"),
        (date(2025, 10, 26), "autumn clock change"),
    ]
    rows = []
    for day, label in examples:
        count = expected_period_count(day)
        first = settlement_period_to_timestamp(day, 1)
        last = settlement_period_to_timestamp(day, count)
        rows.append({"settlement_date": day.isoformat(), "day_type": label, "period_count": count, "first_period_utc": first.isoformat(), "first_period_london": to_london(first).isoformat(), "last_period_utc": last.isoformat(), "last_period_london": to_london(last).isoformat()})
    return pd.DataFrame(rows)


def imbalance_worked_example() -> pd.DataFrame:
    frame = pd.DataFrame({
        "settlement_period": [17, 18, 19, 20],
        "contracted_mwh": [0.80, 0.82, 0.85, 0.86],
        "metered_mwh": [0.77, 0.88, 0.91, 0.83],
    })
    frame["imbalance_mwh"] = frame["metered_mwh"] - frame["contracted_mwh"]
    frame["position"] = frame["imbalance_mwh"].map(
        lambda value: "long" if value > 0 else ("short" if value < 0 else "balanced")
    )
    return frame


def forecast_information_example() -> pd.DataFrame:
    return pd.DataFrame([
        {"forecast_type": "point", "published_values": "single expected MWh", "operator_use": "planning central volume", "limitation": "does not express tail exposure"},
        {"forecast_type": "probabilistic", "published_values": "q10, q50, q90 MWh", "operator_use": "size risk buffers and compare asymmetric costs", "limitation": "requires calibration and explicit issue time"},
    ])


def save_market_artifacts() -> dict[str, Path]:
    research_style()
    settlement = settlement_day_examples()
    imbalance = imbalance_worked_example()
    forecast = forecast_information_example()
    paths = {
        "settlement_table": save_table(settlement, "00_settlement_day_examples"),
        "imbalance_table": save_table(imbalance, "00_imbalance_worked_example"),
        "forecast_table": save_table(forecast, "00_point_vs_probabilistic"),
    }
    FIGURE_ROOT.mkdir(parents=True, exist_ok=True)
    figure, axis = plt.subplots(figsize=(8, 4.5))
    colors = ["#2f73d9", "#4ca855", "#d99a2b"]
    axis.bar(settlement["day_type"], settlement["period_count"], color=colors)
    axis.set_ylim(44, 52)
    axis.set_ylabel("Half-hourly settlement periods")
    axis.set_title("GB settlement-day length changes with daylight saving")
    for index, value in enumerate(settlement["period_count"]):
        axis.text(index, value + 0.25, str(value), ha="center", fontweight="bold")
    figure.tight_layout()
    paths["settlement_figure"] = FIGURE_ROOT / "00_gb_settlement_period_counts.png"
    figure.savefig(paths["settlement_figure"], bbox_inches="tight")
    plt.close(figure)
    return paths
