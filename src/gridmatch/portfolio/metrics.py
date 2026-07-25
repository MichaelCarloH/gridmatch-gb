"""Portfolio comparison metrics, including a transparent cost proxy."""

from __future__ import annotations

import numpy as np

from gridmatch.models.metrics import point_metrics, probabilistic_metrics

HEDGE_COST_GBP_PER_MWH = 75.0


def portfolio_metrics(
    actual: np.ndarray,
    forecast: np.ndarray,
    *,
    q10: np.ndarray | None = None,
    q50: np.ndarray | None = None,
    q90: np.ndarray | None = None,
) -> dict[str, float | None]:
    actual_values = np.asarray(actual, dtype=float)
    forecast_values = np.asarray(forecast, dtype=float)
    normalization = max(float(np.mean(np.abs(actual_values))), 1e-9)
    metrics: dict[str, float | None] = {
        **point_metrics(actual_values, forecast_values, normalization),
        "peak_error": float(
            np.mean(
                np.abs(forecast_values - actual_values)[
                    np.abs(actual_values)
                    >= np.quantile(np.abs(actual_values), 0.95)
                ]
            )
        ),
        "simulated_hedge_cost_gbp": float(
            np.sum(np.abs(forecast_values - actual_values))
            * HEDGE_COST_GBP_PER_MWH
        ),
        "pinball_loss": None,
        "interval_coverage": None,
        "interval_width": None,
    }
    if q10 is not None and q50 is not None and q90 is not None:
        metrics.update(probabilistic_metrics(actual_values, q10, q50, q90))
    return metrics
