"""Auditable site-level data-quality validation and readiness reporting."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import timedelta
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from gridmatch.data.settlements import expected_period_count, validate_settlement_day


@dataclass(frozen=True)
class SiteQualityReport:
    site_id: str
    row_count: int
    expected_rows: int
    valid_timestamp_rows: int
    completeness: float
    missing_periods: int
    duplicate_observations: int
    wrong_interval_count: int
    dst_period_errors: int
    negative_demand_count: int
    negative_generation_count: int
    above_capacity_count: int
    night_solar_count: int
    long_zero_run_count: int
    extreme_spike_count: int
    stale_data: bool
    anomaly_rate: float
    quality_score: float
    site_readiness: str
    recommended_next_action: str


def _long_true_runs(mask: pd.Series, minimum: int) -> pd.Series:
    groups = mask.ne(mask.shift(fill_value=False)).cumsum()
    sizes = mask.groupby(groups).transform("sum")
    return mask & (sizes >= minimum)


def _value_series(frame: pd.DataFrame) -> pd.Series:
    for column in ("energy_mwh", "actual_mwh", "consumption_mwh", "generation_mwh"):
        if column in frame.columns:
            return pd.to_numeric(frame[column], errors="coerce")
    raise ValueError("observations require an energy_mwh or actual_mwh value column")


def validate_site_observations(
    data: pd.DataFrame,
    site: dict[str, Any] | pd.Series,
    *,
    reference_time: pd.Timestamp | None = None,
    stale_after: timedelta = timedelta(hours=2),
    zero_run_periods: int = 12,
) -> tuple[pd.DataFrame, SiteQualityReport]:
    """Return every input row with flags plus a 0–100 readiness report."""
    frame = data.copy().reset_index(drop=True)
    site_data = dict(site)
    site_id = str(site_data["site_id"])
    flags: list[set[str]] = [set() for _ in range(len(frame))]

    def flag(mask: pd.Series | np.ndarray, code: str) -> None:
        values = np.asarray(pd.Series(mask).fillna(False), dtype=bool)
        for index in np.flatnonzero(values):
            flags[int(index)].add(code)

    timestamps = pd.to_datetime(frame.get("timestamp_utc"), utc=True, errors="coerce")
    invalid_timestamp = timestamps.isna()
    flag(invalid_timestamp, "invalid_timestamp")
    duplicate_mask = timestamps.notna() & timestamps.duplicated(keep=False)
    flag(duplicate_mask, "duplicate_timestamp")

    wrong_interval = pd.Series(False, index=frame.index)
    ordered = pd.DataFrame({"timestamp": timestamps, "row": frame.index}).dropna().sort_values("timestamp")
    unique_ordered = ordered.drop_duplicates("timestamp")
    differences = unique_ordered.timestamp.diff()
    bad_rows = unique_ordered.loc[differences.notna() & differences.ne(pd.Timedelta(minutes=30)), "row"]
    wrong_interval.loc[bad_rows.astype(int)] = True
    flag(wrong_interval, "wrong_interval")

    values = _value_series(frame)
    role = str(site_data.get("site_role", frame.get("site_role", pd.Series([""])).iloc[0] if len(frame) else ""))
    technology = str(site_data.get("technology", frame.get("technology", pd.Series([""])).iloc[0] if len(frame) else ""))
    negative = values < 0
    negative_demand = negative & (role == "demand")
    negative_generation = negative & (role == "generation")
    flag(negative_demand, "negative_demand")
    flag(negative_generation, "negative_generation")

    capacity = site_data.get("installed_capacity_mw")
    above_capacity = pd.Series(False, index=frame.index)
    if role == "generation" and capacity is not None and not pd.isna(capacity):
        if "observed_power_mw" in frame:
            above_capacity = pd.to_numeric(frame["observed_power_mw"], errors="coerce") > float(capacity) + 1e-9
        else:
            above_capacity = values > float(capacity) * 0.5 + 1e-9
    flag(above_capacity, "generation_above_capacity")

    night_solar = pd.Series(False, index=frame.index)
    if technology == "solar":
        if "is_daylight" in frame:
            daylight = frame["is_daylight"].fillna(False).astype(bool)
        else:
            local_hour = timestamps.dt.tz_convert("Europe/London").dt.hour
            daylight = local_hour.between(5, 21, inclusive="left")
        night_solar = (~daylight) & (values > 1e-9)
    flag(night_solar, "night_time_solar")

    zero_candidate = values.fillna(0).abs() <= 1e-12
    if technology == "solar" and "is_daylight" in frame:
        zero_candidate &= frame["is_daylight"].fillna(False).astype(bool)
    long_zero = _long_true_runs(zero_candidate, zero_run_periods)
    flag(long_zero, "long_zero_run")

    finite_values = values.dropna()
    extreme_spike = pd.Series(False, index=frame.index)
    if len(finite_values) >= 10:
        median = float(finite_values.median())
        mad = float((finite_values - median).abs().median())
        robust_scale = max(mad * 1.4826, float(finite_values.std()) * 0.15, 1e-9)
        extreme_spike = values > median + 8 * robust_scale
    flag(extreme_spike, "extreme_spike")

    valid_timestamps = timestamps.dropna()
    if valid_timestamps.empty:
        expected_rows = 0
        missing_periods = 0
        dst_errors = 0
        stale = True
    else:
        local_dates = valid_timestamps.dt.tz_convert("Europe/London").dt.date
        first_date, last_date = min(local_dates), max(local_dates)
        dates = pd.date_range(first_date, last_date, freq="D").date
        expected_rows = sum(expected_period_count(day) for day in dates)
        missing_periods = max(expected_rows - int(valid_timestamps.nunique()), 0)
        dst_errors = 0
        for day in dates:
            if expected_period_count(day) != 48:
                day_mask = local_dates == day
                audit_frame = pd.DataFrame({"timestamp_utc": valid_timestamps.loc[day_mask]})
                result = validate_settlement_day(audit_frame, day)
                dst_errors += len(result["missing_periods"]) + len(result["duplicate_periods"]) + len(result["out_of_range_periods"])
        comparison_time = reference_time or pd.Timestamp.now(tz="UTC")
        comparison_time = pd.Timestamp(comparison_time)
        if comparison_time.tzinfo is None:
            comparison_time = comparison_time.tz_localize("UTC")
        else:
            comparison_time = comparison_time.tz_convert("UTC")
        stale = valid_timestamps.max() < comparison_time - stale_after

    unique_valid = int(valid_timestamps.nunique())
    completeness = min(unique_valid / expected_rows, 1.0) if expected_rows else 0.0
    consistency_events = int(duplicate_mask.sum() + wrong_interval.sum() + dst_errors)
    physical_mask = negative_demand | negative_generation | above_capacity | night_solar
    physical_events = int(physical_mask.sum())
    anomaly_mask = long_zero | extreme_spike
    anomaly_rate = float(anomaly_mask.sum() / max(len(frame), 1))
    consistency_rate = max(0.0, 1 - consistency_events / max(len(frame), 1))
    physical_rate = max(0.0, 1 - physical_events / max(len(frame), 1))
    score = 30 * completeness + 20 * consistency_rate + 25 * physical_rate + (0 if stale else 10) + 15 * max(0.0, 1 - anomaly_rate)
    score = round(float(np.clip(score, 0, 100)), 2)
    critical = physical_events > 0 or int(invalid_timestamp.sum()) > 0
    readiness = "ready" if score >= 80 and not critical else "review"
    if critical:
        recommendation = "Correct flagged timestamps or physical values, then revalidate; no rows were removed."
    elif missing_periods or duplicate_mask.any() or wrong_interval.any():
        recommendation = "Resolve coverage and interval issues before modelling."
    elif stale:
        recommendation = "Refresh the latest meter data before modelling."
    else:
        recommendation = "Data is ready for the next validation phase."
    frame["quality_flag"] = ["valid" if not row_flags else "|".join(sorted(row_flags)) for row_flags in flags]
    report = SiteQualityReport(
        site_id=site_id,
        row_count=len(frame),
        expected_rows=expected_rows,
        valid_timestamp_rows=int(timestamps.notna().sum()),
        completeness=round(completeness, 6),
        missing_periods=missing_periods,
        duplicate_observations=int(duplicate_mask.sum()),
        wrong_interval_count=int(wrong_interval.sum()),
        dst_period_errors=dst_errors,
        negative_demand_count=int(negative_demand.sum()),
        negative_generation_count=int(negative_generation.sum()),
        above_capacity_count=int(above_capacity.sum()),
        night_solar_count=int(night_solar.sum()),
        long_zero_run_count=int(long_zero.sum()),
        extreme_spike_count=int(extreme_spike.sum()),
        stale_data=bool(stale),
        anomaly_rate=round(anomaly_rate, 6),
        quality_score=score,
        site_readiness=readiness,
        recommended_next_action=recommendation,
    )
    return frame, report


def generate_demo_quality_artifacts(
    sites_path: Path | str = "data/demo/sites.parquet",
    observations_path: Path | str = "data/demo/observations.parquet",
    output_root: Path | str = "data/quality",
) -> dict[str, Path]:
    sites = pd.read_parquet(sites_path)
    observations = pd.read_parquet(observations_path)
    output = Path(output_root)
    reports_dir = output / "site_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    reference_time = pd.to_datetime(observations["timestamp_utc"], utc=True).max() + pd.Timedelta(minutes=30)
    annotated_frames: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []
    for site in sites.to_dict(orient="records"):
        site_rows = observations[observations["site_id"] == site["site_id"]]
        annotated, report = validate_site_observations(site_rows, site, reference_time=reference_time)
        report_data = asdict(report)
        reports.append(report_data)
        annotated_frames.append(annotated)
        (reports_dir / f"{site['site_id']}.json").write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    summary = pd.DataFrame(reports)
    annotated_all = pd.concat(annotated_frames, ignore_index=True)
    summary_parquet = output / "site_readiness.parquet"
    summary_json = output / "site_readiness.json"
    annotated_path = output / "annotated_observations.parquet"
    summary.to_parquet(summary_parquet, index=False)
    summary_json.write_text(json.dumps(reports, indent=2), encoding="utf-8")
    annotated_all.to_parquet(annotated_path, index=False)
    return {"site_readiness_parquet": summary_parquet, "site_readiness_json": summary_json, "annotated_observations": annotated_path, "site_reports": reports_dir}
