# ^archive
> **Purpose:** Move selected inactive history into reversible, low-context Archive storage.

1. Read [Practices > Archiving].

2. Inventory live and archived records by family, filename, Line-1 Subject, structured fields, count, and size. Do not load full bodies merely to build the inventory.

3. Ask User:
	- a. Which eligible record families to include.
	- b. How much back-history to leave active: a UTC cutoff, newest N per family, named records, or all eligible inactive history.

4. Resolve an exact proposal. Supervision is an eligible family; preserve the newest 30 active records unless User explicitly selects a smaller active window. Exclude Active and Blocked Tasks, all live or archived Follow-Ups and Reminders (both self-archive; reopening mints a new record), and every Marker, Flag, lock, temp file, Wiki file, current project file, Project Subfolder, and everything inside a nested Subproject. Parent archive operations never enter a Subproject. Show the source and destination paths, count, total size, exclusions, and every Task or Snapshot index-link edit.

5. Require the literal confirmation `ARCHIVE`. Any other response leaves the project unchanged.

6. Follow [Practices > Archiving > Safe Move and Restore]. Stop without partial overwrite if a collision or unsafe link state is found. If the Host cannot delete a Marker discovered during cleanup, use [Rules > HostAndMeta > Deletion Fallback]; never move it into the Archive.

7. Verify that each source is absent, each destination has identical content, all indexed links resolve, every archived Task is terminal, and no Marker exists anywhere under `_Axis/Archive/`.

8. Log one Event after the move with the requested boundary, moved paths, exclusions, index edits, verification result, and any restoration instructions. Report the result to User. STOP.
