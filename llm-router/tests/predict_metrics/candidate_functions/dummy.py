"""Baseline: the predict_metrics currently shipped in llm_router.main."""

from src.main import predict_metrics
from src.MetricScores import MetricScores
from src.ModelChoices import ModelChoice

NAME = "dummy"


def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
    return predict_metrics(prompt)
