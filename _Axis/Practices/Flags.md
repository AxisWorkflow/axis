# Flags
> **Purpose:** Define persistent Flags that record durable workflow state.

A Flag is a persistent file that records durable workflow state. A Flag remains valid until the state it records actually changes - Flags do not expire by age. (Timing exceptions: the entry-point files check `starting` and `session-id` for freshness at startup.)

- Flags live in `_Axis/Flags/` and use plain, descriptive filenames (e.g., `project-ready`) - no leading period, so they stay visible in file browsers.
- Write a current UTC timestamp into the body of the Flag when setting it.
- Create, check, and delete a Flag only as directed by the protocol that owns it.

<!-- BEGIN GENERATED: flag-contract -->
| Flag | Lifetime | Valid Line 1 | Freshness exception |
| --- | --- | --- | --- |
| `project-ready` | per-project | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | - |
| `skip-wiki` | per-project | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | - |
| `starting` | per-session | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | < 2 minutes while startup is in flight |
| `session-id` | per-session | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | < 60 seconds for the post-start completion check |
| `dev-mode` | per-session | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | - |
| `promote` | per-session | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | < 10 minutes while a promotion awaits its trusted-surface approval |
| `model` | per-session | model name or `unknown` | - |
| `host-spawn` | per-session | `yes` or `no` | - |
| `host-parallel` | per-session | `yes` or `no` | - |
| `host-shell` | per-session | `yes` or `no` | - |
| `host-local-llm` | per-session | `yes` or `no` | - |
| `host-cloud-sync` | per-session | `yes` or `no` | - |
| `host-storage` | per-session | `atomic` or `serialized` or `unknown` | - |
| `reminder-check` | per-session | `{yyyy.mm.dd.hh.mm.ss.xxxZ}` | current Session ID on Line 1; last trustworthy check on Line 2 |
| `environment-binding` | per-machine | opaque local Axis instance ID | revalidated at Session Start |
| `local-aptitude` | per-machine | tested local-model name | - |
<!-- END GENERATED: flag-contract -->

The lifetime decides whether a Flag is committed: per-project state is committed; per-machine state is gitignored and only its owning command rewrites it; per-session state is gitignored and re-detected at Session Start.

## Flag Details

- `project-ready` - project setup is complete. Set by [Start-Project]; checked by [Start-Session].
- `skip-wiki` - User declined or deferred Wiki setup. Set by [Start-Project]; checked by [Start-Wiki].
- `starting` - Session Start is in flight (an in-flight lock; body = the Session ID). Set by the entry-point files; refreshed (`mtime` touch) as [Start-Session] runs; deleted or cleared only after the startup-artifact gate passes and as the final startup write before the Session ID banner and greeting; treated as stale after 2 minutes.
- `session-id` - Session identity and completion. Line 1 = the Session ID (the timestamp printed in the successful-completion Session ID banner; it also names the Main Marker); Line 2 = a UTC timestamp, refreshed on session resume and by `^save` (so `mtime` reads as last activity). Written and read back by [Start-Session] after all startup artifacts validate, then verified again after `starting` is released and before the banner; compared BY VALUE - never by age - by the entry-point resume ladder.
- `dev-mode` - Development Mode for this Session only. Line 1 = the Development Session ID printed by `^dev`; Line 2 = enabled timestamp. On a non-new conversation, the entry-point Development Mode fast path delegates recovery to `^dev`'s Continuation rules instead of Session Start. The Development procedures treat it as active only when that ID is visible in the current conversation, and every development-only command verifies the Flag before it acts. A brand-new conversation ignores this Flag; normal [Start-Session] clears it.
- `model` - the running model's name as reported by the host. Written by [Start-Session]; shown on the Dashboard and used to resolve `same-as-host`.
- `host-spawn` - written by [Start-Session] and set to `no` on a failed spawn.
- `host-parallel` - written by [Start-Session].
- `host-shell` - written by [Start-Session]; Windows cmd/PowerShell does not satisfy the POSIX-shell Capability.
- `host-local-llm` - written by [Start-Session], re-probed by `^install`, and carries the working base URL on Line 3 when available.
- `host-cloud-sync` - written by [Start-Session]; a detected cloud-synced folder disables parallel writes (see [Lock-File > Prerequisites]).
- `host-storage` - written by [Start-Session]; `atomic`, `serialized`, or `unknown` for the current project location. Only `atomic` together with exact `Storage Policy=auto` permits the lock protocol or parallel writers; see [Practices > Portability > Storage Profile].
- `reminder-check` - per-session Reminder surfacing checkpoint. Line 1 = current Session ID; Line 2 = last trustworthy UTC due check. Missing, malformed, or foreign-session state causes a full due check and never a false advance; see [Practices > Reminders > Surfacing and Session Checkpoint].
- `environment-binding` - optional project-local half of the environment signature. Line 1 = the opaque ID read from `~/.axis/instance-id`; Lines 2-6 are exactly `harness:`, `os:`, `interaction:`, `storage:`, and `verified:`. It is gitignored, never authoritative, and never copied into tracked or visible records; see [Practices > Portability > Optional Environment Signature].
- `local-aptitude` - the Aptitude Check scorecard for the local model on THIS machine. Line 1 = the model name; Line 2 = a UTC timestamp; Line 3 = the five fixture results in order as `PASS`, `RETRY`, or `FAIL` (e.g., `PASS RETRY PASS FAIL PASS`). An optional benchmark block starts on Line 4 with `benchmark: transport=ollama quantization={token} context={integer}` (Ollama is the sole supported transport), followed by stable multi-sample results as `class-score: {task-class} {PASS|CONDITIONAL|FAIL} {passed}/{total} first={first-pass}/{total}`. Valid task classes are `extraction`, `classification`, `constrained-drafting`, `citation-preservation`, `prompt-injection-refusal`, and `marker-and-output-contract`; ignore an unverified fingerprint, malformed or unknown row, or class row without its fingerprint rather than granting aptitude. Written by `^install` or an approved local-model benchmark; read by `^audit` and before matching work is delegated locally. A per-machine Flag: it outlives the session but is worthless on another computer, so it is gitignored and never rewritten at Session Start.

## Reading Flags

Every Flag consumer follows this rule; file existence alone never means a Flag is set:

1. Read the file directly and trim Line 1.
2. Treat a missing file, blank Line 1, literal `cleared`, or a value outside that Flag's documented domain as absent.
3. Follow the consumer's missing-Flag branch. For a per-session Capability, re-detect it when safe; if re-detection is unavailable, treat the Capability as unavailable and use the documented safe degraded behavior. Never grant a Capability from malformed state.
4. Line 2 is metadata, not truth, except where a named protocol explicitly checks freshness (`starting` and the post-start `session-id` completion check).
5. When clearing a Flag and deletion is blocked, write `cleared` on Line 1 under [Rules > HostAndMeta > Deletion Fallback]; every reader therefore sees the same absent state.
