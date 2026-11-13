from pydantic import BaseModel

from .MetricScores import MetricScores
from .ModelChoices import ModelChoice


class Weights(BaseModel):
    """
    How much each metric matters for a task, e.g. 10xQuality + 3xCost + 1xTime.

    Metrics are normalized across the candidate models before weighting, so the weights
    compare like with like: quality / 5 (0-5 scale), cost / highest cost, latency / highest
    latency. score = quality_w * quality - cost_w * cost - time_w * latency; highest wins.
    """

    quality: float = 0.0
    cost: float = 0.0
    time: float = 0.0

    @classmethod
    def from_tolerance(cls, cost_points: float, time_points: float) -> "Weights":
        """
        Weights from trade-offs a person can actually state:
            cost_points: quality points (0-5 scale) worth going from the cheapest to the priciest model
            time_points: quality points worth going from the fastest to the slowest model
        """
        return cls(quality=1.0, cost=cost_points / QUALITY_MAX, time=time_points / QUALITY_MAX)

    @classmethod
    def parse(cls, text: str) -> "Weights":
        """A preset name, or explicit weights like 'q=1,c=0.2,t=0.6' (also quality=/cost=/time=)."""
        if text in PRESETS:
            return PRESETS[text]
        keys = {"q": "quality", "c": "cost", "t": "time"}
        pairs = (part.split("=") for part in text.split(",") if part.strip())
        return cls(**{keys.get(k.strip(), k.strip()): float(v) for k, v in pairs})


QUALITY_MAX = 5.0

# Presets, each set by its stated trade-off (quality points on the 0-5 scale that justify the
# priciest / the slowest model). Tune the tolerances, not the raw weights.
PRESETS: dict[str, Weights] = {
    # Coding: a failed task means a redo, so correctness dominates; half a point justifies the
    # priciest or the slowest model. On our 15 coding eval tasks (quality = pass rate x 5) this
    # picks Sonnet: 15/15 passed, vs Haiku 13/15 for 1/8 of the cost and Opus 14/15 at 2.5x.
    "coding": Weights.from_tolerance(cost_points=0.5, time_points=0.5),
    # Deadline now (e.g. a presentation in minutes): the slowest model must add 3 points, the priciest 1.
    "urgent": Weights.from_tolerance(cost_points=1.0, time_points=3.0),
}


def weighted_scores(scores: dict[ModelChoice, MetricScores], w: Weights) -> dict[ModelChoice, float]:
    """Normalized weighted score per model. Unscored quality counts as 0."""
    max_cost = max(s.cost for s in scores.values()) or 1.0
    max_latency = max(s.latency for s in scores.values()) or 1.0
    return {
        model: w.quality * (s.quality or 0.0) / QUALITY_MAX - w.cost * s.cost / max_cost - w.time * s.latency / max_latency
        for model, s in scores.items()
    }


def pick_model_weighted(scores: dict[ModelChoice, MetricScores], w: Weights) -> ModelChoice:
    """Highest weighted score; ties go to the cheaper model."""
    if not scores:
        raise ValueError("pick_model_weighted needs at least one candidate model")
    ws = weighted_scores(scores, w)
    return max(scores, key=lambda m: (ws[m], -scores[m].cost))
