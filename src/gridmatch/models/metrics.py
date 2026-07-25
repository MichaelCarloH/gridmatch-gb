"""Forecast metrics used by Phase 6 rolling-origin validation."""

from __future__ import annotations

import numpy as np


def pinball_loss(actual: np.ndarray, forecast: np.ndarray, quantile: float) -> float:
    error = np.asarray(actual) - np.asarray(forecast)
    return float(np.mean(np.maximum(quantile * error, (quantile - 1) * error)))


def point_metrics(
    actual: np.ndarray,
    forecast: np.ndarray,
    normalization: float,
) -> dict[str, float]:
    actual_values = np.asarray(actual, dtype=float)
    forecast_values = np.asarray(forecast, dtype=float)
    error = forecast_values - actual_values
    return {
        "mae": float(np.mean(np.abs(error))),
        "rmse": float(np.sqrt(np.mean(error**2))),
        "nmae": float(np.mean(np.abs(error)) / max(normalization, 1e-9)),
        "bias": float(np.mean(error)),
    }


def probabilistic_metrics(
    actual: np.ndarray,
    q10: np.ndarray,
    q50: np.ndarray,
    q90: np.ndarray,
) -> dict[str, float]:
    actual_values = np.asarray(actual, dtype=float)
    lower = np.asarray(q10, dtype=float)
    median = np.asarray(q50, dtype=float)
    upper = np.asarray(q90, dtype=float)
    return {
        "pinball_loss": float(
            np.mean(
                [
                    pinball_loss(actual_values, lower, 0.1),
                    pinball_loss(actual_values, median, 0.5),
                    pinball_loss(actual_values, upper, 0.9),
                ]
            )
        ),
        "interval_coverage": float(
            np.mean((actual_values >= lower) & (actual_values <= upper))
        ),
        "interval_width": float(np.mean(upper - lower)),
    }
