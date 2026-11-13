"""
Candidate implementations of llm_router.main.predict_metrics.

Each module in this package is one candidate and must define:

    NAME = "short_name"   # optional, defaults to the module name

    def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
        ...

Optionally, a candidate that learns from the test data also defines

    def fit(cases: Sequence[TestCase]) -> Callable[[str], dict[ModelChoice, MetricScores]]:
        ...

and the evaluator then scores it leave-one-out (each case predicted by a version
fitted on all other cases). `predict` should be fit(load_cases()), i.e. trained on all cases.
Modules starting with "_" are helpers, not candidates.

Quality is on the 0-5 scale from tests/quality_scale.md.
evaluate_predictions.py discovers every module here automatically.
"""
