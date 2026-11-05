# Context Check
> **Purpose:** Recover Axis guidance after compaction when Python is unavailable.

The entry file's "After compaction" section sends you here when `turn.py --recover` cannot run. Re-read every file of your role's set in full, with bounded reads to each file's end; a summary of a file is not the file.

## Recovery sets

| Role | Re-read in full | State to recover |
| --- | --- | --- |
| Main | `_Axis/Resources/Starting-Context.md` through `_Axis/Resources/Load-Starting-Context.md`; `_Axis/Roles/Main.md`; `_Axis/INSTRUCTIONS.md`; `_Axis/MINDSET.md`; `_Axis/DIRECTIVES.md`; any project overlay, revalidated under `_Axis/Resources/Load-Project-Overlay.md` (activate) | Your last Tracking INTENT or STATUS, the newest Logs, Active Tasks, open Follow-Ups, the newest Snapshot |
| Auxiliary | The startup core as above; `_Axis/Roles/Auxiliary.md`; [Practices > Agents > Auxiliary Agent] | Your last Tracking INTENT or STATUS, the newest Logs |
| Assistant, Group Agent | The startup core; your own role file | Your last Tracking INTENT or STATUS |
| Observer | The startup core; `_Axis/Roles/Observer.md` | None; it writes nothing |

## Without Python

1. Keep your lease without the helper: [Displaced-Session > Persistent hosts and no-shell parity].
2. Re-read your role's set, then recover state from the records named above.
3. Keep every User hold or limit a summary mentions; take no approval for a User-only action from a summary alone.
4. Re-read the set again every tenth turn and before any commit, push, spawn, publication or deletion, because nothing checks for a later loss.
