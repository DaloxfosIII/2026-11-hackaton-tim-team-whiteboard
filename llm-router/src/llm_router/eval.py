"""Run eval-tasks on every model, save each model's output, and score the router against it.

    llm-router-eval                                   # all tasks x haiku/sonnet/opus x 1 run
    llm-router-eval --tasks E01_slugify,H04_json_patch --runs 3
    llm-router-eval --report eval-results/<run-dir>   # re-print the report

Per task/model/run the output dir holds:
    answer.md        the model's final message
    changes.diff     what it changed in the workspace
    tests.txt        hidden-test output (tests are copied in only after the agent exits)
    claude.json      raw Claude Code result (cost, usage, timings)
results.jsonl and report.md sit at the top of the run dir.
"""
import argparse
import asyncio
import difflib
import json
import os
import re
import shutil
import time
from collections import defaultdict
from pathlib import Path
from statistics import mean

from .chat import CLAUDE_BIN, CLI_MODEL, SHORT
from .main import route_prompt_to_model

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "eval-tasks"
ALLOWED = ["Read", "Edit", "Write", "Glob", "Grep", "Bash(python:*)", "Bash(python3:*)", "Bash(ls:*)", "Bash(cat:*)"]


def env() -> dict:
    e = dict(os.environ)
    e.pop("ANTHROPIC_API_KEY", None)  # use the Claude Pro/Max login
    return e


def snapshot(d: Path) -> dict[str, str]:
    return {str(p.relative_to(d)): p.read_text(errors="replace") for p in sorted(d.rglob("*"))
            if p.is_file() and "__pycache__" not in p.parts}


def diff(before: dict, after: dict) -> str:
    out = []
    for f in sorted(before.keys() | after.keys()):
        out += difflib.unified_diff(before.get(f, "").splitlines(True), after.get(f, "").splitlines(True),
                                    f"a/{f}", f"b/{f}")
    return "".join(out)


async def sh(cmd: list[str], cwd: Path, timeout: int, **kw) -> tuple[int, str, str]:
    p = await asyncio.create_subprocess_exec(*cmd, cwd=cwd, stdout=-1, stderr=-1, **kw)
    try:
        out, err = await asyncio.wait_for(p.communicate(), timeout)
    except TimeoutError:
        p.kill()
        return 124, "", f"timeout after {timeout}s"
    return p.returncode, out.decode(errors="replace"), err.decode(errors="replace")


async def one(task: dict, model: str, run: int, out: Path, test_cmd: str, timeout: int) -> dict:
    tdir, rdir = TASKS / "tasks" / task["id"], out / task["id"] / model.split("-")[1] / f"r{run}"
    work = rdir / "work"
    shutil.copytree(tdir / "workspace", work)
    before, prompt = snapshot(work), (tdir / "prompt.md").read_text()

    t0 = time.perf_counter()
    code, stdout, stderr = await sh(
        [CLAUDE_BIN, "-p", prompt, "--model", CLI_MODEL[model], "--output-format", "json",
         "--permission-mode", "dontAsk", "--allowedTools", *ALLOWED, "--strict-mcp-config",
         "--no-session-persistence", "--setting-sources", "project"], work, timeout, env=env())
    wall = time.perf_counter() - t0
    try:
        res = json.loads(stdout)
    except json.JSONDecodeError:
        res = {"is_error": True, "result": f"claude exit {code}: {stderr[-2000:]}"}

    (rdir / "claude.json").write_text(json.dumps(res, indent=2))
    (rdir / "answer.md").write_text(res.get("result") or "")
    (rdir / "changes.diff").write_text(diff(before, snapshot(work)))

    shutil.rmtree(work / "tests", ignore_errors=True)  # hidden tests go in only now
    shutil.copytree(tdir / "tests", work / "tests")
    tcode, tout, terr = await sh(test_cmd.split(), work, 300)
    (rdir / "tests.txt").write_text(tout + terr)
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", tout)) else 0
    failed = sum(int(n) for n in re.findall(r"(\d+) (?:failed|error)", tout))
    return {"task": task["id"], "difficulty": task["difficulty"], "category": task["category"], "model": model,
            "run": run, "pass": tcode == 0, "tests_passed": passed, "tests_total": passed + failed,
            "cost": res.get("total_cost_usd") or 0.0, "latency": wall,
            "ttft": (res.get("ttft_ms") or 0) / 1000, "turns": res.get("num_turns"),
            "is_error": bool(res.get("is_error")), "dir": str(rdir.relative_to(out))}


