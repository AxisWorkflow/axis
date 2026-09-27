# Archiving
> **Purpose:** Move inactive history out of routine context without deleting it or weakening record integrity.

The Archive is reversible, low-context storage under `_Axis/Archive/` or the folder named by [Settings > Archive Location] (see Archive Location below). It preserves history while keeping active record directories focused. Archiving moves a record unchanged; it never rewrites a WORM body, erases evidence, or makes an inactive record look current.

## Archive Location

Every path written `_Axis/Archive/...` in Axis means the same path under the Archive root, and an index link `Archive/{Family}/...` resolves there too:

- Read [Settings > Archive Location]. A missing Setting means the default `_Axis/Archive/`. A project-relative value resolves from the project root; an absolute value names a folder outside the project. Never store a credential, account or host identifier in the value.
- Resolve the root before every Archive read or write. The default root and its family folders are created on first use. A non-default root is **available** only when it already exists as an ordinary directory; never create a missing non-default root, because an absent mount point would silently become local storage.
- When the root is unavailable (unmounted drive, offline share, another machine, malformed value), say so plainly and let only the Archive work wait. Never fall back to `_Axis/Archive/` or split the Archive across two folders. Everything else in Axis continues.
- A self-archiving record (terminal Follow-Up, terminal Reminder, triaged Request) that cannot move stays in its live folder with its terminal fields already written. It counts as closed, pending archive: readers, the queue checks and Session Start treat it as resolved, never as open work to redo. Report the count once per session, and finish the unchanged move the next time the root is available (`^refresh` or the next such closing step).
- Timestamp uniqueness and index-link checks that need an unavailable root cover the live half only and report the archived half unverified.
- The in-project `_Axis/Archive/` folder always remains with its `.gitkeep`; Session Start may leave an empty `Requests/` folder there. While another root is set, no archived record is written there.

**Changing the location** is a User-confirmed move, never a silent redirect. Show the old and new roots, the family counts and any collisions; require User to confirm with `ARCHIVE`. Copy every record to the new root, verify identical bytes and names, update the Setting, then remove the old copies (leaving `_Axis/Archive/.gitkeep`). Stop without removing anything if a copy, verification or the Setting write fails. Log the move.

