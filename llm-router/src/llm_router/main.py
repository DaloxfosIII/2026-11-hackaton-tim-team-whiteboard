import logging

from .ModelChoices import ModelChoice
from .MetricScores import MetricScores
from .RoutingPolicy import DEFAULT_POLICY, RoutingPolicy

logger = logging.getLogger(__name__)


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

    Dummy implementation: fixed numbers, scaled slightly by prompt length.
    """

    scale = 1 + len(prompt) / 1000

    return {
        "claude-haiku-5-5": MetricScores(cost=0.001 * scale, latency=0.5 * scale, quality=0.6),
        "claude-sonnet-5-5": MetricScores(cost=0.01 * scale, latency=1.5 * scale, quality=0.8),
        "claude-opus-5-5": MetricScores(cost=0.05 * scale, latency=3.0 * scale, quality=0.95),
    }


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

    return max(scored, key=lambda model: (expected_reward(scored[model], policy), -scored[model].cost))


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    prompt = "Write a haiku about routers."
    logger.info("Prompt: %r", prompt)
    logger.info("Picked model: %s", route_prompt_to_model(prompt))


if __name__ == "__main__":
    main()
