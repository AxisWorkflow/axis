# Trash
> **Purpose:** Stage deletions in `_Trash/` so pending deletes stay visible, reversible until swept, and cleaned up mechanically.

`_Trash/` is the project's deletion staging area: everything inside it except `.gitkeep` is awaiting permanent deletion. Moving a file there IS the approved delete - the two-step shape changes where deletes go, never whether something may be deleted - so every confirmation rule in [Rules] applies BEFORE the move, and a sweep never re-asks.

A trashed item stays recoverable for at least **2 days**. Automatic sweeps delete only items older than that, so "it is in `_Trash/`" is a real rollback for two days, not only until the next session starts. (Until Version 2.01 every startup emptied `_Trash/`, so an item trashed in one session could be gone minutes later when the next one started.)

## Trashing a File

1. Trash only dead material that is safe to lose; anything worth keeping is archived or left in place, never trashed. Confirm the deletion exactly as if deleting outright, under [Rules > Permissions].
2. Ensure `_Trash/` exists and contains `.gitkeep`; quietly recreate either if missing (User may have deleted the whole folder - that is fine and expected).
3. Move (rename) the file or directory into `_Trash/`, prefixing its name with the current UTC date and two hyphens: `_Trash/{yyyy-mm-dd}--{original name}`. The prefix is the item's trash date; sweeps read it, so never omit it. On a name collision, append `-2`, `-3`, ... to the moved name until it is free. Renaming works on hosts where deleting does not, which is why this is also the standard route under [Rules > HostAndMeta > Deletion Fallback].
4. A trashed item stays recoverable until a sweep deletes it (at least 2 days): if User asks for it back, move it back out and remove the date prefix.

## Sweeping the Trash

- Session Start, `^resume`, and `^refresh` sweep `_Trash/` by age: delete each item whose `{yyyy-mm-dd}--` prefix is 2 or more days before today (UTC), keep everything younger, recreate `.gitkeep` if absent, and report a one-line count of what was removed (`^refresh` lists the names). An item without a valid date prefix (placed there by hand or by an older version) is not deleted: rename it to carry today's date, which starts its 2 days, and include it in the report. If a trustworthy current date is unavailable, delete nothing.
- `^trash` empties on demand, regardless of age, (long-lived sessions accumulate trash): it offers "Delete All?" or "Review Item-by-Item and Delete?". A plain-language request to empty the trash (without the Command) is confirmed with the literal reply `TRASH` first - conversationally requested irreversible deletion warrants one explicit token.
- Sweeps do not re-confirm - anything in `_Trash/` was staged deliberately under the rule above - but they always report, so nothing vanishes silently.
- If the host blocks even this deletion, leave the contents in place, report the count, and remind User to empty `_Trash/` themselves. Do not loop on retries.

## Boundaries

- `_Trash/` is excluded from version control except its `.gitkeep`, and a release ships it empty with exactly that placeholder.
- WORM records (Logs, Snapshots, CX, Audit, Status, terminal Tasks) and archived history belong in [Practices > Archiving], not here - Archive preserves, Trash destroys. Trash one only on User's explicit, named instruction.
- Each Subproject has its own `_Trash/`; a parent never sweeps a child's Trash.
- `_Trash/` is not storage: never park work in it, and never read trashed content back into work without restoring it first.
