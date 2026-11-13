"""
Floor: predict each model's average measured cost, latency and quality, ignoring the prompt.

Any candidate that actually looks at the prompt should beat this. The averages are
computed from the same test cases it is evaluated on, so its score is optimistic.
"""

from statistics import mean

from llm_router.MetricScores import MetricScores
from llm_router.ModelChoices import ModelChoice
from test_data import load_cases

NAME = "model_mean"


def _averages() -> dict[ModelChoice, MetricScores]:
    by_model: dict[ModelChoice, list[MetricScores]] = {}
    for case in load_cases():
        for model, scores in case.actual.items():
            by_model.setdefault(model, []).append(scores)

    averages = {}
    for model, results in by_model.items():
        qualities = [r.quality for r in results if r.quality is not None]
        averages[model] = MetricScores(
            cost=mean(r.cost for r in results),
            latency=mean(r.latency for r in results),
            quality=mean(qualities) if qualities else None,
        )
    return averages


_AVERAGES = _averages()


def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
    return dict(_AVERAGES)
