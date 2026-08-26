# Host and Meta
> **Purpose:** Host tooling expectations, and the Deletion Fallback ladder when a host blocks deletes.


- Agent is encouraged to use tools, skills, MCPs, etc. provided by the host harness.
- Scan `_Axis/Resources/` for Axis procedures (sessions, subagents, locks, templates); look to the host harness for skills, MCPs, and other tooling.
- No schema for the Workflow - it should be fault-tolerant to real human interaction.
- `_Axis/CHANGELOG.md` records release identity and forward structural migrations; current documentation remains authoritative after an update completes.

## Deletion Fallback

Some hosts (e.g., Cowork) block file deletion until User grants permission. If a delete fails with a permission error:

- First, request delete permission from host once (if the host supports such a request).
- If still blocked, clear a Flag by overwriting its body with `cleared` on Line 1 plus a current UTC timestamp on Line 2; treat any Flag whose Line 1 is `cleared` as absent.
- If still blocked, move the file or lock directory into `_Trash/` per [Practices > Trash] - renaming works on hosts where deleting does not, and the next sweep that CAN delete will empty it.
- If even `_Trash/` cannot be emptied when swept, report the count and remind User to empty it; do not keep retrying.
- Log the substitution so the audit trail explains the leftover state.
