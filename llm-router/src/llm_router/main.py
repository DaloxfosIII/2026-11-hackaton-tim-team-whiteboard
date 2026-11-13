import logging

from .ModelChoices import ModelChoice
from .MetricScores import MetricScores
from . import agentic, predictor

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

    Cost and latency: coding/agent tasks use the agentic predictor (fitted on 731 SWE-bench Pro
    agent runs); single questions use the predictor fitted on tests/test_cases.
    Quality: still fixed guesses.
    """

    quality = {"claude-haiku-5-5": 0.6, "claude-sonnet-5-5": 0.8, "claude-opus-5-5": 0.95}
    if agentic.is_agentic(prompt):
        predicted = agentic.predict(prompt)
    else:
        predicted = predictor.predict(predictor.default_params(), prompt)

    return {
        model: MetricScores(cost=predicted[model]["cost"], latency=predicted[model]["latency"], quality=quality[model])
        for model in quality
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
