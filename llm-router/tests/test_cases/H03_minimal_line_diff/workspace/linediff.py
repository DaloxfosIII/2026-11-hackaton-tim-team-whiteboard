Op = tuple[str, str]  # ("=", line) | ("-", line) | ("+", line)


def diff(a: list[str], b: list[str]) -> list[Op]:
    """Return a minimal edit script turning a into b. Do not use difflib. See the task prompt."""
    raise NotImplementedError


def apply(a: list[str], ops: list[Op]) -> list[str]:
    raise NotImplementedError
