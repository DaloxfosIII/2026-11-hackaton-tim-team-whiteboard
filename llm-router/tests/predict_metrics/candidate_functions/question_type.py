"""
Question type: explanatory vs. matter-of-fact, predicted per model as the mean of its class.

Idea: cost and latency depend mostly on the answer's length, and explanatory
questions ("why ...", "explain ...", "compare ...") get long answers, while
matter-of-fact questions ("what is ...", "who wrote ...") get short ones.

Classification is a keyword rule. Any prompt that is not explanatory counts as
matter-of-fact, including calculations ("how many ...", "what is the probability ...").
"""

import re
from collections.abc import Sequence

from candidate_functions._linear import Predictor, fit_linear
from test_data import TestCase, load_cases

NAME = "question_type"

# Word stems that ask for reasoning, mechanisms or discussion rather than a single fact.
EXPLANATORY = re.compile(
    r"\b("
    r"why|explain\w*|describe\w*|discuss\w*|compare\w*|contrast\w*|analy[sz]\w*|evaluate\w*|"
    r"elaborate\w*|justify|argue\w*|argument\w*|counterargument\w*|present|"
    r"differences?|pros and cons|advantages|disadvantages|implications?|"
    r"how (?:does|do|did|can|could|would|is|are)"
    r")\b",
    re.IGNORECASE,
)


def is_explanatory(prompt: str) -> bool:
    return EXPLANATORY.search(prompt) is not None


def fit(cases: Sequence[TestCase]) -> Predictor:
    # With a 0/1 feature the least-squares line passes through both class means,
    # so this predicts the average of the matching class for each model and metric.
    # If the training cases contain only one class, it falls back to the overall mean.
    return fit_linear(cases, lambda prompt: float(is_explanatory(prompt)))


predict = fit(load_cases())
