"""
Linear in prompt length: per model and metric, metric = a + b * len(prompt) in characters.

Idea: longer prompts tend to be more involved questions, which get longer
(more expensive, slower) answers.
"""

from collections.abc import Sequence

from candidate_functions._linear import Predictor, fit_linear
from test_data import TestCase, load_cases

NAME = "prompt_length"


def prompt_length(prompt: str) -> float:
    return float(len(prompt))


def fit(cases: Sequence[TestCase]) -> Predictor:
    return fit_linear(cases, prompt_length)


predict = fit(load_cases())
