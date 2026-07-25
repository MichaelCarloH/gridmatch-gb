"""Correlated simulation for bottom-up portfolio predictive intervals."""

from __future__ import annotations

import numpy as np
import pandas as pd

PORTFOLIO_SIMULATIONS = 600
PORTFOLIO_CORRELATION = 0.35
NORMAL_Q10 = 1.2815515655446004


def simulate_portfolio_quantiles(
    site_rows: pd.DataFrame,
    *,
    rng: np.random.Generator,
    simulations: int = PORTFOLIO_SIMULATIONS,
    correlation: float = PORTFOLIO_CORRELATION,
) -> dict[str, float]:
    """Aggregate site intervals through a one-factor Gaussian approximation.

    Each site uses a split-normal approximation anchored at q10/q50/q90.
    A shared Gaussian factor preserves the documented common correlation while
    an idiosyncratic factor retains diversification. Site samples are physically
    clipped before demand, generation and net-position aggregation.
    """
    if not 0 <= correlation < 1:
        raise ValueError("correlation must satisfy 0 <= correlation < 1")
    rows = site_rows.sort_values("site_id").reset_index(drop=True)
    site_count = len(rows)
    common = rng.standard_normal((simulations, 1))
    independent = rng.standard_normal((simulations, site_count))
    scores = (
        np.sqrt(correlation) * common
        + np.sqrt(1 - correlation) * independent
    )

    q10 = rows["q10_mwh"].to_numpy(dtype=float)
    q50 = rows["q50_mwh"].to_numpy(dtype=float)
    q90 = rows["q90_mwh"].to_numpy(dtype=float)
    lower_scale = np.maximum((q50 - q10) / NORMAL_Q10, 0)
    upper_scale = np.maximum((q90 - q50) / NORMAL_Q10, 0)
    samples = q50 + np.where(
        scores < 0,
        scores * lower_scale,
        scores * upper_scale,
    )
    samples = np.maximum(samples, 0)

    generation = rows["site_role"].eq("generation").to_numpy()
    solar = rows["technology"].eq("solar").to_numpy()
    capacity = rows["installed_capacity_mw"].to_numpy(dtype=float) * 0.5
    samples[:, generation] = np.minimum(
        samples[:, generation],
        capacity[generation],
    )
    if "is_daylight" in rows:
        solar_night = solar & ~rows["is_daylight"].to_numpy(dtype=bool)
        samples[:, solar_night] = 0

    demand_samples = samples[:, ~generation].sum(axis=1)
    generation_samples = samples[:, generation].sum(axis=1)
    net_samples = demand_samples - generation_samples
    output: dict[str, float] = {}
    for target, values in (
        ("demand", demand_samples),
        ("generation", generation_samples),
        ("net", net_samples),
    ):
        quantiles = np.quantile(values, [0.1, 0.5, 0.9])
        output.update(
            {
                f"bottom_up_{target}_q10_mwh": float(quantiles[0]),
                f"bottom_up_{target}_q50_mwh": float(quantiles[1]),
                f"bottom_up_{target}_q90_mwh": float(quantiles[2]),
            }
        )
    return output
