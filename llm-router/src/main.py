import logging
import re
import sys
from pathlib import Path

# Running "python src/main.py" puts src/ on sys.path, not the project root, so
# "from src.X" would fail. Add the project root so both ways of running work.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.ModelChoices import ModelChoice  # noqa: E402
from src.MetricScores import MetricScores  # noqa: E402
from src.RoutingPolicy import DEFAULT_POLICY, RoutingPolicy  # noqa: E402

logger = logging.getLogger(__name__)


def route_prompt_to_model(prompt: str) -> ModelChoice:
    """
    The wrapper function of our router. Will always return a model choice.
    """

    expected_metrics = predict_metrics(prompt)

    model_pick = pick_model(expected_metrics)

    return model_pick


# Word stems that ask for reasoning, mechanisms or discussion rather than a single fact.
_EXPLANATORY = re.compile(
    r"\b("
    r"why|explain\w*|describe\w*|discuss\w*|compare\w*|contrast\w*|analy[sz]\w*|evaluate\w*|"
    r"elaborate\w*|justify|argue\w*|argument\w*|counterargument\w*|present|"
    r"differences?|pros and cons|advantages|disadvantages|implications?|"
    r"how (?:does|do|did|can|could|would|is|are)"
    r")\b",
    re.IGNORECASE,
)

# Per-class medians of the measured results in tests/test_cases (10 cases, 2026-11-13),
# as fitted by tests/predict_metrics/candidate_functions/question_type_median.py.
# Refit and paste again when the test cases change.
_CLASS_MEDIANS: dict[str, dict[ModelChoice, MetricScores]] = {
    "explanatory": {
        "claude-haiku-5-5": MetricScores(cost=0.0005853, latency=6.307, quality=4.5),
        "claude-sonnet-5-5": MetricScores(cost=0.006388, latency=5.331, quality=4.5),
        "claude-opus-5-5": MetricScores(cost=0.018312, latency=8.721, quality=5.0),
    },
    "factual": {
        "claude-haiku-5-5": MetricScores(cost=0.0000323, latency=1.202, quality=5.0),
        "claude-sonnet-5-5": MetricScores(cost=0.000896, latency=1.316, quality=4.0),
        "claude-opus-5-5": MetricScores(cost=0.001572, latency=1.562, quality=5.0),
    },
}


def is_explanatory(prompt: str) -> bool:
    return _EXPLANATORY.search(prompt) is not None


def predict_metrics(prompt: str) -> dict[ModelChoice, MetricScores]:
    """
    This function predicts the metrics that different models will receive on our
    prompt.

    Classifies the prompt as explanatory ("why ...", "explain ...", "compare ...")
    or matter-of-fact, and returns each model's median measured cost, latency and
    quality for that class. Explanatory questions get long answers, so they cost
    roughly 10x more. Quality is on the 0-5 scale from tests/quality_scale.md.
    """

    label = "explanatory" if is_explanatory(prompt) else "factual"
    return {model: scores.model_copy() for model, scores in _CLASS_MEDIANS[label].items()}


def expected_reward(scores: MetricScores, policy: RoutingPolicy) -> float:
    """Expected net value of a call in USD. Requires a quality score."""

    assert scores.quality is not None
    return policy.value_of_correct * scores.quality - scores.cost - policy.latency_cost_per_s * scores.latency


def pick_model(
    scores: dict[ModelChoice, MetricScores],
    policy: RoutingPolicy = DEFAULT_POLICY,
) -> ModelChoice:
    """
    This function uses the scored predicted metrics to pick the correct model.

    Picks the model with the highest expected reward (see RoutingPolicy); ties go
    to the cheaper model. Models without a quality score are skipped, and if none
    has one, the policy's fallback is returned.
    """

    if not scores:
        raise ValueError("pick_model needs at least one candidate model")

    scored = {model: s for model, s in scores.items() if s.quality is not None}
    if not scored:
        logger.warning("No model has a quality score; using fallback %s", policy.fallback)
        return policy.fallback

    # Evaluate every model once and store its ranking values.
    rankings: dict[ModelChoice, tuple[float, float]] = {}
    for model, model_score in scored.items():
        reward = expected_reward(model_score, policy)
        rankings[model] = (reward, -model_score.cost)

    # Higher reward wins; on equal reward, the lower cost wins
    # (cost is negated because max() prefers larger values).
    return max(rankings, key=lambda model: rankings[model])


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    prompt = "Write a haiku about routers."
    logger.info("Prompt: %r", prompt)
    logger.info("Picked model: %s", route_prompt_to_model(prompt))


if __name__ == "__main__":
    main()
