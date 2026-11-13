"""Chat with Claude Code through the router.

Every prompt goes through route_prompt_to_model, then runs as `claude -p --model <pick>`.
Turns share one Claude Code session (--resume), so context carries over even when the
router switches model between turns. Predicted vs actual cost/latency go to logs/runs.jsonl.

    llm-router-chat                      # interactive
    llm-router-chat "fix the typo"       # one shot
    llm-router-chat --model opus ...     # skip the router
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

from .main import predict_metrics, route_prompt_to_model
from .ModelChoices import ModelChoice, ModelChoices

# Router names use dots; Claude Code / API model IDs use dashes.
CLI_MODEL: dict[ModelChoice, str] = {m: m.replace(".", "-") for m in ModelChoices}
SHORT = {m.split("-")[1]: m for m in ModelChoices}  # haiku / sonnet / opus
LOG = Path(os.environ.get("LLM_ROUTER_LOG", Path(__file__).resolve().parents[2] / "logs" / "runs.jsonl"))
CLAUDE_BIN = os.environ.get("CLAUDE_BIN", "claude")


def env(use_api_key: bool) -> dict:
    e = dict(os.environ)
    if not use_api_key:  # use the Claude Pro/Max login instead of billing an API key
        e.pop("ANTHROPIC_API_KEY", None)
    return e


def turn(prompt: str, session: str | None, args, out=None) -> str | None:
    """Route, run one Claude Code turn, stream its output, log metrics. Returns the session id."""
    out = out or sys.stdout
    model = SHORT[args.model] if args.model else route_prompt_to_model(prompt)
    predicted = predict_metrics(prompt)[model]
    print(f"\033[2m[router] -> {model}  (predicted ${predicted.cost:.4f}, {predicted.latency:.1f}s, "
          f"quality {predicted.quality:.2f})\033[0m", file=out, flush=True)

    cmd = [CLAUDE_BIN, "-p", prompt, "--model", CLI_MODEL[model], "--output-format", "stream-json",
           "--verbose", "--permission-mode", args.permission_mode]
    if session:
        cmd += ["--resume", session]
    t0, result = time.perf_counter(), {}
    with subprocess.Popen(cmd, cwd=args.cwd, env=env(args.use_api_key), stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, text=True) as p:
        for line in p.stdout:
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "assistant":
                for b in ev["message"].get("content", []):
                    if b.get("type") == "text" and b["text"].strip():
                        print(b["text"], file=out, flush=True)
                    elif b.get("type") == "tool_use":
                        detail = json.dumps(b.get("input", {}))[:100]
                        print(f"\033[2m  > {b['name']} {detail}\033[0m", file=out, flush=True)
            elif ev.get("type") == "result":
                result = ev
        err = p.stderr.read()
    wall = time.perf_counter() - t0

    if not result:
        print(f"[router] claude failed (exit {p.returncode}): {err.strip()[-500:]}", file=out)
        return session
    print(f"\033[2m[router] actual ${result.get('total_cost_usd', 0):.4f} (API-equivalent), {wall:.1f}s, "
          f"{result.get('num_turns')} turns{'  ERROR' if result.get('is_error') else ''}\033[0m", file=out)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a") as f:
        f.write(json.dumps({
            "ts": time.time(), "prompt": prompt, "model": model, "routed": not args.model,
            "predicted": predicted.model_dump(),
            "actual": {"cost": result.get("total_cost_usd"), "latency": wall, "quality": None},
            "ttft_s": (result.get("ttft_ms") or 0) / 1000, "num_turns": result.get("num_turns"),
            "is_error": result.get("is_error"), "session_id": result.get("session_id"),
        }) + "\n")
    return result.get("session_id") or session


def cli() -> None:
    ap = argparse.ArgumentParser(description="Claude Code behind the llm-router")
    ap.add_argument("prompt", nargs="*", help="one-shot prompt; omit for interactive chat")
    ap.add_argument("--model", choices=sorted(SHORT), help="skip the router and force a model")
    ap.add_argument("--cwd", default=".", help="directory Claude Code works in")
    ap.add_argument("--permission-mode", default="acceptEdits",
                    help="Claude Code permission mode (acceptEdits, dontAsk, bypassPermissions, plan, ...)")
    ap.add_argument("--use-api-key", action="store_true", help="bill ANTHROPIC_API_KEY instead of your plan")
    args = ap.parse_args()

    if args.prompt:
        turn(" ".join(args.prompt), None, args)
        return
    print("llm-router chat. Commands: /model haiku|sonnet|opus|auto, /new, /quit")
    session = None
    while True:
        try:
            prompt = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if prompt in ("/quit", "/exit"):
            break
        if prompt == "/new":
            session = None
            print("[router] new conversation")
        elif prompt.startswith("/model"):
            choice = prompt.split()[-1]
            args.model = None if choice == "auto" else choice if choice in SHORT else args.model
            print(f"[router] model: {args.model or 'auto (router decides)'}")
        elif prompt:
            session = turn(prompt, session, args)


if __name__ == "__main__":
    cli()
