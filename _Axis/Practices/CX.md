# Cross-Examination
> **Purpose:** Define the Cross-Examination process - how Main Agent spawns a CX Subagent, and the procedure a CX Subagent follows.

Two Agents share this procedure, so it is split by role below: Main Agent prepares the Cross-Examination and logs its result, and the CX Subagent performs it. Read only your own half, plus the shared framing here.

LLMs underperform, hallucinate, and overlook problems when they are too accepting of their own assumptions, too familiar and sycophantic with the User, too optimistic in their analysis, too confident in their conclusions and work, too eager to please, and too focused on pushing forward on just one way to solve a problem. Results improve and progress is made more quickly when an independent CX Subagent pushes back on those tendencies. Axis accomplishes that by launching an independent CX Subagent to criticize the work of other Agents.

Specifically, a CX Subagent should:

- Think independently.
- Play devil's-advocate.
- Challenge easy interpretations and simple solutions.
- Cross-check every assumption, assertion, rationale, and conclusion.
- Ask "What might be wrong here, even if it appears correct?"

A Cross-Examination should happen in isolation from the rest of the Workflow. A CX Subagent should not change any of the Core Files (e.g., Logs, Snapshots, Tasks, Notes or Wiki). Instead, a CX Subagent should do all of its own analysis in isolation, write exactly ONE file - the Cross-Examination Report - into `_Axis/CX/`, and return the path to that report in its response (details below). On return, Main Agent Logs an Event referencing the report path - CX Subagents never write Logs themselves.

## Main Agent: Preparing a Cross-Examination

### 1. Behavior and Settings

The CX role text in `_Axis/Roles/CX.md` carries the Cross Examiner's stance, compiled at release from [Template-Mindset] at these levels: Reasoning 2, Exploration 1, Eagerness -2, Skepticism 2, Familiarity -2, Verbosity -2, Simplicity -2, Precision 2, Generalization -2, Rigor 2, Creativity -2, Transparency -2, Budget -1, and CX Frequency 0. Main carries that role text verbatim in the spawn prompt and does not restate it. A CX Subagent does NOT follow the project Mindset in `_Axis/MINDSET.md`.

### 2. Synopsis

The Main Agent should draft a Synopsis to summarize the actions, decisions, work, and results that the CX Subagent needs to review, and then pass the Synopsis to the CX Subagent in the Prompt (not pass Synopsis to CX Subagent by a file link). Mint the report's identifier per [Practices > Timestamps] and name its path, `_Axis/CX/{identifier}.md`, in the task contract.

### 3. On Return

- Log an Event referencing the path of the returned report - the CX Subagent does not Log, so this is the audit-trail entry.
- Review the findings and act on them, or record why you are not, at a level of detail consistent with **Verbosity** in `_Axis/SETTINGS.md`.

## CX Subagent: Performing a Cross-Examination

The CX Subagent follows the role text in `_Axis/Roles/CX.md`, which its prompt carries: how to examine, including the check that the result delivers the decision it promised, and how to write its one report into `_Axis/CX/`.

## Degraded Review

An isolated context is what makes a Cross-Examination worth having. Read `host-spawn` under [Practices > Flags > Reading Flags]. When the host cannot confirm spawn Capability (the Flag is not valid `yes`, or a named CX Model is unreachable and there is no spawn to fall back on), `^cx` offers a degraded in-context review instead: Main Agent performs the review itself, unisolated. It is weaker - Main is examining its own work, and the tendencies listed at the top of this file are precisely the ones it cannot see in itself - so it is offered to User, never assumed, and it is always labelled.

In a degraded review Main Agent does both jobs:

- Adopt the stance in the CX role text (`_Axis/Roles/CX.md`) for the duration of the review; do not follow the project Mindset while reviewing.
- Write exactly ONE report into `_Axis/CX/`, its identifier minted per [Practices > Timestamps], in the shape the CX role text's Report section gives, with Line 1 reading `CX: {topic} (in-context, non-isolated)`. The label is not optional - a future reader must be able to tell an independent critique from a self-review.
- Log the Event referencing the report path, and record in that Log that the review ran in-context because isolation was unavailable. (The CX role text bars a spawned CX Subagent from logging; here there is no Subagent, so Main logs as it normally would.)
- Tell User in one line that the review was non-isolated, and therefore weaker than a spawned Cross-Examination.
