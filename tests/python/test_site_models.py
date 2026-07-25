from __future__ import annotations

import json
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from gridmatch.features.site import (
    FEATURE_COLUMNS,
    build_site_features,
    rolling_origin_splits,
)
from gridmatch.models.baselines import baseline_predictions
from gridmatch.models.site_forecasting import (
    apply_physical_constraints,
    repair_quantiles,
)

ROOT = Path(__file__).resolve().parents[2]
REQUIRED_MODEL_FILES = [
    "baseline.json",
    "statistical.joblib",
    "point.joblib",
    "q10.joblib",
    "q50.joblib",
    "q90.joblib",
    "metadata.json",
    "model_card.md",
]


def _demo_data() -> tuple[pd.DataFrame, pd.DataFrame]:
    return (
        pd.read_parquet(ROOT / "data/demo/sites.parquet"),
        pd.read_parquet(ROOT / "data/demo/observations.parquet"),
    )


def test_site_features_are_day_ahead_and_issue_time_safe() -> None:
    sites, observations = _demo_data()
    site = sites.iloc[0]
    site_observations = observations[observations["site_id"] == site.site_id]
    features = build_site_features(site_observations, site)

    assert set(FEATURE_COLUMNS).issubset(features.columns)
    assert (features["valid_time_utc"] - features["issue_time_utc"]).eq(
        pd.Timedelta(hours=24)
    ).all()
    assert features["horizon_periods"].eq(48).all()

    known = features.dropna(subset=["lag_1"])
    actual_by_time = features.set_index("valid_time_utc")["actual_mwh"]
    expected = actual_by_time.reindex(
        pd.DatetimeIndex(known["issue_time_utc"])
    ).to_numpy()
    np.testing.assert_allclose(known["lag_1"], expected)


def test_rolling_origin_splits_expand_without_time_overlap() -> None:
    sites, observations = _demo_data()
    site = sites.iloc[0]
    features = build_site_features(
        observations[observations["site_id"] == site.site_id],
        site,
    )
    splits = rolling_origin_splits(features, folds=2, test_days=7)

    assert len(splits) == 2
    assert splits[0].training_cutoff < splits[0].test_start.tz_localize("UTC")
    assert splits[1].training_cutoff < splits[1].test_start.tz_localize("UTC")
    assert splits[0].train_mask.sum() < splits[1].train_mask.sum()
    assert not (splits[0].train_mask & splits[0].test_mask).any()
    for split in splits:
        earliest_issue = features.loc[split.test_mask, "issue_time_utc"].min()
        assert split.training_cutoff <= earliest_issue


def test_required_baselines_exist_by_site_type() -> None:
    sites, observations = _demo_data()
    for technology, required in (
        ("grid_supply", {"previous_day", "previous_week", "rolling_same_period"}),
        (
            "solar",
            {
                "previous_day",
                "previous_week",
                "rolling_same_period",
                "persistence",
                "physical_solar",
            },
        ),
        (
            "wind",
            {
                "previous_day",
                "previous_week",
                "rolling_same_period",
                "persistence",
                "physical_wind",
            },
        ),
    ):
        site = sites[sites["technology"] == technology].iloc[0]
        features = build_site_features(
            observations[observations["site_id"] == site.site_id],
            site,
        ).tail(48)
        predictions = baseline_predictions(features, site)
        assert set(predictions) == required
        assert all(len(values) == 48 for values in predictions.values())


def test_quantile_repair_and_physical_constraints() -> None:
    q10, q50, q90 = repair_quantiles(
        np.array([3.0, 1.0]),
        np.array([2.0, 4.0]),
        np.array([1.0, 2.0]),
    )
    assert np.all(q10 <= q50)
    assert np.all(q50 <= q90)

    solar = {
        "site_role": "generation",
        "technology": "solar",
        "installed_capacity_mw": 2.0,
    }
    frame = pd.DataFrame({"is_daylight": [False, True, True]})
    constrained = apply_physical_constraints(
        np.array([0.4, -1.0, 4.0]),
        frame,
        solar,
    )
    np.testing.assert_allclose(constrained, [0.0, 0.0, 1.0])


