# ^archive
> **Purpose:** Run the saved archiving policy, optionally changing it for future rounds.

Usage: `^archive [Never|Default|Aggressive] [--dry-run]`. Accept case-insensitive levels and normalize `Agressive` to `Aggressive`. Reject unknown, duplicate or conflicting options before any mutation.

1. Read [Practices > Archiving]. With no level, use [Settings > Archiving], defaulting to Default only when absent. An explicit valid level is saved before the round. With `--dry-run`, preview the proposed level without saving it or changing any files.
2. At Never, report disabled policy moves. Completed operational recovery still follows its separate lifecycle. Do not ask User to pick families again: the command authorizes the routine reversible policy batch under Default/Autonomous Permissions. Apply [Rules > Permissions] to the exact actions it governs, including Restricted approval requirements.
3. Recover eligible Message closures through [Practices > Messages > Directory discovery and retention], using the saved level and preserving missing-integration holds. Then inventory eligible local history and cold candidates, classify dependencies, and resolve exact paths. Use the optional `archive-storage.py plan|run` accelerator for simple records; follow the complete Practice for related support, link corrections, overflow and legacy migration. A helper hold is work to review, never permission to force a move.
4. Complete verified local moves and active-index pruning. Cold export requires an approved available destination, exact reviewed selection, copy/hash verification, durable catalogs, then checkpoint and checked source retirement. When unavailable, keep the source and finish unrelated local moves. Resume existing bundle IDs instead of duplicating them.
5. Verify names, links, identities and required accounting. Log one concise round Event. Report local moves, cold copies/retirement, bytes actually freed, holds and failures. A saved level persists even if some archive work is deferred. No history rewrite, force-push, new service purchase or cold-history deletion is part of this command.

STOP.
