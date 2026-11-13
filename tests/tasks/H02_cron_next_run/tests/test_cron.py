import time
from datetime import datetime, timedelta

import pytest

from cron import next_run

T0 = datetime(2026, 11, 13, 10, 17, 42)  # a Friday


@pytest.mark.parametrize(
    "expr, after, expected",
    [
        ("* * * * *", T0, datetime(2026, 11, 13, 10, 18)),
        ("* * * * *", datetime(2026, 11, 13, 10, 18), datetime(2026, 11, 13, 10, 19)),
        ("30 * * * *", T0, datetime(2026, 11, 13, 10, 30)),
        ("0 * * * *", T0, datetime(2026, 11, 13, 11, 0)),
        ("0 9 * * *", T0, datetime(2026, 11, 14, 9, 0)),
        ("*/15 * * * *", T0, datetime(2026, 11, 13, 10, 30)),
        ("5-10/2 * * * *", datetime(2026, 11, 13, 10, 6), datetime(2026, 11, 13, 10, 7)),
        ("0 0 1 * *", T0, datetime(2026, 12, 1, 0, 0)),
        ("0 0 1 1 *", T0, datetime(2027, 1, 1, 0, 0)),
        ("0 12 * * MON", T0, datetime(2026, 11, 16, 12, 0)),
        ("0 12 * * 0", T0, datetime(2026, 11, 15, 12, 0)),
        ("0 12 * * 7", T0, datetime(2026, 11, 15, 12, 0)),
        ("0 12 * * mon-fri", datetime(2026, 11, 13, 12, 0), datetime(2026, 11, 16, 12, 0)),
        ("0 8 * * 1,3,5", T0, datetime(2026, 11, 16, 8, 0)),
        ("0 0 29 2 *", T0, datetime(2028, 2, 29, 0, 0)),
        ("0 0 31 * *", T0, datetime(2026, 12, 31, 0, 0)),
        ("0 0 * JAN,jul *", T0, datetime(2027, 1, 1, 0, 0)),
        ("59 23 31 12 *", T0, datetime(2026, 12, 31, 23, 59)),
        ("0 0 * * *", datetime(2026, 12, 31, 23, 59, 59), datetime(2027, 1, 1, 0, 0)),
        ("@hourly", T0, datetime(2026, 11, 13, 11, 0)),
        ("@daily", T0, datetime(2026, 11, 14, 0, 0)),
        ("@weekly", T0, datetime(2026, 11, 15, 0, 0)),
        ("@monthly", T0, datetime(2026, 12, 1, 0, 0)),
        ("@yearly", T0, datetime(2027, 1, 1, 0, 0)),
        ("  0   9  * *  * ", T0, datetime(2026, 11, 14, 9, 0)),
    ],
)
def test_next_run(expr, after, expected):
    assert next_run(expr, after) == expected


def test_dom_and_dow_both_restricted_means_or():
    # 13th of the month OR any Monday -> Monday 16 Nov comes before 13 Dec
    assert next_run("0 0 13 * 1", T0) == datetime(2026, 11, 16, 0, 0)
    # 1st of month OR Friday -> next Friday 20 Nov comes before 1 Dec
    assert next_run("0 0 1 * 5", T0) == datetime(2026, 11, 20, 0, 0)


def test_only_dom_restricted():
    assert next_run("0 0 13 * *", T0) == datetime(2026, 12, 13, 0, 0)


def test_step_in_dom_counts_as_restricted():
    # "*/10" is not exactly "*", so DOM and DOW are OR-ed: day 1,11,21,31 OR Sunday
    assert next_run("0 0 */10 * 0", T0) == datetime(2026, 11, 15, 0, 0)


def test_result_has_zero_seconds_and_micro():
    r = next_run("* * * * *", datetime(2026, 1, 1, 0, 0, 0, 999999))
    assert r == datetime(2026, 1, 1, 0, 1)


def test_impossible_schedule_raises():
    with pytest.raises(ValueError):
        next_run("0 0 30 2 *", T0)


@pytest.mark.parametrize(
    "expr",
    ["", "* * * *", "* * * * * *", "60 * * * *", "* 24 * * *", "* * 0 * *", "* * 32 * *",
     "* * * 13 *", "* * * * 8", "*/0 * * * *", "10-5 * * * *", "a * * * *", "1,,2 * * * *",
     "* * * FOO *", "@sometimes"],
)
def test_invalid(expr):
    with pytest.raises(ValueError):
        next_run(expr, T0)


def test_matches_brute_force():
    def brute(expr_fields, after):
        mins, hours, doms, months, dows, dom_star, dow_star = expr_fields
        t = after.replace(second=0, microsecond=0) + timedelta(minutes=1)
        while True:
            dow = (t.weekday() + 1) % 7
            dom_ok, dow_ok = t.day in doms, dow in dows
            day_ok = (dom_ok and dow_ok) if (dom_star or dow_star) else (dom_ok or dow_ok)
            if t.minute in mins and t.hour in hours and t.month in months and day_ok:
                return t
            t += timedelta(minutes=1)

    cases = [
        ("*/7 3-5 * * *", ({*range(0, 60, 7)}, {3, 4, 5}, set(range(1, 32)), set(range(1, 13)), set(range(7)), True, True)),
        ("0,30 */6 10-12 * *", ({0, 30}, {0, 6, 12, 18}, {10, 11, 12}, set(range(1, 13)), set(range(7)), False, True)),
        ("15 14 * * 2-4", ({15}, {14}, set(range(1, 32)), set(range(1, 13)), {2, 3, 4}, True, False)),
        ("0 0 5 * 6", ({0}, {0}, {5}, set(range(1, 13)), {6}, False, False)),
    ]
    starts = [T0, datetime(2026, 2, 27, 23, 59), datetime(2027, 12, 31, 12, 0)]
    for expr, fields in cases:
        for s in starts:
            assert next_run(expr, s) == brute(fields, s), (expr, s)


def test_fast_enough():
    start = time.perf_counter()
    next_run("0 0 29 2 1", datetime(2026, 3, 1))  # Feb 29 OR Monday
    next_run("0 0 29 2 *", datetime(2026, 3, 1))  # only leap days
    assert time.perf_counter() - start < 1.0
