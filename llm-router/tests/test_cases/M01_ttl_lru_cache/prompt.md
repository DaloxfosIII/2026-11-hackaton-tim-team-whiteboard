Implement the `TTLCache` class in `cache.py`: an LRU cache whose entries also expire. Use only the Python standard library.

- `TTLCache(capacity, ttl, clock=time.monotonic)`. `capacity` must be at least 1 and `ttl` must be greater than 0, otherwise raise `ValueError`. `clock` is a zero-argument callable returning seconds. Always use it instead of reading the time directly; the tests inject a fake clock.
- `set(key, value, ttl=None)` stores a value that expires `ttl` seconds from now (the cache default if `None`). An entry set at time `t` with ttl `x` is live while `clock() < t + x` and expired once `clock() >= t + x`. Setting an existing key replaces its value, resets its expiry and makes it most recently used.
- When inserting a new key into a full cache, first drop all expired entries. If it is still full, evict the least recently used live entry.
- `get(key, default=None)` returns the value, or `default` if the key is missing or expired. A successful `get` makes the entry most recently used. It does not extend its TTL.
- `key in cache` is `True` only for live entries and does not change recency.
- `delete(key)` removes the entry. It returns `True` if a live entry was removed and `False` otherwise.
- `len(cache)` counts only live entries.
- `None` is a valid stored value.

Hidden tests will be run with `python -m pytest` from this directory.
