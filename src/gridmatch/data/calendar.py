"""UK bank-holiday and daylight-saving calendar collection."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import json
from zoneinfo import ZoneInfo

import pandas as pd

from gridmatch.clients.base import CachedHttpClient, FetchResult
from gridmatch.data.schema import SchemaError

BANK_HOLIDAY_URL = "https://www.gov.uk/bank-holidays.json"


def dst_transitions(year: int) -> list[dict[str, object]]:
    london = ZoneInfo("Europe/London")
    records: list[dict[str, object]] = []
    previous = datetime(year, 1, 1, 12, tzinfo=timezone.utc).astimezone(london).utcoffset()
    current = date(year, 1, 2)
    while current < date(year + 1, 1, 1):
        instant = datetime.combine(current, datetime.min.time(), tzinfo=timezone.utc) + timedelta(hours=12)
        offset = instant.astimezone(london).utcoffset()
        if offset != previous:
            records.append({"date": current.isoformat(), "event": "dst_transition", "title": "BST starts" if offset > previous else "BST ends", "data_origin": "public_calendar_rule"})
        previous = offset
        current += timedelta(days=1)
    return records


def collect_calendar(client: CachedHttpClient | None = None, years: tuple[int, ...] = (2025, 2026)) -> tuple[pd.DataFrame, FetchResult]:
    client = client or CachedHttpClient("calendar")
    fetched = client.fetch("bank_holidays", BANK_HOLIDAY_URL, fixture_path="data/fixtures/bank_holidays.json")
    payload = client.read_json(fetched)
    if not isinstance(payload, dict) or not isinstance(payload.get("england-and-wales", {}).get("events"), list):
        raise SchemaError("bank-holiday response missing england-and-wales.events")
    rows = [{"date": event["date"], "event": "bank_holiday", "title": event["title"], "data_origin": fetched.data_origin} for event in payload["england-and-wales"]["events"] if int(event["date"][:4]) in years]
    for year in years:
        rows.extend(dst_transitions(year))
    fixture = Path("data/fixtures/bank_holidays.json")
    if not fetched.used_fixture and not fixture.exists():
        fixture.parent.mkdir(parents=True, exist_ok=True)
        fixture.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return pd.DataFrame(rows).sort_values("date").reset_index(drop=True), fetched
