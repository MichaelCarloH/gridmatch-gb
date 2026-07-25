"""Shared deterministic artifact helpers for research notebooks."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FIGURE_ROOT = PROJECT_ROOT / "artifacts" / "figures"
TABLE_ROOT = PROJECT_ROOT / "artifacts" / "tables"


def project_path(*parts: str) -> Path:
    """Return an absolute path beneath the repository root."""
    return PROJECT_ROOT.joinpath(*parts)


def research_style() -> None:
    plt.rcParams.update({
        "figure.figsize": (10, 5.5),
        "figure.dpi": 120,
        "axes.facecolor": "#f7f8f5",
        "figure.facecolor": "white",
        "axes.edgecolor": "#d6dad5",
        "axes.grid": True,
        "grid.color": "#e2e5e1",
        "grid.linewidth": 0.7,
        "font.size": 10,
        "axes.titleweight": "bold",
    })


def save_table(frame: pd.DataFrame, name: str) -> Path:
    TABLE_ROOT.mkdir(parents=True, exist_ok=True)
    destination = TABLE_ROOT / f"{name}.csv"
    frame.to_csv(destination, index=False)
    return destination
