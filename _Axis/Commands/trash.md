# ^trash
> **Purpose:** Empty `_Trash/` on demand - everything, or item by item.

1. List the current contents of `_Trash/` (name and age, read from each item's `{yyyy-mm-dd}--` trash-date prefix). If empty, say so and STOP.

2. Ask User: "Delete All?" or "Review Item-by-Item and Delete?"
	- **Delete All:** delete everything except `.gitkeep`, recreate `.gitkeep` if absent, and report the count and names.
	- **Review Item-by-Item:** present each item; on Yes delete it, on No leave it in `_Trash/` (an automatic sweep deletes it once it is 2 days old). Report what was deleted and what remains.

3. If the host blocks deletion, follow [Rules > HostAndMeta > Deletion Fallback]: leave the contents, report the count, and remind User to empty `_Trash/` themselves.

4. Log one Event with the mode used and the count deleted.

Note: sweeps at Session Start, `^resume`, and `^refresh` delete only items 2 or more days old ([Practices > Trash]) - `^trash` empties younger items on demand. If User asks in plain language to empty the trash (without typing `^trash`), confirm with the literal reply `TRASH` before deleting - a conversational request to destroy files irreversibly warrants one explicit token. STOP.
