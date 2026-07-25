"""Build the deterministic Phase 3 synthetic portfolio."""

from __future__ import annotations

import logging

from gridmatch.data.synthetic import write_demo_dataset


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")
    for name, path in write_demo_dataset().items():
        print(f"{name}: {path}")
