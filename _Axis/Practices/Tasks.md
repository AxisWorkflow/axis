# Tasks
> **Purpose:** Define how to record, track, and update Tasks.

Break Plan down into congruent Tasks for actual execution. Keep Plan and Tasks synchronized - do not let them drift.

Record each Axis Task in `_Axis/TASKS.md` with the following shape:

- **Name** - the ## heading above the entry; 1 to 5 words to identify task at a glance.
- **Label** - a phrase of 1 to 15 words to summarize what task does.
- **Status** - one of **Active**, **Blocked**, **Completed**, or **Cancelled** (see below).
- **Created** - field; timestamp when task created.
- **Updated** - field; exact UTC timestamp of the latest material edit, or `Unknown` only for a migrated Task whose durable recency cannot be established. New Tasks never use `Unknown`.
- **Completed** - field; timestamp when Status reached **Completed**; `N/A` otherwise.
- **Cancelled** - field; timestamp when Status reached **Cancelled**; `N/A` otherwise.
- **Delivers** - field; optional; names the Deliverable in `_Axis/PROJECT.md` this task aims at; `N/A` when the task serves no single Deliverable.
- **Description** - short body paragraph of < 100 words (blank line before and after).
- **Details** - A link for `[Details...](Tasks/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md)`, or `Archive/Tasks/{timestamp}.md` after a terminal Task is archived.

Field keys in `_Axis/TASKS.md` are exactly `label:`, `status:`, `created:`, `updated:`, `completed:`, `cancelled:`, `delivers:` - lowercase, one per line, YAML-parseable (the Dashboard depends on these keys). Each value ends at its own line break; a key with no value reads as empty, never as the next line. Every material edit to an open Task advances `updated:`; terminal Tasks carry the terminal timestamp there. Do not use filesystem `mtime` as durable Task recency because copy, checkout, and sync operations rewrite it.

## Deliverable Coverage

`_Axis/PROJECT.md` names the Deliverables; `_Axis/TASKS.md` tracks the work; the Project Subfolders hold the output. The `delivers:` field is what joins the three, so that "are we done?" can be answered by reading the index instead of reading everything.

- Write the Deliverable name in `delivers:` exactly as it appears in the **Deliverables** section of `_Axis/PROJECT.md`. When a task genuinely serves more than one, separate them with commas; when it serves none (routine upkeep, research, a spike), write `N/A`.
- When a task carrying a `delivers:` value reaches **Completed**, record the paths of the work products it produced under a `## Produced` heading in that task's detail file in `_Axis/Tasks/` - one path per line as a `- ` bullet. That is the only place a Deliverable is tied to a file, so it has to be written before the task is closed.
- A Deliverable no task names is unclaimed work. Surface it rather than assuming it is covered.
- Producing the file is not the same as meeting the bar. A Deliverable is done when its paths exist AND the relevant **Criteria** in `_Axis/PROJECT.md` have been evaluated against them.
- The `^status` command reports this coverage on every run.

Keep description of each Task in `_Axis/TASKS.md` very focused: only describe what needs to be done and why. Sort tasks in `_Axis/TASKS.md` by approximate order of execution. No section headers. Put all details for Tasks into respective detail files in `_Axis/Tasks/` - that saves on context and helps User to more easily track the project.

Agent and User can look up details for each Task from supporting files. Details include:

- concrete requirements
- acceptance criteria that will be used to decide when this task is complete,
- how success will be evaluated
- references to items in Logs, Notes, Snapshots, other Tasks, and the Wiki.

Each task in `_Axis/TASKS.md` carries one of four **Status** values:

- **Active** - Task is being worked on.
- **Blocked** - Task is on hold (i.e., waiting on an external input or dependency).
- **Completed** - Task is done and verified.
- **Cancelled** - Task was dropped before completion (e.g., obsolete after a Plan revision, scope change, or supersession by another task). Requires a one-line cancellation reason in the detail file.

Logic for **Status** values:

- Never mark a task complete without proving that it meets its requirements.
- When a task transitions to **Completed**, timestamp it with the *Completed* time; leave *Cancelled* as `N/A`.
- When a task transitions to **Cancelled**, timestamp it with the *Cancelled* time, leave *Completed* as `N/A`, and record the cancellation reason in the detail file.
- On either transition, write the same terminal timestamp to `updated:`. A migrated `Unknown` becomes an exact timestamp on the next material change.
- *Completed* and *Cancelled* are mutually exclusive - exactly one carries a timestamp once Status is terminal; both are `N/A` while Status is **Active** or **Blocked**.
- Do NOT use **Completed** for a task that was abandoned - that violates the WORM rule that **Completed** means requirements were met. Use **Cancelled** instead.
- Only Completed and Cancelled Task details are eligible for Archive. Keep their index entries and atomically redirect their Details links under [Practices > Archiving > Indexed Records].
- When the missing input or decision belongs to User, keep the Task **Blocked** and create or reuse a Follow-Up in the same pass under [Practices > Followups]. The Follow-Up carries the exact ask and points to the Task detail; the Task records the blocking condition without duplicating that ask. When a non-User dependency blocks work, keep the Task **Blocked** without creating a Follow-Up.

How to integrate Axis Tasks with the host harness's task management system:

- The overall objective with Axis Tasks is to be "generic and cross-platform", such that an Axis Workflow project can directly port over to a different host and maintain the same task state.

- Some host harnesses (e.g., Cowork, Claude Code) provide their own in-session task tracker that renders progress in the UI. Treat these as ephemeral display only - they are not canonical and may not persist across sessions. `_Axis/TASKS.md` remains the single source of truth for project tasks.

- When working on an Axis Task in a host with a task widget, decompose the work into host-task steps for that session's UI; update the Axis Task in `TASKS.md` once on completion (or at meaningful checkpoints), not on every host-task transition.

- If User asks something like "what are my tasks?", answer from `_Axis/TASKS.md`, not from the host widget.

- Do not fight the host about task management. If host harness sends reminders to use its task tracker, then use it - but at in-session layer, not as canonical store.
