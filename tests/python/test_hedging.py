from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from gridmatch.market.hedging import (
    evaluate_hedge_cost,
    implied_optimal_quantile,
    interpolate_forecast_quantile,
    scenario_recommendation,
)
from gridmatch.market.pipeline import POLICIES
from gridmatch.market.prices import PriceAssumptions, public_price_curve

ROOT = Path(__file__).resolve().parents[2]
FORECAST_ROOT = ROOT / "artifacts/forecasts"
METRIC_ROOT = ROOT / "artifacts/metrics"


def test_asymmetric_cost_decomposition_and_perfect_lower_bound() -> None:
    short = evaluate_hedge_cost(10, 8, 100, 150, 50)
    long = evaluate_hedge_cost(6, 8, 100, 150, 50)
    perfect = evaluate_hedge_cost(10, 10, 100, 150, 50)
    assert short.short_exposure_mwh == 2
    assert short.long_exposure_mwh == 0
    assert short.day_ahead_cost_gbp == 800
    assert short.imbalance_cost_gbp == 300
    assert short.total_cost_gbp == 1100
    assert long.short_exposure_mwh == 0
    assert long.long_exposure_mwh == 2
    assert long.total_cost_gbp == 700
    assert perfect.total_cost_gbp == 1000
    assert perfect.total_cost_gbp <= short.total_cost_gbp
    assert implied_optimal_quantile(100, 150, 50) == 0.5


def test_quantile_interpolation_is_ordered() -> None:
    values = [
        interpolate_forecast_quantile(-2, 0, 4, quantile).item()
        for quantile in np.arange(0.1, 1.0, 0.1)
    ]
    assert values == sorted(values)
    assert values[0] == -2
    assert values[4] == 0
    assert values[-1] == 4


def test_scenario_function_is_deterministic_and_risk_responsive() -> None:
    forecast = {
        "bottom_up_net_q10_mwh": -1.0,
        "bottom_up_net_q50_mwh": 1.0,
        "bottom_up_net_q90_mwh": 3.0,
    }
    base = scenario_recommendation(
        forecast,
        market_reference_price_gbp_mwh=100,
        public_system_price_gbp_mwh=120,
        risk_preference=0,
    )
    repeated = scenario_recommendation(
        forecast,
        market_reference_price_gbp_mwh=100,
        public_system_price_gbp_mwh=120,
        risk_preference=0,
    )
    cautious = scenario_recommendation(
        forecast,
        market_reference_price_gbp_mwh=100,
        public_system_price_gbp_mwh=120,
        risk_preference=1,
    )
    assert base == repeated
    assert cautious["recommended_quantile"] >= base["recommended_quantile"]
    assert cautious["recommended_mwh"] >= base["recommended_mwh"]
    assert base["expected_short_exposure_mwh"] >= 0
    assert base["expected_long_exposure_mwh"] >= 0


def test_public_price_assumptions_are_visible_and_valid() -> None:
    prices = pd.read_parquet(ROOT / "data/processed/prices.parquet")
    curve = public_price_curve(
        prices,
        pd.Series(range(1, 49)),
        assumptions=PriceAssumptions(),
    )
    assert len(curve) == 48
    assert set(curve["price_data_origin"]) == {"public"}
    assert (
        curve["short_price_gbp_mwh"]
        >= curve["market_reference_price_gbp_mwh"]
    ).all()
    assert (
        curve["long_price_gbp_mwh"]
        <= curve["market_reference_price_gbp_mwh"]
    ).all()
    assert set(curve["price_alignment_method"]) == {
        "non_contemporaneous_public_settlement_period_proxy"
    }


def test_every_period_has_a_leakage_safe_recommendation() -> None:
    portfolio = pd.read_parquet(
        FORECAST_ROOT / "portfolio_forecasts.parquet"
    )
    recommendations = pd.read_parquet(
        FORECAST_ROOT / "hedge_recommendations.parquet"
    )
    assert len(recommendations) == len(portfolio) == 626
    assert recommendations["timestamp_utc"].is_unique
    assert (
        recommendations["training_cutoff_utc"]
        <= recommendations["forecast_issue_time_utc"]
    ).all()
    assert (
        recommendations["forecast_issue_time_utc"]
        < recommendations["timestamp_utc"]
    ).all()
    evidence = recommendations[
        "selection_evidence_end_utc"
    ].notna()
    assert (
        recommendations.loc[evidence, "selection_evidence_end_utc"]
        < recommendations.loc[evidence, "forecast_issue_time_utc"]
    ).all()
    assert recommendations["recommended_quantile"].between(0.1, 0.9).all()
    assert (
        recommendations[
            [
                "expected_short_exposure_mwh",
                "expected_long_exposure_mwh",
                "short_exposure_mwh",
                "long_exposure_mwh",
            ]
        ]
        >= 0
    ).all().all()
    assert set(recommendations["price_data_origin"]) == {"public"}
    assert recommendations[
        "perfect_foresight_is_benchmark_only"
    ].all()


def test_policy_backtest_compares_required_policies_and_lower_bound() -> None:
    backtest = pd.read_parquet(
        METRIC_ROOT / "hedge_policy_backtest.parquet"
    )
    assert set(backtest["policy"]) == set(POLICIES)
    assert len(POLICIES) >= 5
    assert backtest.groupby("policy").size().eq(626).all()
    assert (
        backtest[backtest["policy"] == "no_hedge"][
            "hedged_volume_mwh"
        ]
        == 0
    ).all()
    perfect = backtest[backtest["policy"] == "perfect_foresight"]
    np.testing.assert_allclose(
        perfect["hedged_volume_mwh"],
        perfect["realised_net_demand_mwh"],
    )
    lower_bound = perfect[
        ["timestamp_utc", "total_cost_gbp"]
    ].rename(columns={"total_cost_gbp": "lower_bound_gbp"})
    compared = backtest.merge(
        lower_bound,
        on="timestamp_utc",
        validate="many_to_one",
    )
    assert (
        compared["lower_bound_gbp"]
        <= compared["total_cost_gbp"] + 1e-7
    ).all()
    assert perfect["uses_realised_information"].all()
    assert not perfect["eligible_recommendation"].any()


def test_validation_selection_and_backtest_json_are_auditable() -> None:
    text = (METRIC_ROOT / "hedge_backtest.json").read_text(
        encoding="utf-8"
    )
    assert "NaN" not in text
    summary = json.loads(text)
    assert summary["leakage_audit_passed"] is True
    assert summary["perfect_foresight_is_lower_bound_only"] is True
    assert len(summary["policies_compared"]) == 7
    assert (
        summary["cost_assumptions"]["price_alignment_method"]
        == "non_contemporaneous_public_settlement_period_proxy"
    )
    fold_two = summary["selection_history"][1]
    assert fold_two["selection_source"] == "prior_fold_realised_cost"
    assert (
        fold_two["evidence_end_utc"]
        < fold_two["current_fold_earliest_issue_time_utc"]
    )
    costs = fold_two["candidate_total_cost_gbp"]
    expected = min(costs, key=costs.get)
    assert np.isclose(
        fold_two["selected_quantile"],
        int(expected.removeprefix("q")) / 100,
    )
    sensitivity = pd.read_parquet(
        METRIC_ROOT / "hedge_sensitivity.parquet"
    )
    assert len(sensitivity) == 9
    assert sensitivity["mean_recommended_quantile"].between(0.1, 0.9).all()
