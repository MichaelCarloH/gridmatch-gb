"""Public price-reference preparation for prototype hedge scenarios."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

PRICE_ALIGNMENT = "non_contemporaneous_public_settlement_period_proxy"


@dataclass(frozen=True)
class PriceAssumptions:
    """Visible asymmetric settlement assumptions.

    ``short_cost_multiplier`` is the minimum short purchase price relative to
    the market reference. ``long_value_multiplier`` is the maximum recovery
    value for surplus energy relative to that reference.
    """

    short_cost_multiplier: float = 1.35
    long_value_multiplier: float = 0.65

    def __post_init__(self) -> None:
        if self.short_cost_multiplier < 1:
            raise ValueError("Short-cost multiplier must be at least 1")
        if not 0 <= self.long_value_multiplier <= 1:
            raise ValueError("Long-value multiplier must be between 0 and 1")
        if self.short_cost_multiplier <= self.long_value_multiplier:
            raise ValueError("Short cost must exceed long recovery value")


def public_price_curve(
    prices: pd.DataFrame,
    settlement_periods: pd.Series,
    *,
    assumptions: PriceAssumptions = PriceAssumptions(),
) -> pd.DataFrame:
    """Map a cached public snapshot to periods as a disclosed scenario curve."""
    market = prices[
        (prices["price_source"] == "market_index")
        & (prices["dataprovider"] == "APXMIDP")
        & (prices["volume"] > 0)
        & prices["price"].notna()
    ].copy()
    system = prices[
        (prices["price_source"] == "system_price")
        & prices["systemsellprice"].notna()
    ].copy()
    if market.empty:
        raise ValueError("A positive-volume APX market reference is required")
    if system.empty:
        raise ValueError("A public system-price reference is required")

    reference_price = float(
        np.average(market["price"], weights=market["volume"])
    )
    system_by_period = (
        system.groupby("settlementperiod")["systemsellprice"]
        .mean()
        .to_dict()
    )
    system_fallback = float(system["systemsellprice"].median())
    unique_periods = sorted(
        {int(period) for period in settlement_periods.dropna().unique()}
    )
    source_dates = sorted(
        {
            str(value)
            for value in prices["settlementdate"].dropna().unique()
        }
    )
    source_date = ",".join(source_dates)
    rows = []
    for period in unique_periods:
        system_price = float(system_by_period.get(period, system_fallback))
        short_price = max(
            system_price,
            reference_price * assumptions.short_cost_multiplier,
        )
        long_price = min(
            system_price,
            reference_price * assumptions.long_value_multiplier,
        )
        rows.append(
            {
                "settlement_period": period,
                "market_reference_price_gbp_mwh": reference_price,
                "public_system_price_gbp_mwh": system_price,
                "short_price_gbp_mwh": short_price,
                "long_price_gbp_mwh": long_price,
                "short_cost_multiplier": (
                    assumptions.short_cost_multiplier
                ),
                "long_value_multiplier": (
                    assumptions.long_value_multiplier
                ),
                "price_data_origin": "public",
                "price_source": "Elexon Insights snapshot",
                "price_source_settlement_date": source_date,
                "price_alignment_method": PRICE_ALIGNMENT,
            }
        )
    return pd.DataFrame(rows)
