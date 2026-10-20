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
- **Task** - An objective and set of steps to perform as part of the work **Plan** - see [Tasks].
- **Follow-Up** - A specific next action always for **User**; the Agent's follow-through is a **Task** - see [Practices > Followups].
- **Reminder** - A portable record of when Axis should surface information; not a scheduler or authorization - see [Practices > Reminders].
- **Continuity Block** - The portability assessment embedded in every `^save` Snapshot - see [Practices > Portability].
- **Note** - Short-term project fact to persist across sessions - see [Practices > Notes].
- **Idea** - A speculative thought to revisit as project progresses - see [Practices > Ideas].
- **Log** - A WORM file that records an event - lives in `_Axis/Logs/`.
- **Snapshot** - A WORM file that summarizes state at a meaningful point in time.
- **Event** - Anything worth logging: decisions, milestones, mistakes, scope changes.
- **Review** - A dated report on the project's state (`^review`), saved as a Memo in `_Memos/`: what changed since the last one, health-checks, Deliverable coverage. It summarizes and challenges nothing - unlike a Cross-Examination - and the next Review supersedes it.
- **Memo** - A dated Markdown message to User in `_Memos/`, named `YYYY-MM-DD - Subject.md`: decisions, next steps, findings, reports, or the long version of a short reply. Editable, two-way, and never the only home of project state - see [Practices > Memos].
- **Status** - The quick look (`^status`): a one-screen summary of the project in the terminal, or a branded static web page. Built fresh each time; writes no record.
- **Supervision Record** - A WORM parent-project report or action record under `_Axis/Supervision/`, with older active-window overflow under `_Axis/Archive/Supervision/`.
- **Executive Summary** - A one-glance overview at the top of a **Plan** or report.
- **WORM** - An abbreviation for the idea of "write-once, read-many".
- **Timestamp** - A padded string in format `yyyy.mm.dd.hh.mm.ss.xxxZ` (Zulu suffix).
- **Timestamp Claim** - Atomic `mkdir` reservation (`_Temp/{timestamp}.tsclaim/`) of an identifier timestamp while minting - see [Practices > Timestamps].
- **Inbox** - The project's `_Inbox/` drop folder: User puts new material there and Main Agent files each item into a Project Subfolder or the Wiki - see [Practices > Inbox]. The Wiki's own `_Wiki/_Inbox/` holds raw Wiki sources.
- **Index-Detail Pattern** - Convention to store summary info separately from detail info.
- **Lazy-Loading** - Practice of loading detail using **Index-Detail Pattern** only as needed.
- **Archive** - Reversible low-context storage for inactive history under `_Axis/Archive/` or the folder in [Settings > Archive Location] - see [Practices > Archiving].
- **Trash** - Deletion staging under `_Trash/`: each item is dated on arrival and kept at least 2 days before a sweep (Session Start, `^resume`, `^refresh`) deletes it - see [Practices > Trash].
- **Placeholder** - A snippet of text needing completion, surrounded by `{{` and then `}}`.
- **Template Form** - A shipped file still containing `{{...}}` placeholders (not yet filled in).

### Wiki

- **Wiki** - Domain-specific knowledge that is useful for the project.
- **Ingest** - The Wiki intake procedure: read a source and integrate it into `_Wiki/` - see [Practices > Wiki].
- **Library Status Record** - Append-only log of Wiki Review findings - `_Axis/Wiki/Library-Status.md`.

## Initiative

An optional coordinated effort toward one shared outcome, connecting the Plan to related Tasks. Shared scope, success measures, phase, constraints, and next decision live in `_Axis/INITIATIVES.md`; execution stays in Task records. See [Practices > Initiatives].

## Team

An Axis Team of Agents is a chartered group working toward a shared objective, with a separate Team Leader and named members. A Team may carry out several Jobs; the project Main retains acceptance of final results. Its founding record lives in `_Axis/Teams/`. See [Practices > Coordination].

## Team Leader

A separate General Subagent that coordinates an Axis Team of Agents within its Charter. The Team Leader organizes work and proposes Assignments; it cannot enlarge authority or accept its own deliverable as final project completion. Main remains responsible for acceptance.

## Charter

The founding record that defines a Team's purpose, membership, permitted scope, outputs, limits and completion checks. Later accepted changes are recorded as Messages rather than rewriting the founding record.

## Job

One bounded unit of work, tracked from proposal through execution and outcome. An admitted Job fixes its objective, authorized scope, acceptance owner, limits, expiry and completion checks. Its founding record lives in `_Axis/Jobs/`; Assignments, Attempts, results and accepted changes are linked through Messages. One Job may involve several Assignments. Tasks own project commitments; Jobs organize bounded execution. See [Practices > Coordination].

