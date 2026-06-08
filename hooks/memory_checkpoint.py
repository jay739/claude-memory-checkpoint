#!/usr/bin/env python3
"""claude-memory-checkpoint — PostToolUse hook.

Counts tool calls per chat session. When a session crosses the threshold
(default 250, override with MEMORY_CHECKPOINT_EVERY), it injects a directive
telling Claude to write a concise summary of what the chat accomplished into
the project's auto-memory, then resets the counter. The point is token
efficiency across parallel/future chats: they load the summary from memory
instead of re-deriving the whole session.

The memory directory is derived from the session's working directory using
Claude Code's convention (~/.claude/projects/<sanitized-cwd>/memory). Override
it explicitly with MEMORY_CHECKPOINT_DIR if your setup differs.
"""

import sys, os, re, json

THRESHOLD = int(os.environ.get("MEMORY_CHECKPOINT_EVERY", "250"))
STATE_DIR = os.path.expanduser(
    os.environ.get("MEMORY_CHECKPOINT_STATE", "~/.claude/hooks/state")
)


def memory_dir(data):
    """Resolve the auto-memory dir: explicit override, else derive from cwd."""
    override = os.environ.get("MEMORY_CHECKPOINT_DIR")
    if override:
        return os.path.expanduser(override)
    cwd = data.get("cwd") or os.getcwd()
    # Claude Code sanitizes the cwd into the projects dir name by replacing
    # path separators / non-alphanumerics with '-'.  /home/you/project -> -home-you-project
    sanitized = re.sub(r"[^A-Za-z0-9]", "-", cwd)
    claude_dir = os.environ.get("CLAUDE_CONFIG_DIR", os.path.expanduser("~/.claude"))
    return os.path.join(claude_dir, "projects", sanitized, "memory")


def main():
    raw = sys.stdin.read() or "{}"
    try:
        data = json.loads(raw)
    except Exception:
        data = {}

    sid = data.get("session_id") or "default"
    safe = "".join(c for c in sid if c.isalnum() or c in "-_")[:64] or "default"
    state_dir = os.path.expanduser(STATE_DIR)
    os.makedirs(state_dir, exist_ok=True)
    cfile = os.path.join(state_dir, f"memck_{safe}.count")

    try:
        with open(cfile) as f:
            count = int(f.read().strip() or "0")
    except Exception:
        count = 0
    count += 1

    if count >= THRESHOLD:
        try:
            with open(cfile, "w") as f:
                f.write("0")
        except Exception:
            pass
        mem = memory_dir(data)
        directive = (
            f"MEMORY CHECKPOINT: {THRESHOLD} tool calls reached in this chat. "
            "Pause and write a concise summary of what THIS chat has accomplished into the "
            f"auto-memory dir ({mem}). Prefer UPDATING the most relevant existing "
            "project_*.md file; otherwise append a dated entry to project_session_log.md and "
            "add a one-line pointer in MEMORY.md. Capture only what a parallel or future chat "
            "would otherwise have to re-derive: what changed, key decisions and why, current "
            "state, and open threads. Keep it tight. Then resume the user's task."
        )
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PostToolUse",
                        "additionalContext": directive,
                    }
                }
            )
        )
    else:
        try:
            with open(cfile, "w") as f:
                f.write(str(count))
        except Exception:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
