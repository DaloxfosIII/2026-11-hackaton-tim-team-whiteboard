import random

import pytest

from graph import CycleError, topo_sort


def assert_valid_order(deps, order):
    nodes = set(deps) | {d for ds in deps.values() for d in ds}
    assert sorted(order) == sorted(nodes)
    pos = {n: i for i, n in enumerate(order)}
    for n, ds in deps.items():
        for d in ds:
            assert pos[d] < pos[n]


def assert_real_cycle(deps, cycle):
    assert len(cycle) >= 2 and cycle[0] == cycle[-1]
    assert len(set(cycle[:-1])) == len(cycle) - 1
    for a, b in zip(cycle, cycle[1:]):
        assert b in deps.get(a, []), f"{a} does not depend on {b}"


def test_simple_chain():
    assert topo_sort({"c": ["b"], "b": ["a"]}) == ["a", "b", "c"]


def test_lexicographically_smallest_order():
    deps = {"d": ["b", "a"], "c": [], "b": [], "a": []}
    assert topo_sort(deps) == ["a", "b", "c", "d"]
    assert topo_sort({"b": [], "a": ["b"], "c": []}) == ["b", "a", "c"]


def test_nodes_only_in_deps_included():
    assert topo_sort({"app": ["lib", "util"]}) == ["lib", "util", "app"]


def test_empty():
    assert topo_sort({}) == []


def test_duplicate_deps_ok():
    assert topo_sort({"b": ["a", "a"]}) == ["a", "b"]


def test_self_cycle():
    with pytest.raises(CycleError) as e:
        topo_sort({"a": ["a"]})
    assert e.value.cycle == ["a", "a"]


def test_cycle_reported():
    deps = {"a": ["b"], "b": ["c"], "c": ["a"], "x": [], "y": ["x"]}
    with pytest.raises(CycleError) as e:
        topo_sort(deps)
    assert_real_cycle(deps, e.value.cycle)
    assert set(e.value.cycle) == {"a", "b", "c"}


def test_cycle_downstream_of_acyclic_part():
    deps = {"top": ["m1"], "m1": ["m2"], "m2": ["m3"], "m3": ["m1"], "m1x": ["base"]}
    with pytest.raises(CycleError) as e:
        topo_sort(deps)
    assert_real_cycle(deps, e.value.cycle)
    assert set(e.value.cycle) == {"m1", "m2", "m3"}


def test_random_dags():
    rng = random.Random(7)
    for _ in range(50):
        n = rng.randint(1, 40)
        names = [f"n{i:02d}" for i in range(n)]
        rng.shuffle(names)
        deps = {names[i]: rng.sample(names[:i], rng.randint(0, min(i, 4))) for i in range(n)}
        assert_valid_order(deps, topo_sort(deps))


def test_large_graph_is_fast():
    n = 20000
    deps = {f"n{i}": [f"n{i - 1}"] if i else [] for i in range(n)}
    order = topo_sort(deps)
    assert len(order) == n
