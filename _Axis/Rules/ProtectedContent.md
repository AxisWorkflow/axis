# Protected Content
> **Purpose:** The `_U` and `_X` name suffixes, and who may change protection.


- A trailing `_U` on a folder or file marks it User-controlled: Agents read freely but never write, edit, delete, rename, or create inside it. A trailing `_X` marks it excluded: never read, never descended into, never loaded into any Agent's context. Exact-case; a folder's suffix governs its whole subtree. See [Practices > Protected].
- Non-interpreting bulk operations (`^backup`, version control) still cover protected content; `_X` stays out of the Wiki, Snapshots, search, and every summary.
- Only Main Agent changes protection, only on explicit User instruction, by renaming - with reference repair, a WORM Event, and explicit confirmation before any Release.
- Governing files, as listed in [Rules > UntrustedContent], are never written by a delegated agent unless its contract grants it. Where the host guard is installed it refuses file-tool writes to them even then, and Main applies a granted change itself; shell writes and hosts without the guard rely on compliance.
