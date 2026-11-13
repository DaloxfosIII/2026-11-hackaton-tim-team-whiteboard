"""
Send every test case prompt to each model tier and write one result file per tier.

Layout (one folder per case):
    tests/test_cases/<name>/<name>.json                {"prompt": ...}
    tests/test_cases/<name>/<name>-result-<tier>.json  {"returned", "quality", "cost", "latency"}

Quality is written as null so it can be scored later.

By default only missing results are generated: a model is called for a case only
if that case has no result file for that model yet. New cases and new models are
filled in, existing results are left untouched.

Usage:
    uv run python tests/generate_results.py                # only missing results
    uv run python tests/generate_results.py --overwrite    # regenerate all results
"""

import argparse
import json
import logging
import time
from pathlib import Path

import anthropic

from llm_router.MetricScores import MetricScores
from llm_router.ModelChoices import TIERS, ModelChoice

logger = logging.getLogger(__name__)

CASES_DIR = Path(__file__).parent / "test_cases"

# List prices in USD per 1M tokens (input, output), as of 2026-11.
# Haiku's price holds for prompts up to 100K tokens, far above our test prompts.
PRICES_PER_MTOK: dict[ModelChoice, tuple[float, float]] = {
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}

# Same effort for every tier so the comparison is fair. Thinking tokens are
# billed as output tokens and therefore included in the cost.
EFFORT = "medium"
MAX_TOKENS = 16000


def run_prompt(client: anthropic.Anthropic, model: ModelChoice, prompt: str) -> tuple[str, MetricScores]:
    """Send one prompt and return the answer text plus measured cost and latency."""

    start = time.perf_counter()
    response = client.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        output_config={"effort": EFFORT},
        messages=[{"role": "user", "content": prompt}],
    )
    latency = time.perf_counter() - start

    if response.stop_reason in ("refusal", "max_tokens"):
        logger.warning("%s stopped with stop_reason=%s", model, response.stop_reason)

    text = "".join(block.text for block in response.content if block.type == "text")

    input_price, output_price = PRICES_PER_MTOK[model]
    cost = (response.usage.input_tokens * input_price + response.usage.output_tokens * output_price) / 1_000_000

    return text, MetricScores(cost=cost, latency=latency, quality=None)


def generate_results(overwrite: bool = False) -> None:
    """
    Write a result file for every (case, model) pair.

    With overwrite=False (default), pairs that already have a result file are skipped.
    With overwrite=True, every result file is regenerated.
    """

    client = anthropic.Anthropic()

    for case_dir in sorted(p for p in CASES_DIR.iterdir() if p.is_dir()):
        name = case_dir.name
        prompt = json.loads((case_dir / f"{name}.json").read_text(encoding="utf-8"))["prompt"]

        for tier, model in TIERS.items():
            result_path = case_dir / f"{name}-result-{tier}.json"
            if result_path.exists() and not overwrite:
                logger.info("skip  %-28s %-6s (exists)", name, tier)
                continue

            text, scores = run_prompt(client, model, prompt)
            result = {"returned": text, "quality": scores.quality, "cost": scores.cost, "latency": scores.latency}
            result_path.write_text(json.dumps(result, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")
            logger.info("done  %-28s %-6s $%.5f  %.2fs", name, tier, scores.cost, scores.latency)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--overwrite", action="store_true", help="regenerate result files that already exist")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")
    generate_results(overwrite=args.overwrite)


if __name__ == "__main__":
    main()