**Archive in Git** controls whether an in-project Archive is committed. When [Settings > Archive in Git] is `false` and the root is inside the project, `.gitignore` carries exactly this block, and already tracked archived records are untracked with `git rm -r --cached` (the files stay on disk):

	# Archive in Git = false (see _Axis/SETTINGS.md)
	_Axis/Archive/*
	!_Axis/Archive/.gitkeep

Keep `_Axis/Archive/.gitkeep` tracked so the Manifest folder exists in every clone. When the value returns to `true`, remove that block; the next checkpoint commits the Archive again. A root outside the project is never committed, whatever the value. Apply either change with User's Setting change under [Practices > GIT], and Log it.

## Layout

Create a family folder on first use under the Archive root and retain the record's original filename:

	_Axis/Archive/Notes/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Ideas/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Logs/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Snapshots/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Tasks/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/CX/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Audit/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Status/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Supervision/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Followups/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md
	_Axis/Archive/Reminders/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md

Do not pre-load Archive contents at Session Start. Inventory them by family, filename, Line-1 Subject, and structured fields; lazy-load a body only when User asks for archived history or it is needed to restore or verify a record.

## Eligibility

- Notes, Ideas, Logs, Snapshots, CX Reports, Audit Reports, Status Reports, and Supervision records may be archived.
- A triaged request moves to `_Axis/Archive/Requests/` as the closing step of its own adjudication ([Practices > Requests]), not by `^archive`. It self-archives because leaving a resolved request in the live queue would break the empty-queue invariant the per-turn glance depends on. An un-triaged request is never archived - triage it.
- A terminal Follow-Up moves to `_Axis/Archive/Followups/` as the closing step of its own lifecycle ([Practices > Followups]), not by `^archive`. An open Follow-Up is never archived. A terminal Follow-Up is never restored; reopening creates a new record that references the old identifier.
- A terminal Reminder moves to `_Axis/Archive/Reminders/` as the closing step of its own lifecycle ([Practices > Reminders]), not by `^archive`. An open Reminder is never archived. Reopening mints a new record that references the old identifier.
- A Task may be archived only when its Status is **Completed** or **Cancelled**. Active and Blocked Tasks remain live.
- A WORM record remains WORM in the Archive. Its bytes and timestamp filename do not change.
- Markers are never archived. Delete a finished or stale Marker; when deletion is unavailable, clear it or move it to `_Trash/` under [Rules > HostAndMeta > Deletion Fallback].
- Flags, locks, `_Temp/`, `_Axis/Secrets/`, Wiki content, current project files, Project Subfolders, and everything inside a nested Subproject are not archive records.

## Automatic Note Overflow

[Settings > Max Notes] limits active Notes, not retained history. When `_Axis/Notes/` exceeds the limit:

1. Review the oldest Notes and renew any still-current important Note by moving its content to a correctly current timestamp as defined in [Practices > Notes].
2. Select the oldest remaining Notes until the active count equals **Max Notes**.
3. Move them unchanged into `_Axis/Archive/Notes/`. With **Max Notes** set to zero, archive every active Note.
4. Verify every source path is gone, every destination has identical content, and no destination was overwritten.
5. Tell User what moved and include it in the next Log Event.

This overflow is already authorized by the Setting and is reversible, so it needs no extra confirmation.

## Automatic Supervision Overflow

`_Axis/Supervision/` retains a fixed active window of the newest 30 records. After every record-producing `^^` command, and during `^refresh` crash recovery:

1. Inventory live Supervision records by valid timestamp filename without pre-loading bodies.
2. If more than 30 exist, select the oldest excess until exactly 30 remain live.
3. Move each selected record unchanged into `_Axis/Archive/Supervision/`; never overwrite a destination or rewrite the WORM body.
4. Verify source absence, destination presence, identical content, and no live/archive collision.
5. Include the moved paths in the parent Log Event or `^refresh` Event that followed the overflow; never revise the already-created WORM Supervision record to add them.

This fixed window is an implementation bound, not a retention limit. It needs no confirmation because the move is automatic, reversible, and lossless. `^archive` may move more history under User's selected boundary; nothing automatically deletes archived Supervision records.

## User-Requested Archive

The `^archive` command is the only general archive operation. Before moving anything, it asks User both which record families belong in scope and how much back-history should remain active. Accepted boundaries include:

- a UTC cutoff: archive records older than it
- keep the newest N records active in each selected family
- a named list of records
- all eligible inactive history

There is no destructive or guessed default. Present the resolved files, count, size, exclusions, and any index-link changes, then require User to confirm with `ARCHIVE`.

## Indexed Records

Tasks and Snapshots remain visible in their canonical indices after archiving. Move the detail file and atomically change its `[Details...]` link:

- `Tasks/{timestamp}.md` becomes `Archive/Tasks/{timestamp}.md`
- `Snapshots/{timestamp}.md` becomes `Archive/Snapshots/{timestamp}.md`

For an archived Task with `initiative:` membership, also update its reciprocal link in the matching `_Axis/INITIATIVES.md` section under [Practices > Initiatives], retaining the Task timestamp and Initiative key. Do not archive the Initiative automatically.

The links are relative to `_Axis/TASKS.md` and `_Axis/SNAPSHOTS.md`. A sync check accepts either live or Archive detail path, but every linked file must exist and every eligible detail file must have exactly one index entry.

## Safe Move and Restore

1. Resolve every source and destination exactly. If any destination exists, STOP; never overwrite or invent a second identity.
2. Acquire the applicable [Lock-File]. For indexed records, lock the index and detail paths as one operation.
3. Create only the needed family folder, then use an atomic same-volume rename when the Host supports it.
4. Update an indexed record's link in the same protected operation.
5. Verify source absence, destination presence, identical content, valid index links, and zero paths under `_Axis/Archive/Agents/`.
6. Release locks and Log the archive operation after all moves finish, so the new Log cannot accidentally enter the same batch.

Restore by reversing those steps: require an empty live destination, move the unchanged file back, atomically restore its live index link when applicable, verify, and Log the restoration. Never restore a terminal Follow-Up or Reminder. Never restore an archived Task to Active or Blocked merely by moving it; changing Task Status is a separate User-directed operation. Restoring Supervision records may not leave more than 30 active; if it would, require User to select which current records move to Archive in the same operation.
