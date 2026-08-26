# Glossary
> **Purpose:** Define key terms so Agents can reference definitions.

### Axis and Projects

- **Axis Workflow** - The definitions, configuration, and practices in this repository.
- **Axis** - Synonym for **Axis Workflow**.
- **Workflow** - Synonym for **Axis Workflow**.
- **Axis Reference** - A pointer to another **Axis** file > section > subsection.
- **Project** - The folder (and all its contents) governed by one **Axis Workflow**.
- **Subproject** - A complete Axis **Project** nested anywhere in another Project's workspace, recognized by its Standard Setup Anchors, with its own entry files, reserved folders, and Axis control files.
- **Project Name** - Name for project - set in `# Project:` header on Line 1 of [Project].
- **Project Subfolder** - A content folder in the project root, created and managed by Main Agent - see [Practices > Folders].
- **Core Files** - Canonical set of files in `_Axis/` - see [Manifest].
- **Core Practices** - Core procedures and methods - see [Practices].
- **Core Principles** - Core tenets to follow at all times - see [Principles].
- **Entry-Point File** - `AGENTS.md`, `CLAUDE.md`, or `GEMINI.md` - file a **Host** reads first.
- **Command** - A word prefixed with `^` to invoke a predefined procedure (e.g., `^save`).
- **Supervision Command** - A direct-child oversight procedure prefixed with `^^` and governed by [Practices > Supervision].
- **Dashboard** - A live web overview of the project - see [Dashboard].

### Agents and Roles

- **Agent** - Any LLM instance working on the project: a **Main Agent**, **External Agent**, or **Subagent**.
- **User** - The human owner and director of the project.
- **Main Agent** - The singular Agent that starts a **Session** and coordinates **Subagents**.
- **Supervisor** - The relational function a parent Project's Main Agent performs toward recognized direct child Projects; not a fourth Agent role, Project type, Setting, Flag, or registration.
- **Axel** - Persona name for **Main Agent**.
- **Subagent** - Any Agent started by **Main Agent** to work in an isolated (fresh) context.
- **CX Subagent** - A Subagent that cross-examines and stress-tests work.
- **Wiki Subagent** - A Subagent that ingests new sources into the project Wiki.
- **General Subagent** - Any Subagent that is not one of the predefined types.
- **Supervisor Subagent** - A General Subagent assigned read-only direct-child observation and analysis; supervisory authority remains with parent Main.
- **Local Subagent** - Any Subagent running on a local model (typically via Ollama).
- **Aptitude Check** - The five-fixture screening `^install` runs against a local model.
- **Sentinel Token** - Literal `<<AXIS:SUBAGENT>>` at both boundaries of every Subagent prompt.
- **Role Token** - Token naming a Subagent's role, repeated at both Prompt Envelope boundaries.
- **Prompt Envelope** - Nonce-bound three-line header and footer (`<<AXIS:ENVELOPE:{nonce}:BEGIN>>` / `END`) that prove a Subagent brief arrived intact at both ends; validated against the delivered task body, not host-injected framing.
- **Envelope Nonce** - A fresh random identifier binding one Subagent prompt's opening and closing records.
- **Synopsis** - A briefing drafted by **Main Agent** to give a **Subagent** project context.
- **Cross-Examination** - An independent subagent process to stress-test work.
- **CX** - An abbreviation for "cross-examine" or "cross-examination".

### Sessions and Capabilities

- **Session** - One continuous run of a **Main Agent**, from Session Start to wind-down.
- **Session Start** - The startup protocol in [Resources > Start-Session].
- **Session ID** - Timestamp identifying one **Session** - printed in the Session ID banner after successful Session Start validation; see [Practices > Flags].
- **Capability** - A Host facility that conditionally enables an Axis feature - see [Rules > Capabilities].
- **Host** - Agent harness on which **Axis** runs (e.g., Cowork, Cursor, Ollama).
- **Host Harness** - Synonym for **Host**.
- **Degraded Mode** - Fallback when a **Capability** is missing (e.g., no Subagent spawn).
- **Storage Profile** - Current filesystem-write classification: `atomic`, `serialized`, or `unknown` - see [Practices > Portability].
- **Environment Signature** - Optional non-secret local change-detection hint; never identity, authority, or portable truth - see [Practices > Portability].
- **Infrastructure Declaration** - One non-secret `_Axis/ENVIRONMENT.md` row describing a non-portable prerequisite, fallback, safe revalidation, and restoration reference - see [Practices > Portability].
- **Flag** - A persistent file to record durable workflow state - saved in `_Axis/Flags/`.
- **Marker** - An ephemeral file tracking live Agents (Main, External, and Subagent sessions) - in `_Axis/Agents/`.
- **Request** - A cross-boundary message in `_Axis/Requests/`, triaged by the receiving Main Agent - see [Practices > Requests].
- **Tracking** - Append-only per-agent activity telemetry in `_Axis/Tracking/` - one line per checkpoint; telemetry, not evidence (see [Practices > Tracking]).
- **External Agent** - The third Agent role: a restricted always-on agent (read-only, append-only, and Write-new classes) serving beside Main - see [Practices > Agents > External Agent].
- **Tombstone** - `_Axis/Agents/{ID}.kill` - the kill signal that revokes an Agent's Marker lease (see [Practices > Markers > The Lease]).
- **Protected Content** - Name-suffix access control: `_U` = User-controlled, read-only for Agents; `_X` = excluded, invisible to Agents (see [Practices > Protected]).
- **Stale** - Past freshness window (locks 10 sec; `starting` 2 min; `session-id` completion check 60 sec; **Markers** 1 hour).
- **Race Condition** - Two+ Agents writing to same file at same time - see [Lock-File].
- **Batch Lock** - Long-hold on a file lock - see [Lock-File > Batch].
- **Heartbeat** - Periodic `mtime` touch that keeps a **Batch Lock** fresh - see [Lock-File > Batch].

