"""Safe in-memory CSV validation service."""

from __future__ import annotations

from collections import Counter
from io import StringIO
from pathlib import PurePath
from typing import Any

import numpy as np

from api.errors import APIError
from api.services.artifact_repository import json_safe, records
from gridmatch.data.uploads import validate_csv_upload

CSV_CONTENT_TYPES = {
    "text/csv",
    "application/csv",
    "application/vnd.ms-excel",
}


class UploadService:
    def __init__(self, maximum_bytes: int) -> None:
        self.maximum_bytes = maximum_bytes

    def validate(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        content: bytes,
    ) -> dict[str, Any]:
        safe_name = PurePath(filename or "upload.csv").name
        if not safe_name.lower().endswith(".csv"):
            raise APIError(
                415,
                "INVALID_UPLOAD_TYPE",
                "Upload filename must use the .csv extension.",
            )
        if content_type not in CSV_CONTENT_TYPES:
            raise APIError(
                415,
                "INVALID_UPLOAD_TYPE",
                "Upload content type must be CSV.",
            )
        if len(content) > self.maximum_bytes:
            raise APIError(
                413,
                "UPLOAD_TOO_LARGE",
                "CSV upload exceeds the configured size limit.",
                {"maximum_bytes": self.maximum_bytes},
            )
        try:
            decoded = content.decode("utf-8-sig")
        except UnicodeDecodeError as error:
            raise APIError(
                400,
                "MALFORMED_UPLOAD",
                "CSV must be UTF-8 encoded.",
            ) from error
        try:
            result = validate_csv_upload(StringIO(decoded))
        except (ValueError, UnicodeError) as error:
            raise APIError(
                400,
                "MALFORMED_UPLOAD",
                str(error),
            ) from error
        report = dict(result.report)
        row_count = max(int(report["received_rows"]), 1)
        frequency_penalty = (
            0
            if report["inferred_frequency_minutes"] == 30
            else 15
        )
        score = (
            100 * float(report["completeness"])
            - 50 * int(report["anomalies"]) / row_count
            - frequency_penalty
        )
        report["quality_score"] = round(
            float(np.clip(score, 0, 100)),
            2,
        )
        flag_counts: Counter[str] = Counter()
        for value in result.annotated_data["quality_flag"].astype(str):
            if value == "valid":
                continue
            flag_counts.update(value.split("|"))
        report["anomaly_summary"] = dict(sorted(flag_counts.items()))
        report["recommended_actions"] = [
            report.pop("recommended_next_action")
        ]
        return {
            "filename": safe_name,
            **json_safe(report),
            "annotated_preview": records(
                result.annotated_data.head(10)
            ),
            "permanent_storage": False,
        }
