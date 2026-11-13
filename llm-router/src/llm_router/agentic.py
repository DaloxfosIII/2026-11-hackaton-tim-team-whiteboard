"""Cost/latency prediction for agentic coding tasks (multi-turn, tool use, real repos).

1. Token usage per task (turns, output, uncached input, cache reads) is learned from 731
   SWE-bench Pro runs of an Opus agent (tests/agentic_data), as a log-linear function of
   the task text length.
2. Other models: Opus tokens x ratios measured on our own 15 eval tasks run on all three
   models with Claude Code (eval-results, Nov 2026).
3. Cost = tokens x list price. Latency = turns x sec/turn + output tokens x sec/token, also
   fitted on those eval runs. Tool execution time (builds, test suites) is NOT modelled:
   on large repos real wall time can be much longer.

    python -m llm_router.agentic     # held-out error vs a constant-median baseline
"""
import csv
import math
import random
import re
from functools import cache
from pathlib import Path
from statistics import median

from .predictor import lstsq

DATA = Path(__file__).resolve().parents[2] / "tests" / "agentic_data" / "swe_bench_pro_opus.csv"
TARGETS = ("turns", "out", "new_in", "cached")

# USD per MTok: input, output, cache read, cache write (5 min). List prices, Nov 2026.
PRICES = {"claude-opus-5-5": (4.00, 20.00, 0.20, 5.00),
          "claude-sonnet-5-5": (2.00, 10.00, 0.10, 2.50),
          "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125)}
# Token use relative to Opus on the same task (median over our 15 eval tasks).
RATIO = {"claude-opus-5-5": {"turns": 1.0, "out": 1.0, "new_in": 1.0, "cached": 1.0},
         "claude-sonnet-5-5": {"turns": 1.0, "out": 0.74, "new_in": 0.73, "cached": 0.73},
         "claude-haiku-5-5": {"turns": 1.25, "out": 1.89, "new_in": 1.09, "cached": 1.09}}
# Seconds per turn and per output token (least squares on our eval runs, ~5-9% median error there).
SPEED = {"claude-opus-5-5": (0.55, 9.09e-3), "claude-sonnet-5-5": (0.06, 7.07e-3),
         "claude-haiku-5-5": (0.15, 4.45e-3)}

CODING_CUES = {"implement", "fix", "bug", "refactor", "repository", "repo", "codebase", "function",
               "class", "test", "tests", "feature", "migrate", "endpoint", "api", "build", "module", "deploy"}


def is_agentic(prompt: str) -> bool:
    """Coding/agent task (multi-turn, tools) rather than a single question."""
    return len(prompt) > 800 or bool(set(re.findall(r"[a-z]+", prompt.lower())) & CODING_CUES)


def x(prompt_len: float) -> list[float]:
    return [1.0, math.log(prompt_len + 1)]


def load() -> list[dict]:
    with DATA.open() as f:
        return [{k: (v if k in ("instance_id", "repo_language") else float(v)) for k, v in r.items()}
                for r in csv.DictReader(f)]


def fit(rows: list[dict]) -> dict[str, list[float]]:
    X = [x(r["prompt_len"]) for r in rows]
    return {t: lstsq(X, [math.log(r[t] + 1) for r in rows]) for t in TARGETS}


@cache
def params() -> dict[str, list[float]]:
    return fit(load())


def tokens(w: dict, prompt_len: float) -> dict[str, float]:
    f = x(prompt_len)
    return {t: math.exp(sum(a * b for a, b in zip(w[t], f))) - 1 for t in TARGETS}


def price(model: str, tok: dict) -> float:
    _, out, read, write = PRICES[model]
    return (tok["out"] * out + tok["cached"] * read + tok["new_in"] * write) / 1e6


def predict(prompt: str, w: dict | None = None) -> dict[str, dict[str, float]]:
    base = tokens(w or params(), len(prompt))
    out = {}
    for m in PRICES:
        tok = {t: base[t] * RATIO[m][t] for t in TARGETS}
        per_turn, per_out = SPEED[m]
        out[m] = {"cost": price(m, tok), "latency": tok["turns"] * per_turn + tok["out"] * per_out,
                  "turns": tok["turns"]}
    return out


def holdout_report(seed: int = 0, folds: int = 5) -> str:
    """Opus cost on held-out SWE-bench Pro tasks: predictor vs constant median."""
    rows = load()
    random.Random(seed).shuffle(rows)
    model_err, base_err, within2 = [], [], []
    for k in range(folds):
        test = rows[k::folds]
        train = [r for i, r in enumerate(rows) if i % folds != k]
        w = fit(train)
        med = median(price("claude-opus-5-5", r) for r in train)
        for r in test:
            true = price("claude-opus-5-5", r)
            pred = price("claude-opus-5-5", tokens(w, r["prompt_len"]))
            model_err.append(abs(pred - true) / true)
            base_err.append(abs(med - true) / true)
            within2.append(0.5 <= pred / true <= 2)
    return (f"{len(rows)} SWE-bench Pro tasks, {folds}-fold held out, Opus cost: median abs error "
            f"{median(model_err):.0%} (constant median: {median(base_err):.0%}); "
            f"within 2x of truth: {sum(within2) / len(within2):.0%}")


if __name__ == "__main__":
    print(holdout_report())
    for p in ("Fix the off-by-one bug in chunk() in listops.py",
              "Implement OAuth login across the web app and API: " + "requirements ... " * 200):
        print(f"\n{p[:60]!r} ({len(p)} chars)")
        for m, v in predict(p).items():
            print(f"  {m:18} ${v['cost']:.3f}  {v['latency'] / 60:.1f} min  {v['turns']:.0f} turns")
