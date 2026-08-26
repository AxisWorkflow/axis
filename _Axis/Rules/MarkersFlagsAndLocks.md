# Markers, Flags, and Locks
> **Purpose:** Ephemeral live state: what each carries, what is committed, and what Stale means.


- A Marker is ephemeral; save Markers (timestamp-named) in `_Axis/Agents/`.
- A Flag records durable state; save Flags (plain descriptive names) in `_Axis/Flags/`.
- Subagent Markers are ephemeral session-state, never WORM - delete on Subagent return.
- Main-session Markers (`Main: session`) are written at Session Start and refreshed by `^save`, on session resume, and on every Log write. They age out after an abrupt or ordinary host close (Stale at 1 hour); explicit successful `^shutdown`, and verified `^update` after literal `UPDATE`, delete the actor's own Marker.
- Markers are never archived. Delete or clear them; if the Host blocks deletion, move them only to `_Trash/` under Deletion Fallback.
- Exclude all Markers (the whole of `_Axis/Agents/`) from version control via `.gitignore`.
- Exclude from version control every Flag that is not portable truth: the per-session Flags (`starting`, `session-id`, `dev-mode`, `promote`, `model`, `host-spawn`, `host-parallel`, `host-shell`, `host-local-llm`, `host-cloud-sync`, `host-storage`, `reminder-check`) and the per-machine Flags (`local-aptitude`, `environment-binding`). The per-project Flags (`project-ready`, `skip-wiki`) are committed. See [Practices > Flags] for the three lifetimes.
- Stale = past the freshness window (locks: 10 sec; `starting`: 2 min; the `session-id` completion check: 60 sec; Markers: 1 hour).
- Session ID: a UTC timestamp minted by the entry-point file at startup - written into `starting`, stored on Line 1 of `session-id`, naming the Main Marker (body `session: {Session ID}`), and printed in the Session ID banner only after successful startup validation.
- Resume decisions compare the Session ID BY VALUE (in-context ID vs Flag Line 1) - never by file age.
- A Heartbeat (periodic `mtime` touch) keeps a Batch Lock fresh - see [Lock-File > Batch].
