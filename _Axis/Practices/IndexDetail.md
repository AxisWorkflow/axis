# Index-Detail Pattern
> **Purpose:** Define the index-plus-detail storage convention and its recipes.

## The Name Is the Contract

Every detail file in the canonical directories below is named with a UTC timestamp and nothing else:

	{yyyy.mm.dd.hh.mm.ss.xxxZ}.md

	2026.05.18.22.33.24.230Z.md - correct
	2026.05.18.22.33.24.md - WRONG, milliseconds and Z dropped
	2026-05-18T22-33-24Z.md - WRONG, not the Axis format
	survey-results-final.md - WRONG, describes the content instead of time

Four-digit year, two digits for each of month, day, hour, minute and second, three digits of milliseconds, then a capital `Z`, then `.md`. Every field is zero-padded. Nothing is optional and nothing is abbreviated.

This is not a formatting preference. The name is the record's identity: it sorts the project's history, it is the join between an index entry and its detail file, and it is how an Agent on a different model or a different platform finds what an earlier Agent wrote. A file named any other way is not a stylistic variation - it is a record that later Agents will not find, and the damage compounds silently because nothing errors at the time.

The name is also unique across the entire Project - no timestamp names two records, in any directory, live or archived - so a bare timestamp resolves through active/family-local history or a locally retained cold locator. Mint every identifier per [Practices > Timestamps]; Subprojects are separate uniqueness domains.

Memos share the timestamp uniqueness domain but remain outside the Index-Detail pattern: their names retain a subject after the timestamp under [Practices > Memos].

Get the name right first, then write the content.

## How the Pattern Works

This section describes how Axis splits summary information and detailed information to enable lazy-loading and better memory management. This is referred to as the Index-Detail Pattern - a convention wherein there is an index of available items (often with a summary), and then a detail file that corresponds to each item in the index. The detail file is named with a UTC timestamp and holds the body of information.

These directories conform to the **Index-Detail Pattern:**

- `_Axis/Agents/`
- `_Axis/Audit/`
- `_Axis/CX/`
- `_Axis/Followups/`
- `_Axis/Ideas/`
- `_Axis/Logs/`
- `_Axis/Notes/`
- `_Axis/Reminders/`
- `_Axis/Snapshots/`
- `_Axis/Reviews/` (legacy: Reviews written before 2.08, until the first startup on 2.08 moves them to `_Memos/Archive/`; new Reviews are Memos)
- `_Axis/Supervision/`
- `_Axis/Tasks/`
- `_Axis/Teams/`
- `_Axis/Messages/`
- `_Axis/Jobs/`
- `_Axis/Schedules/`

The Index-Detail Pattern is implemented in three ways:

- **Directory** (as the index) + **File** (with the detail)

  The directory is the index - compile a live index by scanning the first line of each file. No sidecar index file exists. To filter by type, scan Subject lines (e.g., `CX:` for CX Reports, `Audit:` for Audit Reports, `Review:` for Reviews, `Subagent:` for Subagent Markers).

  Ideas, Follow-Ups, Reminders, Logs, Notes, CX Reports, Audit Reports, Reviews, and Supervision records follow this method. (Ideas, Follow-Ups, Reminders, and Supervision records add bare `key: value` fields after their Subjects - see their Practices.)

- **Summary File** (as the index) + **File** (with the detail)

  A file with summary information is the index (including cross-file state that a first-line scrape of the detail files will not catch) and multiple detail files catch the full information (one index file and many supporting detail files). The index file and the contents of the directory must stay in sync: if you write a detail file, also append an entry to the index, and vice versa.

  Tasks (`_Axis/TASKS.md` + `_Axis/Tasks/`) and
  Snapshots (`_Axis/SNAPSHOTS.md` + `_Axis/Snapshots/`) follow this method. Teams, Messages, Jobs and Schedules have small rebuildable uppercase indexes; accepted events, not index rows, determine their state. Optional `Teams/{ID}/` work folders are companions, not extra identities. See [Practices > Coordination].

- **Directory-index + Marker**

  A Marker is written as short-term, ephemeral status (not as history). Markers older than 1 hour are presumed dead and obsolete and should be deleted during cleanup, never archived. Check Markers for consistency, and warn if necessary - but do not block.

  Tracking Agents and/or Subagents in `_Axis/Agents/` follows this method. A Marker is written on Subagent spawn and deleted on Subagent return.

Implementation notes:

- Each detail file is named `{yyyy.mm.dd.hh.mm.ss.xxxZ}.md` (see The Name Is the Contract above - this is the one convention with no acceptable variation).
- A record's timestamp is a claim about its content. WORM records never change, so the claim holds by construction; a record that may still change must either move its timestamp with the content (rename it) or carry the change in a field it already defines (`reviewed:` on an Idea, `completed:` on a Task). Never leave revised content sitting under a stale timestamp.
- Each detail file has a subject on Line 1 of the file (≤ 80 chars).
- Scanning filenames and first line from each file will dynamically create an index.
- Lazy-load the entire file ONLY when doing so is actually needed.
- On a filename collision - anywhere in the Project, not just the target directory - increment `xxx` (milliseconds) to prevent merge/overwrite (see [Practices > Timestamps]).
- `xxx` (milliseconds) is always the real millisecond time - mint it with the command in [Practices > Timestamps] step 1, which falls back past BSD/macOS `date` (no `%N`) to an interpreter that has them. Never fill `xxx` with `000` because `date` would not produce it.
- Reserve manual increment of milliseconds for when two mints collide.
- Archived records retain their identity in `_Axis/{Family}/Archive/`; legacy Archive Location remains readable during migration. Reserved `COLD.md` catalogs index timestamped `_Axis/ColdStorage/` retrieval details. Original cold record IDs stay reserved offline and do not create duplicate canonical Tasks.

Implementation recipes for working with Follow-Ups, Reminders, Ideas, Logs, Notes, Snapshots, Supervision, and Tasks:

- `for f in *.md; do head -1 $f; done` - compile an index of all files with subjects.
- `ls -t <dir>/ | head -10` - query the 10 most recent entries.
- `ls <dir>/2026.05.04*` - query entries from a specific date.
- `grep -l "phrase" <dir>/*.md` - query for files containing a phrase.
- `grep -l "^priority: high" _Axis/Ideas/*.md` - query Ideas by a bare field.
