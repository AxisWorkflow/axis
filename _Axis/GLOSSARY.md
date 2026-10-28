# Glossary
> **Purpose:** Define Axis terms so humans and Agents share the same meanings.

### Axis and Projects

- **Axis Workflow** - The definitions, configuration, and practices in this repository.
- **Axis** - Synonym for **Axis Workflow**.
- **Workflow** - Synonym for **Axis Workflow**.
- **Axel** - The Axis mascot and the persona name of the **Main Agent**; External Agents and Subagents are unnamed. Records are signed with the Session ID, never the name.
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
- **Subagent** - Any Agent started by **Main Agent** to work in an isolated (fresh) context.
- **CX Subagent** - A Subagent that cross-examines and stress-tests work.
- **Wiki Subagent** - A Subagent that ingests new sources into the project Wiki.
- **General Subagent** - Any Subagent that is not one of the predefined types.
- **Team Leader** - A separate General Subagent that coordinates an Axis Team of Agents within its Charter. Main accepts the final results.
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
- **Session Binding** - The verified link between an Axis Project and Session and a specific host or provider session.
- **Residency** - How long an agent's host session is kept available: on-demand, warm or managed. Keeping context does not extend an Axis lease.
- **Degraded Mode** - Fallback when a **Capability** is missing (e.g., no Subagent spawn).
- **Storage Profile** - Current filesystem-write classification: `atomic`, `serialized`, or `unknown` - see [Practices > Portability].
- **Environment Signature** - Optional non-secret local change-detection hint; never identity, authority, or portable truth - see [Practices > Portability].
- **Infrastructure Declaration** - One non-secret `_Axis/ENVIRONMENT.md` row describing a non-portable prerequisite, fallback, safe revalidation, and restoration reference - see [Practices > Portability].
- **Flag** - A persistent file to record durable workflow state - saved in `_Axis/Flags/`.
- **Marker** - An ephemeral file tracking live Agents (Main, External, and Subagent sessions) - in `_Axis/Agents/`.
- **Max Concurrent Sessions** - The Setting that limits how many Agent sessions (Main, External, Subagent) may be live on a project at once; default 10 (see [Rules > MarkersFlagsAndLocks > Concurrent Sessions]).
- **Permissions** - The Setting (`Restricted`, `Default`, `Autonomous`) that decides when an Agent confirms a change before making it; it never grants new authority (see [Rules > Permissions]).
- **Tracking** - Append-only per-agent activity channel in `_Axis/Tracking/` - INTENT, STATUS, ASK, REPLY and DONE lines that let every Agent see what others are doing; telemetry, not evidence (see [Practices > Tracking]).
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
- **Initiative** - An optional effort connecting the Plan and related Tasks around one shared outcome - see [Practices > Initiatives].
- **Task** - An objective and set of steps to perform as part of the work **Plan** - see [Tasks].
- **Follow-Up** - A specific next action always for **User**; the Agent's follow-through is a **Task** - see [Practices > Followups].
- **Reminder** - A portable record of when Axis should surface information; not a scheduler or authorization - see [Practices > Reminders].
- **Continuity Block** - The portability assessment embedded in every `^save` Snapshot - see [Practices > Portability].
- **Note** - Short-term project fact to persist across sessions - see [Practices > Notes].
- **Idea** - A speculative thought to revisit as project progresses - see [Practices > Ideas].
- **Log** - A WORM file that records an event - lives in `_Axis/Logs/`.
- **Snapshot** - A WORM file that summarizes state at a meaningful point in time.
- **Event** - Anything worth logging: decisions, milestones, mistakes, scope changes.
- **Review** - A dated project summary from `^review`, saved as a Memo. It covers changes, health and Deliverables; Cross-Examination provides independent challenge.
- **Memo** - An editable, dated message to User in `_Memos/` for decisions, findings or longer explanations. Project state also stays in canonical records - see [Practices > Memos].
- **Status** - The quick look (`^status`): a one-screen summary of the project in the terminal, or a branded static web page. Built fresh each time; writes no record.
- **Supervision Record** - A WORM parent-project report or action record under `_Axis/Supervision/`, with older active-window overflow under `_Axis/Archive/Supervision/`.
- **Executive Summary** - A one-glance overview at the top of a **Plan** or report.
- **WORM** - An abbreviation for the idea of "write-once, read-many".
- **Timestamp** - A padded string in format `yyyy.mm.dd.hh.mm.ss.xxxZ` (Zulu suffix).
- **Timestamp Claim** - Atomic `mkdir` reservation (`_Temp/{timestamp}.tsclaim/`) of an identifier timestamp while minting - see [Practices > Timestamps].
- **Inbox** - The `_Inbox/` drop folder where User supplies material for Main to file - see [Practices > Inbox]. `_Wiki/_Inbox/` holds raw Wiki sources.
- **Index-Detail Pattern** - Convention to store summary info separately from detail info.
- **Index-Detail-Support Pattern** - An index links to a detail record, which links to supporting data or evidence when needed.
- **Support File** - Data or evidence linked from a detail record and kept under that record's identity.
- **Payload** - Structured data carried by a Message or supporting file. It must agree with the readable record.
- **Checksum** - A digest used to detect changed content. It does not prove who wrote or approved it.
- **Lazy-Loading** - Practice of loading detail using **Index-Detail Pattern** only as needed.
- **Archive** - Reversible low-context storage for inactive history under `_Axis/Archive/` or the folder in [Settings > Archive Location] - see [Practices > Archiving].
- **Trash** - Deletion staging under `_Trash/`: each item is dated on arrival and kept at least 2 days before a sweep (Session Start, `^resume`, `^refresh`) deletes it - see [Practices > Trash].
- **Placeholder** - A snippet of text needing completion, surrounded by `{{` and then `}}`.
- **Template Form** - A shipped file still containing `{{...}}` placeholders (not yet filled in).

