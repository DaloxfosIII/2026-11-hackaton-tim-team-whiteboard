import pytest

from llm_router.main import pick_model
from llm_router.MetricScores import MetricScores
from llm_router.RoutingPolicy import RoutingPolicy

DUMMY = {
    "claude-haiku-5-5": MetricScores(cost=0.001, latency=0.5, quality=0.6),
    "claude-sonnet-5-5": MetricScores(cost=0.01, latency=1.5, quality=0.8),
    "claude-opus-5-5": MetricScores(cost=0.05, latency=3.0, quality=0.95),
}


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.01, "claude-haiku-5-5"), (0.10, "claude-sonnet-5-5"), (1.00, "claude-opus-5-5")],
)
def test_pick_moves_up_tiers_as_correctness_gets_more_valuable(value, expected):
    assert pick_model(DUMMY, RoutingPolicy(value_of_correct=value)) == expected


def test_default_policy_picks_sonnet_for_dummy_scores():
    assert pick_model(DUMMY) == "claude-sonnet-5-5"


def test_latency_cost_pushes_toward_faster_model():
    policy = RoutingPolicy(value_of_correct=1.0, latency_cost_per_s=0.2)
    assert pick_model(DUMMY, policy) == "claude-haiku-5-5"


def test_tie_goes_to_cheaper_model():
    scores = {
        "claude-sonnet-5-5": MetricScores(cost=0.5, latency=1.0, quality=0.75),
        "claude-haiku-5-5": MetricScores(cost=0.25, latency=1.0, quality=0.5),
    }
    # Both rewards are exactly 1.0 * q - c = 0.25 (binary-exact values).
    assert pick_model(scores, RoutingPolicy(value_of_correct=1.0)) == "claude-haiku-5-5"


def test_unscored_models_are_skipped():
    scores = dict(DUMMY)
    scores["claude-sonnet-5-5"] = MetricScores(cost=0.01, latency=1.5, quality=None)
    assert pick_model(scores) == "claude-haiku-5-5"


def test_all_unscored_returns_fallback():
    scores = {m: MetricScores(cost=s.cost, latency=s.latency, quality=None) for m, s in DUMMY.items()}
    assert pick_model(scores) == "claude-sonnet-5-5"
    assert pick_model(scores, RoutingPolicy(fallback="claude-opus-5-5")) == "claude-opus-5-5"


def test_zero_cost_does_not_crash():
    scores = {"claude-haiku-5-5": MetricScores(cost=0.0, latency=0.5, quality=0.6)}
    assert pick_model(scores) == "claude-haiku-5-5"


def test_empty_scores_raise():
    with pytest.raises(ValueError):
        pick_model({})
