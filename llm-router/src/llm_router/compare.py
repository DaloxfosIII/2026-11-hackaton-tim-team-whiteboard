"""Naive harness: send each prompt to all three models, report answers, cost and latency side by side.

    llm-router-compare "What is the capital of Australia?"
    llm-router-compare --cases                     # every tests/test_cases/<name>/<name>.json prompt
    llm-router-compare --cases --out report.md

Models run as headless Claude Code (`claude -p`, no tools) on your Claude plan. Cost is Claude
Code's API-equivalent estimate. The router's pick is shown next to the results for comparison.
"""
import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from .chat import CLAUDE_BIN
from .main import route_prompt_to_model
from .ModelChoices import ModelChoices

MODELS = sorted(ModelChoices, key=lambda m: ["haiku", "sonnet", "opus"].index(m.split("-")[1]))
CASES = Path(__file__).resolve().parents[2] / "tests" / "test_cases"


async def ask(model: str, prompt: str, timeout: int = 600) -> dict:
    env = {k: v for k, v in os.environ.items() if k != "ANTHROPIC_API_KEY"}  # use the plan login
    t0 = time.perf_counter()
    p = await asyncio.create_subprocess_exec(
        CLAUDE_BIN, "-p", prompt, "--model", model, "--output-format", "json", "--tools", "",
        "--strict-mcp-config", "--no-session-persistence", "--setting-sources", "",
        stdout=-1, stderr=-1, env=env)
    try:
        out, err = await asyncio.wait_for(p.communicate(), timeout)
        r = json.loads(out)
    except (TimeoutError, json.JSONDecodeError):
        r = {"is_error": True, "result": "timeout or bad output"}
    return {"answer": r.get("result", ""), "cost": r.get("total_cost_usd") or 0.0,
            "latency": time.perf_counter() - t0, "ttft": (r.get("ttft_ms") or 0) / 1000,
            "error": bool(r.get("is_error"))}


async def compare(name: str, prompt: str) -> dict:
    results = await asyncio.gather(*(ask(m, prompt) for m in MODELS))
    return {"name": name, "prompt": prompt, "router_pick": route_prompt_to_model(prompt),
            "results": dict(zip(MODELS, results))}


def render(rows: list[dict]) -> str:
    short = lambda m: m.split("-")[1]  # noqa: E731
    out = ["# Model comparison", "", "| case | router pick | " + " | ".join(f"{short(m)} $ / s" for m in MODELS)
           + " |", "|---" * (len(MODELS) + 2) + "|"]
    for r in rows:
        out.append(f"| {r['name']} | {short(r['router_pick'])} | " + " | ".join(
            f"{x['cost']:.4f} / {x['latency']:.1f}" + (" ERR" if x["error"] else "")
            for x in r["results"].values()) + " |")
    tot = {m: sum(r["results"][m]["cost"] for r in rows) for m in MODELS}
    out += ["", "Total $: " + ", ".join(f"{short(m)} {tot[m]:.4f}" for m in MODELS)
            + f", router {sum(r['results'][r['router_pick']]['cost'] for r in rows):.4f}", ""]
    for r in rows:
        out += [f"## {r['name']}", "", f"> {r['prompt']}", ""]
        for m, x in r["results"].items():
            pick = " (router pick)" if m == r["router_pick"] else ""
            out += [f"**{short(m)}**{pick}: ${x['cost']:.4f}, {x['latency']:.1f}s, first token {x['ttft']:.1f}s",
                    "", x["answer"].strip(), ""]
    return "\n".join(out)


def cli() -> None:
    ap = argparse.ArgumentParser(description="Send prompts to all models and compare")
    ap.add_argument("prompt", nargs="*")
    ap.add_argument("--cases", action="store_true", help="use every prompt in tests/test_cases")
    ap.add_argument("--out", help="write the markdown report here (default: print)")
    args = ap.parse_args()
    items = [(d.name, json.loads((d / f"{d.name}.json").read_text())["prompt"])
             for d in sorted(CASES.iterdir()) if d.is_dir()] if args.cases else [("prompt", " ".join(args.prompt))]

    async def run():
        return [await compare(n, p) for n, p in items]  # one case at a time, 3 models in parallel

    report = render(asyncio.run(run()))
    if args.out:
        Path(args.out).write_text(report)
        print(f"wrote {args.out}")
    else:
        print(report)


if __name__ == "__main__":
    cli()
