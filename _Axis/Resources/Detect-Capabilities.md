# Detect Capabilities
> **Purpose:** Record the running model and detect the host facts used as Capabilities. Followed by [Start-Session] once per session; `^install` re-probes `host-local-llm`. Definitions and the feature-requirements table live in [Rules > Capabilities].

## Step 1: Record Model

1. Determine the model you are running on from your system context. Keep the model's name exactly as reported; if no name is available, record `unknown`.
2. Do not infer a Main Agent quality class from model-name fragments or parameter count. The entry-point protocol already enforced the standard-capability Main Agent prerequisite before Session Start; this file records facts, not eligibility.

## Step 2: Detect Host Facts

1. `host-spawn` = `yes` when the host provides a tool to spawn Subagents (e.g., Cowork `Task`, Claude Code `Agent`) - inspect your tool inventory.
2. `host-parallel` = `yes` when multiple Subagents can run at the same time.
3. `host-shell` = `yes` only when shell commands run in a POSIX-like shell. Verify with a probe: `uname -s && date -u +"%Y.%m.%d"` - both must succeed and the date must be a well-formed stamp. Git Bash (`MINGW*`/`MSYS*`) and WSL (`Linux`) pass; Windows cmd and PowerShell fail - on failure set `no` and queue a one-line warning, for delivery with the greeting, advising User to relaunch the host from WSL or Git Bash.
4. `host-local-llm` = `yes` when a local Ollama endpoint answers a probe from your shell: `curl -s --max-time 2 http://localhost:11434/v1/models` (Ollama is the sole supported local runtime). Record the working base URL (`http://localhost:11434/v1`) on Line 3 of the Flag body - [Start-Subagent] reads it from there. On a sandboxed or remote shell, `localhost` is the sandbox - not the User's machine - so the probe correctly yields `no`. If `host-shell` is `no`, set `no`. Re-probe after `^install`.
5. `host-cloud-sync` = `yes` when the project root appears to live in a cloud-synced folder. Heuristic probe (case-insensitive): the absolute project path contains `Library/CloudStorage`, `Mobile Documents`, `com~apple~CloudDocs`, `Dropbox`, `OneDrive`, or `Google Drive`; or an ancestor folder holds a `.dropbox` or `.dropbox.cache` marker; or `df -T .` reports a FUSE filesystem. Best-effort only - if User corrects the value in chat, update the Flag and log the correction. When `yes`, parallel writes are unsafe: Lock-File prerequisites are NOT met - use its Degraded Mode (see [Lock-File > Prerequisites]) and queue a one-line notice for delivery with the greeting.
6. Read `Storage Policy` from `_Axis/SETTINGS.md` before deciding `host-storage`. Exact `single-writer`, missing, or malformed policy sets `serialized` without attempting to raise it; queue one warning only for missing/malformed policy. Under exact `auto`, set `serialized` when `host-cloud-sync=yes`. Otherwise, when shell and ordinary same-directory operations are available, test a non-record sibling in `_Temp/`: create complete content, read it back, rename it in the same directory, verify content and usable `mtime`, then remove it. If that passes, `host-cloud-sync=no`, and no independent-replica arrangement is known, set `atomic`; if the local operations fail but serialized reads/writes work, set `serialized`; otherwise set `unknown`. A one-process probe cannot prove distributed atomicity. User may lower the persistent ceiling by changing `Storage Policy` to `single-writer`; record the correction in a Log. Changing it back to `auto` requires this fresh probe and never directly grants atomicity. `serialized` and `unknown` disable parallel writers and use [Lock-File > Degraded Mode].

## Step 3: Record Flags

1. Write each result into its own Flag (`model`, `host-spawn`, `host-parallel`, `host-shell`, `host-local-llm`, `host-cloud-sync`, `host-storage`): the value on Line 1, a current UTC timestamp on Line 2.
2. If a spawn attempt later fails mid-session, set `host-spawn` to `no`, Log under [Practices > Logs > Capability Downgrades], and continue serially. STOP.
