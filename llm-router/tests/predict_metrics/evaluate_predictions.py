"""
Run every candidate prediction function over the test cases and compare its
predictions with the measured results, per model and per metric.

Candidates that define fit(cases) are scored leave-one-out: each case is
predicted by a version fitted on all other cases, so fitting cannot simply
memorize the answer. Candidates with only predict() are scored as they are.

Error measure: squared residual (predicted - actual)^2, aggregated as
MSE and RMSE (RMSE is in the metric's own unit: USD, seconds, quality points).
Only compare a metric across candidates, not metrics with each other: their
scales differ by orders of magnitude.

Writes an Excel report with three sheets:
    Summary    one row per candidate
    By model   one row per candidate and model
    Details    one row per candidate, case and model with predicted, actual, residual

Usage:
    uv run python tests/predict_metrics/evaluate_predictions.py
    uv run python tests/predict_metrics/evaluate_predictions.py --out report.xlsx
"""

import argparse
import importlib
import logging
import math
import pkgutil
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))  # llm-router/, so `src` imports

import candidate_functions  # noqa: E402
from src.MetricScores import MetricScores  # noqa: E402
from src.ModelChoices import ModelChoice  # noqa: E402
from test_data import TestCase, load_cases

logger = logging.getLogger(__name__)

METRICS = ("cost", "latency", "quality")
RESULTS_DIR = Path(__file__).parent / "results"
BEST_FILL = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")

Predictor = Callable[[str], dict[ModelChoice, MetricScores]]
Fitter = Callable[[Sequence[TestCase]], Predictor]


@dataclass(frozen=True)
class Candidate:
    predict: Predictor
    fit: Fitter | None  # present -> scored leave-one-out

    @property
    def evaluation(self) -> str:
        return "leave-one-out" if self.fit is not None else "as is"


def discover_candidates() -> dict[str, Candidate]:
    """Import every module in candidate_functions and return {NAME: candidate}. Skips modules starting with "_"."""

    candidates: dict[str, Candidate] = {}
    for module_info in sorted(pkgutil.iter_modules(candidate_functions.__path__), key=lambda m: m.name):
        if module_info.name.startswith("_"):
            continue
        try:
            module = importlib.import_module(f"candidate_functions.{module_info.name}")
        except Exception:
            logger.exception("could not import candidate %s, skipping it", module_info.name)
            continue

        predict = getattr(module, "predict", None)
        if not callable(predict):
            logger.warning("candidate %s has no predict() function, skipping it", module_info.name)
            continue

        name = getattr(module, "NAME", module_info.name)
        if name in candidates:
            logger.warning("duplicate candidate name %r in %s, skipping it", name, module_info.name)
            continue
        fit = getattr(module, "fit", None)
        candidates[name] = Candidate(predict=predict, fit=fit if callable(fit) else None)
    return candidates


def evaluate(candidates: dict[str, Candidate], cases: tuple[TestCase, ...]) -> pd.DataFrame:
    """One row per (candidate, case, model) with predicted, actual and squared residual per metric."""

    rows = []
    for name, candidate in candidates.items():
        for case in cases:
            error = None
            try:
                if candidate.fit is not None:
                    predict = candidate.fit([other for other in cases if other is not case])
                else:
                    predict = candidate.predict
                predictions = predict(case.prompt)
            except Exception as exc:
                logger.warning("%s failed on %s: %r", name, case.name, exc)
                predictions, error = {}, repr(exc)

            for model, actual in case.actual.items():
                predicted = predictions.get(model)
                row = {"candidate": name, "evaluation": candidate.evaluation, "case": case.name, "model": model, "error": error}
                for metric in METRICS:
                    p = getattr(predicted, metric) if predicted is not None else None
                    a = getattr(actual, metric)
                    row[f"{metric}_predicted"] = p
                    row[f"{metric}_actual"] = a
                    row[f"{metric}_sq_residual"] = (p - a) ** 2 if p is not None and a is not None else None
                rows.append(row)

    return pd.DataFrame(rows)


def summarize(details: pd.DataFrame, by: list[str]) -> pd.DataFrame:
    """Aggregate squared residuals into MSE, RMSE and counts per group."""

    def aggregate(group: pd.DataFrame) -> pd.Series:
        out = {}
        for metric in METRICS:
            sq = group[f"{metric}_sq_residual"].dropna()
            mse = sq.mean() if len(sq) else math.nan
            out[f"{metric}_MSE"] = mse
            out[f"{metric}_RMSE"] = math.sqrt(mse) if len(sq) else math.nan
            out[f"{metric}_n"] = len(sq)
            # Actual value exists but the candidate gave no prediction for it.
            out[f"{metric}_missing"] = int(
                (group[f"{metric}_actual"].notna() & group[f"{metric}_predicted"].isna()).sum()
            )
        out["errors"] = int(group["error"].notna().sum())
        return pd.Series(out)

    return details.groupby(by, sort=False)[details.columns.drop(by)].apply(aggregate).reset_index()


def write_report(path: Path, summary: pd.DataFrame, by_model: pd.DataFrame, details: pd.DataFrame) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Summary", index=False)
        by_model.to_excel(writer, sheet_name="By model", index=False)
        details.to_excel(writer, sheet_name="Details", index=False)

        for sheet_name, df in (("Summary", summary), ("By model", by_model), ("Details", details)):
            ws = writer.sheets[sheet_name]
            ws.freeze_panes = "B2"
            for cell in ws[1]:
                cell.font = Font(bold=True)
            for i, column in enumerate(df.columns, start=1):
                width = max(len(str(column)), *(len(f"{v:.6g}" if isinstance(v, float) else str(v)) for v in df[column]))
                ws.column_dimensions[get_column_letter(i)].width = min(width + 2, 60)

        # Mark the lowest error per metric: across candidates in Summary,
        # and across candidates for the same model in By model.
        highlight_best(writer.sheets["Summary"], summary, groups=None)
        highlight_best(writer.sheets["By model"], by_model, groups="model")


def highlight_best(ws, df: pd.DataFrame, groups: str | None) -> None:
    error_columns = [c for c in df.columns if c.endswith(("_MSE", "_RMSE"))]
    for column in error_columns:
        col_idx = df.columns.get_loc(column) + 1 # ty: ignore
        grouped = [df] if groups is None else [g for _, g in df.groupby(groups, sort=False)]
        for group in grouped:
            values = group[column].dropna()
            if values.empty:
                continue
            best = values.min()
            for row_idx in values.index[values == best]:
                ws.cell(row=row_idx + 2, column=col_idx).fill = BEST_FILL  # +1 header, +1 one-based


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, help="output .xlsx path (default: results/prediction_eval_<timestamp>.xlsx)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(message)s")

    cases = load_cases()
    candidates = discover_candidates()
    if not candidates:
        raise SystemExit("no candidates found in candidate_functions/")
    logger.info("%d cases, candidates: %s", len(cases), ", ".join(candidates))

    details = evaluate(candidates, cases)
    summary = summarize(details, by=["candidate", "evaluation"])
    by_model = summarize(details, by=["candidate", "evaluation", "model"]).sort_values(["model", "candidate"], ignore_index=True)

    out = args.out or RESULTS_DIR / f"prediction_eval_{datetime.now():%Y-%m-%d_%H-%M-%S}.xlsx"
    write_report(out, summary, by_model, details)

    with pd.option_context("display.width", 200, "display.float_format", "{:.6g}".format):
        print(summary[["candidate", "evaluation", *(f"{m}_RMSE" for m in METRICS), "errors"]].to_string(index=False))
    logger.info("report written to %s", out)


if __name__ == "__main__":
    main()
