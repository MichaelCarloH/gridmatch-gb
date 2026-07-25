"""Fetch compact public Phase 3 datasets with caching and fixture fallback."""

from __future__ import annotations

import logging

from gridmatch.data.public import collect_all_public_data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    for name, path in collect_all_public_data().items():
        print(f"{name}: {path}")
