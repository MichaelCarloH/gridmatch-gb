"""Great Britain electricity settlement-period conversions."""

from __future__ import annotations

from datetime import date as Date, datetime, time, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd

LONDON = ZoneInfo("Europe/London")
UTC = timezone.utc
PERIOD = timedelta(minutes=30)


def _date(value: Date | str) -> Date:
    return value if isinstance(value, Date) and not isinstance(value, datetime) else Date.fromisoformat(str(value))


def _local_midnight_utc(value: Date | str) -> datetime:
    day = _date(value)
    return datetime.combine(day, time.min, tzinfo=LONDON).astimezone(UTC)


def expected_period_count(date: Date | str) -> int:
    """Return 46, 48 or 50 according to the Europe/London settlement day."""
    day = _date(date)
    start = _local_midnight_utc(day)
    end = _local_midnight_utc(day + timedelta(days=1))
    return int((end - start) / PERIOD)


def timestamp_to_settlement_period(timestamp_utc: datetime | pd.Timestamp | str) -> tuple[Date, int]:
    """Convert an aligned UTC timestamp to GB settlement date and period."""
    timestamp = pd.Timestamp(timestamp_utc)
    if timestamp.tzinfo is None:
        raise ValueError("timestamp_utc must be timezone-aware")
    timestamp = timestamp.tz_convert("UTC")
    local_date = timestamp.tz_convert("Europe/London").date()
    start = pd.Timestamp(_local_midnight_utc(local_date))
    elapsed = timestamp - start
    if elapsed < pd.Timedelta(0) or elapsed % pd.Timedelta(minutes=30) != pd.Timedelta(0):
        raise ValueError("timestamp_utc must align to a GB half-hour boundary")
    period = int(elapsed / pd.Timedelta(minutes=30)) + 1
    if period > expected_period_count(local_date):
        raise ValueError("timestamp falls outside the derived settlement day")
    return local_date, period


def settlement_period_to_timestamp(date: Date | str, period: int) -> pd.Timestamp:
    """Convert a GB settlement date/period to an unambiguous UTC timestamp."""
    day = _date(date)
    expected = expected_period_count(day)
    if not isinstance(period, int) or not 1 <= period <= expected:
        raise ValueError(f"period must be between 1 and {expected} for {day}")
    return pd.Timestamp(_local_midnight_utc(day) + (period - 1) * PERIOD)


def validate_settlement_day(data: pd.DataFrame, date: Date | str) -> dict[str, Any]:
    """Audit one settlement day without altering or dropping any observations."""
    day = _date(date)
    expected = expected_period_count(day)
    if "settlement_period" in data.columns:
        if "settlement_date" in data.columns:
            mask = pd.to_datetime(data["settlement_date"], errors="coerce").dt.date == day
            periods = pd.to_numeric(data.loc[mask, "settlement_period"], errors="coerce")
        else:
            periods = pd.to_numeric(data["settlement_period"], errors="coerce")
    elif "timestamp_utc" in data.columns:
        derived: list[int] = []
        for raw in data["timestamp_utc"]:
            try:
                settlement_date, period = timestamp_to_settlement_period(raw)
                if settlement_date == day:
                    derived.append(period)
            except (TypeError, ValueError):
                continue
        periods = pd.Series(derived, dtype="Int64")
    else:
        raise ValueError("data must contain settlement_period or timestamp_utc")
    valid_periods = periods.dropna().astype(int)
    expected_set = set(range(1, expected + 1))
    observed_set = set(valid_periods.tolist())
    duplicates = sorted(valid_periods[valid_periods.duplicated(keep=False)].unique().tolist())
    out_of_range = sorted(observed_set - expected_set)
    missing = sorted(expected_set - observed_set)
    return {
        "settlement_date": day.isoformat(),
        "expected_periods": expected,
        "row_count": int(len(valid_periods)),
        "unique_period_count": int(len(observed_set & expected_set)),
        "missing_periods": missing,
        "duplicate_periods": duplicates,
        "out_of_range_periods": out_of_range,
        "is_valid": not missing and not duplicates and not out_of_range and len(valid_periods) == expected,
    }


def to_london(timestamp_utc: datetime | pd.Timestamp | str) -> pd.Timestamp:
    timestamp = pd.Timestamp(timestamp_utc)
    if timestamp.tzinfo is None:
        raise ValueError("timestamp_utc must be timezone-aware")
    return timestamp.tz_convert("Europe/London")
