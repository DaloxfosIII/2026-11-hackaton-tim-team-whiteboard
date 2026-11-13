"""
Candidate implementations of llm_router.main.predict_metrics.

Each module in this package is one candidate and must define:

    NAME = "short_name"   # optional, defaults to the module name

    def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
        ...

Quality is on the 0-5 scale from tests/quality_scale.md.
evaluate_predictions.py discovers every module here automatically.
"""
