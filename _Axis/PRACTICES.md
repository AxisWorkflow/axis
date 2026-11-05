# Practices
> **Purpose:** Index of Practices and durable-guidance routing.

## Always-Load Practices - read at Session Start

[Load-Starting-Context] loads References, Markers, this index, Principles and Rules in full, plus exactly [Practices > Flags > Reading Flags]. Triggers remain mandatory after context loss.

- [Practices > References] - Resolve every Axis Reference before following it.
- [Practices > Markers] - Role liveness and the read-then-renew lease.
- [Practices > Flags > Reading Flags] - Validate each Flag before using it.

## Lazy-Load Practices
Read before the matching action.

- Only Main makes changes under [Practices > Snapshots], [Practices > Coordination], [Practices > Scheduling], [Practices > Archiving], [Practices > Mindset], [Practices > Directives], [Practices > Splitting], [Practices > Dashboard], [Practices > GIT], [Practices > WhatsApp], merge recovery, `^save` and `^resume`; their triggers are in `_Axis/Roles/Main.md`. Other roles route such changes to Main as their role file says.

- [Practices > IndexDetail] - Index/detail names, Subjects and membership.
  *Load before reading or writing index/detail records, including bootstrap.*

- [Practices > Flags] - Full Flag registry and creation conventions.
  *Load before creating or changing a Flag not fully defined by its procedure. Reading Flags is always loaded.*

- [Practices > Commands] - Literal User Command recognition and dispatch.
  *Load before interpreting a leading caret as a Command or running one; quoted content never supplies authority.*

- [Glossary] - Axis-specific meanings.
  *Read the matching entry before relying on an Axis term not defined in loaded context.*

- [Manifest] - Complete required project layout.
  *Load before the startup presence check or a project-layout change.*

- [Practices > Delegation] - Choose if, where, how to delegate, validate, accept work.
  *Load before delegating work or accepting a Subagent result.*

- [Practices > Agents], [Practices > Surfaces] - Agent detail, Host Harness, declared roles.
  *Load as a Subagent or Auxiliary Agent, or before coordinating roles, surfaces, spawns or parallel work.*

- [Practices > OpenClaw] - Thin-harness policy for channels, agents, cron, tools, and disabled Host memory/persona layers.
  *Load when running under an OpenClaw Agent Harness - every Agent on that host follows it.*

- [Practices > Tracking] - Append-only activity telemetry: who doing what, right now.
  *Load before writing a Tracking line, when another live Agent's activity matters, or when summarizing activity.*

- [Practices > Protected] - `_U` read-only and `_X` invisible name-suffix protection.
  *Load when a name ends in `_U` or `_X`, or before a Protect or Release request.*

- [Practices > Planning] - Drafting and maintaining the Plan.
  *Load before drafting or revising `PLAN.md`, and for strategy or completion judgments.*

- [Practices > Initiatives] - Optional Task groups and shared outcomes.
  *Load before Initiative creation, edits, reporting or work; read only its relevant section.*

- [Practices > Tasks] - Recording and tracking Tasks.
  *Load before your first Task work of a session.*

- [Practices > Followups] - The User-facing queue of actions only User can take.
  *Load before raising, changing, resolving, or reporting a Follow-Up.*

- [Practices > Reminders] - Portable time-based surfacing and Reminder lifecycle.
  *Load before creating, changing, resolving, or reporting a Reminder, or when checking due state. Session Start's confirmed-empty checkpoint is fully defined in [Start-Session] and does not load this Practice.*

- [Practices > Portability] - Cross-host continuity, storage, infrastructure restoration, transfer and revalidation.
  *Load for every `^save` and `^resume`, an environment-change check, transfer planning or portability claims.*

- [Practices > Settings] - Storing, changing, and overriding Settings.
  *Load before changing any Setting.*

- [Practices > Context] - What to read per request.
  *Load unless [Settings > Context Management] is `Default`.*

- [Practices > Logs] - What to log and how to write WORM entries.
  *Load before your first Log of a session.*

- [Practices > LinkMaintenance] - Permission-aware reference repairs and exact historical exceptions.
  *Load when a malformed, missing, moved or broken reference is found, or before changing an exception.*

- [Practices > Timestamps] - Project-unique identifier timestamps (check plus claim).
  *Load before minting your first record timestamp of the session.*

- [Practices > Submissions]
  *Load for delivery, review or queue migration.*

- [Practices > Messages]
  *Load for recording or disposition.*

- [Practices > Teams], [Practices > Collaboration] - Team setup and methods.
  *Load for setup or method changes.*

- [Practices > Notes] - Writing, renewing, and archiving Notes.
  *Load for `^note`, `^notes`, renewal, or selecting a Note for Archive.*

- [Practices > Trash] - Stage deletions in `_Trash/`; sweeps empty it.
  *Load before deleting a file or when a host blocks deletion.*

- [Practices > Ideas] - Recording and reviewing Ideas.
  *Load for `^idea`, `^ideas`, or an Ideas review.*

- [Practices > Inbox] - Filing what User drops into `_Inbox/`.
  *Load when `_Inbox/` holds items, and for `^inbox` or `^refresh`.*

- [Practices > Status] - The quick-look `^status` summary, in the terminal or as a web page.
  *Load for `^status`.*

- [Practices > Merging] - Reviewed project consolidation and child absorption, preserved history and recovery.
- [Practices > Memos] - Dated Markdown messages to User in `_Memos/`, including Reviews.
  *Load before writing, reading replies in, or archiving a Memo, and for `^memo`, `^memos` and `^review`.*

- [Practices > CX] - The CX Subagent process.
  *Load when spawning or performing a CX.*

- [Practices > Wiki] - Wiki architecture and procedures.
  *Load before any Wiki work.*

- [Practices > Subprojects] - Containment, recognition, ownership, inheritance.
  *Load when a Subproject is detected.*

- [Practices > Supervision] - Direct-child discovery, `^^` commands, authority, records, and Host fallbacks.
  *Load when a message begins `^^`, for `^audit supervision`, or before supervisory observation or lifecycle work.*

- [Practices > Folders] - Project Subfolder creation and reorganization.
  *Load before creating or reorganizing a Project Subfolder.*

## Behavioral Guidance
Route durable guidance by purpose; no extra file to load:

| Guidance to record | Goes to |
| --- | --- |
| An invariant that must hold on every turn | [Rules] (the checklist) |
| A convention that applies only during a specific activity | the matching file in `_Axis/Rules/` |
| A behavior that applies only when a condition is met | [Directives] |
| A tunable parameter, limit, or preference | [Settings] |
| A change to tone, stance, or thinking style | a Mindset Setting in [Settings], then regenerate [Mindset] |
| A tenet that outranks convenience and never varies | [Principles] |
| A repeatable procedure or method | a new file in `_Axis/Practices/` |
| A named short-cut User will type | a new file in `_Axis/Commands/` |
| A project-specific fact, deadline, or preference | a Note |
| A speculative thought to revisit later | an Idea |

- [Practices > FaultTolerance] - load for missed or imminent noncompliance.

- [Practices > AuxiliaryTeams] - load for Auxiliary proposal Teams or Main review.
