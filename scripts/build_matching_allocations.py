"""Build Phase 8 forecast and realised renewable allocations."""

from __future__ import annotations

import json

from gridmatch.matching.pipeline import build_matching_allocations


if __name__ == "__main__":
    result = build_matching_allocations()
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"artifacts", "figures", "limitations"}
            },
            indent=2,
        )
    )
