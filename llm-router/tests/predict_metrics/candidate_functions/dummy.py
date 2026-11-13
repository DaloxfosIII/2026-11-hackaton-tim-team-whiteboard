"""Baseline: the predict_metrics currently shipped in llm_router.main."""

from llm_router.main import predict_metrics
from llm_router.MetricScores import MetricScores
from llm_router.ModelChoices import ModelChoice

NAME = "dummy"


def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
    return predict_metrics(prompt)
