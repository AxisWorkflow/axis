# Permissions
> **Purpose:** How the Permissions Setting decides when an Agent confirms a change with User before acting, and the gates no level removes.

Permissions ([Settings > Permissions]) sets how often an Agent stops to confirm work it would otherwise do. The question at every level is risk, not size: a large change that destroys nothing and follows User's intent is safe; a small one that cannot be undone may not be.

## Levels

| Level | The Agent confirms before acting when... | It proceeds without asking when... |
| --- | --- | --- |
| `Restricted` | the change deletes, overwrites, moves, renames or otherwise cannot be undone exactly, or User has not asked for it by name | the work is read-only, or it is the exact change User just requested |
| `Default` | User's intent is unclear; the change makes a design or direction choice User has not made; it starts live model or other gated work; or it destroys something that cannot be restored | User's intent is clear and the change carries little risk: it can be undone, or it removes only what is verifiably disposable or already preserved |
| `Autonomous` | User's intent is unclear, or the change cannot be rolled back and getting it wrong would be major | anything else, including design and direction choices that serve User's stated goal and reversible gated work within agreed limits |

Missing, blank or unrecognized values mean `Default`.

## Judging a change

- **Clear intent** means User asked for the change or the outcome it serves, or the project's own records (Plan, Tasks, Initiatives, standing instructions) plainly call for it - for example closing an Initiative whose Tasks are all finished and whose text says it is done. A plausible guess is not clear intent.
- **Little risk** means nothing of value is lost: the change is additive (a Git commit, a new record, a new file), reversible (Git history, `_Trash/` before a sweep, a restorable Archive move), or removes only material verifiably regenerable or saved elsewhere.
- **Rollback** means the prior state can be restored exactly. Say which rollback exists when you rely on it.
- When unsure which side of a line a change falls on, treat it as the more cautious case for the current level.

## Confirmation words

Some Commands ask for a literal word before acting (`ARCHIVE`, `TRASH`). At `Restricted` only User supplies it. At `Default` and `Autonomous`, when the level lets the underlying action proceed, the Agent may supply the word itself: state that it did, and record it in the Command's Log Event. The gates below keep their own confirmation at every level.

## Gates no level removes

Every level still stops for: `^pub`, `^update` and `^promote`; publishing, pushing, rewriting shared history or sending anything outside the project; spending money or paid usage beyond an included subscription; creating, reading or moving Secrets; editing or deleting WORM records or archived history; role, lease and startup rules; deleting or reorganizing a Subproject; and anything a Principle, Rule or [Practices > Protected] forbids. Live model or boot work at `Autonomous` still keeps the project's stated limits. A project's standing instructions may add gates; they may not remove these.

## Acting without asking

When a level lets you proceed, still use the safest mechanism: prefer `_Trash/` or a retained copy to outright deletion, verify before removing, and keep every normal record (Tracking, Logs, index updates). In the final answer, list what you changed without asking, with its rollback, so User can reverse it. A User reply that questions an unconfirmed change is a correction, not a new request: undo it where possible and apply the answer.
