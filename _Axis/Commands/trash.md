# ^trash
> **Purpose:** Empty `_Trash/` on demand - everything, or item by item.

1. List the current contents of `_Trash/` (name and age). If empty, say so and STOP.

2. Ask User: "Delete All?" or "Review Item-by-Item and Delete?"
	- **Delete All:** delete everything except `.gitkeep`, recreate `.gitkeep` if absent, and report the count and names.
	- **Review Item-by-Item:** present each item; on Yes delete it, on No leave it in `_Trash/` (it remains staged for the next sweep). Report what was deleted and what remains.

3. If the host blocks deletion, follow [Rules > HostAndMeta > Deletion Fallback]: leave the contents, report the count, and remind User to empty `_Trash/` themselves.

4. Log one Event with the mode used and the count deleted.

Note: sweeps at Session Start, `^resume`, and `^refresh` still empty `_Trash/` automatically - `^trash` exists for long-lived sessions where trash accumulates between sweeps. If User asks in plain language to empty the trash (without typing `^trash`), confirm with the literal reply `TRASH` before deleting - a conversational request to destroy files irreversibly warrants one explicit token. STOP.
