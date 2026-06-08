#!/usr/bin/env bash
# claude-memory-checkpoint installer.
# Copies the hook into ~/.claude/hooks/ and merges the hook config into
# ~/.claude/settings.json (preserving everything already there).
# Idempotent: safe to re-run. Requires python3 for the JSON merge.
#
# Configure the cadence at install time:
#   MEMORY_CHECKPOINT_EVERY=300 ./install.sh
set -euo pipefail

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CLAUDE_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
HOOK_SRC="$SRC_DIR/hooks/memory_checkpoint.py"
HOOK_DST="$CLAUDE_DIR/hooks/memory_checkpoint.py"
SETTINGS="$CLAUDE_DIR/settings.json"
EVERY="${MEMORY_CHECKPOINT_EVERY:-250}"

mkdir -p "$CLAUDE_DIR/hooks"
cp "$HOOK_SRC" "$HOOK_DST"
chmod +x "$HOOK_DST"

EVERY="$EVERY" python3 - "$SETTINGS" <<'PY'
import json, os, sys

settings = sys.argv[1]
every = os.environ["EVERY"]
try:
    with open(settings) as f:
        cfg = json.load(f)
except FileNotFoundError:
    cfg = {}
except json.JSONDecodeError:
    print(f"ERROR: {settings} is not valid JSON; fix it and re-run.", file=sys.stderr)
    sys.exit(1)

cmd = f"MEMORY_CHECKPOINT_EVERY={every} python3 ~/.claude/hooks/memory_checkpoint.py 2>/dev/null || true"
hooks = cfg.setdefault("hooks", {})
arr = hooks.setdefault("PostToolUse", [])

# Drop any prior install of this hook so re-running doesn't duplicate it.
def is_ours(group):
    return any("memory_checkpoint.py" in h.get("command", "") for h in group.get("hooks", []))
arr[:] = [g for g in arr if not is_ours(g)]

# No matcher => counts every tool call.
arr.append({"hooks": [{"type": "command", "command": cmd}]})

with open(settings, "w") as f:
    json.dump(cfg, f, indent=2)
    f.write("\n")
print(f"Merged PostToolUse memory-checkpoint hook (every {every} tool calls) into {settings}")
PY

echo
echo "Installed. Every $EVERY tool calls in a chat, Claude is asked to summarize the session"
echo "into your auto-memory so parallel/future chats load the summary instead of re-deriving."
echo
echo "Requires Claude Code auto-memory to be enabled (autoMemoryEnabled)."
echo "Override the memory location with MEMORY_CHECKPOINT_DIR if your setup is non-standard."
echo
echo "Open /hooks in Claude Code once (or restart) to load the new config."
echo "To remove: ./uninstall.sh"