def report(rows: list[dict], tasks: list[dict]) -> str:
    models = sorted({r["model"] for r in rows}, key=lambda m: ["haiku", "sonnet", "opus"].index(m.split("-")[1]))
    by = defaultdict(list)
    for r in rows:
        by[r["task"], r["model"]].append(r)
    short = {m: m.split("-")[1] for m in models}
    lines = ["| task | diff | router pick | " + " | ".join(f"{short[m]} pass / $ / s" for m in models)
             + " | cheapest passing | router ok |", "|---" * (len(models) + 5) + "|"]
    totals = defaultdict(lambda: {"pass": 0.0, "cost": 0.0})
    for t in tasks:
        if not any((t["id"], m) in by for m in models):
            continue
        pick = route_prompt_to_model((TASKS / "tasks" / t["id"] / "prompt.md").read_text())
        stat = {m: (mean(r["pass"] for r in by[t["id"], m]), mean(r["cost"] for r in by[t["id"], m]),
                    mean(r["latency"] for r in by[t["id"], m])) for m in models if (t["id"], m) in by}
        passing = [m for m in stat if stat[m][0] >= 0.5]
        oracle = min(passing, key=lambda m: stat[m][1]) if passing else None
        for name, m in [("router", pick), ("oracle", oracle or max(stat, key=lambda m: stat[m][0])),
                        *[(f"always {short[m]}", m) for m in models]]:
            if m in stat:
                totals[name]["pass"] += stat[m][0]
                totals[name]["cost"] += stat[m][1]
        lines.append(f"| {t['id']} | {t['difficulty']} | {short.get(pick, pick)} | "
                     + " | ".join(f"{stat[m][0]:.0%} / {stat[m][1]:.3f} / {stat[m][2]:.0f}" if m in stat else "-"
                                  for m in models)
                     + f" | {short.get(oracle, '-')} | {'yes' if pick in passing else 'NO'} |")
    n = len({r["task"] for r in rows})
    lines += ["", "| policy | pass rate | total $ (API-equivalent) |", "|---|---|---|"]
    lines += [f"| {k} | {v['pass'] / n:.0%} | {v['cost']:.3f} |" for k, v in totals.items()]
    return "\n".join(lines)


async def main_async(args) -> Path:
    spec = json.loads((TASKS / "tasks.json").read_text())
    tasks = [t for t in spec["tasks"] if not args.tasks or t["id"] in args.tasks.split(",")]
    models = [SHORT[m] for m in args.models.split(",")]
    out = Path(args.out) / time.strftime("%Y%m%d-%H%M%S")
    out.mkdir(parents=True)
    sem = asyncio.Semaphore(args.jobs)
    results = out / "results.jsonl"

    async def guarded(t, m, r):
        async with sem:
            row = await one(t, m, r, out, spec["test_cmd"], args.timeout)
        with results.open("a") as f:
            f.write(json.dumps(row) + "\n")
        print(f"{row['task']:32} {m:18} r{r} {'PASS' if row['pass'] else 'fail'} "
              f"{row['tests_passed']}/{row['tests_total']} ${row['cost']:.3f} {row['latency']:.0f}s", flush=True)
        return row

    rows = await asyncio.gather(*(guarded(t, m, r) for t in tasks for m in models for r in range(1, args.runs + 1)))
    (out / "report.md").write_text(report(rows, spec["tasks"]))
    return out


def cli() -> None:
    ap = argparse.ArgumentParser(description="Run eval-tasks on every model and score the router")
    ap.add_argument("--tasks", help="comma-separated task ids (default: all)")
    ap.add_argument("--models", default="haiku,sonnet,opus")
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=3, help="parallel Claude Code runs")
    ap.add_argument("--timeout", type=int, default=1200, help="seconds per agent run")
    ap.add_argument("--out", default=str(ROOT / "eval-results"))
    ap.add_argument("--report", help="re-print the report for an existing run dir")
    args = ap.parse_args()
    if args.report:
        rows = [json.loads(line) for line in (Path(args.report) / "results.jsonl").read_text().splitlines()]
        print(report(rows, json.loads((TASKS / "tasks.json").read_text())["tasks"]))
        return
    out = asyncio.run(main_async(args))
    print(f"\n{(out / 'report.md').read_text()}\n\nOutputs: {out}")


if __name__ == "__main__":
    cli()
