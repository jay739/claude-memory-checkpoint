# claude-memory-checkpoint

**Periodically summarize a long [Claude Code](https://github.com/anthropics/claude-code) chat into project memory, so your other chats don't re-derive the same context.**

If you run several chats about the same project, each one re-reads files and re-discovers context, burning tokens. This hook counts tool calls in a chat and, once it crosses a threshold, asks Claude to drop a tight summary of what the chat accomplished into your auto-memory. Parallel and future chats then load that summary instead of rebuilding it from scratch.

## How it works

- A no-matcher `PostToolUse` hook runs after **every** tool call and increments a per-session counter (kept in `~/.claude/hooks/state/`).
- When a chat crosses the threshold (default **250** tool calls), the hook injects a directive via `hookSpecificOutput.additionalContext` telling Claude to write/update a summary in the project's memory dir, then resets the counter.
- The summary captures only what a future chat would otherwise re-derive: what changed, key decisions and why, current state, and open threads.

The counter is **per chat** (keyed by `session_id`), so each long chat checkpoints itself independently.

## Requirements

- Claude Code **auto-memory enabled** (`autoMemoryEnabled` in settings). This hook writes into the auto-memory directory; without it there's nowhere to write.
- `python3`.

## Install

```bash
git clone https://github.com/jay739/claude-memory-checkpoint
cd claude-memory-checkpoint
./install.sh                          # default: every 250 tool calls
MEMORY_CHECKPOINT_EVERY=300 ./install.sh   # less frequent
```

The installer copies `hooks/memory_checkpoint.py` into `~/.claude/hooks/` and **merges** a hook entry into `~/.claude/settings.json` (existing settings/hooks preserved; re-running replaces rather than duplicates). Open `/hooks` once (or restart) to load it.

## Configuration

| Env var                   | Default                 | Meaning                                       |
| ------------------------- | ----------------------- | --------------------------------------------- |
| `MEMORY_CHECKPOINT_EVERY` | `250`                   | Tool calls per chat before a checkpoint fires |
| `MEMORY_CHECKPOINT_DIR`   | derived from cwd        | Override the memory directory explicitly      |
| `MEMORY_CHECKPOINT_STATE` | `~/.claude/hooks/state` | Where per-session counters live               |

By default the memory directory is derived from your session's working directory using Claude Code's convention: `~/.claude/projects/<sanitized-cwd>/memory`. If your auto-memory lives somewhere non-standard, set `MEMORY_CHECKPOINT_DIR`.

## Note on coverage

A chat that ends **before** the threshold won't write a summary (it counts tool calls, not wall-clock or session end). If you want a guaranteed summary at the end of every chat regardless of length, pair this with a `Stop` hook.

## Uninstall

```bash
./uninstall.sh
```

## License

MIT
