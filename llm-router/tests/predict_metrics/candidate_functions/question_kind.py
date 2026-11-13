"""
Three question kinds, predicted per model as the class median:

    puzzle       reasoning or calculation tasks: the model has to work something
                 out, which costs thinking tokens even if the final answer is short
    explanatory  asks for reasoning, mechanisms or discussion: long answers
    factual      everything else: short answers

Puzzle wins over explanatory when both match (e.g. "How many ...? Explain why."):
working out the answer is the core of the task, the explanation is a by-product.
"""

import re
from collections.abc import Sequence

from candidate_functions._class_median import Predictor, fit_class_median
from candidate_functions.question_type import is_explanatory
from test_data import TestCase, load_cases

NAME = "question_kind"

# Words that signal counting, calculating or logical/probabilistic reasoning.
PUZZLE_WORDS = re.compile(
    r"\b("
    r"probability|probabilit\w+|chance|odds|expected value|"
    r"how (?:many|much|long|far|often)|"
    # Explicit verb forms: an open stem like compute\w* would also match "computer".
    r"calculat(?:e|es|ed|ing|ion)|comput(?:e|es|ed|ing|ation)|solv(?:e|es|ed|ing)|prove|"
    r"puzzle\w*|riddle\w*|paradox\w*"
    r")\b",
    re.IGNORECASE,
)
# Numbers in the prompt (14:45, 2, 24-hour): word problems carry their data as numbers.
NUMBER = re.compile(r"\d+(?:[.,:]\d+)?")
MIN_NUMBERS_FOR_PUZZLE = 2


def is_puzzle(prompt: str) -> bool:
    return PUZZLE_WORDS.search(prompt) is not None or len(NUMBER.findall(prompt)) >= MIN_NUMBERS_FOR_PUZZLE


def classify(prompt: str) -> str:
    if is_puzzle(prompt):
        return "puzzle"
    if is_explanatory(prompt):
        return "explanatory"
    return "factual"


def fit(cases: Sequence[TestCase]) -> Predictor:
    return fit_class_median(cases, classify)


predict = fit(load_cases())
