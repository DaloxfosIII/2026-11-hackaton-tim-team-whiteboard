import pytest

from llm_router.main import route_prompt_to_model
from llm_router.MetricScores import MetricScores
from llm_router.Weights import PRESETS, Weights, pick_model_weighted

SCORES = {
    "claude-haiku-5-5": MetricScores(cost=0.001, latency=0.5, quality=3.0),
    "claude-sonnet-5-5": MetricScores(cost=0.01, latency=1.5, quality=4.0),
    "claude-opus-5-5": MetricScores(cost=0.05, latency=3.0, quality=4.75),
}


# Means over our 15 coding eval tasks (eval-results 2026-11-13): quality = pass rate x 5.
CODING_EVAL = {
    "claude-haiku-5-5": MetricScores(cost=0.0090, latency=39.6, quality=5 * 13 / 15),
    "claude-sonnet-5-5": MetricScores(cost=0.0742, latency=20.8, quality=5.0),
    "claude-opus-5-5": MetricScores(cost=0.1844, latency=36.5, quality=5 * 14 / 15),
}


def test_coding_preset_picks_what_won_our_coding_eval():
    assert pick_model_weighted(CODING_EVAL, PRESETS["coding"]) == "claude-sonnet-5-5"


def test_urgent_picks_fastest():
    assert pick_model_weighted(SCORES, PRESETS["urgent"]) == "claude-haiku-5-5"
    assert pick_model_weighted(CODING_EVAL, PRESETS["urgent"]) == "claude-sonnet-5-5"  # fastest there


def test_only_two_presets():
    assert set(PRESETS) == {"coding", "urgent"}


def test_tolerance_meaning():
    # Opus is +0.75 quality over Sonnet: worth it only if the full cost range is worth < ~0.94 points.
    assert pick_model_weighted(SCORES, Weights.from_tolerance(cost_points=0.5, time_points=0)) == "claude-opus-5-5"
    assert pick_model_weighted(SCORES, Weights.from_tolerance(cost_points=2.0, time_points=0)) != "claude-opus-5-5"


def test_parse():
    assert Weights.parse("urgent") == PRESETS["urgent"]
    assert Weights.parse("q=1, c=0.2, t=0.6") == Weights.parse("quality=1,cost=0.2,time=0.6") == PRESETS["urgent"]


def test_default_routing_unchanged():
    p = "Write a haiku about routers."
    assert route_prompt_to_model(p) == route_prompt_to_model(p, None)
