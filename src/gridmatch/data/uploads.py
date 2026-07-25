"""CSV meter-upload validation with row-level audit flags."""

from __future__ import annotations

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import IO, Any

import numpy as np
import pandas as pd

REQUIRED_UPLOAD_COLUMNS = ("timestamp", "consumption_kwh", "generation_kwh")


@dataclass
class UploadValidationResult:
    report: dict[str, Any]
    annotated_data: pd.DataFrame


def validate_csv_upload(source: Path | str | IO[str]) -> UploadValidationResult:
    frame = pd.read_csv(source, dtype="string")
    missing_columns = sorted(set(REQUIRED_UPLOAD_COLUMNS) - set(frame.columns))
    if missing_columns:
        raise ValueError(f"upload missing required columns: {', '.join(missing_columns)}")
    annotated = frame.copy()
    flags: list[set[str]] = [set() for _ in range(len(annotated))]

    def flag(mask: pd.Series | np.ndarray, code: str) -> None:
        values = np.asarray(pd.Series(mask).fillna(False), dtype=bool)
        for index in np.flatnonzero(values):
            flags[int(index)].add(code)

    timestamps = pd.to_datetime(annotated["timestamp"], utc=True, errors="coerce")
    consumption = pd.to_numeric(annotated["consumption_kwh"], errors="coerce")
    generation = pd.to_numeric(annotated["generation_kwh"], errors="coerce")
    flag(timestamps.isna(), "invalid_timestamp")
    flag(consumption.isna(), "invalid_consumption")
    flag(generation.isna(), "invalid_generation")
    flag(consumption < 0, "negative_consumption")
    flag(generation < 0, "negative_generation")
    duplicate_mask = timestamps.notna() & timestamps.duplicated(keep=False)
    flag(duplicate_mask, "duplicate_timestamp")

    valid_unique = timestamps.dropna().drop_duplicates().sort_values()
    differences = valid_unique.diff().dropna()
    if differences.empty:
        inferred = None
        expected_rows = len(valid_unique)
        interval_consistent = len(valid_unique) <= 1
    else:
        inferred_delta = differences.mode().iloc[0]
        inferred = int(inferred_delta.total_seconds() // 60)
        expected_rows = int((valid_unique.iloc[-1] - valid_unique.iloc[0]) / inferred_delta) + 1
        interval_consistent = bool((differences == inferred_delta).all())
    if not interval_consistent and len(annotated):
        flag(pd.Series(True, index=annotated.index), "inconsistent_interval")
    completeness = min(len(valid_unique) / expected_rows, 1.0) if expected_rows else 0.0
    annotated["timestamp_utc"] = timestamps
    annotated["consumption_mwh"] = consumption / 1000
    annotated["generation_mwh"] = generation / 1000
    annotated["data_origin"] = "uploaded"
    annotated["quality_flag"] = ["valid" if not row_flags else "|".join(sorted(row_flags)) for row_flags in flags]
    anomaly_count = int(sum(bool(row_flags) for row_flags in flags))
    ready = inferred == 30 and completeness >= 0.98 and anomaly_count == 0
    report = {
        "date_range": {
            "start_utc": valid_unique.iloc[0].isoformat() if len(valid_unique) else None,
            "end_utc": valid_unique.iloc[-1].isoformat() if len(valid_unique) else None,
        },
        "inferred_frequency_minutes": inferred,
        "expected_rows": expected_rows,
        "received_rows": len(annotated),
        "preserved_rows": len(annotated),
        "completeness": round(completeness, 6),
        "duplicates": int(duplicate_mask.sum()),
        "anomalies": anomaly_count,
        "site_readiness": "ready" if ready else "review",
        "recommended_next_action": "Upload accepted; retain the validated audit file." if ready else "Correct flagged rows and provide complete 30-minute intervals, then revalidate.",
        "units": {"input": "kWh", "output": "MWh"},
        "data_origin": "uploaded",
    }
    return UploadValidationResult(report=report, annotated_data=annotated)
