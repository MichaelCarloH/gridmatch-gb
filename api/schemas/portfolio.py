"""Portfolio API enums and response aliases."""

from typing import Literal

PortfolioMethod = Literal[
    "baseline",
    "bottom_up",
    "direct",
    "reconciled",
]
PortfolioTarget = Literal["demand", "generation", "net"]
