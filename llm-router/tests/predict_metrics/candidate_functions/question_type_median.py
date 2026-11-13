"""
Like question_type (explanatory vs. matter-of-fact), but predicts the class median
instead of the class mean, so one extreme case cannot pull its class up.
"""

from collections.abc import Sequence

from candidate_functions._class_median import Predictor, fit_class_median
from candidate_functions.question_type import is_explanatory
from test_data import TestCase, load_cases

NAME = "question_type_median"


def classify(prompt: str) -> str:
    return "explanatory" if is_explanatory(prompt) else "factual"


def fit(cases: Sequence[TestCase]) -> Predictor:
    return fit_class_median(cases, classify)


predict = fit(load_cases())
