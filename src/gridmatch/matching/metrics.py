"""Conservation-safe renewable-matching metric helpers."""

from __future__ import annotations

import numpy as np


def safe_ratio(numerator: float, denominator: float) -> float:
    """Return a bounded ratio, using zero for a zero denominator."""
    if denominator <= 0:
        return 0.0
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def weighted_average(
    values: np.ndarray,
    weights: np.ndarray,
) -> float:
    """Return a matched-MWh weighted mean, or zero with no weight."""
    total_weight = float(np.sum(weights))
    if total_weight <= 0:
        return 0.0
    return float(np.average(values, weights=weights))
