# ^memos
> **Purpose:** List live Memos, read User's replies, and archive finished ones.

1. Main Agent only for changes. An External Agent lists only, and STOPs.

2. Load [Practices > Memos]. List `_Memos/` (not `Archive/`): name, Status, and Updated time from each header. Mark a memo `waiting on you` that was edited after its Updated time as replied.

3. With `archive`, run the Archiving rule in [Practices > Memos] and report what moved. With `replies`, read and handle the replies of each memo marked as replied. Otherwise show the list, `waiting on you` first, then STOP.

4. Log one Event when memos moved or replies were recorded. STOP.
