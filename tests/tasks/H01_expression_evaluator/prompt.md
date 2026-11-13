Implement `evaluate(source, variables=None)` in `expr.py`. It is a safe arithmetic expression evaluator that always returns a `float`. Do not use `eval`, `exec`, the builtin `compile` or the `ast` module. Keep the provided `ExprError` class and raise it (never another exception type) for every syntax or evaluation error.

Grammar and semantics. These match Python's rules for the same operators:
- Numbers: `12`, `3.5`, `.5`, `3.`, and an optional exponent `1e3`, `1.5E-2`.
- Binary operators `+ - * / % **` and unary `+` / `-`, which can repeat (`--3`).
- Precedence, from lowest to highest: `+ -`, then `* / %`, then unary `+ -`, then `**`. `**` is right-associative and binds tighter than a unary minus on its left but not on its right: `-2 ** 2 == -4`, `2 ** -1 == 0.5`, `2 ** 3 ** 2 == 512`. `%` follows Python float semantics (`-7 % 3 == 2`).
- Parentheses, and arbitrary whitespace including tabs and newlines.
- Identifiers `[A-Za-z_][A-Za-z0-9_]*` are looked up in `variables`. An unknown variable raises `ExprError` with the variable's name in the message.
- Function calls: `min(...)` and `max(...)` take one or more arguments, `abs(x)` takes exactly one. Any other function name, a wrong argument count, empty arguments (`max(1,)`) or a function name used without a call raises `ExprError`.
- Division or modulo by zero, empty input, unbalanced parentheses, dangling operators, adjacent operands (`1 2`) and unknown characters all raise `ExprError`.

Hidden tests will be run with `python -m pytest` from this directory.
