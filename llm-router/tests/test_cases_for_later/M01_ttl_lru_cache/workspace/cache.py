import time


class TTLCache:
    """LRU cache whose entries also expire after a time-to-live. See the task prompt."""

    def __init__(self, capacity: int, ttl: float, clock=time.monotonic):
        raise NotImplementedError

    def get(self, key, default=None):
        raise NotImplementedError

    def set(self, key, value, ttl: float | None = None) -> None:
        raise NotImplementedError

    def delete(self, key) -> bool:
        raise NotImplementedError

    def __contains__(self, key) -> bool:
        raise NotImplementedError

    def __len__(self) -> int:
        raise NotImplementedError
