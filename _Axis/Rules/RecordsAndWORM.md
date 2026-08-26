# Records and WORM
> **Purpose:** Which records are write-once, and the exact line shape of each record family.


- Files in `_Axis/Tasks/` are WORM, once Task is Completed or Cancelled.
- Files in `_Axis/Logs/` are WORM from creation - never edit or delete a Log.
- Files in `_Axis/Snapshots/` are WORM, once saved and presented to User.
- Files in `_Axis/CX/` are WORM, once saved and presented to User.
- Files in `_Axis/Audit/` are WORM, once saved and presented to User.
- Files in `_Axis/Status/` are WORM, once saved and presented to User.
- Files in `_Axis/Supervision/` are WORM, once saved and presented to User.
- Files in `_Axis/Followups/` are mutable only while open; terminal Follow-Ups move to `_Axis/Archive/Followups/` and are WORM.
- Files in `_Axis/Reminders/` are mutable only while open; terminal Reminders move to `_Axis/Archive/Reminders/` and are WORM.
- Logs and Snapshots are retained indefinitely unless User moves inactive history through `^archive`; archived copies remain unchanged and WORM.
- Never overwrite a Status Report - each has its own timestamped file.
- Task Status values are: Active, Blocked, Completed, Cancelled.
- Log files: Line 1=Subject (≤ 80 chars), Line 2=blank, Line 3=`by:` author (e.g., `by: Main Agent`), Lines 4+ = body.
- Note files: Line 1=Subject (≤ 80 chars), Line 2=blank, Lines 3+ = body (≤ 250 words).
- Idea files: Line 1=Subject, Line 2=blank, then `status:` / `priority:` / `created:` / `reviewed:` fields, then body.
- Follow-Up files: Line 1=`Follow-Up: {ask}` (≤ 80 chars), Line 2=blank, then `type:` / `raised:` / `updated:` / `due:` / `blocks:` / `resolved:` / `outcome:` / `resolution-ref:` fields, then one self-contained ask paragraph.
- Reminder files: Line 1=`Reminder: {subject}` (≤ 80 chars), Line 2=blank, then `created:` / `updated:` / `due-at:` / `timezone:` / `target:` / `reopens:` / `outcome:` fields, then one standalone reminder paragraph.
- Task entries in `TASKS.md`: lowercase field keys `label:` / `status:` / `created:` / `updated:` / `completed:` / `cancelled:` / `delivers:`, one per line (YAML-parseable), then a short description and a `[Details...]` link. `updated:` is an exact UTC timestamp or the migration-only value `Unknown`; `delivers:` is `N/A` when no Deliverable applies, otherwise use the exact Deliverable name from `_Axis/PROJECT.md`.
- Snapshot entries in `SNAPSHOTS.md`: a `## {timestamp}` heading, a < 200-word summary, and a `[Details...]` link.
- Marker files: Line 1=Subject (`Main: session`, `External: {host}`, or `Subagent: {role}`), Line 2=blank. Main and External Markers carry `session: {Session ID}` plus the host; Subagent Markers carry start time, return condition, and Log pointer.
- CX Report files: Line 1=`CX: {topic}`; Audit Report files: Line 1=`Audit: {topic}`; Status Report files: Line 1=`Status: {topic}`; Supervision files: Line 1=`Supervision: {action} - {scope}` (each ≤ 80 chars).
- Directive entries in `DIRECTIVES.md`: a `## {name}` heading with `#### Keywords` / `#### Description` / `#### Triggers` / `#### Behavior` subsections.
- Archive the oldest excess Notes when count exceeds **Max Notes** in Settings.
- Automatic Note archiving is purely count-based - there is no time-based expiry of Notes.
- Archive storage is reversible and lives under `_Axis/Archive/{record-family}/`; WORM records retain their bytes and timestamp identities.
- Only Completed or Cancelled Tasks may be archived. Their canonical index entries remain and link to `Archive/Tasks/{timestamp}.md`.
- Open Follow-Ups live only in `_Axis/Followups/`; terminal Follow-Ups self-archive unchanged under `_Axis/Archive/Followups/` and are never restored.
- Open Reminders live only in `_Axis/Reminders/`; terminal Reminders self-archive unchanged under `_Axis/Archive/Reminders/` and reopening creates a new identity.
- `_Axis/Supervision/` keeps the newest 30 active records; oldest excess records move unchanged to `_Axis/Archive/Supervision/` and remain WORM.
