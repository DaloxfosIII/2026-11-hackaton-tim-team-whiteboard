
from pydantic import BaseModel


class MetricScores(BaseModel):
    cost: float # Cost in USD
    latency: float # Latency in seconds
    quality: float # Quality on our defined scale
