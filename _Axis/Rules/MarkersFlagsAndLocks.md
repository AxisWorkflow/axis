# Markers, Flags, and Locks
> **Purpose:** Ephemeral live state: what each carries, what is committed, and what Stale means.


- A Marker is ephemeral; save Markers (timestamp-named) in `_Axis/Agents/`.
- A Flag records durable state; save Flags (plain descriptive names) in `_Axis/Flags/`.
- Subagent Markers are ephemeral session-state, never WORM - delete on Subagent return.
- Main-session Markers (`Main: session`) are written at Session Start and refreshed by `^save`, on session resume, and on every Log write. They age out after an abrupt or ordinary host close (Stale at 1 hour); explicit successful `^shutdown`, and verified User-invoked `^update` under its routine/exception policy, delete the actor's own Marker.
- Markers are never archived. Delete or clear them; if the Host blocks deletion, move them only to `_Trash/` under Deletion Fallback.
- Exclude all Markers (the whole of `_Axis/Agents/`) from version control via `.gitignore`.
- Exclude from version control every Flag that is not portable truth: the per-session Flags (`starting`, `session-id`, `project-overlay`, `promote`, `model`, `host-spawn`, `host-parallel`, `host-shell`, `host-local-llm`, `host-cloud-sync`, `host-storage`, `reminder-check`) and the per-machine Flags (`local-aptitude`, `environment-binding`). The per-project Flags (`project-ready`, `skip-wiki`) are committed. See [Practices > Flags] for the three lifetimes.
- Stale = past the freshness window (locks: 10 sec; `starting`: 2 min; the `session-id` completion check: 60 sec; Markers: 1 hour).
- Session ID: a UTC timestamp minted by the entry-point file at startup - written into `starting`, stored on Line 1 of `session-id`, naming the Main Marker (body `session: {Session ID}`), and printed in the Session ID banner only after successful startup validation.
- Resume decisions compare the Session ID BY VALUE (in-context ID vs Flag Line 1) - never by file age.
- A Heartbeat (periodic `mtime` touch) keeps a Batch Lock fresh - see [Lock-File > Batch].

## Concurrent Sessions

[Settings > Max Concurrent Sessions] limits how many Agent sessions are live at once. A live session is a Marker in `_Axis/Agents/` whose `mtime` is under 1 hour and that has no `{ID}.kill` sibling, whatever its Subject (`Main: session`, `External: {host}` or `Subagent: {role}`).

- Before creating the Marker for a new External Agent or Subagent, count live sessions. When the count already equals or exceeds the limit, do not start it: an External Agent tells User the project already has that many active sessions and stops without a Marker; Main runs the work itself or waits for a Subagent to return.
- Main is never refused on this count; the one-Main rule already bounds it.
- The count is taken at start and is advisory against a simultaneous start by another Agent; it is not a lock. Stale and tombstoned Markers never count.

