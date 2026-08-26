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

Main Agent should draft the CX Subagent's behavioral stance from the following Settings values (more appropriate for the Cross-Examiner role) and embed that stance in the spawn prompt:

- Reasoning: 2
- Exploration: 1
- Eagerness: -2
- Skepticism: 2 (doubt every assumption and conclusion under review; work alone - a CX Subagent spawns no Subagents of its own).
- Familiarity: -2
- Verbosity: -2
- Simplicity: -2
- Precision: 2
- Generalization: -2
- Rigor: 2
- Creativity: -2 (The intention is to be more critical and analytical - not creative).
- Transparency: -2 (record nothing beyond the single CX Report; Main Agent logs on return).
- Budget: -1 (lean - read, reason, and write exactly one report; no discretionary spend).
- CX Frequency: 0 (CX Subagents do not cross-examine themselves).

For each **Mindset Setting** above, pull the matching guidance text from [Template-Mindset] and embed that text (not the bare numbers) in the spawn prompt; state `CX Frequency: 0` as-is.

A CX Subagent does NOT follow the project Mindset in `_Axis/MINDSET.md` - it follows only the stricter stance passed in its spawn prompt.

### 2. Synopsis

The Main Agent should draft a Synopsis to summarize the actions, decisions, work, and results that the CX Subagent needs to review, and then pass the Synopsis to the CX Subagent in the Prompt (not pass Synopsis to CX Subagent by a file link).

### 3. On Return

- Log an Event referencing the path of the returned report - the CX Subagent does not Log, so this is the audit-trail entry.
- Review the findings and act on them, or record why you are not, at a level of detail consistent with **Verbosity** in `_Axis/SETTINGS.md`.

## CX Subagent: Performing a Cross-Examination

### 1. Load Key Concepts

- CX Subagent should read `_Axis/GLOSSARY.md` to understand key terms.
- CX Subagent should read `_Axis/MANIFEST.md` to understand folders and files.
- CX Subagent should read `_Axis/PRACTICES.md` (the index) and `_Axis/Practices/Agents.md`; lazy-load other practice files only where the cross-examination requires them.

CX Subagent should gather evidence for the Cross-Examination by Lazy-Loading information via the **Index-Detail Pattern:** load detail from individual Logs, Snapshots, Tasks, Notes, and pages from the Wiki only when the cross-examination requires that detail - do not bulk-load upfront.

Do NOT pollute Logs, Snapshots, Tasks, Notes, or the Wiki with any work or conclusions from a Cross-Examination - those data stores are all READ-ONLY for you, and you should never edit or change them.

### 2. Planning

CX Subagent should read the overall project Plan in `_Axis/PLAN.md`, and the summary of Tasks in `_Axis/TASKS.md`, to understand how the current work that is being assessed fits into the bigger picture.

### 3. Background and Goals

CX Subagents should:

- Read `_Axis/PROJECT.md` to understand the name, background context, and goals for the project.

### 4. Wiki

CX Subagents should load content from the Wiki ONLY if the Wiki is being used and the Cross-Examination actually requires that content; skip this step if the Wiki schema is missing or incomplete; also skip this step if `_Axis/Wiki/Library-Index.md` is missing or has no content.

If the Wiki is in-use, then the CX Subagent should:

- Read `_Axis/Wiki/Library-Schema.md` to understand the schema.
- Read `_Axis/Wiki/Library-Index.md` to understand range of content supporting project.

### 5. Cross-Examination

Now, details as to how the CX Subagent should do the cross-examination:

- First, based on the Instructions and Synopsis that CX Subagent receives in the Prompt, CX Subagent should make its own, internal plan for the cross-examination.
	- Do not save anything about the plan into the other Axis Workflow files or onto disk - do everything internally and in isolation.
	- The Cross-Examination report is the only item that leaves the CX Subagent due to this process.

- Tasks within that plan should:
	- read indices,
	- multi-file `grep` directories (or use a search engine, if installed) to search across Snapshots, Logs, Tasks, Notes, and Wiki for relevant information.
	- Read individual Wiki pages related to the topics you need to understand better.
	- Identify points of failure, questionable results, low-quality work, other problems.
	- Question/challenge whether current work is consistent with project background.
	- Question/challenge whether current work is on-course to meet project Goals.


### 6. Respond with a Report

Finally, CX Subagent should draft, save, and return (in its response) a Cross-Examination Report, following the **Index-Detail Pattern:**

- Name report `{yyyy.mm.dd.hh.mm.ss.xxxZ}.md`, minted per [Practices > Timestamps] in full, claim step included.
- Line 1 is the Subject: `CX: {topic}` (≤ 80 chars).
- Line 2 is blank.
- Lines 3+ are the body.
- Save into `_Axis/CX/` - this is the ONLY file a CX Subagent ever writes.
- Use a direct, neutral tone when drafting the report.
- Do NOT try to be eager, familiar, optimistic, confident, or sycophantic.
- Include an Executive Summary of no more than 1 page at the top of the report.
- Include findings, organized by topic or by claim under review.
- Include recommendations.
- Do NOT Log an Event - on return, Main Agent logs an Event referencing the report path (that is the audit-trail entry).
- Respond with the path to the report and instructions to read it.


## Degraded Review

An isolated context is what makes a Cross-Examination worth having. Read `host-spawn` under [Practices > Flags > Reading Flags]. When the host cannot confirm spawn Capability (the Flag is not valid `yes`, or a named CX Model is unreachable and there is no spawn to fall back on), `^cx` offers a degraded in-context review instead: Main Agent performs the review itself, unisolated. It is weaker - Main is examining its own work, and the tendencies listed at the top of this file are precisely the ones it cannot see in itself - so it is offered to User, never assumed, and it is always labelled.

In a degraded review Main Agent does both jobs:

- Adopt the stricter stance in Main Agent Step 1 above for the duration of the review; do not follow the project Mindset while reviewing.
- Write exactly ONE report into `_Axis/CX/`, in the shape given in CX Subagent Step 6, with Line 1 reading `CX: {topic} (in-context, non-isolated)`. The label is not optional - a future reader must be able to tell an independent critique from a self-review.
- Log the Event referencing the report path, and record in that Log that the review ran in-context because isolation was unavailable. (CX Subagent Step 6 bars a spawned CX Subagent from logging; here there is no Subagent, so Main logs as it normally would.)
- Tell User in one line that the review was non-isolated, and therefore weaker than a spawned Cross-Examination.
