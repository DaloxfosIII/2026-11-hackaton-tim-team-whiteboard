"""
Floor: predict each model's average measured cost, latency and quality, ignoring the prompt.

Any candidate that actually looks at the prompt should beat this.
"""

from collections.abc import Sequence

from candidate_functions._linear import Predictor, fit_linear
from test_data import TestCase, load_cases

NAME = "model_mean"


def fit(cases: Sequence[TestCase]) -> Predictor:
    # A constant feature makes the least-squares line the plain mean.
    return fit_linear(cases, lambda prompt: 0.0)


predict = fit(load_cases())
