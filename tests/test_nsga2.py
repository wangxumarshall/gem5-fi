"""Unit tests for the gem5-independent NSGA-II core in ``tools/nsga2.py``."""

import math
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from nsga2 import (  # noqa: E402
    crowding_distance,
    dominates,
    fast_non_dominated_sort,
    knee_point,
    run_nsga2,
)


def test_dominates_maximisation():
    assert dominates((2.0, 1.0), (1.0, 1.0))
    assert dominates((1.0, 2.0), (1.0, 1.0))
    assert not dominates((1.0, 1.0), (1.0, 1.0))
    assert not dominates((1.0, 0.0), (0.0, 1.0))
    with pytest.raises(ValueError):
        dominates((1.0,), (1.0, 2.0))


def test_fast_non_dominated_sort_orders_fronts():
    objectives = [
        (3.0, 0.0),  # front 0
        (2.0, 1.0),  # front 0
        (1.0, 2.0),  # front 0
        (0.0, 3.0),  # front 0
        (1.0, 1.0),  # dominated by (2, 1) and (1, 2)
        (0.0, 0.0),  # front 2
    ]
    fronts = fast_non_dominated_sort(objectives)
    assert fronts[0] == [0, 1, 2, 3]
    assert fronts[1] == [4]
    assert fronts[2] == [5]


def test_crowding_distance_boundaries_infinite_and_span_ordered():
    objectives = [(0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (5.0, 0.0)]
    distance = crowding_distance(objectives, [0, 1, 2, 3])
    assert distance[0] == math.inf
    assert distance[3] == math.inf
    assert 0.0 < distance[1] < distance[2] < math.inf


def test_crowding_distance_small_front():
    distance = crowding_distance([(0.0, 0.0), (1.0, 0.0)], [0, 1])
    assert distance == {0: math.inf, 1: math.inf}


def test_nsga2_finds_shifted_tradeoff_front():
    # The single gene trades off the two objectives, so every value is on the
    # Pareto front and the search must keep the whole range, not collapse to
    # the point with the highest sum.
    def objective(genes):
        return (float(genes[0]), float(3 - genes[0]))

    result = run_nsga2(objective, genome_length=1, gene_space=4,
                       population_size=24, generations=12, seed=7)
    assert result.pareto
    fronts = [(individual.genes, individual.objectives)
              for individual in result.pareto]
    for left_genes, left_obj in fronts:
        for right_genes, right_obj in fronts:
            if left_genes == right_genes:
                continue
            assert not dominates(right_obj, left_obj), (left_obj, right_obj)
    assert [genes for genes, _ in fronts] == [(0,), (1,), (2,), (3,)]


def test_nsga2_is_deterministic_and_counts_evaluations():
    def objective(genes):
        return (float(sum(genes)), float(-sum((g - 2) ** 2 for g in genes)))

    first = run_nsga2(objective, genome_length=4, gene_space=5,
                      population_size=16, generations=6, seed=123)
    second = run_nsga2(objective, genome_length=4, gene_space=5,
                       population_size=16, generations=6, seed=123)
    assert [i.genes for i in first.population] == \
           [i.genes for i in second.population]
    assert [i.objectives for i in first.pareto] == \
           [i.objectives for i in second.pareto]
    # Initial population + one full offspring batch per generation.
    assert first.evaluations == 16 * (1 + 6)


def test_nsga2_rejects_bad_arguments():
    with pytest.raises(ValueError):
        run_nsga2(lambda genes: genes, 0, 2)
    with pytest.raises(ValueError):
        run_nsga2(lambda genes: genes, 2, 1)
    with pytest.raises(ValueError):
        run_nsga2(lambda genes: genes, 2, 2, population_size=1)
    with pytest.raises(ValueError):
        run_nsga2(lambda genes: (), 2, 2)


def test_knee_point_prefers_highest_worst_objective():
    def objective(genes):
        return (float(genes[0]), float(genes[1]))

    result = run_nsga2(objective, genome_length=2, gene_space=4,
                       population_size=16, generations=6, seed=3)
    knee = knee_point(result.pareto)
    assert knee is not None
    worst = min(knee.objectives)
    assert worst == max(min(individual.objectives)
                        for individual in result.pareto)
