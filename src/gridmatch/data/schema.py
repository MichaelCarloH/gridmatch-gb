"""Small explicit schema checks used at public-data boundaries."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

import pandas as pd


class SchemaError(ValueError):
    pass


def require_columns(frame: pd.DataFrame, required: Iterable[str], dataset: str) -> None:
    missing = sorted(set(required) - set(frame.columns))
    if missing:
        raise SchemaError(f"{dataset} missing required columns: {', '.join(missing)}")


def require_records(payload: Any, dataset: str) -> list[Mapping[str, Any]]:
    if isinstance(payload, list) and all(isinstance(item, Mapping) for item in payload):
        return payload
    if isinstance(payload, Mapping):
        for key in ("data", "result", "results", "records", "items"):
            value = payload.get(key)
            if isinstance(value, list) and all(isinstance(item, Mapping) for item in value):
                return value
            if isinstance(value, Mapping):
                for nested in ("records", "results", "data"):
                    records = value.get(nested)
                    if isinstance(records, list) and all(isinstance(item, Mapping) for item in records):
                        return records
    raise SchemaError(f"{dataset} response does not contain a record list")
