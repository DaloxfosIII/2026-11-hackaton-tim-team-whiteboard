# Agentic cost data

`swe_bench_pro_opus.csv`: one row per SWE-bench Pro task (731), derived from

- per-turn token counts of Claude Opus 4.7 agent runs: [netpreme/coding_agent_traces](https://huggingface.co/datasets/netpreme/coding_agent_traces), config `opus-pro`
- task text lengths: [ScaleAI/SWE-bench_Pro](https://huggingface.co/datasets/ScaleAI/SWE-bench_Pro), config `v1`

Columns: `prompt_len` = characters of problem statement + requirements + interface; `turns`; token sums over the run:
`out` (output), `new_in` (uncached input, priced as cache write), `cached` (cache-read input).
No wall-clock times are in the source; latency is modelled from turns and output tokens (see `predictor.py`).
