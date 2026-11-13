from typing import Literal, get_args

## Definition of possible models.
## A Literal type is type safe (checkers reject any other string), and the
## runtime set is derived from it so both can never drift apart.
ModelChoice = Literal[
    "claude-haiku-5.5",
    "claude-sonnet-5.5",
    "claude-opus-5.5",
]

ModelChoices: frozenset[str] = frozenset(get_args(ModelChoice))
