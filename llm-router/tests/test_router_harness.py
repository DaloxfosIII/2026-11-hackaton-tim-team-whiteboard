"""Offline tests: dummy router picks, and the chat harness against a fake `claude` binary."""
import json
import stat
from types import SimpleNamespace

from llm_router import chat
from llm_router.main import route_prompt_to_model

FAKE_CLAUDE = """#!/usr/bin/env python3
import json, sys
args = sys.argv[1:]
open(sys.argv[0] + ".args", "a").write(json.dumps(args) + "\\n")
print(json.dumps({"type": "assistant", "message": {"content": [
    {"type": "tool_use", "name": "Read", "input": {"file_path": "x.py"}},
    {"type": "text", "text": "hello from " + args[args.index("--model") + 1]}]}}))
print(json.dumps({"type": "result", "is_error": False, "total_cost_usd": 0.01, "num_turns": 2,
                  "ttft_ms": 500, "session_id": "sess-1"}))
"""


def test_chat_turn_routes_streams_resumes_and_logs(tmp_path, monkeypatch, capsys):
    fake = tmp_path / "claude"
    fake.write_text(FAKE_CLAUDE)
    fake.chmod(fake.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setattr(chat, "CLAUDE_BIN", str(fake))
    monkeypatch.setattr(chat, "LOG", tmp_path / "runs.jsonl")
    args = SimpleNamespace(model=None, cwd=str(tmp_path), permission_mode="acceptEdits", use_api_key=False)

    first = route_prompt_to_model("Fix the typo in the README")  # whatever the team router picks
    session = chat.turn("Fix the typo in the README", None, args)
    args.model = "opus"
    chat.turn("now refactor it", session, args)

    out = capsys.readouterr().out
    assert f"hello from {first}" in out and "hello from claude-opus-5-5" in out
    calls = [json.loads(line) for line in (tmp_path / "claude.args").read_text().splitlines()]
    assert "--resume" not in calls[0] and calls[1][calls[1].index("--resume") + 1] == "sess-1"
    log = [json.loads(line) for line in (tmp_path / "runs.jsonl").read_text().splitlines()]
    assert [r["model"] for r in log] == [first, "claude-opus-5-5"]
    assert log[0]["routed"] and not log[1]["routed"] and log[0]["actual"]["cost"] == 0.01
