"""Reusable Elexon BMRS client for compact, date-bounded retrievals."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
import json
from typing import Any, Iterable, Mapping

from gridmatch.clients.base import CachedHttpClient, FetchResult
from gridmatch.data.schema import require_records


class ElexonClient:
    base_url = "https://data.elexon.co.uk/bmrs/api/v1"

    def __init__(self, http: CachedHttpClient | None = None, fixture_root: Path | str = "data/fixtures/elexon") -> None:
        self.http = http or CachedHttpClient("elexon")
        self.fixture_root = Path(fixture_root)

    def _get(self, name: str, endpoint: str, params: Mapping[str, Any] | None = None) -> tuple[list[Mapping[str, Any]], FetchResult]:
        fetched = self.http.fetch(name, f"{self.base_url}{endpoint}", params=params, fixture_path=self.fixture_root / f"{name}.json")
        records = require_records(self.http.read_json(fetched), name)
        fixture = self.fixture_root / f"{name}.json"
        if not fetched.used_fixture and not fixture.exists():
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(json.dumps({"data": records[:25], "fixture_provenance": fetched.source_url}, indent=2, default=str), encoding="utf-8")
        return records, fetched

    def paginated(self, name: str, endpoint: str, params: Mapping[str, Any] | None = None, *, page_size: int = 500, max_pages: int = 10) -> tuple[list[Mapping[str, Any]], list[FetchResult]]:
        all_records: list[Mapping[str, Any]] = []
        fetches: list[FetchResult] = []
        for page in range(1, max_pages + 1):
            query = dict(params or {}) | {"page": page, "pageSize": page_size}
            records, fetched = self._get(f"{name}_page_{page}", endpoint, query)
            all_records.extend(records)
            fetches.append(fetched)
            if len(records) < page_size:
                break
        return all_records, fetches

    def bm_units(self) -> tuple[list[Mapping[str, Any]], FetchResult]:
        return self._get("bm_units", "/reference/bmunits/all")

    def actual_generation(self, settlement_date: date | str, settlement_period: int) -> tuple[list[Mapping[str, Any]], FetchResult]:
        return self._get("b1610", "/datasets/B1610", {"settlementDate": str(settlement_date), "settlementPeriod": settlement_period})

    def market_index(self, start: datetime | str, end: datetime | str) -> tuple[list[Mapping[str, Any]], FetchResult]:
        return self._get("market_index", "/balancing/pricing/market-index", {"from": str(start), "to": str(end)})

    def system_prices(self, settlement_date: date | str) -> tuple[list[Mapping[str, Any]], FetchResult]:
        return self._get("system_prices", f"/balancing/settlement/system-prices/{settlement_date}")
