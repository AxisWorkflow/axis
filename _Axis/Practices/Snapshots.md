# Snapshots
> **Purpose:** Define when and how to save Snapshots.

Save a faithful, auditable record of the relevant interactions and project state when:

- Running the `^save` command.
- There is a major development or shift in direction of the project.
- User signals session is winding down (see [Directives > Save a Snapshot on Wind-Down]).

The Axis Workflow has no engine-level hook for "end of session" - and the User may close the browser or step away without notice. Attempting to detect a wind-down of the session is a partial mitigation; the most reliable way to capture end-of-session state is to run the `^save` command.

To save a **Snapshot:**

- Mint a project-unique timestamp for the new Snapshot per [Practices > Timestamps].
- Capture what a later Agent needs to continue: conclusions, decisions, actions, interactions, artifacts, file changes, open questions, and verification results.
- Record the current Follow-Up queue as a count plus the exact timestamp IDs of every open Follow-Up. Do not copy their asks into Snapshot prose; the IDs preserve the point-in-time state without creating a second version of mutable User-facing questions.
- Record the current Reminder queue as a count plus the exact timestamp IDs of every open Reminder. Do not duplicate Reminder bodies.
- A Snapshot created by `^save` contains exactly one `## Continuity` block in the shape defined by [Practices > Portability]. Other lifecycle Snapshots may include the latest known portability result but never claim a fresh assessment unless they ran the same checks.
- For each material decision, record the conclusion, assumptions, evidence, alternatives considered, uncertainty, verification, and why the chosen option won. Summarize this decision record; never request or preserve hidden private reasoning.
- Save Snapshot details to `_Axis/Snapshots/{yyyy.mm.dd.hh.mm.ss.xxxZ}.md`.
- Summarize into < 200 words and append to bottom of `_Axis/SNAPSHOTS.md`.
- When reporting a saved Snapshot to User, identify it only by timestamp ID or its project-root-relative path. Never expose an absolute, home-relative, or drive-prefixed path, including through a clickable link.
