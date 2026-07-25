"""Execute Phase 5 notebooks deterministically and build a research index."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
import time

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = ROOT / "notebooks"
OUTPUT_ROOT = ROOT / "artifacts" / "notebooks"
INDEX_PATH = OUTPUT_ROOT / "notebook_index.json"
KERNEL_NAME = "gridmatch-phase5"

NOTEBOOKS = [
    ("00_gb_market_and_settlement", "GB market roles, settlement-day mechanics and imbalance context", "GB delivery days contain 46, 48 or 50 half-hourly periods."),
    ("01_site_map_and_public_assets", "Operational REPD technology, capacity and geographic evidence", "3,100 operational projects are analysed with coordinate validity retained."),
    ("02_data_quality_and_site_profiles", "Simulated site profiles and row-preserving quality evidence", "All 12 sites are ready while 5,086 rule-based flags remain auditable."),
    ("03_weather_features", "Weather availability, coordinate alignment and leakage methodology", "Forecast-vintage issue time must be preserved separately; ERA5 is not a vintage archive."),
]


def _write_index(entries: list[dict]) -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def _prepare_kernel() -> str:
    """Create a repository-local kernelspec pinned to the active interpreter."""
    jupyter_data = OUTPUT_ROOT / ".jupyter"
    kernel_dir = jupyter_data / "kernels" / KERNEL_NAME
    kernel_dir.mkdir(parents=True, exist_ok=True)
    kernel_spec = {
        "argv": [
            sys.executable,
            "-m",
            "ipykernel_launcher",
            "-f",
            "{connection_file}",
        ],
        "display_name": "GridMatch Phase 5",
        "language": "python",
        "metadata": {"debugger": False},
    }
    (kernel_dir / "kernel.json").write_text(
        json.dumps(kernel_spec, indent=2),
        encoding="utf-8",
    )
    existing = os.environ.get("JUPYTER_PATH")
    os.environ["JUPYTER_PATH"] = (
        str(jupyter_data)
        if not existing
        else str(jupyter_data) + os.pathsep + existing
    )
    return KERNEL_NAME


def execute_all() -> list[dict]:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    os.environ["PYTHONHASHSEED"] = "0"
    os.environ["MPLBACKEND"] = "Agg"
    python_path = str(ROOT / "src")
    os.environ["PYTHONPATH"] = python_path + os.pathsep + os.environ.get("PYTHONPATH", "")
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    kernel_name = _prepare_kernel()
    entries: list[dict] = []
    for name, summary, key_result in NOTEBOOKS:
        source = SOURCE_ROOT / f"{name}.ipynb"
        destination = OUTPUT_ROOT / f"{name}.executed.ipynb"
        started = time.perf_counter()
        execution_timestamp = datetime.now(timezone.utc).isoformat()
        try:
            document = nbformat.read(source, as_version=4)
            NotebookClient(
                document,
                timeout=600,
                kernel_name=kernel_name,
                allow_errors=False,
            ).execute(cwd=str(ROOT))
            nbformat.write(document, destination)
            status = "executed"
        except Exception as exc:
            status = "failed"
            entries.append({"name": name, "status": status, "summary": summary, "key_result": str(exc), "output_path": destination.relative_to(ROOT).as_posix(), "execution_timestamp": execution_timestamp, "duration_seconds": round(time.perf_counter() - started, 3), "artifact_links": []})
            _write_index(entries)
            raise
        artifact_links = sorted(path.relative_to(ROOT).as_posix() for path in list((ROOT / "artifacts" / "figures").glob(f"{name[:2]}_*")) + list((ROOT / "artifacts" / "tables").glob(f"{name[:2]}_*")))
        entries.append({"name": name, "status": status, "summary": summary, "key_result": key_result, "output_path": destination.relative_to(ROOT).as_posix(), "execution_timestamp": execution_timestamp, "duration_seconds": round(time.perf_counter() - started, 3), "artifact_links": artifact_links})
        _write_index(entries)
        print(f"{name}: {status} ({entries[-1]['duration_seconds']}s)")
    return entries


if __name__ == "__main__":
    execute_all()
