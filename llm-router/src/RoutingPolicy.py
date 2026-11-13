from pydantic import BaseModel

from .ModelChoices import ModelChoice


class RoutingPolicy(BaseModel):
    """
    Prices that turn predicted metrics into one expected reward in USD.

    reward = value_of_correct * quality - cost - latency_cost_per_s * latency

    See "Economic Evaluation of LLMs" (arXiv 2507.03834) and "A Unified Approach
    to Routing and Cascading for LLMs" (arXiv 2410.10347).
    """

    value_of_correct: float = 0.10  # USD value of a fully correct answer (quality = 1)
    latency_cost_per_s: float = 0  # USD per second of waiting (0.008 for $30/hr)
    fallback: ModelChoice = "claude-sonnet-5-5"  # used when no model has a quality score


DEFAULT_POLICY = RoutingPolicy()
