"""Deterministic LP allocator for commercial renewable matching."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence

import numpy as np

from gridmatch.matching.distance import great_circle_distance_km

try:
    from scipy.optimize import linprog
except ImportError:  # pragma: no cover - deployment fallback
    linprog = None

MatchingMode = Literal["maximum_match", "local_preference"]
SOLVER_TOLERANCE = 1e-8


@dataclass(frozen=True)
class MatchParticipant:
    """Typed input for one generator or consumer."""

    site_id: str
    available_mwh: float
    latitude: float
    longitude: float
    region: str
    technology: str = ""


@dataclass(frozen=True)
class Allocation:
    """One non-zero generator-to-consumer commercial allocation."""

    generator_site_id: str
    consumer_site_id: str
    matched_mwh: float
    distance_km: float
    allocation_score: float


@dataclass(frozen=True)
class AllocationResult:
    """Allocation result with solver provenance and conservation totals."""

    allocations: tuple[Allocation, ...]
    total_generation_mwh: float
    total_demand_mwh: float
    matched_mwh: float
    matching_mode: MatchingMode
    solver: str


def _pair_costs(
    generators: Sequence[MatchParticipant],
    consumers: Sequence[MatchParticipant],
    mode: MatchingMode,
) -> tuple[np.ndarray, np.ndarray]:
    """Build deterministic secondary costs and pair distances."""
    generator_count = len(generators)
    consumer_count = len(consumers)
    distances = np.array(
        [
            great_circle_distance_km(
                generator.latitude,
                generator.longitude,
                consumer.latitude,
                consumer.longitude,
            )
            for generator in generators
            for consumer in consumers
        ],
        dtype=float,
    )
    pair_order = np.arange(
        generator_count * consumer_count,
        dtype=float,
    )
    if pair_order.size > 1:
        pair_order /= pair_order.size - 1

    if mode == "maximum_match":
        return pair_order * 1e-6, distances

    distance_scale = max(float(distances.max()), 1.0)
    normalized_distance = distances / distance_scale
    region_penalty = np.array(
        [
            0.0 if generator.region == consumer.region else 1.0
            for generator in generators
            for consumer in consumers
        ],
        dtype=float,
    )
    technologies = sorted(
        {generator.technology for generator in generators}
    )
    technology_rank = {
        technology: position
        for position, technology in enumerate(technologies)
    }
    technology_denominator = max(len(technologies) - 1, 1)
    technology_preference = np.array(
        [
            abs(
                technology_rank[generator.technology]
                - (consumer_number % max(len(technologies), 1))
            )
            / technology_denominator
            for generator in generators
            for consumer_number, consumer in enumerate(consumers)
        ],
        dtype=float,
    )
    costs = (
        0.80 * normalized_distance
        + 0.15 * region_penalty
        + 0.049 * technology_preference
        + 0.001 * pair_order
    )
    return costs, distances


def _constraint_matrix(
    generator_count: int,
    consumer_count: int,
) -> np.ndarray:
    matrix = np.zeros(
        (
            generator_count + consumer_count,
            generator_count * consumer_count,
        ),
        dtype=float,
    )
    for generator_number in range(generator_count):
        start = generator_number * consumer_count
        matrix[generator_number, start : start + consumer_count] = 1.0
    for consumer_number in range(consumer_count):
        matrix[
            generator_count + consumer_number,
            consumer_number::consumer_count,
        ] = 1.0
    return matrix


def _greedy_fallback(
    generators: Sequence[MatchParticipant],
    consumers: Sequence[MatchParticipant],
    costs: np.ndarray,
) -> np.ndarray:
    """Deterministic fallback used only if SciPy is unavailable."""
    remaining_generation = np.array(
        [participant.available_mwh for participant in generators],
        dtype=float,
    )
    remaining_demand = np.array(
        [participant.available_mwh for participant in consumers],
        dtype=float,
    )
    consumer_count = len(consumers)
    solution = np.zeros(len(costs), dtype=float)
    for pair_number in np.argsort(costs, kind="stable"):
        generator_number = int(pair_number // consumer_count)
        consumer_number = int(pair_number % consumer_count)
        matched = min(
            remaining_generation[generator_number],
            remaining_demand[consumer_number],
        )
        solution[pair_number] = matched
        remaining_generation[generator_number] -= matched
        remaining_demand[consumer_number] -= matched
    return solution


def solve_allocation(
    generators: Sequence[MatchParticipant],
    consumers: Sequence[MatchParticipant],
    *,
    mode: MatchingMode = "maximum_match",
) -> AllocationResult:
    """Maximise volume, then deterministically minimise secondary cost.

    All generator-consumer pairs are feasible in this prototype. Therefore
    ``min(total generation, total demand)`` is the exact maximum volume. The
    LP fixes that total as an equality and optimises only the transparent
    secondary preference, ensuring locality can never reduce matched MWh.
    """
    if mode not in {"maximum_match", "local_preference"}:
        raise ValueError(f"Unsupported matching mode: {mode}")
    ordered_generators = tuple(
        sorted(generators, key=lambda participant: participant.site_id)
    )
    ordered_consumers = tuple(
        sorted(consumers, key=lambda participant: participant.site_id)
    )
    if any(participant.available_mwh < 0 for participant in ordered_generators):
        raise ValueError("Generator availability cannot be negative")
    if any(participant.available_mwh < 0 for participant in ordered_consumers):
        raise ValueError("Consumer demand cannot be negative")

    total_generation = float(
        sum(participant.available_mwh for participant in ordered_generators)
    )
    total_demand = float(
        sum(participant.available_mwh for participant in ordered_consumers)
    )
    target_match = min(total_generation, total_demand)
    if (
        not ordered_generators
        or not ordered_consumers
        or target_match <= SOLVER_TOLERANCE
    ):
        return AllocationResult(
            allocations=(),
            total_generation_mwh=total_generation,
            total_demand_mwh=total_demand,
            matched_mwh=0.0,
            matching_mode=mode,
            solver="scipy-highs" if linprog is not None else "greedy-fallback",
        )

    costs, distances = _pair_costs(
        ordered_generators,
        ordered_consumers,
        mode,
    )
    if linprog is None:
        solution = _greedy_fallback(
            ordered_generators,
            ordered_consumers,
            costs,
        )
        solver = "greedy-fallback"
    else:
        matrix = _constraint_matrix(
            len(ordered_generators),
            len(ordered_consumers),
        )
        limits = np.array(
            [
                *(
                    participant.available_mwh
                    for participant in ordered_generators
                ),
                *(participant.available_mwh for participant in ordered_consumers),
            ],
            dtype=float,
        )
        result = linprog(
            c=costs,
            A_ub=matrix,
            b_ub=limits,
            A_eq=np.ones((1, len(costs)), dtype=float),
            b_eq=np.array([target_match], dtype=float),
            bounds=(0, None),
            method="highs",
        )
        if not result.success:
            raise RuntimeError(f"Matching optimisation failed: {result.message}")
        solution = np.where(
            np.asarray(result.x) > SOLVER_TOLERANCE,
            np.asarray(result.x),
            0.0,
        )
        solver = "scipy-highs"

    allocations = []
    consumer_count = len(ordered_consumers)
    for pair_number, matched in enumerate(solution):
        if matched <= SOLVER_TOLERANCE:
            continue
        generator_number = pair_number // consumer_count
        consumer_number = pair_number % consumer_count
        allocations.append(
            Allocation(
                generator_site_id=ordered_generators[
                    generator_number
                ].site_id,
                consumer_site_id=ordered_consumers[consumer_number].site_id,
                matched_mwh=float(matched),
                distance_km=float(distances[pair_number]),
                allocation_score=float(costs[pair_number]),
            )
        )
    matched_total = float(sum(row.matched_mwh for row in allocations))
    if not np.isclose(
        matched_total,
        target_match,
        atol=SOLVER_TOLERANCE,
        rtol=0,
    ):
        raise RuntimeError("Allocation does not conserve maximum matched volume")
    return AllocationResult(
        allocations=tuple(allocations),
        total_generation_mwh=total_generation,
        total_demand_mwh=total_demand,
        matched_mwh=matched_total,
        matching_mode=mode,
        solver=solver,
    )
