# Protected
> **Purpose:** Name-suffix access control for User-owned content: `_U` marks read-only, `_X` marks invisible.

The name is the contract: a trailing suffix on a folder or file tells every Agent what it may do there. Suffixes are exact-case, checked on the final name segment, and a folder's suffix governs everything inside it recursively.

## The Two Suffixes

- **`_U` - User-controlled (read-only for Agents).** A folder like `Projections_U/` or a file like `Terms_U.md` may be READ freely, but Agents never write, edit, delete, rename, or move it - and never create new files inside a `_U` folder. It is User-curated space; a revision an Agent proposes lands elsewhere (e.g., `Drafts/`) for User to adopt.
- **`_X` - excluded (invisible to Agents).** A folder like `Archive_X/` or a file like `Diary_X.md` is never read, never descended into, and never loaded into any Agent's context. Its name may appear in a directory listing; its content does not exist for Agents. Status answers and audits report it only as "excluded content present."

## The Carve-Out: Non-Interpreting Operations

`_U` and `_X` bind what enters Agent CONTEXT and what Agents may MUTATE - not mechanical bulk operations that neither read nor interpret content. `^backup` copies protected content like everything else (a backup that skips your most-protected files protects nothing), and version control tracks `_U` content normally. `_X` content stays out of the Wiki, out of Snapshots, out of search, and out of every summary.

## Protect and Release

Only Main Agent changes protection, only on explicit User instruction, and the mechanism is a rename:

1. User asks in plain language ("protect my cashflow projections" / "release the correspondence folder").
2. Main confirms the exact target and the resulting name (`Projections/` → `Projections_U/`), notes that renaming changes the path, then applies it.
3. Main repairs references it owns - links in Tasks, records, and Wiki pages that point at the old path - and Logs a WORM Event naming old path, new path, and direction.
4. RELEASING (removing a suffix) is the risky direction: restate what becomes editable or visible, and proceed only on User's explicit confirmation.

## Boundaries

- Suffix conventions bind honest Agents; they are not cryptography. For content that must be technically unreadable, User keeps it outside the project or uses OS permissions.
- External Agents: `_U` and `_X` are never Write-new destinations; `_X` is invisible to them like every Agent.
- Subagents inherit the same rules; Main never routes a Subagent into `_U` for writing or `_X` at all.
- These suffixes are for User content in the open workspace. Workflow folders (`_Axis/`, `_Temp/`, `_Trash/`, `Wiki/`) never carry them.
