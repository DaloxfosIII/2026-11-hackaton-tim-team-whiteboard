from typing import Literal, get_args

## Definition of possible models.
## A Literal type is type safe (checkers reject any other string), and the
## runtime set is derived from it so both can never drift apart.
## The strings are the exact Claude API model IDs.
ModelChoice = Literal[
    "claude-haiku-5-5",
    "claude-sonnet-5-5",
    "claude-opus-5-5",
]

ModelChoices: frozenset[str] = frozenset(get_args(ModelChoice))

## Short tier names used in test result file names (<case>-result-<tier>.json).
TIERS: dict[str, ModelChoice] = {
    "haiku": "claude-haiku-5-5",
    "sonnet": "claude-sonnet-5-5",
    "opus": "claude-opus-5-5",
}
