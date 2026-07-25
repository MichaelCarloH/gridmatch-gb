from __future__ import annotations

import json
from pathlib import Path
import warnings

import joblib
import numpy as np
import pandas as pd

from gridmatch.features.portfolio import (
    PORTFOLIO_FEATURE_COLUMNS,
    build_portfolio_features,
)
from gridmatch.portfolio.simulation import simulate_portfolio_quantiles

ROOT = Path(__file__).resolve().parents[2]
TARGETS = ("demand", "generation", "net")
PROBABILISTIC_METHODS = ("bottom_up", "direct", "reconciled")


def test_portfolio_features_are_aggregate_and_issue_safe() -> None:
    sites = pd.read_parquet(ROOT / "data/demo/sites.parquet")
    observations = pd.read_parquet(ROOT / "data/demo/observations.parquet")
    features = build_portfolio_features(observations, sites)

    assert set(PORTFOLIO_FEATURE_COLUMNS).issubset(features.columns)
    assert len(features) == observations["timestamp_utc"].nunique()
    assert (features["valid_time_utc"] - features["issue_time_utc"]).eq(
        pd.Timedelta(hours=24)
    ).all()
    assert features["horizon_periods"].eq(48).all()
    np.testing.assert_allclose(
        features["actual_net_mwh"],
        features["actual_demand_mwh"] - features["actual_generation_mwh"],
    )


def test_correlated_simulation_is_deterministic_and_not_quantile_summing() -> None:
    rows = pd.DataFrame(
        {
            "site_id": ["a", "b"],
            "site_role": ["demand", "demand"],
            "technology": ["grid_supply", "grid_supply"],
            "installed_capacity_mw": [2.0, 2.0],
            "is_daylight": [True, True],
            "q10_mwh": [0.2, 0.3],
            "q50_mwh": [0.5, 0.6],
            "q90_mwh": [0.9, 1.0],
        }
    )
    first = simulate_portfolio_quantiles(
        rows,
        rng=np.random.default_rng(42),
        simulations=10_000,
        correlation=0.35,
    )
    second = simulate_portfolio_quantiles(
        rows,
        rng=np.random.default_rng(42),
        simulations=10_000,
        correlation=0.35,
    )
    assert first == second
    assert (
        first["bottom_up_demand_q10_mwh"]
        < first["bottom_up_demand_q50_mwh"]
        < first["bottom_up_demand_q90_mwh"]
    )
    assert not np.isclose(
        first["bottom_up_demand_q10_mwh"],
        rows["q10_mwh"].sum(),
    )


def test_portfolio_forecast_schema_timing_and_intervals() -> None:
    forecasts = pd.read_parquet(
        ROOT / "artifacts/forecasts/portfolio_forecasts.parquet"
    )
    assert len(forecasts) == 626
    assert set(forecasts["validation_fold"]) == {1, 2}
    assert set(forecasts["data_origin"]) == {"simulated"}
    assert (
        forecasts["training_cutoff_utc"] <= forecasts["issue_time_utc"]
    ).all()
    assert (forecasts["issue_time_utc"] < forecasts["valid_time_utc"]).all()
    np.testing.assert_allclose(
        forecasts["actual_net_mwh"],
        forecasts["actual_demand_mwh"]
        - forecasts["actual_generation_mwh"],
    )
    for method in PROBABILISTIC_METHODS:
        for target in TARGETS:
            q10 = forecasts[f"{method}_{target}_q10_mwh"]
            q50 = forecasts[f"{method}_{target}_q50_mwh"]
            q90 = forecasts[f"{method}_{target}_q90_mwh"]
            assert (q10 <= q50).all()
            assert (q50 <= q90).all()
    for target in TARGETS:
        weights = forecasts[f"reconciliation_weight_{target}"]
        assert weights.between(0, 1).all()


