# Notes for agents working on this repo

## Cost and latency prediction is ready to use

`llm_router.main.predict_metrics` is still the dummy. Don't build a cost/latency predictor from scratch; plug in one of these:

- **Single questions** (`llm-router/src/llm_router/predictor.py`): `predictor.predict(predictor.default_params(), prompt)` returns `{model: {"cost", "latency"}}`. Per model it fits least squares on log cost and log latency, using `[1, log(prompt chars), explain-cue]` and the measured results in `tests/test_cases`.
  - The candidate `loglinear_cue` in `tests/predict_metrics/candidate_functions/` wraps it.
  - On `evaluate_predictions.py` (10 cases, leave-one-out) it has the lowest cost RMSE (0.0105 vs 0.0149 for the next best) and the lowest latency RMSE (7.2s vs 9.1s).
- **Coding/agent tasks** (`llm-router/src/llm_router/agentic.py`): `agentic.predict(prompt)` returns cost, latency, turns and calibrated 80% ranges (`cost_range`, `latency_range`). Use `agentic.is_agentic(prompt)` to decide which predictor applies.
  - Token use comes from 731 SWE-bench Pro Opus agent runs (`tests/agentic_data`). Model ratios and speed come from the 15 eval tasks run on all three models.
  - Accuracy: median error 46% (constant median: 51%). A single run varies about 2x either way, so prefer the ranges over the point estimate. Build and test execution time is not modelled.
  - Text TF-IDF, repo history and early-turn cost were tried and were no better.

Wiring either predictor into `predict_metrics` changes routing, so that's a team decision. Quality is still the open problem.

## Harness (all on the Claude Pro/Max login via `claude -p`, no API key needed)

- `llm-router-chat`: chat with Claude Code where every prompt goes through `route_prompt_to_model`. Logs predicted vs actual metrics to `llm-router/logs/runs.jsonl`.
- `llm-router-compare --cases`: sends every `tests/test_cases` prompt to all three models and writes a side-by-side markdown report.
- `llm-router-eval`: runs `tests/test_cases_for_later` on all three models with hidden tests, saves each model's output, and scores the router against the cheapest passing model.

## Testing

- `uv run python -m pytest tests/test_pick_model.py tests/test_router_harness.py` runs the real unit tests.
- A bare `pytest tests` also collects the hidden eval-task tests under `test_cases_for_later`, which fail by design.
