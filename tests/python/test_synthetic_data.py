from __future__ import annotations

import pandas as pd

from gridmatch.data.synthetic import generate_portfolio


def test_synthetic_generation_is_deterministic(synthetic_portfolio) -> None:
    sites_first, observations_first = synthetic_portfolio
    sites_second, observations_second = generate_portfolio()
    pd.testing.assert_frame_equal(sites_first, sites_second)
    pd.testing.assert_frame_equal(observations_first, observations_second)


def test_required_site_count_and_types(synthetic_portfolio) -> None:
    sites, _ = synthetic_portfolio
    assert len(sites) >= 12
    demand = sites[sites.site_role == "demand"].business_archetype.value_counts()
    assert demand["office"] >= 2
    assert demand["warehouse"] >= 2
    assert demand["retail"] >= 2
    assert demand["hospitality"] >= 1
    assert demand["manufacturing"] >= 1
    generation = sites[sites.site_role == "generation"].technology.value_counts()
    assert generation["solar"] >= 2
    assert generation["wind"] >= 2


def test_minimum_180_day_half_hourly_coverage(synthetic_portfolio) -> None:
    _, observations = synthetic_portfolio
    counts = observations.groupby("site_id").size()
    assert (counts >= 180 * 48).all()
    coverage = observations.groupby("site_id").timestamp_utc.agg(["min", "max"])
    assert (((coverage["max"] - coverage["min"]) + pd.Timedelta(minutes=30)) >= pd.Timedelta(days=180)).all()


def test_generation_respects_physical_limits(synthetic_portfolio) -> None:
    sites, observations = synthetic_portfolio
    generation = observations[observations.site_role == "generation"].merge(sites[["site_id", "installed_capacity_mw"]], on="site_id")
    assert (generation.observed_power_mw >= 0).all()
    assert (generation.observed_power_mw <= generation.installed_capacity_mw + 1e-9).all()
    assert (generation.energy_mwh <= generation.installed_capacity_mw * 0.5 + 1e-9).all()


def test_solar_is_zero_outside_daylight(synthetic_portfolio) -> None:
    _, observations = synthetic_portfolio
    solar_night = observations[(observations.technology == "solar") & (~observations.is_daylight)]
    assert not solar_night.empty
    assert (solar_night.observed_power_mw == 0).all()


def test_simulated_origin_is_explicit(synthetic_portfolio) -> None:
    sites, observations = synthetic_portfolio
    assert set(sites.data_origin) == {"simulated"}
    assert set(observations.data_origin) == {"simulated"}
