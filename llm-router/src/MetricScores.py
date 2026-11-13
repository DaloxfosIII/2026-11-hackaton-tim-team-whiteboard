
from pydantic import BaseModel


class MetricScores(BaseModel):
    cost: float # Cost in USD
    latency: float # Latency in seconds
    quality: float | None # Quality on our defined scale; None = not scored yet
