class ExprError(ValueError):
    """Raised for any syntax or evaluation error."""


def evaluate(source: str, variables: dict[str, float] | None = None) -> float:
    """Evaluate an arithmetic expression. Do not use eval/exec/ast/compile. See the task prompt."""
    raise NotImplementedError