def test_bottom_up_totals_equal_site_aggregation() -> None:
    site = pd.read_parquet(
        ROOT / "artifacts/forecasts/site_forecasts.parquet"
    )
    portfolio = pd.read_parquet(
        ROOT / "artifacts/forecasts/portfolio_forecasts.parquet"
    )
    keys = ["validation_fold", "valid_time_utc"]
    demand = (
        site[site["site_role"] == "demand"]
        .groupby(keys)
        .agg(
            expected_actual_demand=("actual_mwh", "sum"),
            expected_bottom_up_demand=("point_mwh", "sum"),
        )
    )
    generation = (
        site[site["site_role"] == "generation"]
        .groupby(keys)
        .agg(
            expected_actual_generation=("actual_mwh", "sum"),
            expected_bottom_up_generation=("point_mwh", "sum"),
        )
    )
    expected = demand.join(generation).reset_index()
    merged = portfolio.merge(expected, on=keys, validate="one_to_one")
    np.testing.assert_allclose(
        merged["actual_demand_mwh"],
        merged["expected_actual_demand"],
    )
    np.testing.assert_allclose(
        merged["actual_generation_mwh"],
        merged["expected_actual_generation"],
    )
    np.testing.assert_allclose(
        merged["bottom_up_demand_point_mwh"],
        merged["expected_bottom_up_demand"],
    )
    np.testing.assert_allclose(
        merged["bottom_up_generation_point_mwh"],
        merged["expected_bottom_up_generation"],
    )


def test_direct_portfolio_models_are_loadable() -> None:
    root = ROOT / "artifacts/models/portfolio"
    for target in TARGETS:
        destination = root / target
        for name in (
            "statistical.joblib",
            "point.joblib",
            "q10.joblib",
            "q50.joblib",
            "q90.joblib",
            "metadata.json",
        ):
            assert (destination / name).is_file()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert hasattr(joblib.load(destination / "point.joblib"), "predict")
    card = (root / "model_card.md").read_text(encoding="utf-8")
    assert "Gaussian" in card
    assert "simulated" in card.lower()
    assert "not a Phase 9 hedge strategy" in card


def test_portfolio_metrics_and_attribution_artifacts() -> None:
    metrics_json = (
        ROOT / "artifacts/metrics/portfolio_metrics.json"
    ).read_text(encoding="utf-8")
    assert "NaN" not in metrics_json
    payload = json.loads(metrics_json)
    metrics = pd.read_parquet(
        ROOT / "artifacts/metrics/portfolio_metrics.parquet"
    )

    assert payload["forecast_rows"] == 626
    assert payload["bottom_up_totals_equal_site_aggregation"]
    assert payload["all_intervals_ordered"]
    assert set(payload["best_method_by_target_mae"]) == set(TARGETS)
    assert set(metrics["target"]) == set(TARGETS)
    assert set(metrics["method"]) == {
        "baseline",
        "bottom_up",
        "direct",
        "reconciled",
    }
    assert {
        "mae",
        "rmse",
        "bias",
        "peak_error",
        "pinball_loss",
        "interval_coverage",
        "simulated_hedge_cost_gbp",
    }.issubset(metrics.columns)

    for name in (
        "site_error_contributions.parquet",
        "technology_error_contributions.parquet",
        "region_error_contributions.parquet",
        "site_error_correlation.parquet",
    ):
        assert (ROOT / "artifacts/metrics" / name).is_file()
    site_contributions = pd.read_parquet(
        ROOT / "artifacts/metrics/site_error_contributions.parquet"
    )
    assert site_contributions["site_id"].nunique() == 12
    assert np.isclose(site_contributions["absolute_error_share"].sum(), 1)
    correlation = pd.read_parquet(
        ROOT / "artifacts/metrics/site_error_correlation.parquet"
    )
    assert correlation.shape == (12, 12)

    for name in (
        "portfolio_comparison.png",
        "portfolio_error_correlation_heatmap.png",
    ):
        path = ROOT / "artifacts/figures" / name
        assert path.is_file()
        assert path.stat().st_size > 0
