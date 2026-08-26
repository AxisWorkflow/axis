# Trash
> **Purpose:** Stage deletions in `_Trash/` so pending deletes stay visible, reversible until swept, and cleaned up mechanically.

`_Trash/` is the project's deletion staging area: everything inside it except `.gitkeep` is awaiting permanent deletion. Moving a file there IS the approved delete - the two-step shape changes where deletes go, never whether something may be deleted - so every confirmation rule in [Rules] applies BEFORE the move, and a sweep never re-asks.

## Trashing a File

1. Confirm the deletion exactly as if deleting outright ([Rules]: confirm with User before deleting any file you did not create as scratch).
2. Ensure `_Trash/` exists and contains `.gitkeep`; quietly recreate either if missing (User may have deleted the whole folder - that is fine and expected).
3. Move (rename) the file or directory into `_Trash/`. On a name collision, append `-2`, `-3`, ... to the moved name until it is free. Renaming works on hosts where deleting does not, which is why this is also the standard route under [Rules > HostAndMeta > Deletion Fallback].
4. A trashed item stays recoverable until a sweep runs: if User asks for it back, move it back out.

## Sweeping the Trash

- Session Start, `^resume`, and `^refresh` sweep `_Trash/`: delete everything except `.gitkeep`, recreate `.gitkeep` if absent, and report a one-line count of what was removed (`^refresh` lists the names).
- `^trash` empties on demand between sweeps (long-lived sessions accumulate trash): it offers "Delete All?" or "Review Item-by-Item and Delete?". A plain-language request to empty the trash (without the Command) is confirmed with the literal reply `TRASH` first - conversationally requested irreversible deletion warrants one explicit token.
- Sweeps do not re-confirm - anything in `_Trash/` was staged deliberately under the rule above - but they always report, so nothing vanishes silently.
- If the host blocks even this deletion, leave the contents in place, report the count, and remind User to empty `_Trash/` themselves. Do not loop on retries.

## Boundaries

- `_Trash/` is excluded from version control except its `.gitkeep`, and a release ships it empty with exactly that placeholder.
- WORM records (Logs, Snapshots, CX, Audit, Status, terminal Tasks) and archived history belong in [Practices > Archiving], not here - Archive preserves, Trash destroys. Trash one only on User's explicit, named instruction.
- Each Subproject has its own `_Trash/`; a parent never sweeps a child's Trash.
- `_Trash/` is not storage: never park work in it, and never read trashed content back into work without restoring it first.
