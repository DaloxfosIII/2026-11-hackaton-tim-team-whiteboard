Implement `next_run(expr, after)` in `cron.py`. It returns the first naive `datetime` strictly after `after` (seconds and microseconds of the result are 0) that matches a cron expression. Use only the Python standard library; no cron packages.

Expression format:
- Five whitespace-separated fields: minute (0–59), hour (0–23), day-of-month (1–31), month (1–12), day-of-week (0–7, where 0 and 7 are both Sunday). Extra whitespace around or between fields is allowed.
- Each field is a comma-separated list of items. An item is `*`, a value `n`, a range `a-b` (requires `a <= b`), or any of those followed by a step `/s` with `s >= 1`. `n/s` means from `n` to the field maximum in steps of `s`.
- Month names `JAN`–`DEC` and weekday names `SUN`–`SAT` are allowed anywhere a number is, case-insensitive (`mon-fri`).
- Macros: `@hourly`, `@daily`, `@weekly` (Sunday 00:00), `@monthly`, `@yearly` and `@annually`.
- Day matching: a day-of-month or day-of-week field counts as "restricted" unless it is exactly `*`. If both are restricted, a day matches when either one matches (standard cron OR rule). Otherwise both must match.
- Raise `ValueError` for a wrong field count, out-of-range values, empty list items, a zero step, a reversed range, unknown names or unknown macros.
- If nothing matches within 8 years after `after` (e.g. `0 0 30 2 *`), raise `ValueError`.
- It must be fast: well under a second even for schedules like "Feb 29 only". Do not step minute by minute across years.

Hidden tests will be run with `python -m pytest` from this directory.
