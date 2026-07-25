"""Train and validate all Phase 6 site-level forecast stacks."""

from __future__ import annotations

import json

from gridmatch.models.training import train_all_sites


if __name__ == "__main__":
    result = train_all_sites()
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key != "metrics"
            },
            indent=2,
            allow_nan=False,
        )
    )