def test_every_site_has_loadable_model_artifacts() -> None:
    sites, _ = _demo_data()
    for site_id in sites["site_id"]:
        directory = ROOT / "artifacts/models" / site_id
        for name in REQUIRED_MODEL_FILES:
            path = directory / name
            assert path.is_file(), path
            assert path.stat().st_size > 0, path
        for name in (
            "statistical.joblib",
            "point.joblib",
            "q10.joblib",
            "q50.joblib",
            "q90.joblib",
        ):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", DeprecationWarning)
                assert hasattr(joblib.load(directory / name), "predict")

    for fallback in ("global_demand", "global_solar", "global_wind"):
        directory = ROOT / "artifacts/models" / fallback
        assert (directory / "metadata.json").is_file()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert hasattr(joblib.load(directory / "point.joblib"), "predict")


def test_forecast_artifact_schema_ordering_and_physical_constraints() -> None:
    sites, _ = _demo_data()
    forecasts = pd.read_parquet(
        ROOT / "artifacts/forecasts/site_forecasts.parquet"
    )
    required = {
        "site_id",
        "issue_time_utc",
        "valid_time_utc",
        "horizon_periods",
        "training_cutoff_utc",
        "model_version",
        "feature_version",
        "baseline_mwh",
        "point_mwh",
        "q10_mwh",
        "q50_mwh",
        "q90_mwh",
        "actual_mwh",
    }
    assert required.issubset(forecasts.columns)
    assert set(forecasts["site_id"]) == set(sites["site_id"])
    assert set(forecasts["data_origin"]) == {"simulated"}
    assert (forecasts["issue_time_utc"] < forecasts["valid_time_utc"]).all()
    assert (
        forecasts["training_cutoff_utc"] <= forecasts["issue_time_utc"]
    ).all()
    assert forecasts["horizon_periods"].eq(48).all()
    assert (forecasts["q10_mwh"] <= forecasts["q50_mwh"]).all()
    assert (forecasts["q50_mwh"] <= forecasts["q90_mwh"]).all()
    assert (forecasts[["point_mwh", "q10_mwh", "q50_mwh", "q90_mwh"]] >= 0).all().all()

    generation = forecasts[forecasts["site_role"] == "generation"].merge(
        sites[["site_id", "installed_capacity_mw"]],
        on="site_id",
    )
    maximum = generation["installed_capacity_mw"] * 0.5
    assert generation[["point_mwh", "q10_mwh", "q50_mwh", "q90_mwh"]].le(
        maximum,
        axis=0,
    ).all().all()
    solar_night = forecasts[
        (forecasts["technology"] == "solar") & ~forecasts["is_daylight"]
    ]
    assert solar_night[["point_mwh", "q10_mwh", "q50_mwh", "q90_mwh"]].eq(
        0
    ).all().all()


def test_metrics_include_all_sites_baselines_and_improvement() -> None:
    sites, _ = _demo_data()
    metrics_json = (
        ROOT / "artifacts/metrics/site_metrics.json"
    ).read_text(encoding="utf-8")
    assert "NaN" not in metrics_json
    payload = json.loads(metrics_json)
    metrics = pd.read_parquet(ROOT / "artifacts/metrics/site_metrics.parquet")

    assert payload["site_count"] == len(sites)
    assert payload["rolling_origin_folds"] == 2
    assert payload["all_quantiles_ordered"]
    assert payload["models_improving_canonical_baseline"] >= 1
    assert set(payload["global_fallbacks"]) == {
        "global_demand",
        "global_solar",
        "global_wind",
    }
    assert set(metrics["site_id"]) == set(sites["site_id"])
    for site_id in sites["site_id"]:
        site_metrics = metrics[metrics["site_id"] == site_id]
        assert {"baseline", "statistical", "ml_probabilistic"}.issubset(
            set(site_metrics["model_type"])
        )
    assert {
        "mae",
        "rmse",
        "nmae",
        "bias",
        "pinball_loss",
        "interval_coverage",
        "interval_width",
    }.issubset(metrics.columns)