### Wiki

- **Wiki** - Domain-specific knowledge that is useful for the project.
- **Ingest** - The Wiki intake procedure: read a source and integrate it into `_Wiki/` - see [Practices > Wiki].
- **Library Status Record** - Append-only log of Wiki Review findings - `_Axis/Wiki/Library-Status.md`.


### Coordination and Jobs

- **Team** - An Axis Team of Agents working toward a shared objective under a Charter - see [Practices > Coordination].
- **Team Infrastructure** - Common identity, authority, lifecycle, communication, workspace and recovery mechanisms used by Teams.
- **Collaboration Pattern** - A reusable starting method for how members work together. It grants no permissions.
- **Collaboration Plan** - A specific versioned method with assignments, exchanges, participation, synthesis and acceptance.
- **Team Setup** - Turning an objective and constraints into a feasible charter and collaboration plan.
- **Participation Period** - When a member must remain available for its assigned work and exchanges.
- **Team Artifact** - An attributable, immutable revision of a member's work, distinct from a release Artifact.

- **Charter** - A Team's founding record defining its purpose, members, scope, outputs, limits and completion checks.
- **Job** - A bounded unit of work with an agreed objective, scope, limits and completion checks. Tasks track project commitments; Jobs organize execution.
- **Mandate** - The objective, authority, scope, limits and completion conditions agreed when a Job is admitted.
- **Admission** - Main's approval to start a Job within its stated scope and limits.
- **Dispatch** - Assigning an Attempt to an eligible agent and authorizing its start. The intent is recorded before execution.
- **Attempt** - One execution of work within a Job, with an assigned agent and a recorded result or uncertain outcome.
- **Acceptance** - Main's recorded approval of a specific control change, disposition or validated result.
- **Authority** - A User instruction or permitted delegation allowing a specific action within stated limits. Messages and Permissions do not expand it.
- **Control Epoch** - A numbered version of Team or Job control state that distinguishes current authority from superseded assignments or membership.
- **Operation Key** - A stable identifier used to recognize repeated requests for the same operation and prevent duplicate Jobs.
- **Deduplication** - Checking recorded identities to avoid importing or admitting the same work again.
- **Reconciliation** - Resolving an uncertain or interrupted operation from evidence before deciding whether it can safely continue or repeat.
- **Retry** - Another Attempt after a failure that is safe to repeat, within the Job's existing authority and limits.
- **Placement** - The verified local binding of a project copy, host and Main allowed to dispatch or accept Coordination effects.

### Messages and Delivery

- **Message** - An immutable communication record in `_Axis/Messages/` with an author, recipient, kind and content. Recording it does not approve an action or validate a result.
- **Assignment** - A Message giving an agent a specific part of a Job within its agreed scope and limits.
- **Submission** - Information delivered through `_Axis/Submissions/` for receiving Main to review and handle. It may carry a Message, proposal, question or result.
- **Offer** - A Message proposing help, a capability or a contribution; it does not authorize work to start.
- **Question** - A Message asking for information or clarification about the work.
- **Answer** - A Message replying to a linked Question.
- **Receipt** - A Message acknowledging a specific stage of delivery or handling. It does not imply approval or completion.
- **Result** - A Message reporting an Attempt's output, evidence and limitations, including failure or partial progress.
- **Validation** - A Message recording whether evidence meets a Job's completion checks. Main accepts the outcome before treating the work as successful.
- **Decision** - A Message recording a disposition or accepted outcome. Main's applicable authority governs changes to project control state.
- **Control** - A Message recording a lifecycle change, such as a pause, cancellation or member replacement. Main acceptance is required.
- **Transfer** - A Message recording a stage of moving an Inbox item between projects. The source stays until its owner verifies destination acceptance.
- **Parent Directive** - A Message carrying User's task from a recognized parent project through `^^do`. It is distinct from a conditional behavior in `_Axis/DIRECTIVES.md`.
- **Delivery Envelope** - A Submission's package of content, origin, destination, expiry and integrity information. It is distinct from a Subagent Prompt Envelope.
- **Transport** - The mechanism carrying a Delivery Envelope to the receiving Submissions queue. Delivery does not mean acceptance or completion.
- **Disposition** - Main's recorded handling of a Message, such as admitted, declined, validated or closed.
- **Correlation** - A shared reference linking Messages about the same exchange or operation.

### Scheduling

- **Schedule** - A portable definition of when bounded work should be considered, with its scope, authority and limits - see [Practices > Scheduling].
- **Trigger** - A time or verified event condition that prompts evaluation of a Schedule.
- **Occurrence** - One planned instance of a Schedule, identified by its revision and scheduled time or verified event.
- **Execution Revision** - The fixed Schedule revision that determines an Occurrence's action and timing. Later edits do not replay admitted work.
- **Overlap Policy** - A Schedule's rule for new work that becomes due while earlier work is still active.
- **Missed-Work Policy** - A Schedule's bounded rule for overdue Occurrences, such as skipping or combining them.
