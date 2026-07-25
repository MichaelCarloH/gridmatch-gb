from __future__ import annotations

from datetime import date, datetime, timezone

from gridmatch.data.models import ForecastSchema, ObservationSchema, PriceSchema, SiteSchema, WeatherSchema


def test_all_core_schemas_validate() -> None:
    site = SiteSchema(site_id="site-1", name="Site One", site_role="demand", technology="grid_supply", business_archetype="office", latitude=51.5, longitude=-0.1, installed_capacity_mw=1.0, data_origin="simulated")
    observation = ObservationSchema(site_id=site.site_id, timestamp_utc="2025-01-01T00:00:00+00:00", settlement_date=date(2025, 1, 1), settlement_period=1, consumption_mwh=0.2, actual_mwh=0.2, source="demo", retrieved_at=datetime.now(timezone.utc))
    forecast = ForecastSchema(site_id=site.site_id, issue_time_utc="2024-12-31T12:00:00Z", valid_time_utc="2025-01-01T00:00:00Z", settlement_date="2025-01-01", settlement_period=1, horizon_periods=24, model_id="placeholder", model_version="0", q10_mwh=0.1, q50_mwh=0.2, q90_mwh=0.3, point_mwh=0.2)
    weather = WeatherSchema(site_id=site.site_id, issue_time_utc="2024-12-31T12:00:00Z", valid_time_utc="2025-01-01T00:00:00Z", temperature_2m=8, cloud_cover=70, shortwave_radiation=0, wind_speed_10m=5, wind_speed_100m=8, wind_direction_100m=270, pressure=1012, weather_model="fixture")
    price = PriceSchema(timestamp_utc="2025-01-01T00:00:00Z", settlement_date="2025-01-01", settlement_period=1, market_index_price_gbp_mwh=75, system_price_gbp_mwh=80, source="fixture")
    assert observation.timestamp_utc.tzinfo == timezone.utc
    assert forecast.q10_mwh <= forecast.q50_mwh <= forecast.q90_mwh
    assert weather.valid_time_utc.tzinfo == timezone.utc
    assert price.timestamp_utc.tzinfo == timezone.utc
