import pathlib
import random
import re

import pytest

from expr import ExprError, evaluate


@pytest.mark.parametrize(
    "src, expected",
    [
        ("1 + 2 * 3", 7),
        ("(1 + 2) * 3", 9),
        ("10 / 4", 2.5),
        ("10 - 3 - 2", 5),
        ("2 ** 3 ** 2", 512),
        ("-2 ** 2", -4),
        ("2 ** -1", 0.5),
        ("(-2) ** 2", 4),
        ("--3", 3),
        ("+-+3", -3),
        ("7 % 3", 1),
        ("-7 % 3", 2),
        ("2 * -3", -6),
        ("1.5e2 + .5", 150.5),
        ("1E-3 * 1000", 1),
        ("max(1, 5, 3)", 5),
        ("min(4, -2)", -2),
        ("abs(-3.5)", 3.5),
        ("max(1, min(2, 3)) * 2", 4),
        ("  1\t+\n1 ", 2),
        ("2*(3+(4-1))**2", 72),
    ],
)
def test_values(src, expected):
    result = evaluate(src)
    assert isinstance(result, float)
    assert result == pytest.approx(expected)


def test_variables():
    assert evaluate("rate * qty + fee_1", {"rate": 2.5, "qty": 4, "fee_1": 1}) == 11.0
    assert evaluate("-x ** 2", {"x": 3}) == -9.0


@pytest.mark.parametrize(
    "src",
    ["", "   ", "1 +", "(1", "1)", "1 2", "foo(1)", "abs(1, 2)", "abs()", "max()",
     "x", "1 / 0", "5 % 0", "2 **", "* 3", "1 +* 2", "max(1,)", "max(,1)",
     "3 $ 4", "1..2", "abs", "(", "()"],
)
def test_errors(src):
    with pytest.raises(ExprError):
        evaluate(src)


def test_unknown_variable_message_names_it():
    with pytest.raises(ExprError, match="speed"):
        evaluate("speed * 2", {"time": 1})


def test_matches_python_on_random_expressions():
    rng = random.Random(1234)

    def gen(depth):
        if depth == 0 or rng.random() < 0.3:
            return str(rng.randint(1, 9))
        kind = rng.random()
        if kind < 0.15:
            return "-" + gen(depth - 1)
        if kind < 0.25:
            return "(" + gen(depth - 1) + ")"
        op = rng.choice(["+", "-", "*", "/"])
        return gen(depth - 1) + " " + op + " " + gen(depth - 1)

    for _ in range(300):
        src = gen(5)
        try:
            expected = float(eval(src))
        except ZeroDivisionError:
            with pytest.raises(ExprError):
                evaluate(src)
            continue
        assert evaluate(src) == pytest.approx(expected), src


def test_no_eval():
    src = (pathlib.Path(__file__).resolve().parent.parent / "expr.py").read_text()
    for banned in ("eval(", "exec(", "import ast", "from ast"):
        assert banned not in src
    assert not re.search(r"(?<![\w.])compile\(", src), "builtin compile() is not allowed"
