"""Unit tests for the memory_checkpoint hook: counter behavior and the
threshold-crossing checkpoint directive."""

import json
import os
import subprocess
import sys
from pathlib import Path

HOOK = Path(__file__).resolve().parents[1] / "hooks" / "memory_checkpoint.py"


def run_hook(tmp_path: Path, session: str, every: str = "3") -> str:
    env = dict(
        os.environ,
        MEMORY_CHECKPOINT_EVERY=every,
        MEMORY_CHECKPOINT_STATE=str(tmp_path / "state"),
        MEMORY_CHECKPOINT_DIR=str(tmp_path / "memory"),
    )
    payload = json.dumps({"session_id": session, "cwd": str(tmp_path)})
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=payload,
        capture_output=True,
        text=True,
        env=env,
        check=True,
    )
    return proc.stdout


def counter(tmp_path: Path, session: str) -> int:
    f = tmp_path / "state" / f"memck_{session}.count"
    return int(f.read_text().strip() or "0")


def test_below_threshold_counts_silently(tmp_path):
    assert run_hook(tmp_path, "s1").strip() == ""
    assert run_hook(tmp_path, "s1").strip() == ""
    assert counter(tmp_path, "s1") == 2


def test_threshold_emits_directive_and_resets(tmp_path):
    run_hook(tmp_path, "s2")
    run_hook(tmp_path, "s2")
    out = run_hook(tmp_path, "s2")
    assert "additionalContext" in out
    assert counter(tmp_path, "s2") == 0


def test_sessions_are_independent(tmp_path):
    run_hook(tmp_path, "a")
    run_hook(tmp_path, "b")
    assert counter(tmp_path, "a") == 1
    assert counter(tmp_path, "b") == 1
