import logging

from .ModelChoices import ModelChoice
from .MetricScores import MetricScores

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
    Quality is on the 0-5 scale from tests/quality_scale.md.
    """

    scale = 1 + len(prompt) / 1000

    return {
        "claude-haiku-5-5": MetricScores(cost=0.001 * scale, latency=0.5 * scale, quality=3.0),
        "claude-sonnet-5-5": MetricScores(cost=0.01 * scale, latency=1.5 * scale, quality=4.0),
        "claude-opus-5-5": MetricScores(cost=0.05 * scale, latency=3.0 * scale, quality=4.75),
    }


def pick_model(scores: dict[ModelChoice, MetricScores]) -> ModelChoice:
    """
    This function uses the scored predicted metrics to pick the correct model.

    Dummy implementation: best quality per dollar. Unscored quality counts as 0.
    """

    return max(scores, key=lambda model: (scores[model].quality or 0.0) / scores[model].cost)


def main() -> None:
    logging.basicConfig(level=logging.INFO)

    prompt = "Write a haiku about routers."
    logger.info("Prompt: %r", prompt)
    logger.info("Picked model: %s", route_prompt_to_model(prompt))


if __name__ == "__main__":
    main()
