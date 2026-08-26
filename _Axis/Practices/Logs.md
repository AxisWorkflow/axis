# Logs
> **Purpose:** Define what to log and how to write WORM Log entries.

Logged events are used for long-term reference of all major events, such as:

- Project kickoff
- Changes to scope
- Completed milestones
- Decisions & rationale
- Strong feedback or guidance from User
- Mistakes and dead-ends
- Other events you deem important

Logs are strictly Write-Once-Read-Many (WORM) - no exceptions. Never overwrite files in `_Axis/Logs/`. Logs are retained indefinitely unless User moves inactive history through `^archive`; archived Logs remain unchanged and WORM. Sessions that need minimal logging can set **Transparency** to -2 in [Settings] (only important problems, errors, and exceptions get recorded).

**How to log an Event.** Mint a project-unique identifier timestamp per [Practices > Timestamps] (existence check across all record directories, then the atomic claim - both unconditional), then create the file `_Axis/Logs/{timestamp}.md` following the Index-Detail Pattern: Line 1 is a short Subject (≤ 80 chars) identifying the event, Line 2 is blank, Line 3 is a `by:` line naming the author (e.g., `by: Main Agent` - Subagents do not write Logs, but Main logs on their behalf), Lines 4+ are the body with whatever a future reader will need - decision, rationale, redacted input/output summaries, content digests, and links to related Tasks, Snapshots, or Notes. Never copy a credential, secret, full Subagent prompt, or raw embedded source into a Log; put an explicitly requested diagnostic prompt in `_Axis/Secrets/` or `_Temp/` instead. Logs are WORM: never edit or delete a log file after writing. If the timestamp collides with an existing file, increment the `xxx` milliseconds suffix and retry. After writing a Log, touch (`mtime` refresh) your own `Main: session` Marker in the same pass - Log writes are the heartbeat that keeps an active session's Marker fresh (see [Practices > Markers]).

## Capability Downgrades

Whenever a missing or failed Capability changes how work runs, use the Subject `Capability downgrade: {feature}` and include these bare fields:

	feature: {feature affected}
	missing-capability: {invalid, absent, or unavailable Host fact}
	behavior-used: {safe degraded behavior}
	work-skipped: {work that did not run, or N/A}
	user-impact: {material effect, or none}

This fixed Subject powers the Dashboard and `^audit`. Do not treat an absent local endpoint as an error by itself; Log it only when a requested feature actually downgrades.
