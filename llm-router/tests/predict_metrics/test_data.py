"""
Load the test cases and their measured results.

Layout (one folder per case):
    tests/test_cases/<name>/<name>.json                {"prompt": ...}
    tests/test_cases/<name>/<name>-result-<tier>.json  {"returned", "quality", "cost", "latency"}
"""

import json
import logging
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from src.MetricScores import MetricScores
from src.ModelChoices import TIERS, ModelChoice

logger = logging.getLogger(__name__)

CASES_DIR = Path(__file__).parent.parent / "test_cases"


@dataclass(frozen=True)
class TestCase:
    name: str
    prompt: str
    actual: dict[ModelChoice, MetricScores]  # only models that have a result file


@cache
def load_cases() -> tuple[TestCase, ...]:
    """Read every case folder. Models without a result file are left out of `actual`."""

    cases = []
    for case_dir in sorted(p for p in CASES_DIR.iterdir() if p.is_dir()):
        name = case_dir.name
        prompt = json.loads((case_dir / f"{name}.json").read_text(encoding="utf-8"))["prompt"]

        actual: dict[ModelChoice, MetricScores] = {}
        for tier, model in TIERS.items():
            result_path = case_dir / f"{name}-result-{tier}.json"
            if not result_path.exists():
                logger.warning("missing result: %s %s", name, tier)
                continue
            result = json.loads(result_path.read_text(encoding="utf-8"))
            actual[model] = MetricScores(cost=result["cost"], latency=result["latency"], quality=result["quality"])

        cases.append(TestCase(name=name, prompt=prompt, actual=actual))
    return tuple(cases)
