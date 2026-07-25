"""Shared resilient HTTP client with immutable local response caching."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
import logging
from pathlib import Path
import shutil
from typing import Any, Mapping

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class FetchResult:
    path: Path
    retrieved_at: str
    source_url: str
    data_origin: str
    from_cache: bool
    used_fixture: bool
    retrieval_mode: str


class CachedHttpClient:
    """GET-only client; nothing is downloaded during module import."""

    def __init__(
        self,
        source_name: str,
        raw_root: Path | str = "data/raw",
        timeout_seconds: float = 20.0,
        retries: int = 3,
    ) -> None:
        self.source_name = source_name
        self.raw_root = Path(raw_root) / source_name
        self.raw_root.mkdir(parents=True, exist_ok=True)
        self.timeout_seconds = timeout_seconds
        retry = Retry(
            total=retries,
            connect=retries,
            read=retries,
            backoff_factor=0.4,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "GridMatch-GB/0.1 data-research"})
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    @staticmethod
    def _cache_key(url: str, params: Mapping[str, Any] | None) -> str:
        canonical = json.dumps({"url": url, "params": params or {}}, sort_keys=True, default=str)
        return sha256(canonical.encode("utf-8")).hexdigest()[:16]

    def fetch(
        self,
        dataset_name: str,
        url: str,
        *,
        params: Mapping[str, Any] | None = None,
        suffix: str = ".json",
        fixture_path: Path | str | None = None,
        force: bool = False,
    ) -> FetchResult:
        cache_path = self.raw_root / f"{dataset_name}-{self._cache_key(url, params)}{suffix}"
        metadata_path = cache_path.with_suffix(cache_path.suffix + ".metadata.json")
        if cache_path.exists() and not force:
            metadata = self._read_metadata(metadata_path)
            LOGGER.info("cache hit dataset=%s path=%s", dataset_name, cache_path)
            return FetchResult(
                path=cache_path,
                retrieved_at=metadata.get("retrieved_at", self._mtime_iso(cache_path)),
                source_url=url,
                data_origin="public",
                from_cache=True,
                used_fixture=metadata.get("source_mode") == "fixture",
                retrieval_mode="fixture" if metadata.get("source_mode") == "fixture" else "cache",
            )

        try:
            LOGGER.info("fetching dataset=%s url=%s", dataset_name, url)
            response = self.session.get(url, params=params, timeout=self.timeout_seconds)
            response.raise_for_status()
            retrieved_at = datetime.now(timezone.utc).isoformat()
            self._atomic_write(cache_path, response.content)
            self._write_metadata(metadata_path, url, retrieved_at, "public", "live", params)
            return FetchResult(cache_path, retrieved_at, response.url, "public", False, False, "live")
        except requests.RequestException as exc:
            fixture = Path(fixture_path) if fixture_path else None
            if fixture and fixture.exists():
                retrieved_at = datetime.now(timezone.utc).isoformat()
                LOGGER.warning("external fetch failed; using labelled fixture dataset=%s error=%s", dataset_name, exc)
                self._atomic_copy(cache_path, fixture)
                self._write_metadata(metadata_path, url, retrieved_at, "public", "fixture", params)
                return FetchResult(cache_path, retrieved_at, url, "public", False, True, "fixture")
            raise RuntimeError(f"Unable to fetch {dataset_name} and no fixture is available: {exc}") from exc

    @staticmethod
    def read_json(result: FetchResult) -> Any:
        return json.loads(result.path.read_text(encoding="utf-8-sig"))

    @staticmethod
    def _atomic_write(path: Path, content: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_bytes(content)
        temp.replace(path)

    @staticmethod
    def _atomic_copy(path: Path, source: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        shutil.copyfile(source, temp)
        temp.replace(path)

    @staticmethod
    def _write_metadata(path: Path, url: str, retrieved_at: str, origin: str, source_mode: str, params: Mapping[str, Any] | None) -> None:
        path.write_text(json.dumps({"source_url": url, "retrieved_at": retrieved_at, "data_origin": origin, "source_mode": source_mode, "params": params or {}}, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def _read_metadata(path: Path) -> dict[str, Any]:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    @staticmethod
    def _mtime_iso(path: Path) -> str:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
