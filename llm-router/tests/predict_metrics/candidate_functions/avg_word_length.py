"""
Linear in average word length: per model and metric, metric = a + b * mean word length.

Idea: longer words hint at technical or academic vocabulary, i.e. harder topics.
Words are runs of letters/digits, so punctuation does not inflate the length.
"""

import re
from collections.abc import Sequence

from candidate_functions._linear import Predictor, fit_linear
from test_data import TestCase, load_cases

NAME = "avg_word_length"

WORD = re.compile(r"\w+")


def avg_word_length(prompt: str) -> float:
    words = WORD.findall(prompt)
    return sum(map(len, words)) / len(words) if words else 0.0


def fit(cases: Sequence[TestCase]) -> Predictor:
    return fit_linear(cases, avg_word_length)


predict = fit(load_cases())