### Configuration and Behavior

- **Settings** - Tunable parameters and preferences - see [Settings].
- **Application Settings** - **Settings** that configure operations (models, limits, language) rather than behavior - see [Settings].
- **Mindset Settings** - **Settings** that shape Mindset - see the Mindset Settings section of [Settings].
- **Mindset** - General guidance for Agent behavior - see [Mindset].
- **Provenance Stamp** - The `<!-- generated-from: ... -->` line ending [Mindset]; drives regeneration.
- **Profile** - Preconfigured **Settings** (Fast, Standard, Deep) - see [Template-Profiles].
- **Rule** - Invariant Workflow guidance: the always-on checklist in [Rules], plus the lazy-loaded subject files in `_Axis/Rules/`.
- **Directive** - Conditional behavior to follow when triggered - see [Directives].

### Records and Memory

- **Plan** - Work plan to orchestrate the project (updated as work proceeds) - see [Plan].
- **Task** - An objective and set of steps to perform as part of the work **Plan** - see [Tasks].
- **Follow-Up** - A specific next action always for **User**; the Agent's follow-through is a **Task** - see [Practices > Followups].
- **Reminder** - A portable record of when Axis should surface information; not a scheduler or authorization - see [Practices > Reminders].
- **Continuity Block** - The portability assessment embedded in every `^save` Snapshot - see [Practices > Portability].
- **Note** - Short-term project fact to persist across sessions - see [Practices > Notes].
- **Idea** - A speculative thought to revisit as project progresses - see [Practices > Ideas].
- **Log** - A WORM file that records an event - lives in `_Axis/Logs/`.
- **Snapshot** - A WORM file that summarizes state at a meaningful point in time.
- **Event** - Anything worth logging: decisions, milestones, mistakes, scope changes.
- **Status Report** - User-facing report with a fast, one-glance read of project status.
- **Supervision Record** - A WORM parent-project report or action record under `_Axis/Supervision/`, with older active-window overflow under `_Axis/Archive/Supervision/`.
- **Executive Summary** - A one-glance overview at the top of a **Plan** or report.
- **WORM** - An abbreviation for the idea of "write-once, read-many".
- **Timestamp** - A padded string in format `yyyy.mm.dd.hh.mm.ss.xxxZ` (Zulu suffix).
- **Timestamp Claim** - Atomic `mkdir` reservation (`_Temp/{timestamp}.tsclaim/`) of an identifier timestamp while minting - see [Practices > Timestamps].
- **Index-Detail Pattern** - Convention to store summary info separately from detail info.
- **Lazy-Loading** - Practice of loading detail using **Index-Detail Pattern** only as needed.
- **Archive** - Reversible low-context storage for inactive history under `_Axis/Archive/` - see [Practices > Archiving].
- **Trash** - Deletion staging under `_Trash/`: contents await the next sweep (Session Start, `^resume`, `^refresh`) - see [Practices > Trash].
- **Placeholder** - A snippet of text needing completion, surrounded by `{{` and then `}}`.
- **Template Form** - A shipped file still containing `{{...}}` placeholders (not yet filled in).

### Wiki

- **Wiki** - Domain-specific knowledge that is useful for the project.
- **Ingest** - The Wiki intake procedure: read a source and integrate it into `Wiki/` - see [Practices > Wiki].
- **Library Status Record** - Append-only log of Wiki Review findings - `_Axis/Wiki/Library-Status.md`.
