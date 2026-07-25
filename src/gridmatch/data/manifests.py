"""Machine-readable provenance manifests."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class SourceManifest:
    dataset_name: str
    source_url: str
    retrieved_at: str
    raw_path: str
    processed_path: str
    schema_version: str
    data_origin: str
    license_or_terms: str = ""
    retrieval_mode: str = "live"

    def write(self, root: Path | str = "data/manifests") -> Path:
        destination = Path(root) / f"{self.dataset_name}.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(asdict(self), indent=2, sort_keys=True), encoding="utf-8")
        return destination
