"""Predict cost and latency per model from the measured results in tests/test_cases.

Per model, fits log(cost) and log(latency) by least squares on three prompt features:
    1, log(prompt chars), explain-cue (why / explain / causes / ... -> long answers)
Cost and latency track answer length, and answer length tracks the kind of question far
more than prompt length, hence the cue feature.

    python -m llm_router.predictor     # leave-one-out error vs a per-model median baseline
"""
import json
import math
import re
from functools import cache
from pathlib import Path
from statistics import median

CASES = Path(__file__).resolve().parents[2] / "tests" / "test_cases"
TIERS = {"haiku": "claude-haiku-5-5", "sonnet": "claude-sonnet-5-5", "opus": "claude-opus-5-5"}
EXPLAIN_CUES = {"why", "explain", "cause", "causes", "how", "describe", "compare", "discuss", "argue",
                "argument", "prove", "reason", "reasons", "difference", "evaluate", "analyze", "analyse"}


def features(prompt: str) -> list[float]:
    words = set(re.findall(r"[a-z]+", prompt.lower()))
    return [1.0, math.log(len(prompt) + 1), float(bool(words & EXPLAIN_CUES))]


def load(cases: Path = CASES) -> list[dict]:
    rows = []
    for d in sorted(p for p in cases.iterdir() if p.is_dir()):
        prompt = json.loads((d / f"{d.name}.json").read_text())["prompt"]
        for tier, model in TIERS.items():
            f = d / f"{d.name}-result-{tier}.json"
            if f.exists():
                r = json.loads(f.read_text())
                rows.append({"case": d.name, "prompt": prompt, "model": model, "cost": r["cost"],
                             "latency": r["latency"], "quality": r.get("quality")})
    return rows


def lstsq(X: list[list[float]], y: list[float], ridge: float = 1e-3) -> list[float]:
    """Solve (X^T X + ridge*I) w = X^T y by Gaussian elimination. Ridge keeps tiny samples stable."""
    n = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) + (ridge if i == j else 0.0) for j in range(n)] for i in range(n)]
    b = [sum(r[i] * t for r, t in zip(X, y)) for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda k: abs(A[k][c]))
        A[c], A[p], b[c], b[p] = A[p], A[c], b[p], b[c]
        for k in range(c + 1, n):
            f = A[k][c] / A[c][c]
            A[k] = [a - f * ac for a, ac in zip(A[k], A[c])]
            b[k] -= f * b[c]
    w = [0.0] * n
    for c in reversed(range(n)):
        w[c] = (b[c] - sum(A[c][k] * w[k] for k in range(c + 1, n))) / A[c][c]
    return w


def fit(rows: list[dict]) -> dict:
    """{model: {"cost": weights, "latency": weights}} on log scale."""
    out = {}
    for model in TIERS.values():
        rs = [r for r in rows if r["model"] == model]
        if len(rs) < 3:
            continue
        X = [features(r["prompt"]) for r in rs]
        out[model] = {k: lstsq(X, [math.log(max(r[k], 1e-9)) for r in rs]) for k in ("cost", "latency")}
    return out


def predict(params: dict, prompt: str) -> dict[str, dict[str, float]]:
    x = features(prompt)
    return {m: {k: math.exp(sum(a * b for a, b in zip(w, x))) for k, w in p.items()} for m, p in params.items()}


@cache
def default_params() -> dict:
    return fit(load())


def loo_report() -> str:
    """Leave-one-case-out median absolute % error, predictor vs per-model median baseline."""
    rows = load()
    cases = sorted({r["case"] for r in rows})
    err = {(m, k, w): [] for m in TIERS.values() for k in ("cost", "latency") for w in ("model", "baseline")}
    for c in cases:
        train, test = [r for r in rows if r["case"] != c], [r for r in rows if r["case"] == c]
        params = fit(train)
        for r in test:
            pred = predict(params, r["prompt"])[r["model"]]
            for k in ("cost", "latency"):
                base = median(t[k] for t in train if t["model"] == r["model"])
                err[r["model"], k, "model"].append(abs(pred[k] - r[k]) / r[k])
                err[r["model"], k, "baseline"].append(abs(base - r[k]) / r[k])
    lines = [f"{len(cases)} cases, leave-one-out median abs error (predictor vs median baseline)"]
    for m in TIERS.values():
        lines.append(f"  {m:18} cost {median(err[m, 'cost', 'model']):4.0%} vs {median(err[m, 'cost', 'baseline']):4.0%}"
                     f"   latency {median(err[m, 'latency', 'model']):4.0%} vs {median(err[m, 'latency', 'baseline']):4.0%}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(loo_report())
