import logging
import re

from .ModelChoices import ModelChoice
from .MetricScores import MetricScores

logger = logging.getLogger(__name__)

# Dummy router: keyword + length heuristics, so routing is visible end to end before a
# real predictor exists. Replace predict_metrics with a model trained on eval-task results.
HARD_WORDS = {"refactor", "architecture", "design", "migrate", "migration", "concurrency", "race",
              "parser", "algorithm", "optimize", "security", "multifile", "debug", "legacy"}
EASY_WORDS = {"rename", "typo", "format", "comment", "docstring", "explain", "what", "list",
              "summarize", "translate", "hello", "hi"}

# Per model: (base quality, quality lost per unit of difficulty, $ per call, seconds per call)
PROFILE: dict[ModelChoice, tuple[float, float, float, float]] = {
    "claude-haiku-5-5": (0.90, 0.30, 0.002, 2.0),
    "claude-sonnet-5-5": (0.95, 0.15, 0.02, 6.0),
    "claude-opus-5-5": (0.98, 0.05, 0.04, 10.0),
}
QUALITY_BAR = 0.80  # pick the cheapest model predicted to clear this


def difficulty(prompt: str) -> float:
    """0 = trivial, ~1 = typical coding task, 2+ = hard."""
    words = set(re.findall(r"[a-z]+", prompt.lower()))
    score = 0.5 + min(len(prompt) / 1500, 1.0)
    score += 0.6 * len(words & HARD_WORDS) - 0.4 * len(words & EASY_WORDS)
    return max(score, 0.0)


def route_prompt_to_model(prompt: str) -> ModelChoice:
    """
    The wrapper function of our router. Will always return a model choice.
    """

    expected_metrics = predict_metrics(prompt)

    model_pick = pick_model(expected_metrics)

    return model_pick


def predict_metrics(prompt: str) -> dict[ModelChoice, MetricScores]:
    """
    This function predicts the metrics that different models will receive on our
    prompt.

    Dummy implementation: quality falls with difficulty, fastest for small models;
    cost and latency grow with prompt length.
    """

    d = difficulty(prompt)
    scale = 1 + len(prompt) / 1000
    return {
        model: MetricScores(cost=cost * scale, latency=lat * scale, quality=max(base - drop * d, 0.0))
        for model, (base, drop, cost, lat) in PROFILE.items()
    }


def pick_model(scores: dict[ModelChoice, MetricScores]) -> ModelChoice:
    """
    This function uses the scored predicted metrics to pick the correct model.

    Dummy implementation: cheapest model predicted to clear QUALITY_BAR,
    else the highest predicted quality.
    """

    good = [m for m in scores if (scores[m].quality or 0.0) >= QUALITY_BAR]
    if good:
        return min(good, key=lambda m: scores[m].cost)
    return max(scores, key=lambda m: scores[m].quality or 0.0)


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    for prompt in ("Fix the typo in the README", "Write a function that merges two sorted lists",
                   "Refactor the legacy parser for concurrency and design a migration plan"):
        logger.info("%-75r -> %s (difficulty %.2f)", prompt, route_prompt_to_model(prompt), difficulty(prompt))


if __name__ == "__main__":
    main()
