"""Training primitives and physical post-processing for site forecasts."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from gridmatch.features.site import FEATURE_COLUMNS, FEATURE_VERSION

MODEL_VERSION = "site-forecast-v1"


@dataclass
class ModelStack:
    statistical: Pipeline
    point: HistGradientBoostingRegressor
    q10: HistGradientBoostingRegressor
    q50: HistGradientBoostingRegressor
    q90: HistGradientBoostingRegressor


def _histogram_model(
    *,
    loss: str = "squared_error",
    quantile: float | None = None,
) -> HistGradientBoostingRegressor:
    return HistGradientBoostingRegressor(
        loss=loss,
        quantile=quantile,
        learning_rate=0.07,
        max_iter=70,
        max_leaf_nodes=23,
        min_samples_leaf=30,
        l2_regularization=0.2,
        random_state=20260725,
    )


def train_model_stack(
    train_frame: pd.DataFrame,
    feature_columns: list[str] | None = None,
) -> ModelStack:
    columns = feature_columns or FEATURE_COLUMNS
    features = train_frame[columns]
    target = train_frame["actual_mwh"].to_numpy(dtype=float)
    statistical = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
            ("ridge", Ridge(alpha=2.0)),
        ]
    ).fit(features, target)
    point = _histogram_model().fit(features, target)
    q10 = _histogram_model(loss="quantile", quantile=0.1).fit(features, target)
    q50 = _histogram_model(loss="quantile", quantile=0.5).fit(features, target)
    q90 = _histogram_model(loss="quantile", quantile=0.9).fit(features, target)
    return ModelStack(statistical, point, q10, q50, q90)


def repair_quantiles(
    q10: np.ndarray,
    q50: np.ndarray,
    q90: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ordered = np.sort(np.column_stack([q10, q50, q90]), axis=1)
    return ordered[:, 0], ordered[:, 1], ordered[:, 2]


def apply_physical_constraints(
    values: np.ndarray,
    frame: pd.DataFrame,
    site: pd.Series | dict,
) -> np.ndarray:
    metadata = dict(site)
    constrained = np.maximum(np.asarray(values, dtype=float), 0)
    if str(metadata["site_role"]) == "generation":
        maximum_energy = float(metadata["installed_capacity_mw"]) * 0.5
        constrained = np.minimum(constrained, maximum_energy)
    if str(metadata["technology"]) == "solar":
        constrained = np.where(
            frame["is_daylight"].to_numpy(dtype=bool),
            constrained,
            0.0,
        )
    return constrained


def predict_model_stack(
    stack: ModelStack,
    frame: pd.DataFrame,
    site: pd.Series | dict,
    feature_columns: list[str] | None = None,
) -> dict[str, np.ndarray]:
    columns = feature_columns or FEATURE_COLUMNS
    features = frame[columns]
    predictions = {
        "statistical_mwh": apply_physical_constraints(
            stack.statistical.predict(features),
            frame,
            site,
        ),
        "point_mwh": apply_physical_constraints(
            stack.point.predict(features),
            frame,
            site,
        ),
        "q10_mwh": apply_physical_constraints(
            stack.q10.predict(features),
            frame,
            site,
        ),
        "q50_mwh": apply_physical_constraints(
            stack.q50.predict(features),
            frame,
            site,
        ),
        "q90_mwh": apply_physical_constraints(
            stack.q90.predict(features),
            frame,
            site,
        ),
    }
    predictions["q10_mwh"], predictions["q50_mwh"], predictions["q90_mwh"] = (
        repair_quantiles(
            predictions["q10_mwh"],
            predictions["q50_mwh"],
            predictions["q90_mwh"],
        )
    )
    return predictions


__all__ = [
    "FEATURE_VERSION",
    "MODEL_VERSION",
    "ModelStack",
    "apply_physical_constraints",
    "predict_model_stack",
    "repair_quantiles",
    "train_model_stack",
]
