from datetime import datetime


def next_run(expr: str, after: datetime) -> datetime:
    """Return the first time strictly after `after` that matches the cron expression.

    Do not use third-party cron libraries. See the task prompt for the rules.
    """
    raise NotImplementedError
