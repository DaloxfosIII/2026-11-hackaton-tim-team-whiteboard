"""
Shared helper (not a candidate: modules starting with "_" are skipped by discovery).

fit_linear fits, per model and per metric, a one-feature least-squares line
    metric = intercept + slope * feature(prompt)
and returns a predict function. Predictions are clipped to valid ranges:
cost and latency >= 0, quality within 0-5.
"""

from collections.abc import Callable, Sequence
from statistics import mean

from src.MetricScores import MetricScores 
from src.ModelChoices import ModelChoice 
from test_data import TestCase

Predictor = Callable[[str], dict[ModelChoice, MetricScores]]
Feature = Callable[[str], float]

QUALITY_MIN, QUALITY_MAX = 0.0, 5.0


def _ols(points: list[tuple[float, float]]) -> tuple[float, float] | None:
    """Return (intercept, slope), or None without data. Constant x falls back to the mean."""

    if not points:
        return None
    xs, ys = zip(*points)
    x_mean, y_mean = mean(xs), mean(ys)
    sxx = sum((x - x_mean) ** 2 for x in xs)
    if sxx == 0:
        return y_mean, 0.0
    slope = sum((x - x_mean) * (y - y_mean) for x, y in points) / sxx
    return y_mean - slope * x_mean, slope


def fit_linear(cases: Sequence[TestCase], feature: Feature) -> Predictor:
    models = sorted({model for case in cases for model in case.actual})
    lines: dict[tuple[ModelChoice, str], tuple[float, float] | None] = {}
    for model in models:
        for metric in ("cost", "latency", "quality"):
            points = [
                (feature(case.prompt), value)
                for case in cases
                if model in case.actual and (value := getattr(case.actual[model], metric)) is not None
            ]
            lines[(model, metric)] = _ols(points)

    def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
        x = feature(prompt)

        def at(model: ModelChoice, metric: str) -> float | None:
            line = lines[(model, metric)]
            return None if line is None else line[0] + line[1] * x

        predictions = {}
        for model in models:
            cost, latency, quality = at(model, "cost"), at(model, "latency"), at(model, "quality")
            if cost is None or latency is None:
                continue  # no data for this model
            predictions[model] = MetricScores(
                cost=max(cost, 0.0),
                latency=max(latency, 0.0),
                quality=None if quality is None else min(max(quality, QUALITY_MIN), QUALITY_MAX),
            )
        return predictions

    return predict
