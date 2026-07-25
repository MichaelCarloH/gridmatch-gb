from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from gridmatch.data.settlements import (
    expected_period_count,
    settlement_period_to_timestamp,
    timestamp_to_settlement_period,
    validate_settlement_day,
)


def _day_frame(day: date) -> pd.DataFrame:
    return pd.DataFrame({"timestamp_utc": [settlement_period_to_timestamp(day, period) for period in range(1, expected_period_count(day) + 1)]})


def test_normal_day_has_48_periods() -> None:
    day = date(2025, 1, 15)
    assert expected_period_count(day) == 48
    assert validate_settlement_day(_day_frame(day), day)["is_valid"]


def test_spring_transition_has_46_periods() -> None:
    day = date(2025, 3, 30)
    assert expected_period_count(day) == 46
    assert validate_settlement_day(_day_frame(day), day)["is_valid"]


def test_autumn_transition_has_50_periods() -> None:
    day = date(2025, 10, 26)
    assert expected_period_count(day) == 50
    assert validate_settlement_day(_day_frame(day), day)["is_valid"]


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2025-01-15T00:00:00Z", (date(2025, 1, 15), 1)),
        ("2025-03-30T01:00:00Z", (date(2025, 3, 30), 3)),
        ("2025-10-26T01:00:00Z", (date(2025, 10, 26), 5)),
    ],
)
def test_utc_to_settlement_conversion(timestamp: str, expected: tuple[date, int]) -> None:
    assert timestamp_to_settlement_period(timestamp) == expected


def test_settlement_to_utc_conversion_handles_repeated_hour() -> None:
    day = date(2025, 10, 26)
    assert settlement_period_to_timestamp(day, 1) == pd.Timestamp("2025-10-25T23:00:00Z")
    assert settlement_period_to_timestamp(day, 3) == pd.Timestamp("2025-10-26T00:00:00Z")
    assert settlement_period_to_timestamp(day, 5) == pd.Timestamp("2025-10-26T01:00:00Z")


def test_spring_day_rejects_period_47() -> None:
    with pytest.raises(ValueError):
        settlement_period_to_timestamp(date(2025, 3, 30), 47)
