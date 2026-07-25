"""Build Phase 7 bottom-up, direct and reconciled portfolio forecasts."""

from __future__ import annotations

import json

from gridmatch.portfolio.training import build_portfolio_forecasts


if __name__ == "__main__":
    result = build_portfolio_forecasts()
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key not in {"metrics", "reconciliation_weights"}
            },
            indent=2,
        )
    )
