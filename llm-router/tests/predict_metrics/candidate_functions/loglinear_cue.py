"""
Per model, log(cost) and log(latency) as least squares on [1, log(prompt chars), explain-cue],
see llm_router/predictor.py. Fitting in log space keeps predictions positive and handles the
100x spread between one-line facts and long explanations. Quality: per-model mean.
"""

from collections.abc import Sequence
from statistics import mean

from llm_router import predictor
from llm_router.MetricScores import MetricScores
from llm_router.ModelChoices import ModelChoice
from test_data import TestCase, load_cases

NAME = "loglinear_cue"


def fit(cases: Sequence[TestCase]):
    rows = [{"prompt": c.prompt, "model": m, "cost": s.cost, "latency": s.latency}
            for c in cases for m, s in c.actual.items()]
    params = predictor.fit(rows)
    quality = {m: mean(q) for m in params
               if (q := [c.actual[m].quality for c in cases if m in c.actual and c.actual[m].quality is not None])}

    def predict(prompt: str) -> dict[ModelChoice, MetricScores]:
        p = predictor.predict(params, prompt)
        return {m: MetricScores(cost=v["cost"], latency=v["latency"], quality=quality.get(m)) for m, v in p.items()}

    return predict


predict = fit(load_cases())
