from breach.engine.graph import enumerate_simple_paths
from breach.levels.models import Component, Level


def make_level(components: list[tuple[str, str, bool]], edges: list[tuple[str, str]], entry_points: list[str]) -> Level:
    return Level(
        id="t",
        title="t",
        brief="t",
        threat_level="low",
        budget=1,
        components=[Component(id=i, type=t, label=i, asset=a) for i, t, a in components],
        edges=edges,
        entry_points=entry_points,
        cards_available=[],
    )


def test_linear_path():
    level = make_level(
        [("a", "internet", False), ("b", "x", False), ("c", "x", True)],
        [("a", "b"), ("b", "c")],
        ["a"],
    )
    assert enumerate_simple_paths(level) == [["a", "b", "c"]]


def test_branching_paths_both_found():
    level = make_level(
        [
            ("a", "internet", False),
            ("b", "x", False),
            ("c", "x", False),
            ("d", "x", True),
        ],
        [("a", "b"), ("a", "c"), ("b", "d"), ("c", "d")],
        ["a"],
    )
    assert enumerate_simple_paths(level) == [["a", "b", "d"], ["a", "c", "d"]]


def test_cycle_does_not_loop_forever_and_is_not_a_simple_path():
    level = make_level(
        [("a", "internet", False), ("b", "x", False), ("c", "x", True)],
        [("a", "b"), ("b", "a"), ("b", "c")],
        ["a"],
    )
    assert enumerate_simple_paths(level) == [["a", "b", "c"]]


def test_no_path_to_asset_returns_empty():
    level = make_level(
        [("a", "internet", False), ("b", "x", True)],
        [],
        ["a"],
    )
    assert enumerate_simple_paths(level) == []


def test_multiple_entry_points_and_assets():
    level = make_level(
        [
            ("a1", "internet", False),
            ("a2", "internet", False),
            ("b", "x", True),
            ("c", "x", True),
        ],
        [("a1", "b"), ("a2", "c")],
        ["a1", "a2"],
    )
    assert enumerate_simple_paths(level) == [["a1", "b"], ["a2", "c"]]


def test_entry_point_that_is_itself_an_asset_is_skipped():
    level = make_level(
        [("a", "internet", True), ("b", "x", True)],
        [("a", "b")],
        ["a"],
    )
    assert enumerate_simple_paths(level) == [["a", "b"]]
