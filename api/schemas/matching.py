"""Renewable-matching API enums."""

from typing import Literal

AllocationType = Literal["forecast", "realised"]
MatchingMode = Literal["maximum_match", "local_preference"]
