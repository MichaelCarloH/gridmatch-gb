"""NESO CKAN client with package, resource and datastore support."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any, Mapping

from gridmatch.clients.base import CachedHttpClient, FetchResult


class NesoClient:
    base_url = "https://api.neso.energy/api/3/action"

    def __init__(self, http: CachedHttpClient | None = None, fixture_root: Path | str = "data/fixtures/neso") -> None:
        self.http = http or CachedHttpClient("neso")
        self.fixture_root = Path(fixture_root)

    def _action(self, action: str, name: str, params: Mapping[str, Any]) -> tuple[dict[str, Any], FetchResult]:
        fetched = self.http.fetch(name, f"{self.base_url}/{action}", params=params, fixture_path=self.fixture_root / f"{name}.json")
        payload = self.http.read_json(fetched)
        if not isinstance(payload, dict) or not payload.get("success", False) or not isinstance(payload.get("result"), dict):
            raise ValueError(f"NESO {action} returned an invalid CKAN response")
        fixture = self.fixture_root / f"{name}.json"
        if not fetched.used_fixture and not fixture.exists():
            fixture.parent.mkdir(parents=True, exist_ok=True)
            fixture.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
        return payload["result"], fetched

    def package_search(self, query: str, rows: int = 10) -> tuple[dict[str, Any], FetchResult]:
        return self._action("package_search", "package_search", {"q": query, "rows": rows})

    def package_show(self, package_id: str) -> tuple[dict[str, Any], FetchResult]:
        return self._action("package_show", "package_show", {"id": package_id})

    def discover_resources(self, package_id: str) -> tuple[list[dict[str, Any]], dict[str, Any], FetchResult]:
        package, fetched = self.package_show(package_id)
        resources = [item for item in package.get("resources", []) if isinstance(item, dict)]
        return resources, package, fetched

    def datastore_search(self, resource_id: str, limit: int = 100, offset: int = 0) -> tuple[dict[str, Any], FetchResult]:
        return self._action("datastore_search", "datastore_search", {"resource_id": resource_id, "limit": limit, "offset": offset})

    def download_csv(self, resource_url: str, name: str = "resource_csv") -> FetchResult:
        return self.http.fetch(name, resource_url, suffix=".csv", fixture_path=self.fixture_root / f"{name}.csv")
