"""Deterministic NSGA-II for small discrete sequence sets.

This module is intentionally independent of gem5 and of the AutoµSens data
model so the multi-objective core can be unit-tested with synthetic functions.
All objectives are **maximised**; a solution dominates another only when it is
no worse in every objective and strictly better in at least one.

The implementation follows Deb et al. (2002): fast non-dominated sorting,
crowding-distance preservation, binary tournament selection, uniform crossover
and per-gene mutation. Randomness comes from a caller-provided seed, and every
tie is broken by genome order so repeated runs are byte-for-byte deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Callable, Iterable, Sequence


@dataclass(frozen=True)
class Individual:
    genes: tuple[int, ...]
    objectives: tuple[float, ...]

    def key(self):
        return self.genes


@dataclass
class ParetoResult:
    population: list[Individual]
    pareto: list[Individual]
    generations: int
    evaluations: int
    seed: int


def dominates(left: Sequence[float], right: Sequence[float]) -> bool:
    """True when *left* Pareto-dominates *right* under maximisation."""
    if len(left) != len(right):
        raise ValueError("objective vectors must have the same length")
    better = False
    for a, b in zip(left, right):
        if a < b:
            return False
        if a > b:
            better = True
    return better


def fast_non_dominated_sort(
        objectives: Sequence[Sequence[float]]) -> list[list[int]]:
    """Return Pareto fronts as lists of indices, best front first."""
    count = len(objectives)
    dominated_by: list[list[int]] = [[] for _ in range(count)]
    domination_count = [0] * count
    first: list[int] = []

    for p in range(count):
        p_obj = objectives[p]
        for q in range(count):
            if p == q:
                continue
            q_obj = objectives[q]
            if dominates(p_obj, q_obj):
                dominated_by[p].append(q)
            elif dominates(q_obj, p_obj):
                domination_count[p] += 1
        if domination_count[p] == 0:
            first.append(p)

    fronts: list[list[int]] = []
    current = first
    while current:
        fronts.append(sorted(current))
        following: list[int] = []
        for p in current:
            for q in dominated_by[p]:
                domination_count[q] -= 1
                if domination_count[q] == 0:
                    following.append(q)
        current = following
    return fronts


def crowding_distance(objectives: Sequence[Sequence[float]],
                      front: Sequence[int]) -> dict[int, float]:
    """Crowding distance for members of one front (boundaries are infinite)."""
    members = list(front)
    distance = {index: 0.0 for index in members}
    if not members:
        return distance
    if len(members) <= 2:
        for index in members:
            distance[index] = math.inf
        return distance

    dimensions = len(objectives[0])
    for dimension in range(dimensions):
        ordered = sorted(members, key=lambda i: (objectives[i][dimension], i))
        low = objectives[ordered[0]][dimension]
        high = objectives[ordered[-1]][dimension]
        distance[ordered[0]] = math.inf
        distance[ordered[-1]] = math.inf
        if high <= low:
            continue
        span = high - low
        for position in range(1, len(ordered) - 1):
            previous = objectives[ordered[position - 1]][dimension]
            following = objectives[ordered[position + 1]][dimension]
            distance[ordered[position]] += (following - previous) / span
    return distance


def _tournament(rng: random.Random, population: Sequence[Individual],
                rank: dict[int, int], crowding: dict[int, float],
                size: int) -> int:
    contenders = rng.sample(range(len(population)), size)
    best = contenders[0]
    for index in contenders[1:]:
        if rank[index] < rank[best]:
            best = index
        elif rank[index] == rank[best]:
            if crowding[index] > crowding[best]:
                best = index
            elif crowding[index] == crowding[best] and \
                    population[index].genes < population[best].genes:
                best = index
    return best


def _uniform_crossover(rng: random.Random, left: tuple[int, ...],
                       right: tuple[int, ...]) -> tuple[tuple[int, ...], ...]:
    first, second = [], []
    for a, b in zip(left, right):
        if rng.random() < 0.5:
            first.append(a)
            second.append(b)
        else:
            first.append(b)
            second.append(a)
    return tuple(first), tuple(second)


def _mutate(rng: random.Random, genes: tuple[int, ...],
            gene_space: int, mutation_rate: float) -> tuple[int, ...]:
    values = list(genes)
    for index in range(len(values)):
        if rng.random() < mutation_rate:
            choice = rng.randrange(gene_space - 1)
            if choice >= values[index]:
                choice += 1
            values[index] = choice
    return tuple(values)


def run_nsga2(objective_fn: Callable[[tuple[int, ...]], Sequence[float]],
              genome_length: int,
              gene_space: int,
              population_size: int = 32,
              generations: int = 20,
              seed: int = 42,
              crossover_rate: float = 0.9,
              mutation_rate: float | None = None,
              tournament_size: int = 2) -> ParetoResult:
    """Run NSGA-II and return the final population and its Pareto front.

    ``objective_fn`` maps a genome to a vector of objective values (all
    maximised). Duplicate genomes are allowed in the population, but the
    returned Pareto front is de-duplicated by genome with the best objective
    vector kept.
    """
    if genome_length <= 0:
        raise ValueError("genome_length must be positive")
    if gene_space <= 1:
        raise ValueError("gene_space must be at least 2")
    if population_size < 2:
        raise ValueError("population_size must be at least 2")
    if generations < 0:
        raise ValueError("generations must not be negative")
    if not 0.0 <= crossover_rate <= 1.0:
        raise ValueError("crossover_rate must be in [0, 1]")
    if mutation_rate is None:
        mutation_rate = 1.0 / genome_length
    if not 0.0 <= mutation_rate <= 1.0:
        raise ValueError("mutation_rate must be in [0, 1]")
    if tournament_size < 2:
        raise ValueError("tournament_size must be at least 2")

    rng = random.Random(seed)
    evaluations = 0

    def evaluate(genes: tuple[int, ...]) -> Individual:
        nonlocal evaluations
        values = tuple(float(value) for value in objective_fn(genes))
        if not values:
            raise ValueError("objective_fn returned an empty vector")
        if any(not math.isfinite(value) for value in values):
            raise ValueError("objective_fn returned a non-finite value")
        evaluations += 1
        return Individual(genes=genes, objectives=values)

    population = [
        evaluate(tuple(rng.randrange(gene_space)
                       for _ in range(genome_length)))
        for _ in range(population_size)
    ]

    def assign(pop: Sequence[Individual]):
        objectives = [individual.objectives for individual in pop]
        fronts = fast_non_dominated_sort(objectives)
        rank: dict[int, int] = {}
        crowding: dict[int, float] = {}
        for level, front in enumerate(fronts):
            distances = crowding_distance(objectives, front)
            for index in front:
                rank[index] = level
                crowding[index] = distances[index]
        return rank, crowding, fronts

    for _ in range(generations):
        rank, crowding, _ = assign(population)
        offspring: list[Individual] = []
        while len(offspring) < population_size:
            left_index = _tournament(
                rng, population, rank, crowding, tournament_size)
            right_index = _tournament(
                rng, population, rank, crowding, tournament_size)
            left = population[left_index].genes
            right = population[right_index].genes
            if rng.random() < crossover_rate:
                first, second = _uniform_crossover(rng, left, right)
            else:
                first, second = left, right
            offspring.append(evaluate(_mutate(
                rng, first, gene_space, mutation_rate)))
            if len(offspring) < population_size:
                offspring.append(evaluate(_mutate(
                    rng, second, gene_space, mutation_rate)))

        combined = list(population) + offspring
        combined_rank, combined_crowding, fronts = assign(combined)
        selected: list[int] = []
        for front in fronts:
            if len(selected) + len(front) <= population_size:
                selected.extend(front)
            else:
                remaining = population_size - len(selected)
                ordered = sorted(
                    front,
                    key=lambda index: (
                        -combined_crowding[index],
                        combined[index].genes,
                    ),
                )
                selected.extend(ordered[:remaining])
                break
        population = [combined[index] for index in selected]

    rank, crowding, fronts = assign(population)
    front = fronts[0] if fronts else []
    # De-duplicate by genome; keep a single deterministic representative.
    unique: dict[tuple[int, ...], Individual] = {}
    for index in front:
        individual = population[index]
        unique.setdefault(individual.genes, individual)
    pareto = sorted(unique.values(), key=lambda individual: individual.genes)
    return ParetoResult(population=population, pareto=pareto,
                        generations=generations, evaluations=evaluations,
                        seed=seed)


def knee_point(pareto: Iterable[Individual]) -> Individual | None:
    """Pick a deterministic knee: highest worst-objective, then sum, then genes."""
    members = list(pareto)
    if not members:
        return None
    return max(members, key=lambda individual: (
        min(individual.objectives),
        sum(individual.objectives),
        tuple(-gene for gene in individual.genes),
    ))
