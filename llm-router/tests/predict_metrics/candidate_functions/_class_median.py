"""
Shared helper (not a candidate: modules starting with "_" are skipped by discovery).

fit_class_median sorts prompts into classes and predicts, per model and metric,
the median of the training cases in the same class. The median keeps a single
extreme case from dragging the whole class up, unlike the mean.
If a class has no training cases, it falls back to the model's overall median.
"""

from collections.abc import Callable, Sequence
from statistics import median

from llm_router.MetricScores import MetricScores
from llm_router.ModelChoices import ModelChoice
from test_data import TestCase

Predictor = Callable[[str], dict[ModelChoice, MetricScores]]
Classifier = Callable[[str], str]

METRICS = ("cost", "latency", "quality")


def _medians(results: list[MetricScores]) -> dict[str, float | None]:
    out: dict[str, float | None] = {}
    for metric in METRICS:
        values = [v for r in results if (v := getattr(r, metric)) is not None]
        out[metric] = median(values) if values else None
    return out


def fit_class_median(cases: Sequence[TestCase], classify: Classifier) -> Predictor:
    by_class: dict[tuple[ModelChoice, str], list[MetricScores]] = {}
    by_model: dict[ModelChoice, list[MetricScores]] = {}
    for case in cases:
        label = classify(case.prompt)
        for model, scores in case.actual.items():
            by_class.setdefault((model, label), []).append(scores)
            by_model.setdefault(model, []).append(scores)

    class_medians = {key: _medians(results) for key, results in by_class.items()}
    overall_medians = {model: _medians(results) for model, results in by_model.items()}

    def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
        label = classify(prompt)
        predictions = {}
        for model, overall in overall_medians.items():
            m = class_medians.get((model, label), overall)
            predictions[model] = MetricScores(
                cost=m["cost"],
                latency=m["latency"],
                quality=m["quality"] if m["quality"] is not None else overall["quality"],
            )
        return predictions

    return predict