## Mandate

The objective, authority, scope, limits and completion conditions fixed when a Job is admitted. Changing the work does not silently expand the existing Mandate; the change needs an explicit accepted revision or a new Job.

## Message

An immutable communication record in `_Axis/Messages/`, identified by its own project-unique timestamp. A Message has an author, recipient, kind, content and references to related work. Kinds include Assignment, Question, Answer, Receipt, Result, Validation, Decision and Control. Main and narrowly authorized workers may create Messages; recording one does not itself approve the requested action or validate a reported result. Outcomes are new linked Messages, not edits to the original. See [Practices > Messages].

## Assignment

A type of [Message](#message) that gives an agent a specific portion of a [Job](#job), within that Job's authorized scope and limits. For example, a landing-page review Job can have one Assignment to check mobile layout and another to check accessibility. An Assignment is stored in `_Axis/Messages/`, not a separate Assignments folder; it does not create or enlarge the Job's authority.

## Submission

Information presented to a Project's Main Agent for review and disposition through `_Axis/Submissions/`. It may contain proposed work, a Question, an Answer, a Result or a Message already recorded by another Project. Permitted senders create new Submissions; receiving Main alone processes them. A Submission describes a delivery/review role, not a Message kind. Messages hold recorded communications and decisions; recording one does not approve an action or validate a result. The 3.00 upgrade migrates the old Requests queue while preserving its bytes and outcomes. See [Practices > Submissions].

## Offer

A type of Message proposing available help, capability or a contribution. Recording an Offer does not accept it or authorize a start.

## Question

A type of Message asking for clarification or information relevant to the work. Its reply is an Answer linked to the original Question.

## Answer

A type of Message responding to a Question. It retains the relationship to that Question and any relevant Job or Team; its content is evaluated under the same authority rules as other Messages.

## Receipt

A type of Message acknowledging a specified stage, such as receipt of a request or a worker's acknowledgement of an Assignment. A Receipt records what was observed; it does not imply approval or completion, and it does not ask for another Receipt.

## Result

A type of Message reporting an Attempt's output, evidence, limitations and remaining work. A Result can report failure or partial progress. A retained Result awaiting Validation is checked, not automatically rerun.

## Validation

A type of Message recording whether retained evidence satisfies the Job's completion checks. Main accepts the validation outcome before treating the work as successful; a worker's claim or team consensus is not sufficient.

## Decision

A type of Message recording a disposition or accepted outcome, with references to the affected work. Only a decision accepted under Main's applicable authority can change project control state.

## Control

A type of Message recording a lifecycle change such as pause, cancellation or membership replacement. A valid Control identifies the affected Team or Job, its preceding accepted state and the current Control Epoch. Main acceptance is required.

## Transfer

A type of Message recording a stage of moving an Inbox item between recognized projects: prepared, copied-and-verified, destination-accepted or source-retired. The source is retained until its owner verifies the receiver's acceptance of the exact contents. See [Practices > Coordination > Session and transfer boundaries].

## Parent Directive

A Message carrying a task User gave a child project through `^^do` in its recognized parent. The child verifies its origin, exact scope and Parent Authority before applying it. This use of directive is distinct from a conditional behavior in `_Axis/DIRECTIVES.md`. See [Practices > Messages > Directives].

## Delivery Envelope

The bounded package carried by a Submission, carrying content plus its origin, destination, expiry and integrity information. It links to the originating Message or proposal and the receiver's imported Message. A Delivery Envelope is distinct from the nonce-bound Prompt Envelope used to start a Subagent.

## Transport

The mechanism that carries a Delivery Envelope into the receiving Submissions queue. A transport's success establishes delivery at most; acceptance, execution and validated completion require their own records. Host notifications may point to those records but do not replace them.

## Admission

Main's acceptance of a proposed undertaking as a bounded Job after checking its authority, scope, limits and relevant history. Admission records permission to proceed within those bounds, not successful completion.

## Disposition

Main's recorded handling of a Message, such as received, admitted, declined, referred, validated, rejected or closed. Each change is a new related Message, preserving the earlier record.

## Dispatch

The controlled step that assigns an Attempt to an eligible agent or executor and authorizes its start within the admitted Job. The dispatch intent is recorded before starting the external operation; recording intent alone does not prove the operation started.

## Attempt

One identified execution attempt within a Job, including the assigned agent, scope, start intent and eventual result or uncertain outcome. Several Attempts can belong to the same Job; retries and replacements remain subject to its shared limits.

## Acceptance

Main's recorded acceptance of a particular control change, disposition or validated result under current authority. Acceptance is specific to that action: importing a Message does not accept its requested work, and admitting a Job does not accept its final result.

## Authority

The applicable User instruction or permitted delegation that allows an action within an exact scope and set of limits. A Message, timer, claimed sender or checksum cannot create Authority. Permissions governs when confirmation is required; it does not enlarge Authority.

## Control Epoch

A numbered generation of Team or Job control used to distinguish current assignments and membership from superseded ones. A stale epoch cannot authorize new work or revive a terminal Job.

## Correlation

A shared reference connecting Messages about the same exchange or operation. Each Message keeps its own timestamp identity; Correlation links the discussion without merging its records or granting authority.

## Operation Key

A stable identifier used to recognize the same intended operation when admission is requested again. Repeating it must not create another Job for the same operation; conflicting contents require reconciliation. It is distinct from a Message's timestamp ID.

## Deduplication

Checking retained origin, operation or occurrence identities before importing or admitting work again. Duplicate delivery or a repeated trigger should reuse the existing mapping. This does not guarantee that an external side effect happened exactly once.

## Reconciliation

Resolving an ambiguous, conflicting or interrupted operation from retained evidence before deciding what can safely happen next. Missing replies and timeouts do not prove failure and do not justify blindly repeating an external effect.

## Schedule

A portable definition of when bounded work should be considered, including its Trigger, timezone, scope, authority, expiry and limits. Main owns the current definition in `_Axis/Schedules/`, with immutable revision Messages. A Schedule proposes an Occurrence; it does not grant authority or guarantee that a timer is available. See [Practices > Scheduling].

## Trigger

The supported time or verified event condition that prompts evaluation of a Schedule. A host timer is one possible trigger source; without a configured trigger, Axis checks schedules at manual or checkpoint turns.

## Occurrence

One specific planned instance of a Schedule, identified by its Project, Schedule, Execution Revision and planned UTC instant or verified event. Main checks the identity before Job admission so repeated evaluation does not create duplicate work.

## Execution Revision

The immutable Schedule revision that determines the action and timing of an Occurrence. An admitted Job stays tied to its reviewed revision; editing the Schedule's current view does not replay already admitted work.

## Retry

Another Attempt after a classified failure that is safe to repeat, within the existing authority and finite limits. An uncertain external effect needs Reconciliation; a retained Result awaiting Validation needs checking rather than another Attempt.

## Overlap Policy

A Schedule's rule for an Occurrence that becomes due while earlier work is still active. The policy limits simultaneous or queued work instead of treating every trigger as permission to start another Job.

## Missed-Work Policy

A Schedule's bounded rule for overdue Occurrences, such as skipping them or combining eligible missed work into one occurrence. Expiry and catch-up limits still apply; returning online does not create unlimited backlog authority.

## Placement

The explicitly activated local binding that identifies the project copy, host and Main allowed to dispatch or accept Coordination effects. A move, copy, changed Main or expired binding requires revalidation. Placement is a local safeguard, not a distributed lock. See [Practices > Coordination > Local activation].

## Session Binding

The checked relationship between an Axis Project and Session and an exact host/provider session handle and generation. A process ID, terminal title or most-recent conversation is not enough to establish this relationship or restore authority.

## Residency

The desired lifetime of an agent's host session. On-demand starts it when work needs it; warm retains a reusable context; managed adds explicitly configured lifecycle or restart support. The 3.00 baseline supports on-demand startup; warm and managed require supported integrations and opt-in. A retained context does not keep an Axis lease valid.

## Payload

The structured data carried by a Message, Delivery Envelope or supporting file for machine processing and validation. A readable Markdown record may include a labelled JSON payload; the human-visible information and the processed values must agree.

## Support File

A companion containing structured data, original output or other evidence linked from a detail record. It belongs to that record's identity unless it is itself an independently created record with its own timestamp. Referenced support must remain available and match any recorded integrity digest.

## Index-Detail-Support Pattern

An optional extension of the Index-Detail Pattern: a Markdown index points to a Subject-first Markdown detail, which links to supporting data or evidence when needed. A companion bundle can use the detail's owning timestamp without becoming a second independent record. Standalone records retain their own unique timestamps.

## Checksum

A digest used to detect changes to record content or linked support. Where a record requires an integrity check, changed content must be reviewed before it is processed. A matching checksum does not prove authorship, approval or agreement between a human summary and its payload; those require separate checks.
