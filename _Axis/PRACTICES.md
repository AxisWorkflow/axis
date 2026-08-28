# Practices
> **Purpose:** Index of all Core Practices, plus the routing table for durable guidance.

## Always-Load Practices - read at Session Start
> **Note:** Practices to always load and read at Session Start.

- [Practices > References] - The Axis Reference notation and how to resolve it.
- [Practices > IndexDetail] - Index-plus-detail storage convention and recipes.
- [Practices > Flags] - Persistent Flags that record durable workflow state.
- [Practices > Markers] - Ephemeral Markers that track in-flight activity.
- [Practices > Commands] - How User invokes Commands and how Agents run them.

## Lazy-Load Practices - read when trigger applies
> **Note:** Practices to read when the trigger applies.

- [Practices > Delegation] - Choose if, where, how to delegate, validate, accept work.
  *Load before delegating work or accepting a Subagent result.*

- [Practices > Agents] - Full operating detail for all Agents, plus the Host Harness.
  *Load when you are a Subagent or an External Agent, or before coordinating roles, spawns, or parallel work.*

- [Practices > OpenClaw] - Thin-harness policy for channels, agents, cron, tools, and disabled Host memory/persona layers.
  *Load when running under an OpenClaw Agent Harness - every Agent on that host follows it.*

- [Practices > Tracking] - Append-only activity telemetry: who doing what, right now.
  *Load before writing a Tracking line, when another live Agent's activity matters, or when summarizing activity.*

- [Practices > Protected] - `_U` read-only and `_X` invisible name-suffix protection.
  *Load when a name ends in `_U` or `_X`, or before a Protect or Release request.*

- [Practices > Planning] - Drafting and maintaining the Plan.
  *Load before drafting or revising `PLAN.md`.*

- [Practices > Tasks] - Recording and tracking Tasks.
  *Load before your first Task work of a session.*

- [Practices > Followups] - The User-facing queue of actions only User can take.
  *Load before raising, changing, resolving, or reporting a Follow-Up.*

- [Practices > Reminders] - Portable time-based surfacing and Reminder lifecycle.
  *Load before creating, changing, resolving, or reporting a Reminder, or when checking due state.*

- [Practices > Portability] - Cross-host continuity, storage policy/profiles, infrastructure restoration, transfer modes, and environment revalidation.
  *Load for every `^save` and `^resume`, an environment-change boot check, transfer planning, or portability claims.*

- [Practices > Settings] - Storing, changing, and overriding Settings.
  *Load before changing any Setting.*

- [Practices > Snapshots] - When and how to save Snapshots.
  *Load before saving a Snapshot (e.g., `^save`).*

- [Practices > Logs] - What to log and how to write WORM entries.
  *Load before your first Log of a session.*

- [Practices > Timestamps] - Project-unique identifier timestamps (check plus claim).
  *Load before minting your first record timestamp of the session.*

- [Practices > Requests] - Cross-boundary messages the receiving Main Agent triages.
  *Load when the queue is non-empty, or before writing into another Project's queue.*

- [Practices > Notes] - Writing, renewing, and archiving Notes.
  *Load for `^note`, `^notes`, renewal, or selecting a Note for Archive.*

- [Practices > Archiving] - Moving inactive history out of routine context.
  *Load for `^archive`, automatic Note overflow, restoration, or Archive checks.*

- [Practices > Trash] - Stage deletions in `_Trash/`; sweeps empty it.
  *Load before deleting a file or when a host blocks deletion.*

- [Practices > Ideas] - Recording and reviewing Ideas.
  *Load for `^idea`, `^ideas`, or an Ideas review.*

- [Practices > Mindset] - How the behavioral Mindset is generated and followed.
  *Load when regenerating Mindset.*

- [Practices > Directives] - Conditional Directives and trigger design.
  *Load when adding or revising a Directive.*

- [Practices > Status] - Composing and saving Status Reports.
  *Load for `^status`.*

- [Practices > CX] - The CX Subagent process.
  *Load when spawning or performing a CX.*

- [Practices > Wiki] - Wiki architecture and procedures.
  *Load before any Wiki work.*

- [Practices > Dashboard] - The Dashboard web app.
  *Load for `^dashboard` or Dashboard revisions.*

- [Practices > GIT] - Adaptive setup, synchronization, checkpoints, encrypted Secrets transport, and rollback.
  *Load before any Git action, and during the Git phases of `^save` and `^resume`.*

- [Practices > Subprojects] - Containment, recognition, ownership, inheritance.
  *Load when a Subproject is detected.*

- [Practices > Supervision] - Direct-child discovery, `^^` commands, authority, records, and Host fallbacks.
  *Load when a message begins `^^`, for `^audit supervision`, or before supervisory observation or lifecycle work.*

- [Practices > Folders] - Project Subfolder creation and reorganization.
  *Load before creating or reorganizing a Project Subfolder.*

- [Practices > WhatsApp] - Set up text messaging with WhatsApp via OpenClaw.
  *Load when User asks to set up a text messaging channel with WhatsApp.*

## Behavioral Guidance
> **Note:** Where durable guidance belongs; routing only - there is no file to load.

Several files carry behavioral guidance, and choosing between them is a judgment call. Route by what the guidance IS, not by where it came from:

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
