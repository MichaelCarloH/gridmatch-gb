"""Build Phase 9 hedge recommendations and policy backtest."""

from __future__ import annotations

import json

from gridmatch.market.pipeline import build_hedge_backtest


if __name__ == "__main__":
    result = build_hedge_backtest()
    print(
        json.dumps(
            {
                key: value
                for key, value in result.items()
                if key
                not in {
                    "policy_metrics",
                    "selection_history",
                    "artifacts",
                    "figures",
                    "limitations",
                }
            },
            indent=2,
        )
    )
