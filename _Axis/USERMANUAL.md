# Axis Workflow User Manual
> **Purpose:** How to use the Axis Workflow day to day: setup, commands, the Dashboard, the Wiki, working across tools and machines, and working with Agents and models. For the technical and compliance reference, see [SPECIFICATION](/_Axis/SPECIFICATION.md).
> **Version:** 3.21

**Looking for something?** Jump to the [Topic Index](#topic-index) at the end of this manual, or ask your Agent `^help <topic>`.

## Contents

- [Getting Started](#getting-started): [Setup](#setup), [Guided project setup](#guided-project-setup), [How Axis Works](#how-axis-works), [Tips](#tips) and the [FAQ](#faq)
- [Everyday Use](#everyday-use): [Commands](#commands), the [Dashboard](#reading-the-dashboard), [Inbox](#inbox), [Memos](#memos), the [Wiki](#wiki), [Settings](#settings), [archiving](#archiving-policy-and-cold-history) and [child projects](#supervising-child-projects)
- [Working Across Tools and Machines](#working-across-tools-and-machines): [Portability](#portability), [file sharing](#file-sharing), [terminal sessions](#terminal-sessions-and-model-access) and [remote access from a laptop or phone](#remote-access-from-a-laptop-or-phone)
- [Agents and Models](#agents-and-models): roles, an [Axis Team of Agents](#an-axis-team-of-agents-and-its-jobs), [Scheduling](#scheduling), [Subagents](#subagents) and [Delegation](#delegation)
- [OpenClaw Integration](#openclaw-integration)
- [Integrations](#integrations)
- [Trademarks](#trademarks), [License](#license) and [Copyright](#copyright)
- [Topic Index](#topic-index)

## Getting Started

### Setup

**Install** by download:

- [Download](https://github.com/AxisWorkflow/axis/releases/latest/download/axis-project.zip) **Axis**.
- Unzip the downloaded file.
- You now have a new project folder called `/axis-project/`.
- Rename `/axis-project/` for your project (e.g.: `/My Project/`).
- Mount your AI tool (Claude Cowork, ChatGPT Work, Codex, Antigravity CLI, Claude Code, ...) to the folder.
- **Note:** For the complete shell-backed feature set on Windows, use **WSL** or **Git Bash**. Without a POSIX-like shell, Axis keeps its canonical file workflow and degrades shell-dependent enhancements.

Axis reserves six underscore-prefixed folders in your project: `_Axis/`, `_Inbox/`, `_Memos/`, `_Temp/`, `_Trash/` and the readable `_Wiki/`. Drop new material in `_Inbox/`, read reports and decisions in `_Memos/`, and browse knowledge in `_Wiki/`. You can generally ignore the others and work with your Agent. One exception: deposit secret files into `_Axis/Secrets/` by hand so they never go through chat.

Your own content lives in normal folders that your Agent creates and organizes as the work develops; add `_U` to a folder name to make it read-only for Agents, or `_X` to hide it from Agents completely.

**Alternative Install** via GitHub:

- Click the green "**Use this template**" button on [GitHub](https://github.com/AxisWorkflow/axis).
- Or run: `npx tiged AxisWorkflow/axis "My Project"` from a terminal.
- Typically do not `git clone` - you want your own, independent repo for your project.

**Set up your project** (allow time to review the goal and plan):

- Type `Start Axis` in a compatible host attached to the project folder. Most supported entry routes also treat any first message as a start request; some desktop apps treat a plain greeting as small talk. If the host has not loaded the entry instructions, follow its folder/instruction setup before continuing.
- Your Agent can help you set up a [Project](/_Axis/PROJECT.md) (background, objectives, deliverables, ...).
- The download has no `README.md`. During setup Axis creates a short one for your project (or replaces the Axis README if you cloned the repository instead of downloading). This User Manual stays at [`_Axis/USERMANUAL.md`](/_Axis/USERMANUAL.md) and the technical reference at [`_Axis/SPECIFICATION.md`](/_Axis/SPECIFICATION.md). Start with this manual for any question or problem; the Specification is rarely needed - it is for deep diagnostics, extending Axis, technical or compliance reviews, and contributors. The root Axis license is removed unless you already chose a project license; Axis itself remains covered by [`_Axis/LICENSE`](/_Axis/LICENSE). Use `^help manual` whenever you want to browse this manual, or `^help` followed by a word or question to find a topic.



### Guided project setup

Quick Setup asks for a name and a paragraph; Interactive Setup offers a deeper interview. Choose either. After setup, ask “Help me turn my goal into a plan and first tasks,” or type `^onboard setup`. The Agent asks only what is missing, then drafts a Project, Plan and Tasks for you to review. You can stop, skip questions or decline a formal Plan. The ordinary `^onboard` tour captures a Note, an Idea and a Review.

Use conversation, a paragraph, or copy this form into chat:

- Project name and background:
- Outcome I want, and who it is for:
- What success would look like:
- What to deliver, and what is outside scope:
- Time, people, budget, access and other limits:
- A useful next action:
- Facts or documents to use; unknowns or disagreements to keep visible:

“Unknown” is a useful answer. The Agent should keep uncertainties visible, put prerequisites before dependent Tasks, and show you the next feasible action. Tell it what is inaccurate, missing or unrealistic before work follows the Plan. The form needs no terminal, installation or optional integration; it works in the chat you already use for Axis.

For example: “I need a one-page museum welcome guide for adult visitors. English only for this pilot; 90 minutes available, no printing budget. Draft directions through the entrance, local-history room, courtyard and exit. Hours and accessibility details are unknown. Do not publish it.” The first Task can draft those directions while final review waits for the missing facts. This is an illustrative project, not a measured result or a promise of completion time.

### How Axis Works

> **How does the Workflow actually work?**

**1. Setup Axis:**

- Download and drop in the Axis files (see [Setup](#setup)).

**2. Define a project:**

- Give your project a name, background, and goals in [Project](/_Axis/PROJECT.md).

**3. Select a profile:**

- Configure [Settings](/_Axis/SETTINGS.md).
- Set general behavior in [Mindset](/_Axis/MINDSET.md).

**4. Start Axis:**

- Open a chat in the project folder with a compatible AI host and type `Start Axis`. Startup time depends on the host and project. If you step away for hours, the same chat checks its session before continuing; if another chat has taken over as Main, the old one stops and tells you. If the host resumes without write access, the Agent makes no changes and asks you to rerun it with write access. After the greeting, the Agent loads the required project context before its first substantive answer.

An optional integration can check a session without making it appear recently active. The check does not wake the Agent, extend its lease or authorize work; ordinary conversation turns still renew the lease.

**5. Agents follow a standardized protocol:**

- Key terms in [Glossary](/_Axis/GLOSSARY.md).
- Standard operating procedures in [Practices](/_Axis/PRACTICES.md).
- Broad guidance in [Principles](/_Axis/PRINCIPLES.md).
- Invariant rules (to keep top-of-mind) in [Rules](/_Axis/RULES.md).
- Conditional triggers (for situational behaviors) in [Directives](/_Axis/DIRECTIVES.md). New Axis versions can add default Directives; the first session after an update adds any you are missing and says so. To keep one out, delete it and add `<!-- axis:omit-directive: {its name} -->` to that file.
- Subject-by-subject rule detail in [Rules](/_Axis/Rules/), lazy-loaded when an activity needs it.

Before a download approval prompt, the default **Explain Download Permissions** Directive has the Agent describe the source, expected contents, destination when known, and whether the action only saves or also opens, runs, installs or imports the file. Unknowns are stated; permission to save is not permission to execute. It adds no approval step to an otherwise authorized retrieval.

When a verification test fails, **Testing Calibration** has the Agent check whether the failure reflects the test's original purpose. If a test is unnecessarily strict, the Agent explains the evidence and discusses revisions with you before changing its acceptance criteria. It preserves the failed result and avoids repeating an unchanged test without a reason to expect useful new evidence.

**6. Users/Agents co-manage the project by:**

- **Plan** - A high-level overview of how the project is organized is in the [Plan](/_Axis/PLAN.md).
- **Tasks** - Sequential steps to perform work under the plan is in [Tasks](/_Axis/TASKS.md).
- **Snapshots** - Context saved for review or transfer between sessions is in [Snapshots](/_Axis/SNAPSHOTS.md).
- **Reminders** - Specific time-based information is queued in [Reminders](/_Axis/Reminders/).

**7. Provide input:**

- **Notes** - Record specific, factual information for the project in [Notes](/_Axis/Notes/).
- **Ideas** - Record potential areas for improvement/exploration for the project in [Ideas](/_Axis/Ideas/).
- **Wiki** - Build a repository of domain knowledge for the project in the Wiki.
- **Chat** - Submit specific instructions by interactive chat or the API.

**8. Track work:**

- **Dashboard** - Launch a dashboard (`^dashboard`) for a live overview of the workflow.
- **Obsidian** - The free and wildly popular Markdown Editor, running on your computer.
- **Memos** - Dated messages from your Agent in `_Memos/`: decisions for you, next steps, findings, and Reviews.
- **Reviews** - Periodic assessments made at key junctures, saved as Memos.
- **Follow-ups** - Specific actions assigned to the User are tracked in Follow-Ups.
- **Cross-Examination** - Periodic review and critique of work by a devil's advocate.
- **Logs** - Direct Agents to audit the record and double-check work.



### Tips

- **Find a topic.** Type `^help` followed by a word or a question, for example `^help openclaw` or `^help teams`. Your Agent answers from this manual and lists every related section, here and in the Specification, with links. Close spellings and everyday words work too, and `^help index` lists all topics. The same list is the [Help Index](/_Axis/HELPINDEX.md).

- **Readable phone replies.** WhatsApp, SMS and similar messaging replies use short paragraphs with a blank line between them, including after a greeting before a longer answer and between distinct sections.

- **Tell side-by-side sessions apart.** WhatsApp, SMS and similar channels open each message with three lines, `A X I S   W O R K F L O W`, then ` > ` with the Project name and ` > ` with the project folder, followed by a blank line, with no dividing lines or final READY prompt. On a terminal or in a desktop app, every finished answer starts with the spaced-out Axis Workflow title, indented one space, between two dividers of 14 hyphens with single spaces between them (`- - - - - - - - - - - - - -`), and ends with one blank line and `> READY`, a bar and the project folder, without a closing divider, for example `> READY | ~/Projects/Taxes:` (followed by two spaces and `(Still working in the background)` while background work continues). The startup banner opens with the same three lines and lists Session, Project, Folder, Model, Context, Agent, Version and Status, in that order, at the left margin; Model shows the model the Agent reported in readable form, or `Unknown`; Context shows the effective `Two-pass` or `Default` method, and Axel, your Main Agent, greets you under it. On WhatsApp, SMS and similar channels the three opening lines stand in for the banner. When you run several projects in split terminal panes, a glance shows which project each pane belongs to and whether it is waiting for you.

- **Save and Resume.** Type `^save` when you leave and `^resume` when you return. With a configured Git remote, save sends a checked checkpoint when synchronization permits, and resume receives it before reconstructing the work. Both run the complete portability and infrastructure checks; use explicit handoff language or `^shutdown` when changing computers so only one copy remains active.

- **Use Reminders for time, Follow-Ups for ownership.** Ask naturally ("remind me Tuesday at 9") or run `^reminders`. A Reminder records when Axis should surface information at its next checkpoint; it is portable Markdown, not a background alarm. A Follow-Up remains the queue of actions only you can complete.

- **Capture facts as they appear.** For example, typing `^note Publishing deadline is July 5` will record that fact and your Agent will automatically consider how it affects the Plan.

- **Review working guidance.** Run `^notes` to surface the Notes that matter now, verify aging facts, renew still-important guidance, and offer obsolete history for Archive.

- **Capture ideas as they occur to you.** Same approach as notes; just type `^idea ...` and Axis will capture it for later brainstorming.

- **Clear what is waiting on you.** Run `^followups` for the complete queue of questions, decisions, and actions that only you can complete. A Follow-Up points back to the Task or project record it affects, so the ask does not drift across several summaries.

- **Cross-Examine your work.** Before you rely on an important deliverable, type `^cx` - an independent Cross-Examiner will stress-test the assumptions and write a critique you can read. When Cross-Examination runs on a local model, there is no per-token provider charge, so make `^cx` a habit rather than a splurge and cross-examine early drafts, not just final deliverables.

- **Monitor everything from a browser.** `^dashboard` opens a live, self-refreshing overview - project, plan, tasks, ideas, notes, logs, and health warnings at a glance. Separate **Reminders**, **User Follow Up**, and **Agent Activity** cards distinguish what is coming due, what waits on you, and what the Agent should advance next. The always-visible Review carries the deeper Recent Developments analysis, so coming back after a week away does not mean reading the whole project. The Dashboard is the live view; `^status` is the quick look (one screen, or a web page), and `^review` is the dated report you can file, print, or email.

- **Run cheap.** `^install ollama` tests a small local model before using it for qualified routine delegation - and only when it catches the planted flaw in at least 4 of 5 identical runs of the aptitude screen does critique route to it. This is one of the biggest budget levers in Axis: local cross-examination has no per-token provider charge, so your frontier-model budget goes to the work that deserves it and you can afford to cross-examine far more often than you otherwise would.

- **Refresh your project.** Run the `^refresh` command now and then to identify stale file locks for quiescent recovery, remove dead Markers, archive over-limit Notes, delete leftover scratch files, and realign your Plan with your Tasks.

- **Keep coordination history available.** Coordination reads the relevant Archive family folders (and compatible flat year folders), without scanning unrelated development evidence. If a required archived record is cloud-only on macOS, make that specific record available offline and retry. Unavailable history holds new deduplicated work and index refresh.

- **Keep large history manageable.** Use the [archiving policy and cold-history procedure](#archiving-policy-and-cold-history) to review history before moving it. **Cold Storage Location** names a destination for approved cold storage; **Archive Location** is retained for legacy lookup. Keep generated caches outside your Markdown vault when practical. A slow vault may also need maintenance under the editor's own guidance.

- **Link your Wiki.** Run the `^wiki lint` command now and then to health-check your knowledge base - always a good idea.

- **Audit hidden problems.** Run the `^audit` command to perform a read-only health check. It will check hygiene, delegation failures, cross-examination coverage, secrets in the wrong place, records in sync, etc. - and then report findings with recommendations.

- **See where things stand.** `^status` prints a one-screen summary: the project, path, model and counts, then direction, current work, what is waiting on you, upcoming Reminders, recent activity and the next decisions. It writes nothing, so run it whenever you like. Add `web` for a branded page in your browser, or `deep dive` (or just ask for more) for the full picture.

- **Ask for a Review.** `^review` writes a dated report for you and your Agent, opening with what has changed since the last one - commits, records written, Wiki activity - followed by health-checks and Deliverable coverage. A Review summarizes the project; it does not challenge the work (that is `^cx`) and it is lighter than `^audit`. Older project records may call a Review a Status Report. Schedule one as a regular event on systems with a scheduler.

- **Ask for a custom report.** You can always ask your Agent to draft plain-language version of a Review to send to a client, a boss, or another stakeholder - just ask your Agent.

### FAQ

**Who coordinates my project?**
**Who is Axel?**

Axel is the Axis mascot and the name your Main Agent introduces itself with - the persona of the Agent that coordinates your project. An Auxiliary Agent, Assistant, Group Agent or Observer also greets as Axel and names its role; the Subagents Main spawns (for cross-examination or Wiki work) are unnamed. Records are always signed with the Session ID, never the name. The startup block identifies the project, folder and Agent role, with a Session ID for roles that have a recorded session.

**Is my data local?**
By default. Axis is just files in your project folder - no remote Axis backend, account, or telemetry. The optional Dashboard uses a loopback-only server on your own computer. If you choose a Git remote for portability, tracked project state is also stored by that provider; plaintext Secrets remain excluded unless you deliberately enable the encrypted capsule. Whatever your AI tool sends to its model is governed by that tool, not by Axis.

**Which AI tools work with Axis?**
A host must load the complete project-root `AGENTS.md`, directly or through the exact `@./AGENTS.md` pointer in `CLAUDE.md` or `GEMINI.md`. If imports are unsupported, ask it to read and follow `AGENTS.md` directly. Import handling varies by host and version; see [Host Channels](/_Axis/Resources/Host-Channels.md). You can switch hosts mid-project; the project folder is the source of truth.

**Do I need Ollama or a local model?**
No. Local models are an optional upgrade for cheaper Subagents and Cross-Examination - run `^install` if you want one.

**Does Axis require Git, Ollama, OpenClaw, or age?**
No. Axis has no add-on runtime dependency: its canonical Markdown workflow continues without any of them. Git adds versioned synchronization, Ollama adds local-model delegation, OpenClaw adds always-on channels and schedules, and `age` adds encrypted Secrets transport. Python is optional too: the helper scripts speed up startup and enforce some checks, and without Python your Agent follows the same procedures by hand. When one is unavailable, Axis reports the narrower capability loss and uses the portable file-based or manual fallback; unrelated work continues.

**Where do I put API keys and secrets?**
In `_Axis/Secrets/`. Plaintext there never enters Git, and Agents only open it when a task needs a credential, never copy values anywhere else, and never show a value in chat even when you ask; they point you to the file so you can view it yourself. Optional encrypted transport can commit only a public recipient and verified ciphertext so authorized computers can restore the plaintext with a separate private identity (see [Encrypted Secrets Between Computers](#encrypted-secrets-between-computers) for its limits).

**How do I update to a newer Axis?**
First check which release is installed: the `Version:` row of the startup banner shows it, and so does `current-version` near the top of `_Axis/CHANGELOG.md`. An installation at 3.20 or later updates in one step, as described below. An installation at 3.19 or earlier must update to 3.20 first, because its own update procedure accepts only a release whose three entry files are identical, and every release after 3.20 keeps the complete instructions in `AGENTS.md` alone. Type `^update v3.20`, let that update finish, close the old session and start a fresh one. After the Agent confirms in the fresh session that the update is complete, type `^update` for the latest release. If a plain `^update` on such an installation stops at the entry files, it has applied nothing; continue with `^update v3.20`. A child project at 3.19 or earlier needs the same order: `^^update all to v3.20` first, then `^^update`. If the exact 3.20 release cannot be verified, stop for a reviewed migration. Keep the installed update checks intact; do not choose a version from a test fixture.

Run `^update`. Your Agent downloads an exact official release into temporary staging, compares it with both your installed release and local project, previews the migration, and proceeds when it is expected and unexceptional. Your `^update` invocation is sufficient; there is no extra `UPDATE` entry. A conflict or exceptional migration asks only for the specific decision needed. After a successful migration, `^update` shuts down the old Axis session itself - do not run `^shutdown` afterward. Close that window (or terminal) and start a new session so the updated Workflow loads.

When an old updater or pre-commit checker blocks an update, Axis loads a conditional bootstrap/recovery procedure. An exact known checker repair preserves staged, unstaged and untracked work, keeps ordinary commit checks, and does not itself complete adoption. Customized or unrecognized checkers remain held for review.

**Does it run on Windows?**
Yes. WSL or Git Bash unlocks the complete shell-backed feature set. Without a POSIX-like shell, the canonical file workflow still runs through the host's file tools; shell-dependent enhancements report the limitation and use their documented fallback where one exists.

**Can I rename the `_Axis/` folder?**
No - the implementation files for Axis reference `_Axis/`, `_Temp/`, `_Trash/`, and `_Wiki/` literally. You can rename the parent folder holding the entire project, but do not rename those specific folders within it.

**Can I use my own README for my project?**
Yes. The Axis README you see on GitHub is not part of the download, and a cloned copy is replaced during setup. Project Setup creates a README for your project; Axis refreshes only its bounded project-summary block during `^review`, `^save`, and outgoing `^git` checkpoints, and anything you write outside that block remains yours. Use `^help manual` or `^help <topic>` to browse this manual without loading all of it.

**Can I use a different entry file?**
No - use the `AGENTS.md`, `CLAUDE.md`, and/or `GEMINI.md` files provided by Axis. They are reserved Workflow machinery: `AGENTS.md` holds the instructions, and the other two contain only `@./AGENTS.md` plus a final newline. Put standing project or host guidance in `_Axis/INSTRUCTIONS.md`; `^update` can then replace entry machinery without erasing your instructions.

**Can my project live in Dropbox, Google Drive, or OneDrive?**
That can work, but Axis detects cloud-synced folders and disables parallel writes, which degrades performance (see [File Sharing](#file-sharing) and the Specification's [Known Limitations](/_Axis/SPECIFICATION.md#known-limitations-and-open-issues)). A plain local folder is better.

**Where do Subprojects go?**
Anywhere your organization puts them: a Subproject is any folder that is itself a complete Axis Project - carrying the standard entry files, `_Axis/` with its core control files, and `_Temp/`. Nest one inside `Clients/Acme/`, keep one at the project root - Axis recognizes it by what it carries, not by where it sits.

**Can a Subproject contain its own Subprojects?**
Yes. Nesting is recursive: any complete Axis Project inside another is that project's child. Each session inherits ordinary guidance from its nearest enclosing Axis Project. The ultimate parent has oversight over the entire nested tree by default, including grandchildren and deeper projects; work is relayed through the owning Mains.

**Can a Subproject have its own Git repository and GitHub repository?**
Yes. Choose one arrangement deliberately: let the outer repository track the child's files, keep an independent inner repository and add that child's exact path to the outer `.gitignore`, or configure the child as a Git submodule. A nested repository is not automatically ignored: if it is added accidentally, Git normally warns and stages a gitlink pointer instead of the child's files. When Axis first sees a new or unclassified child, Main Agent stops before changing or staging anything, explains the three choices, asks you to select one, applies and verifies the Git configuration, and records the decision in a parent Note and Event. Git stores the operational arrangement; GitHub hosting is optional.

**What happens to Subprojects when I clone the parent repository?**
Parent-tracked children arrive with the parent. An independent child ignored by the parent must be cloned separately into its exact path in the workspace. A submodule is recorded by commit pointer and must be populated with `git submodule update --init --recursive` or a recursive clone.

## Everyday Use

### Commands

**You do not actually need commands** - you can do everything you need to do just by asking your Agent. Power Users, however, may prefer to use a few of the following, pre-defined commands. Invoke a command by typing `^<command>` (e.g., `^help`).

For example, the text...

> `^note Publishing deadline is July 5, 2026`

...will direct an Agent to save the associated text (`Publishing deadline is July 5, 2026`) into a new **Note**. Agents process new notes with contextual awareness, so in this case the Agent might also enquire about adjusting the Plan, adding Tasks, and taking other actions to make the publishing deadline.

| Command      | Purpose                                                                                                        |
| ------------ | -------------------------------------------------------------------------------------------------------------- |
| `^archive`   | Run the saved archiving policy, optionally changing it for future rounds.                                   |
| `^audit`     | Run a read-only project audit - records, hygiene, delegation, coverage - and save the findings as a report.    |
| `^axis` | Inspect or attach to an exactly bound project session. |
| `^backup`    | Back up the entire project to a User-named location outside the project folder.                                |
| `^board`     | Show what every Agent is doing - open work, questions between Agents, and overlaps. |
| `^cx`        | Launch a Cross-Examination.                                                                                    |
| `^dashboard` | Launch the Axis Dashboard in a browser.                                                                        |
| `^feedback`  | Send a bug report, feature request or question OUTSIDE this project, to the Axis Workflow developers - prepared here, sent only on your word. |
| `^followups` | Review the User's open Follow-Ups, or add, update, resolve, withdraw, or convert one.                          |
| `^git`       | Save or receive project changes through safe, adaptive Git synchronization.                                    |
| `^help`      | Summarize and list all commands, answer general questions, and find where a topic is explained.                |
| `^idea`      | Save an Idea into `_Axis/Ideas/` for future exploration.                                                       |
| `^ideas`     | Review Ideas - update status and priority, archive, and surface top priorities.                                |
| `^inbox`     | Scan the project's `_Inbox/` and file what arrived.                                                            |
| `^install`   | Install extensions, tools, skills, MCPs, CLIs, functions, etc.                                                 |
| `^jobs` | Inspect bounded work, attempts, authority and outcomes. |
| `^kill`      | Stop another live Agent by revoking its Marker lease (tombstone; User-only).                                   |
| `^log`       | Manually Log an entry into `_Axis/Logs/`.                                                                      |
| `^memo`      | Write or update a Memo for User in `_Memos/`.                                                                  |
| `^memos`     | List live Memos, read User's replies, and archive finished ones.                                               |
| `^merge` | Absorb a project folder, combining its records, Memos and Wiki into one continuing project. |
| `^note`      | Manually save a Note into `_Axis/Notes/`.                                                                      |
| `^notes`     | Review active Notes - surface salient guidance, renew aging facts, and archive obsolete history.               |
| `^onboard`   | Guide a new User through a five-minute tour - one Note, one Idea, one Review.                           |
| `^plan`      | Draft (or redraft) a Project Plan and harmonize it with Tasks.                                                 |
| `^profile`   | Select a Profile, change Settings, and draft a Mindset.                                                        |
| `^refresh`   | Refresh the project - sweep stale state, resync records, and realign Plan with Tasks.                          |
| `^reminders` | Review and manage the portable Reminder queue.                                                                 |
| `^review`    | Write a Review - a dated report on the project's state, saved as a Memo in `_Memos/`.                          |
| `^resume`    | Pick up where project left off - load latest Snapshot, Tasks, recent Logs.                                     |
| `^save`      | Sync workflow and save a Snapshot.                                                                             |
| `^schedule` | Create, inspect and control portable schedules. |
| `^settings`  | Step through and potentially adjust each setting.                                                              |
| `^shutdown`  | Gracefully stop this Agent - save (Main), log, delete own Marker, and end the session.                         |
| `^split` | Turn a project subfolder into an independent Axis Subproject with relevant parent history. |
| `^status`    | Show where the project stands on one screen; `^status web` for a branded page, `^status deep dive` for more. |
| `^tasks`     | List Tasks at a glance, and optionally apply a quick update.                                                   |
| `^team` | Create and control an Axis Team of Agents. |
| `^trash`     | Empty `_Trash/` on demand - everything, or item by item.                                                       |
| `^undo`      | Roll back recent changes to a checkpoint - confirm the target, checkpoint the current state, then restore.     |
| `^update`    | Update Axis Workflow machinery to an official release while preserving project state and local customizations. |
| `^wiki`      | Set up, update, and/or maintain the Wiki.                                                                      |

`^upgrade` works as another name for `^update`, and `^restore` as another name for `^resume`.

Supervision uses a separate double-caret namespace. These commands cover recognized nested Axis Projects; actions reach deeper projects through each immediate parent. No registration or Supervisor Setting is required.

| Supervision command | Purpose |
| --- | --- |
| `^^help` | Explain supervision commands, authority, records, and fallbacks. |
| `^^list` | List all recognized descendants and their live Agent picture. |
| `^^status [child\|all]` | Summarize progress, blockers, activity, and Agent state. |
| `^^inspect <child>` | Perform a deeper read-only inspection of one child. |
| `^^message <child> <text>` | Persist an outbound Message and a bounded child submissions envelope, then optionally notify its exactly bound session. |
| `^^start <child\|all>` | Start a genuine child Main session when the Host supports project boot. |
| `^^stop <child>` | Stop the exact child Main gracefully or fence its lease. |
| `^^restart <child>` | Stop and start a child without overlapping Main sessions. |
| `^^update [child\|all] [to vX.YY] [stop-agents]` | Update every Axis project nested below this one, each through its own `^update` and fresh-session adoption. |
| `^^schedule ...` | Record and optionally provision recurring read-only supervision. |

### Reading the Dashboard

The Dashboard is a live interpretation of Axis records, not a second database. It refreshes every 30 seconds, and the timestamp at the lower left tells you when the most recent read finished. Reload forces the same complete read immediately. The header's count line puts each count before its label and summarizes Agents, Tasks, Ideas, Notes, Logs, Reviews, Snapshots, Cross-Examinations (CX), and Audits; an amber Review or Snapshot count means its documented cadence is overdue. `Reviews` in that count line means saved reports, not the conditional untitled findings box.

The **Configuration** card reports installed identity, selected models, and Host facts:

| Field | How to read it |
|---|---|
| **Version** | Installed Axis release from `_Axis/CHANGELOG.md`; `Unknown` means the version metadata is missing or malformed. |
| **Profile** | The named Settings profile whose values currently match, or `Custom`/`Unknown` when they do not. |
| **Main Model** | The standard-capability model running the current Main Agent session. |
| **Model access** | How this session reaches its model, as recorded for the session: `Subscription`, `API key`, or `Unverified` when the route has not been confirmed. |
| **Local Model** | The model selected in Settings for bounded local delegation. Selection alone does not mean the model is reachable or vetted. |
| **CX Model** | The model assigned to Cross-Examination. `same-as-host` is resolved to the current Main Model. |
| **CX Frequency** | When independent Cross-Examination runs: Never, Final deliverables, Key steps, or Every step. |
| **Fault Tolerance** | The Fault Tolerance level from Settings with its name, from `Strict (-2)` to `Very Lenient (+2)`; a missing value shows `Balanced (+1)` and a malformed one `Invalid - Strict (-2)`. |
| **Last Snapshot** | Age of the newest saved project-context Snapshot from its portable UTC filename, or `None` when no Snapshot exists. A clone or folder copy cannot make an old Snapshot look newly created. |
| **Portability** | Result from the newest `^save` Continuity block: `Ready`, `Degraded`, or `Unverified`. It is historical until the next save or resume revalidation. |
| **Subagents** | `Ready` when this host can start additional Agents; otherwise `Not available` with the reason, or `Unknown`. |
| **Parallel** | Whether the host can run eligible Subagents concurrently. |
| **Shell** | Whether the Main Agent can run terminal commands in this project. |
| **Cloud-Safe** | Whether the current project location may use Axis's ordinary concurrent-write protocol. `✓` requires both `Storage Policy=auto` and a freshly established `atomic` storage profile; `Unavailable` means Axis is deliberately using serialized single-writer behavior; `Unknown` means policy or storage could not be established and is treated as serialized. It does not mean that a cloud provider itself has been security-audited. |
| **Local Platform** | One statement about local models on this machine: whether the local endpoint is reachable, whether local Subagents can use it, and the selected Local Model's Axis readiness, for example `Ready - endpoint available, subagents ok`. The five installation checks cover exact token output, field extraction, constrained summary, flaw spotting, and long-input fidelity. `Ready` means all five passed; `Retest` means at least one passed only after retry; `Review` means at least one failed. `Not available - no local model endpoint` means no supported local endpoint is reachable in this session. `Endpoint available - local model not yet checked` means no selected model or valid matching scorecard establishes readiness. This is an Axis task-readiness result, not a general intelligence score. |

For capability rows, `✓` means the fact is confirmed available, `Unavailable` means it is confirmed absent, and `Unknown` means the Dashboard could not validate the current Flag. When findings exist, the untitled card above the opening row explains unavailable or unknown facts in complete sentences, so the symbols never carry the whole diagnosis themselves.

**Mindset** shows how each behavior differs from its default: `Much Less -2`, `Less -1`, `-` for no adjustment, `More +1`, and `Much More +2`. The word is the practical interpretation; the signed number is the stored Settings value.

The conditional full-width findings box is a deterministic browser check, not an Agent response. It has no label because each bullet is written to stand alone. When findings exist, it appears at the top of the third column, above Agents, and lists independently understandable results from project setup, stale sessions or locks, queued requests, Notes pressure, Host limitations, recent capability downgrades, and the newest Snapshot's safe infrastructure summary without repeating them in an aggregate count; with no findings, the box is absent. Infrastructure appears only when a declared logical item was `absent` or `unverified`; healthy `present` and `not-applicable` declarations remain invisible, and the browser never reads Environment or Secrets content to produce these notices. Refresh failures stay out of the findings box: affected cards retain their local fallback, while the footer reads `Partial Refresh on: {timestamp}` until the next complete refresh. Faded-red medium-weight notices require particular attention. By contrast, **Review** can contain Agent judgment: its full-width card follows Plan, showing the newest report's opening synopsis or `No Review yet - use ^review.` until one exists, with links to read it in full or list every Review. **Snapshots** closes the page with the five newest Snapshot summaries.

**Exploring from the Dashboard.** You can read the project without Obsidian. Click any count in the header (for example `15 CX`) for a pop-up list of those records, newest first, and click one to read it; `Back` returns to the list and `Open in new tab` keeps it open beside the Dashboard. `More…` at the bottom of a card does the same for that card, `View diagram…` enlarges the Plan diagram, and the ☰ menu at the top right opens the User Manual, Help Index, Glossary, Plan, Settings and other documents or record lists in new tabs, and switches between light, dark and system themes. Everything is read-only. Topic and section links move to the named heading in the current document or open the linked document at that heading. The reader and its pop-ups support these links; ordinary links without a section open the document at its top.

Reload does not contact an Agent or model. It immediately re-fetches the same approved Markdown files, Flags, and record listings used by the 30-second automatic refresh, then reruns the Dashboard's client-side parsing and mechanical checks. Reasoned changes appear only after an Agent has written a new source record; Reload makes that state visible sooner.

The remaining cards are direct views of project records. **Project** runs tall in the left column. **Tasks**, **Ideas**, **Notes**, **Logs**, **Reminders**, **User Follow Up**, and **Agent Activity** stack in the right column. Reminders is the portable queue ordered by exact UTC due time; User Follow Up holds questions, decisions, and actions only you can complete; Agent Activity covers overdue work or maintenance the Agent can advance, rather than completed-event history. A Reminder remains a checkpoint view, not proof that a background alarm is running. Snapshot and Review cadence comes from each record's UTC filename, so a clone or copy does not reset it. Ideas, Notes, and Logs show their newest entries; Logs also includes a 14-day activity sparkline. A full-width **Teams, Messages and Jobs** card lists cached rows from the Coordination views; open a record to check authority and limits before acting. **Wiki** appears only when the Library is in use. **Plan** renders the current execution summary and diagram with a bundled, version-pinned Mermaid renderer, never a remotely executed script. **Tasks** is the operational work queue at the top of the right column. It shows an explicit range and total, with a status filter and Previous/Next controls for pages of 25; the selection stays in place across refreshes. Its age labels come from each Task's durable `updated:` field rather than filesystem `mtime`. The always-visible **Review** follows Plan without another divider and reads `No Review yet - use ^review.` until the first report exists. Its `Recent Developments` section is the deeper synthesized view, including commit history that the browser-only Dashboard cannot inspect.

### Inbox

Drop anything new for the project into `_Inbox/`: documents, data, images, notes or Wiki sources. At the start of the next session, or when you type `^inbox`, your Agent files each item where it belongs. Project material goes into the right Project Subfolder, with a new one created when nothing fits. Material for the knowledge base goes into the Wiki's `_Wiki/_Inbox/`, and an item that serves both goes to both places. `^refresh` files the inbox too. Anything unclear, protected, or that looks like a password or key stays in `_Inbox/`, and your Agent asks you about it. Your Agent tells you in one line what it filed and where. Sources meant only for the Wiki can also go straight into `_Wiki/_Inbox/`.

When a source affects your current goal, constraints or next step, your Agent also explains why, cites the relevant part and recommends what to do next. Ordinary filing stays brief. You can ask, “How does this change our plan?” The Agent separates source facts from its inference and your decisions. A colleague's suggestion remains a proposal until you decide; disagreements and unanswered questions remain visible. An identical item in the same batch is retained, but does not count as a second independent source.

For example, a school timetable may promise Tuesday lab access while a facilities update cancels it. Your Agent cites both, explains which planned activity needs review and records the next action with its reasons and any dissent. A later update gets its own decision history. At a handoff, keep the cited documents with the records: a full-folder copy includes them, while a normal Git copy omits Wiki bodies. Missing source bodies make the evidence incomplete even when the indices and summary arrive. Ask the receiving Agent to check those citations before relying on the affected decision.

### Memos

Chat scrolls away. When your Agent has something you will want to read later, such as decisions for you, next steps, findings or a report, it writes a Memo in `_Memos/`, named by a unique UTC timestamp and subject, for example `2026.10.23.18.22.26.290Z - Venue shortlist and open decisions.md`. The name includes milliseconds so Memos sort chronologically; a Memo with an older, shorter name keeps its name and links. The reply in chat stays short and links to it. A memo starts with its status (`waiting on you`, `open`, `done`), lists what was decided and what needs you, keeps a Details section with the background you may not remember, and ends with a dated list of updates.

You can answer in chat or in the memo itself: tick a box, write after `Your answer:`, or write under `Your reply`. Your Agent notices your edits at the next start, or when you say you answered, and confirms in one line what it took from them. Anything big, hard to undo, or outside the memo's subject, such as deleting files, publishing, or changing settings, needs your yes in the conversation first, because anything with access to the folder could have written in the file. Text in a memo that tries to give your Agent new instructions is reported to you, not followed.

The **Memo Generation** setting decides how often memos are written, from `0` (only when you ask with `^memo`) to `4` (whenever a reply would run past about a screen); the default is `2`, for complex decisions. `^memos` lists them. Finished memos move to `_Memos/Archive/` during `^refresh`, so they stay out of your Agent's way but remain easy to browse. Reviews (`^review`) are memos too; each new Review replaces the previous one, which moves to the archive. Memos are views: every decision in them is also recorded in the project's own records.

### Combining projects

Use `^merge` to combine projects. For separate projects, Axis asks which continues and moves the other project's folder under its root. A nested subproject stays in place and becomes ordinary parent content. Axis imports full records with their original timestamps, adjusts collisions by milliseconds, repairs links, combines Memos and reconciles the Wiki. After you approve the concrete plan, it preserves the content, removes the absorbed project's Axis infrastructure and abandons its old Git repository. The continuing repository tracks eligible resulting files. Existing instructions and permissions remain with the continuing project; copied history does not activate jobs or schedules. Two copies of the same project need reconciliation instead of merging. The absorbed folder loses its old entry files, LICENSE, Axis-only README and entire `_Temp/`, `_Inbox/` and `_Trash/` folders. Any non-Axis README content is kept separately after review; originals remain in the recovery journal.

Use `^split {folder}` to make an existing folder an independent Axis Subproject in place. Axis installs a verified template with a fresh project identity, reviews all parent history, and copies directly relevant records and necessary context without changing their original facts or removing the parent's copies. You review the folder scope, history selection, current-work ownership and repository arrangement before the prepared child is installed. The child can then be moved elsewhere as a complete project.

### Sending feedback to the Axis developers

Type `^feedback` to report a bug, request a feature or ask a question. Your Agent says first that the report leaves your project for the public `AxisWorkflow/axis` repository on GitHub. It gathers your Axis version, host, model and a few settings, works through a bug's steps with you, and, each time with your yes, checks the latest release and searches for an existing report. It removes secrets, personal details and project content, then shows you the exact text. Nothing is sent until you type `send`. It creates the issue with the GitHub command-line tool when that is signed in, otherwise gives you a prefilled link or a saved draft to paste. Security problems never go public: `^feedback` sends you to GitHub's private vulnerability reporting instead. The Axis maintainers make the fixes themselves; outside pull requests are not accepted.

### Initiatives

Use an Initiative when several Tasks pursue one shared outcome. For example, a Plan to grow a service might include an Initiative to improve first-time setup, with separate Tasks to investigate delays, make a change, and check the result. The Plan holds priorities, the Initiative holds shared scope and current phase, and Tasks hold the actual work.

Ask your Agent to create or update an Initiative, or use `^plan` and `^tasks`. Its shared record lives in `_Axis/INITIATIVES.md`; Tasks can link to it with an optional `initiative:` key. The Dashboard shows an Initiative link beside linked Tasks. Small projects can keep using only their Plan and Tasks. A completed Task does not automatically mean the shared outcome is achieved.

### Wiki

**Axis** will offer to build a Wiki knowledge base for your project. Should you do so?

A knowledge base takes work to maintain: sources change, cross-references break and summaries can conflict. Axis gives the Agent a documented way to organize that work in files. You choose the sources and questions, review consequential conclusions and keep backups. Agent assistance reduces some manual work; it does not guarantee complete or correct maintenance.

Retrieval can answer a question directly from source documents. Axis also keeps a persistent synthesis so useful summaries and connections can be revisited without reconstructing every earlier conversation. The two approaches can complement each other; the saved synthesis still needs checking against its sources.

During Wiki processing, the Agent reads sources, extracts relevant information and updates linked Markdown pages. It can identify contradictions and connect new evidence to earlier work. Raw sources remain available for verification; summaries are maintained interpretations, not replacements for the original material.

The Wiki is a persistent project artifact. Its value depends on source quality, accurate citations and continued review. A missing cross-reference or overlooked contradiction remains possible, so ask the Agent to show the source behind an important claim.

The Agent writes and maintains the Wiki while you direct the work and review its conclusions. Its Markdown files are portable. The shipped `.gitignore` excludes Wiki content because it may be large or binary-heavy, so back it up with a full-folder copy or backup service rather than assuming a normal Git checkpoint includes it.

The Wiki lives in `_Wiki/`, with raw sources in `_Wiki/_Inbox/`. If an older project keeps its Wiki in a root `Wiki` folder without the underscore, or its Wiki inbox in `_Wiki/Inbox/` (the layout before 2.06), the first start after an update moves them to the current names. Point Obsidian or any other tool that saved into the old inbox at `_Wiki/_Inbox/`.

### Wiki Images

The Wiki can include images. Saving attachments locally makes them available even if a source URL later breaks. Whether an Agent sees an inline image depends on the host: when the text reader does not provide image content, the Agent must open the referenced image separately before relying on it.

- In Obsidian `Settings` → `Files and links`, choose `In the folder specified below` for `Default location for new attachments`, then select `_Wiki/_Inbox/`. See [Obsidian's attachment guidance](https://obsidian.md/help/attachments); labels can vary by version.

- Then in `Settings` → `Hotkeys`, search for `Download` to find `Download attachments for current file` and bind it to a hotkey (e.g. Ctrl+Shift+D).

- After clipping an article, hit the hotkey and all images get downloaded to local disk.

- Agents will scan and link images in `_Wiki/_Inbox/` as part of their normal Wiki ingestion and maintenance routines.

### Settings

The Axis Workflow follows a set of tunable parameters in [Settings](/_Axis/SETTINGS.md). Each Setting controls one aspect of how the Agent reasons, communicates, or manages the project. The easiest way to change Settings is to **select a Profile**, but you can also edit Settings one-by-one by directly editing [`_Axis/SETTINGS.md`](/_Axis/SETTINGS.md) or by requesting help from your Agent.

The behavioral controls are **Reasoning** (depth), **Exploration** (alternatives), **Eagerness** (accommodation of your framing), **Skepticism** (questioning the Agent's own claims), **Familiarity** (tone), **Verbosity** (amount of explanation), **Simplicity**, **Precision** and **Generalization** (solution tradeoffs), **Rigor** (verification), **Creativity** (novelty), **Transparency** (record detail), and **Budget** (discretionary effort). Use `^settings` to review their ranges and values. These guide behavior; they do not directly set the host model's API parameters.

**Verbosity** controls the amount of communication, independently of reasoning and verification effort. At `-1`, updates are brief and report only major actions, results and blockers; code excerpts, diffs and command output appear only when you ask. At `-2`, answers use maximum terseness.

One Setting worth calling out is **Budget** (Frugal to Unconstrained). It steers how freely the Agent spends time, tokens, and compute on discretionary work - optional Subagents, richer models, deeper exploration, fuller records - and drives a few hard limits like how much history is re-read at startup. Note that Budget *steers* spending; it cannot *meter* it, because the Workflow has no portable way to see your actual bill or token usage. Treat it as a dial for effort, not a spending cap.

A **hard bound**, such as an approved spending cap or work window, stays binding until its owner extends it. An agreed **deadline** uses only the existing completion-grace rule. A **target** is an advisory planning figure, and a **forecast** is a prediction: if either is missed, the Agent replans or updates its estimate while useful work continues within the real bounds. If an agreed time limit is ambiguous, it is treated as a deadline. Delegated task contracts carry the same distinctions, absolute UTC hard time bounds and cumulative usage; interruption or lost context renews none of them.

**Permissions** (Restricted, Default, Autonomous) sets how often the Agent stops to ask before changing things. `Restricted` asks before anything that deletes, overwrites or cannot be undone. `Default` goes ahead when your intent is clear and nothing of value could be lost - tidying disposable scratch, committing to Git, closing finished work, archiving - and asks when it is unsure what you want, when a design or direction choice is still yours, before live model runs, and before anything that cannot be undone. `Autonomous` acts whenever your intent is clear and asks only when it is unsure or a mistake could not be undone and would matter. At `Default` and `Autonomous` the Agent may supply a command's confirmation word (such as `TRASH`) itself and tells you it did. No level publishes, pushes, runs `^update`, spends money, touches Secrets or rewrites history without you, except the narrowly logged reference corrections described under Keeping Links Valid. `Default` acts on what you actually said (or what your Plan and Tasks say); `Autonomous` may also act on what plainly follows from your goal. Every level asks before loosening a test or safety check to make work pass, and before touching anything outside the project folder that the Agent did not create itself. Typing `^update` or `^pub` is itself your go-ahead: the Agent never starts them on its own, but does not ask again when you type them. Whatever the Agent changes without asking is listed in its answer with how to undo it; at `Autonomous` it also lists any design or direction choices it made for you. Things moved to `_Trash/` stay there at least 2 days before an automatic sweep deletes them (`^trash` empties it sooner). New projects start at `Default`; say "set Permissions to Autonomous" (or edit the Setting) to change it.

**Max Concurrent Sessions** (default 10) caps recorded sessions, including Main, Auxiliary, Assistant, Group Agent and Subagent sessions. An Observer writes no Marker and does not count. Admission and delegation check the cap; stale sessions (idle over an hour) do not count. When a new session cannot be admitted, the Agent reports the limit rather than claiming it started.

**Fault Tolerance** controls bounded handling of minor deviations: -2 is strict, -1 requires ordinary repair, 0 may disclose a harmless cosmetic deviation, +1 also permits up to two minutes of eligible completion grace, and +2 permits a capped 5% grace and audited cosmetic WORM repairs. Standard defaults to +1, Fast to +2 and Deep to -1. The Dashboard shows the level. This setting never changes a failed check into a pass, authorizes a substantive history edit, raises spending limits, or overrides hard deadlines, security or host controls. See [Practices > FaultTolerance] for the exact boundaries.

**Context Management** (default `Default`) chooses how your agent decides what to read from the project for each request. `Two-Pass` makes it check the index first, pick only the records it needs, and open just those. In Axis's tests that used about 38% fewer tokens on Claude, with every answer still correct, but it did not help Codex. Axis suggests the right value for the model you use, once per session, and changes it only if you agree. This is an area under active development; the Specification's [Context Management](/_Axis/SPECIFICATION.md#context-management) section has the details and the evidence.

Another is **Skepticism** (-2 to +2). It steers how hard the Agent doubts its own work - whether it stops to ask *why* a conclusion holds, names the assumptions sitting underneath it, and goes looking for the evidence that would prove it wrong. At the highest setting the Agent explores competing explanations in parallel before committing to one. Skepticism points inward, at the Agent's own reasoning; **CX Frequency** points outward, buying an independent critic once the work is done.

### Keeping Links Valid

Axis repairs genuine broken references as it encounters them. At **Autonomous**, it never asks for repair permission. At **Default**, it repairs routine cases automatically and asks only when an exceptional or drastic change needs a substantive choice. At **Restricted**, it asks before every repair, including index links; you can approve an explicitly listed batch at once. The same policy covers narrow, logged reference corrections in write-once records, never changes to their meaning. If the intended target cannot be established, Axis reports that rather than inventing one.

An old Log may intentionally quote a mistake. Axis can record that exact occurrence in optional `_Axis/EXCEPTIONS.md` without editing the Log. The exception binds the file, its complete content hash, the finding, line and occurrence, and explains why it is intentional. It does not exempt the same bad reference elsewhere; changed source bytes invalidate it. Scans report matches as acknowledged rather than defects. Adding or changing an exception follows the same permission policy as a repair. Read-only checks such as `^audit` stay read-only. You can ask to review the registry; removing an entry makes its unresolved finding visible again.

A link into another project produces a warning and a Log; it does not block your save. Axis keeps a record when a report is renamed or a referenced file is trashed, so historical citations remain understandable. If a genuine record check blocks a checkpoint, you can explicitly approve the named files and check for that exact commit, or give a standing instruction that Axis then cites; unrelated safeguards continue to apply. An exact-file approval also works on a first Git commit. An update makes its own local checkpoint after adoption, including the record edits the update itself required, and a delegated update verifies that commit. Missing coordination folders and empty summary files are created automatically, preserving existing contents. Scratch folder names are not record IDs. A genuine reference error requires repair or approval.

### Archiving policy and cold history

`^archive` runs the saved policy. `^archive Never`, `^archive Default` and `^archive Aggressive` also save that choice for later rounds; `--dry-run` previews without changing anything. Default keeps terminal work active for 30 days, Aggressive for 7. Tasks and other records archive into their own family’s `Archive/` folder, with directory listings as the history index. Active/blocked work stays active.

Cold storage moves eligible old bodies and bulky closed diagnostics outside the project and Git. Small local catalogs preserve identities and retrieval locations even when the device is offline. Copies are hash-checked and catalogued before their sources retire. An unavailable drive leaves local sources intact. Cloud sync is distinguished from verified remote upload. Never disables history moves, including overflow, but not disposal of completed temporary recovery. Git or backups provide historical undo; a temporary update or merge recovery folder protects only the unfinished operation through validated startup. No archiving level rewrites Git history.

### Supervising Child Projects

If one Axis Project contains other Axis Projects in its subfolders (for example a portfolio of clients, or several workstreams of one product), the parent can keep an eye on them and direct them for you. Nothing needs to be registered: Axis finds the full nested project tree from the folders themselves, the next time you ask. Putting a project inside another gives the outer project authority over it. If you don't want that, keep it as a separate project, or set its Parent Authority to `advise`.

Type these in the parent project:

| Command | What it does |
| --- | --- |
| `^^help` | Explains supervision and lists these commands. |
| `^^list` | Lists every descendant project, its immediate parent and whether an Agent is active. |
| `^^status [child\|all]` | Summarizes where one or all children stand: plan, tasks, follow-ups, recent activity. |
| `^^inspect <child>` | Takes a deeper read-only look at one child. |
| `^^message <child> <text>` | Leaves a written request in the child's queue; its own Agent decides what to do with it. |
| `^^do <child\|all> <task> [with <file>]` | Gives a child an order it must carry out, refer back to you, or decline for a stated reason. A session in the child does the work under the child's own rules. `with` hands the child a file from this project. |
| `^^start`, `^^stop`, `^^restart <child>` | Starts or stops the child's Agent, when your AI host supports it. |
| `^^update [child\|all]` | Updates every Axis project nested anywhere below this one to this project's Axis version (or a named release). It shows a preview first, asks before stopping any Agent that is working in a project, updates projects in parallel (parents before the projects nested inside them) through their own `^update`, and reports each result; a project that fails or needs a decision is reported and the others continue. |
| `^^schedule ...` | Defines a bounded recurring supervision check; automatic wake-up needs a configured host trigger. |

Good to know:

- The parent never edits a child's Plan, Tasks, records or files. It reads, reports and sends requests; each child's own Agent stays in charge of that child. The one file it puts into a child is a document you hand over with `^^do ... with`, which lands in the child's `_Inbox/`.
- Supervision reaches every nested descendant by default. Work passes through each owning Main with the same approved scope and limits; routine descent requires no new per-level approval. The report identifies any held or unreachable branch.
- Status and inspection results are saved in the parent's `_Axis/Supervision/` folder, so you can look back at them.
- Starting, stopping and scheduling depend on your AI host (for example OpenClaw). Without that support, Axis tells you the manual step instead.

#### Directing a child project

Use `^^do` when you want a child to act, not just to know. For example, in the parent:

> **User:** `^^do Taxes file this statement and update the quarterly estimate with 1099-INT.pdf`

The parent moves `1099-INT.pdf` into `Taxes/_Inbox/`, writes the order down, and starts a session in `Taxes` (on hosts that can, such as Claude Code and Codex). That session checks the order really came from its parent, saves a checkpoint (a Git commit when the child uses Git), does the work in its own records, and reports back with that checkpoint as the point to roll back to. The parent then tells you what changed. Where the host can run it in the background, as Claude Code can, you can keep working while the child does; the parent reports when it is done. If the host cannot start a session, the parent tells you which folder to open; the order waits there.

- **Binding.** A child carries out a checked order, refers it back to you (for example when it needs your answer), or declines it for a stated reason such as an expired order or an unsafe state. It never quietly ignores it. For that task the order outranks the child's own standing instructions; the child reports any conflict. It never moves a secret out of the child or changes which session is in charge there.
- **Changes that can't be undone** exactly, pushing, publishing, spending money, or loosening a safeguard are listed for your approval before the child starts, and never go to `all` children at once. Your approval in the parent counts as your confirmation in the child.
- **`all`** shows you the exact order, the children and how many sessions it will start, then runs one child first and the rest one at a time. A failure in that first child stops the run.
- **Filing to children automatically.** When you drop a document into the parent's `_Inbox/` and it clearly belongs to one child, the parent delivers it to that child's `_Inbox/`. If you have written a standing instruction in the parent's `_Axis/INSTRUCTIONS.md`, for example "tax documents go to Taxes, which files them and updates the estimate", the parent issues that order itself, for tasks that can be undone, right after it greets you. Otherwise it suggests the `^^do` and offers to write such an instruction for you, so the next one routes on its own.
- **Each child decides** how far its parent may direct it with the **Parent Authority** Setting: `direct` (the default) or `advise`, where orders become requests the child may decline. Use `advise` for a child someone else runs. Only you, working in the child, can raise it back to `direct`.
- **Know the limit.** These are instructions the agents follow, not locks. An agent that was tricked into misbehaving in the parent could send an order you never gave, and the child could not tell. Recovery is the child's checkpoint: roll back to it.

The complete rules are in the [Specification](/_Axis/SPECIFICATION.md#supervision).



## Working Across Tools and Machines

To control a session that stays on your desktop from another device, see [Remote access from a laptop or phone](#remote-access-from-a-laptop-or-phone). The portability procedures below apply when work moves to another host or project copy.

### Portability

Axis always supports the simplest fallback: `^save`, stop the old session, copy the entire project folder, then `^resume` in its new location. Git makes the same serialized handoff faster and less error-prone. It does not turn two live copies into one shared project, so keep one writer at a time.

#### What the Commands Do

- **`^git` adapts to the state it finds.** With no repository, it checks for Git, offers an official install if needed, initializes the project, and commits its current state. With a local repository but no remote, it makes a local checkpoint and offers to create a private GitHub repository. With a configured remote, it fetches first, then follows the checked synchronization procedure: fast-forward incoming work, checkpoint and push outgoing work, merge verified non-overlapping paths when permitted, or report that everything is current. Conflicting or uncertain changes stop for reconciliation. After an incoming update, it automatically runs the `^resume` summary.
- **`^save` is the normal sending action.** It fetches first, runs the full portability and infrastructure assessment, refreshes the optional encrypted Secrets capsule, writes the Snapshot and Save Event, checks that every record name is well formed and that no write-once record (a Log, a Snapshot, a finished Task, archived history and the like) was edited, commits them together, rechecks the remote, and pushes when history is still linear. A failed record check stops the commit and names the files; the Snapshot stays saved locally. Offline or authentication failure does not lose the save: the local checkpoint remains and is reported as not yet verified remotely.
- **`^resume` is the normal receiving action.** It fetches before reading the saved Snapshot, saves any unsent local work first, takes the incoming work (combining both sides when they changed different files), receives the optional encrypted Secrets capsule, and then runs the complete portability, infrastructure, queues, and continuity checks. If incoming changes replace Workflow instructions, Axis ends the old session and asks you to start a fresh one so the new instructions actually load.
- **`^undo` adds recovery history.** It shows the exact target and asks before restoring. It uses a revert or a new restore commit; it never silently resets history, force-pushes, or discards later work.

Bare `^git` is convenient, but normal handoff is easier to remember as **save on the computer you are leaving, resume on the computer you are joining**. Routine `^save` does not shut down, because it is also useful as an ordinary checkpoint. `^shutdown` always saves first, so on the computer you are leaving `^shutdown` alone is enough; saying that a save is for a handoff, shutdown, or another computer does the same. Do not keep editing the sending copy after that point.

`^resume` (or `^restore`) is meant to be the only thing you type on the computer you are joining. Axis keeps the project on one branch, the remote's default (usually `main`), so you never switch branches yourself: a save made on another branch moves the project back to `main`, and a resume also brings in work an older save sent elsewhere. If the computer you are joining has changes it never sent, resume saves them first; when the other computer changed different files, it combines both sides, and it stops to ask only when the same file changed on both. With **Auto Send** on (new projects start with it on), Axis also sends your work each time it records a milestone and when you type `^shutdown`, so a computer you walk away from without `^save` has usually sent its work already; with it off, `^shutdown` tells you about work that was never sent. An Archive Location inside your home folder is kept as a `~/...` path, so it works on each computer that has that folder.

#### Optional Startup Check

Set **Remote Freshness** to `on` to check the configured Git upstream once when a Main session starts. Incoming commits produce a recommendation to run `^resume`; local files stay untouched, and no merge or push runs automatically. New projects start with `auto` (below); existing projects keep their setting, and a project without the Setting behaves as `off`. The optional check needs Git, Python 3 and supported local storage; offline or unavailable checks report freshness as unverified while Axis remains usable. It adds no background polling and does not replace saving and shutting down the other computer.

Set it to `auto` for zero-delay handoff: when the other computer saved and pushed, and this copy has no unsaved work, Axis fast-forwards to the latest commits while it starts, before it reads anything, and says so in one line. If this computer has unsent changes, both computers have new work, or Axis's own instruction files arrived in the update, it tells you to run `^resume` (or, for new instruction files, to start a fresh conversation). It never merges, discards or pushes anything.

#### First-Time Git Setup

1. In the project, type `^git`.
2. Axis verifies Git and the repository boundary, initializes a local repository if needed, inspects what will be committed, and creates the first checkpoint.
3. Axis offers to create a remote. If you accept GitHub hosting, it checks the `gh` CLI and authentication, offers official setup where needed, and asks you to confirm the owner, name, and visibility. The default is a new **private**, empty repository.
4. Axis pushes the first checkpoint and verifies the upstream. Declining the remote still leaves a useful local undo history; you can run `^git` later to add one.

Git and GitHub's CLI are optional system tools, not mandatory Axis installs. Axis asks before installing either and remains usable if you decline. An existing non-GitHub Git remote does not require `gh`.

#### Desktop → Laptop → Desktop

On the desktop before leaving:

1. Finish the current task or reach a safe stopping point.
2. Run `^shutdown` (or say `^save for handoff to my laptop`).
3. Wait for confirmation that the checkpoint was pushed. If it was saved only locally, do not assume the laptop has it.

On the laptop:

1. The first time only, authenticate the laptop to GitHub and clone the private repository into a new folder - use GitHub Desktop, or `gh repo clone OWNER/REPOSITORY "Project Name"`. The sending Agent reports the repository identity without exposing a credential-bearing URL.
2. If encrypted Secrets transport is enabled, separately copy the one private project identity to the same protected external key location described below.
3. Mount your AI tool to the cloned project and type `^resume`.
4. Work normally. Before leaving the laptop, say `^save for handoff to my desktop` and wait for the verified push.

Back on the desktop:

1. Do not reopen the old conversation as a writer.
2. Start a new session in the desktop project and type `^resume`.
3. Axis fetches and fast-forwards the laptop checkpoint before reconstructing the work. The desktop's earlier shutdown record is preserved unchanged and joins the next ordinary checkpoint; you never have to discard it just to receive the handoff.

If the same file changed on both computers, Axis stops. It preserves both sides and asks for a reviewed reconciliation instead of guessing, stashing, rebasing, or force-pushing.

#### Encrypted Secrets Between Computers

Plaintext under `_Axis/Secrets/` never enters Git, even when the remote is private. If you want Git handoff to carry those files, ask Axis to **enable encrypted Secrets transport**. Axis offers the official `age` tool if it is missing, creates one project identity outside the project at `~/.axis/keys/`, and commits only a public recipient file plus one encrypted capsule whose interior hides the original filenames. The local binding used for conflict detection also stays ignored.

The easiest way to give another computer that identity is a password. Once, on a computer that has it, open a terminal in the project folder and run `bash _Axis/Resources/secrets-capsule.sh password-set`, then choose a long password (or leave it empty and `age` makes one for you). On each new computer, after the project arrives, run `bash _Axis/Resources/secrets-capsule.sh unlock` in a terminal and type the password; Axis installs the identity and never asks again on that computer. Type the password only into that terminal prompt, never into the chat. Anyone with both your repository and the password can read your Secrets, so keep the repository private. Alternatively, copy that one private identity once - by encrypted removable media or a private password-manager/file-transfer method you control - to the same external location on every authorized computer. Either way, keep one protected recovery copy. Never put the identity in the project, Git, chat, Notes, or any location shared more broadly than the project. A clone without it can still receive the project but cannot restore its encrypted Secrets. Once configured, `^save` seals local Secrets and `^resume` receives them automatically. Failed receipt either restores and verifies the prior plaintext and binding or returns a recovery-required state while retaining protected local originals. Axis stops Secrets synchronization until that recovery is resolved. If both computers changed plaintext Secrets independently, Axis preserves both sides and asks which computer is authoritative.

Encryption protects the repository copy, not the endpoints: any process with access to a computer's plaintext project or private identity can read the Secrets, and anyone who obtained an older capsule plus the identity may retain that historical access. Prefer operating-system keychains or host-native secret stores for high-value credentials, rotate exposed credentials, and keep the GitHub repository private as defense in depth.

#### Full-Folder and Offline Fallbacks

For a thumb drive, file share, ZIP, or other full-folder transfer:

1. On the source, run `^shutdown` and confirm its save completed.
2. Copy the whole project folder only after shutdown. Do not delete the source copy until the receiver is verified.
3. On the destination, mount the copied folder and run `^resume`.
4. Keep the previous copy as a temporary recovery point; once the destination is confirmed, archive or securely remove obsolete copies - especially removable-media copies containing plaintext Secrets.

This fallback carries ignored project content that a normal Git clone omits, including Wiki content and plaintext Secrets, but it still cannot carry installed tools, login sessions, keychains, environment variables, local services, browser state, or host scheduler jobs. Axis records those dependencies by logical name in `_Axis/ENVIRONMENT.md`, checks them on every save and resume, and reports what must be restored without revealing secret values or machine identifiers.

Git also omits `_Temp/`, `_Trash/`, Wiki content, session/machine Flags, Markers, Tracking, ignored Subprojects, and plaintext Secrets unless the encrypted capsule is enabled. A Snapshot is the conversation-independent continuity record; the live chat itself and unsaved work never travel. For independent Subprojects, choose parent-tracked, independent repository, or intentional submodule deliberately - cloning the parent cannot infer or repair an ambiguous nested repository.

### Porting between AI Platforms

The promise on the tin is that you can point a different AI tool at the same folder and carry on. That is not a happy accident of storing things in markdown - it is the property the startup protocol is built around.

**One complete entry source.** `AGENTS.md` holds Axis's entry instructions. `CLAUDE.md` and `GEMINI.md` each import that sibling file with `@./AGENTS.md`. A host without import support can read `AGENTS.md` directly. If a host delivers the same instructions twice, Axis's guard avoids repeating a completed startup only while the same project's complete, unchanged instructions and own session identity remain in current context. Turn checks and full recovery after compaction still apply. This does not prevent a host from inserting duplicate text into context or establish a token saving.

**Startup decides by identity, never by clock.** Each session mints a Session ID, uses it for its in-flight lock and Main Marker, validates the complete startup record, writes and reads it back on Line 1 of `_Axis/Flags/session-id`, and only then prints it in the Session ID banner with the greeting. When a conversation resumes - or when a compaction summary wipes the Agent's memory of having started at all - the protocol compares that ID by value and takes one of four rungs. It never reasons from file age, so it cannot be fooled by a slow sync, a rewritten timestamp, or a machine whose clock disagrees. A new tool opening the folder has no matching Session ID banner, so it correctly runs a full startup instead of pretending to resume.

**Capabilities are detected, not configured.** Main eligibility is checked before startup. At every Session Start the Agent records its model, probes spawn/parallel/shell/local-model/cloud-sync facts, and establishes the current storage profile beneath the persistent Storage Policy ceiling. Each conditional feature declares what it needs in [Rules > Capabilities](/_Axis/Rules/Capabilities.md). Moving to a tool that cannot spawn Subagents makes Cross-Examination degrade to a clearly labelled in-context review and Wiki ingest drop to one source per pass. Each material downgrade is logged.

**Flags carry a lifetime, and the lifetime decides what travels.**

| Lifetime | Examples | In git? | Rewritten |
| --- | --- | --- | --- |
| per-project | `project-ready`, `skip-wiki` | Yes | When the decision changes |
| per-machine | `local-aptitude`, `environment-binding` | No | Only by the owning probe/protocol |
| per-session | `model`, `host-*`, `reminder-check` | No | Every Session Start or owning checkpoint |

Clone the project onto a new machine and you inherit its decisions and nothing false about the current environment. The scorecard proving your local model can spot a planted flaw stays on the computer where that was actually measured.

**An optional environment signature notices many switches early.** When local access permits, Axis creates one non-secret timestamp ID at `~/.axis/instance-id` and compares it with a gitignored project binding. The comparison can notice a different computer/profile, harness, interaction mode, storage profile, Git clone, or copied folder and trigger a bounded boot-time validation. That validation compares the latest saved Axis version, active record IDs, transfer omissions, and infrastructure statuses before the first answer after the greeting; it does not run the queues or pretend to be a full `^resume`. The signature stores no hostname, username, hardware identifier, account, or secret, never prints or commits the raw ID, and never grants authority. If either file is missing or inaccessible, Axis simply falls back to the ordinary save/resume checks.

**Non-portable infrastructure is declared, then checked.** `_Axis/ENVIRONMENT.md` lists the logical tools, credentials, authentication, local services, environment variables, host integrations, and scheduler jobs a project relies on - without their values, accounts, local paths, secret filenames, or host job IDs. Each row names its consumer, whether it is required, a fallback, one fixed safe revalidation method, and a portable setup reference. `^save` records only `present`, `absent`, `unverified`, or `not-applicable`; `^resume` rechecks every row and names anything that was present on the source but is absent or unverified now, so a human knows what must be restored.

Declaration is supplemented by a deliberately narrow discovery pass: Axis can notice fixed tool-manifest categories, project-local integration/automation indicators, schedule language in active Notes, and the single fact that ignored credential material exists. It reports undeclared categories and counts only. It never lists secret/config filenames, reads credential content, enumerates `PATH` or environment variables, searches keychains/home directories/global schedulers, or contacts a remote service to improve a label. Authentication and host jobs that cannot be checked safely remain `unverified`; this is an honest restoration inventory, not a machine audit.

**Delegation ports too.** Every Subagent prompt is self-contained and bookended by a fresh nonce-bound envelope. The opening and closing records both carry `<<AXIS:SUBAGENT>>`, the same role, and the same random nonce. A Subagent's role is fixed by those validated boundaries rather than inferred, so the same prompt carries the same role and contract across hosts; each host must still honor it. A prompt cut at either end by a smaller context window is designed to fail loudly rather than quietly work from a fragment - the carried rules refuse in most measured trials, and the Main-side gates catch what slips. Where Python runs, Main checks each assembled prompt with a small script before sending it.

**What ports, and what does not.** Canonical files can port: plan, tasks, follow-ups, reminders, notes, ideas, logs, snapshots, reviews, audits, cross-examinations, archived history, Wiki, settings, infrastructure declarations, and generated mindset. A same-folder switch sees them all. A full copy carries files but not installed tools, environment variables, authentication, keychains, local services, browser sessions, or host jobs. A Git clone also omits plaintext Secrets unless their optional encrypted capsule is configured, plus Wiki content, session/machine Flags, Markers, Tracking, scratch, Trash, and ignored Subprojects. The external private capsule identity never travels through Git. The conversation and unsaved work cannot travel; Snapshots are the continuity layer. In a repository-backed `^save`, the Snapshot and its Save Event enter the same selected commit. The later `^shutdown` Event and Tracking tail are operational evidence rather than canonical project state; because shutdown does not commit, a Git clone may omit that tail without making the saved checkpoint incomplete.

Every successful `^save` creates a portability-assessed checkpoint and sends it when the configured upstream and checks permit. `^resume` first runs the checked incoming Git procedure, then revalidates the checkpoint in the current environment. Linear history can fast-forward; the documented disjoint-path route can merge non-overlapping changes, while conflicting or uncertain paths hold for reconciliation. Axis cannot install tools without permission, reconcile arbitrary simultaneous replicas, or stop an unreachable old host.

The checks distinguish five modes: same-folder host switch, full-folder transfer, Git clone to a new sole writer, shared authoritative filesystem, and independently writable replicas. The last mode is not automatically merge-safe: use one writer, finish synchronization/reconciliation, then resume on the receiver. For a full-folder move, save and `^shutdown` the source Main before copying so its live lease is not transported as active work.

One honest note: a session's Marker stays fresh for an hour, and no file can tell a tool you closed from one still running. So a port may prompt a single question about whether another session is live. Say that you switched, and your Agent clears it.

### File Sharing

Axis needs no file server: a project is a folder. A shared authoritative folder gives participants one copy, but does not prove safe concurrent writes. Detected network mounts and cloud-sync locations use serialized operation. Independently writable sync or Git replicas also require serialized handoffs: `^save`, stop the old writer, synchronize or reconcile completely, then `^resume` on the receiver. Conflict copies are findings, never merge instructions.

- **Share narrowly.** Export only the project directories through the OS file server (SMB on macOS), with a dedicated non-admin account per client machine. Never share home directories, keychains, SSH keys, or credentials.

- **Reach it privately.** Connect remote machines over an encrypted private mesh such as [Tailscale](https://tailscale.com) using its device names, and restrict that network path to the file-sharing port. Never port-forward or expose the file server to the public internet.

- **Unreachable means stop writing.** If the authoritative share goes away, Agents stop writing. A network timeout is not a successful lock, and no client promotes its own copy to writable authority. Even a successful local lock operation does not prove that a network filesystem coordinates multiple writers correctly; keep the detected serialized policy.

- **Keep churn local.** Only real project content lives on the share. Caches, sandboxes, build artifacts, `node_modules`, and agent scratch belong on each machine's own disk.

- **Back up from the owner.** Version control travels with the folder, but backups run on the authoritative machine (e.g., Time Machine plus an encrypted off-site copy) to a destination no Agent can write.

### Terminal sessions and model access

`python3 _Axis/Resources/axis-roles.py retire`, run from the project folder, ends that project's live Main: it shows the session's recent activity, asks you to type `RETIRE` (or takes `--yes` from your own scripts), fences its lease with the same record `^kill` writes and logs the retirement. The session stops at its next turn; its records stay. After `^install axis`, `axis retire [path]` is the short form. Use a terminal outside your agent: inside an agent's shell the command runs in agent mode and refuses a User retirement. In agent mode it acts only on a direct child project, for the calling agent's own valid Main session and a Log or Supervision record that session wrote with `requested-by: owner`, the action and the exact child path; Main writes that record only when you, the verified owner, gave the command, never for a colleague in a shared chat. Agent shells are recognized from the environment markers of Claude Code, Codex and OpenClaw and from the `axis` utility's own markers; recognition of a shell run by the Antigravity CLI or Grok Build is not verified. On Claude Code the guardrails hook also refuses the User forms of `axis retire` and `axis start`. These checks catch mistakes; an agent with an unrestricted shell on another host could still pose as you. Without Python 3, wait for the takeover limit, or write the tombstone by hand: create `_Axis/Agents/{Session ID}.kill` with `killed-by: user`, the UTC time and a reason, then delete `_Axis/Agents/{Session ID}.md`.

The `axis` terminal utility is an opt-in add-on for macOS, Linux and WSL, set up by `^install axis`. Axis works without it: open the folder in your agent as usual. It gives `axis retire` as a short form, starts a terminal in a declared role ([Assistants, Group Agents and Observers](#assistants-group-agents-and-observers)) and keeps one terminal session per project ([The optional axis utility](#the-optional-axis-utility)).

Model Access chooses `subscription`, `api-key`, or `either`; the default is subscription. Optional Model Access Claude and Model Access Codex settings override it. Either prefers verified included access and never authorizes paid fallback. A trusted Main launcher reads private provider files from Secrets only at launch, or uses the selected host credential. API use needs your spending approval. Terminal `--allow-api` authorizes that interactive paid session; use provider billing controls for a hard account cap. Automated routes retain their explicit cumulative budget and uncertain charges until reconciled. Credential values are never part of launch arguments, records or version control. Claude may ask you to approve an environment API key on its first interactive use. Until that choice is confirmed, Axis reports access as unverified. A sandboxed child may also need host approval for its Git checkpoint and narrowly scoped access to the parent submissions queue.

| Where typed | Command | Purpose |
| --- | --- | --- |
| Agent conversation | `^install axis` | Opt in to the `axis` terminal utility |
| Agent conversation | `^settings` | Set project Model Access |
| Terminal, in the project folder | `python3 _Axis/Resources/axis-roles.py retire` | End the project's live Main after you type `RETIRE` |
| Terminal | `axis retire [path]` | The same, after `^install axis` |
| Terminal | `axis [path] --role Assistant --surface laptop` | Start a declared session (the surface needs a row in your surface table) |

### Remote access from a laptop or phone

Keep the project and its running terminal agent on one authoritative computer, then use your laptop or phone as another screen and keyboard. This is useful when you want to check progress or answer an approval prompt while away from the desk. The desktop must remain available; the remote device does not receive a second working copy of the project.

This is an optional terminal route. Ordinary Axis still works through a compatible Agent host without Python, tmux, Tailscale or a phone app. If your organization prevents installation or remote login, use its approved access method or the [save and handoff procedures](#portability).

```text
Your laptop              Your phone
      \                    /
       Private network, such as Tailscale
                       |
                   SSH login
                       |
       Authoritative desktop computer
                       |
       axis -> tmux -> existing agent
                       |
             One Axis project folder
```

The host setup below covers macOS and Linux. A Windows desktop needs the launcher inside WSL and a separately verified SSH/network startup arrangement; [Tailscale documents the WSL-specific constraints](https://tailscale.com/docs/install/windows/wsl2). A Windows laptop can connect through its approved SSH client.

The diagram shows one running agent reached from two devices. Tailscale provides the network path, SSH signs you into the computer, and tmux holds the terminal while you disconnect. The agent still uses its selected model provider and account. This does not turn an ordinary desktop-app conversation into a remotely attachable terminal.

#### The optional axis utility

`axis` is a terminal command that keeps one tmux session per project, so you can return to the same running agent after you disconnect. It is an add-on: `^install axis` sets it up after showing what it adds, and it needs a POSIX shell, Python 3 and tmux. Project setup offers it once, in one line, when the host has a POSIX shell and Python 3 and no `axis` command is found; nothing is installed without your yes.

Typed alone, `axis` prints its help and starts nothing; so do `axis help`, `axis --help` and `axis -h`. To open the session of the folder you are in, name it: `axis .`.

| Command | Purpose |
| --- | --- |
| `axis` | Print the help; nothing starts |
| `axis . --agent codex` | Create or reattach to the session of the current folder (`claude`, or `none` for a shell; the default is `codex`) |
| `axis /path/to/project --agent codex` | The same for another project |
| `axis /path/to/project --detach` | Create or keep that session without attaching to it |
| `axis start [path]` | Open a fresh session; refused beside a live Main, or while an earlier terminal session for the project is still open |
| `axis ls` | List Axis tmux sessions |
| `axis projects [roots]` | List projects under chosen roots and their direct children; `AXIS_PROJECT_ROOTS` holds a reusable path-separated root list |

Repeating a command attaches to the same session without starting a second agent.

#### Prepare once, at the desktop

Ask your Agent or IT administrator to help with these steps while you still have local access. Installation, account sign-in, SSH keys, access rules and power settings are separate setup choices to review before they change.

1. **Choose the computer and account.** Keep the authoritative project there. Remote login must use the same operating-system account that owns the tmux session. Record the computer's private-network name, that account name and the project path for your own use. A different account will not normally see the same tmux sessions.
2. **Prepare the Axis terminal.** In your Main conversation, use `^install axis` to set up the optional launcher and check Python 3 and tmux. Use an already available, supported agent CLI with verified included subscription access. The launcher supports `codex`, `claude`, or `none` for a shell. It does not require a custom `ai` script or a shared tmux configuration. If Main is currently in another app or terminal, complete `^shutdown` there first, then start the new terminal session and use `^resume`.
3. **Prepare a private network.** If you choose Tailscale, follow its [official installation guide](https://tailscale.com/docs/install) on the desktop and your remote devices, then join the intended private network through your own account or your organization's invitation. Confirm the plan fits your use: its [Personal plan](https://tailscale.com/pricing) is for non-commercial use. A school or workplace should use an approved existing service or entitlement. This guide requires no paid fallback, client upgrade or new provider API account.
4. **Enable an approved SSH login.** On a Mac, Apple's [Remote Login](https://support.apple.com/en-mt/guide/mac-help/mchlp1066/27/mac/27) is under System Settings, General, Sharing; select only the users who need access. On Linux, use the distribution's OpenSSH instructions, such as [Ubuntu's guide](https://ubuntu.com/server/docs/how-to/security/openssh-server/). Tailscale connectivity alone does not enable ordinary SSH. Keep a working local login while testing remote authentication.
5. **Verify the connection and identity.** For ordinary OpenSSH, compare the first connection's host-key fingerprint with the desktop's trusted fingerprint before accepting it. Give each remote device its own approved key where possible; only its public key is added to the desktop. Never paste a password, private key or recovery code into an Agent conversation. Follow the [OpenSSH host-key guidance](https://man.openbsd.org/ssh#VERIFYING_HOST_KEYS) when a fingerprint changes.

**Access rules matter.** Have the owner or administrator permit only the intended devices/users and SSH destination. Tailscale's initial policy permits communication among all devices, and its policies do not restrict ordinary local-network traffic. Review the [access-control guidance](https://tailscale.com/docs/features/access-control/acls) with the host's own login and firewall settings. This route does not require forwarding SSH from the public internet; Tailscale [usually works without opening firewall ports](https://tailscale.com/docs/reference/faq/firewall-ports).

**Tailscale SSH is an alternative login service.** It is supported as a server on Linux and the open-source macOS CLI variant, not the normal Mac apps. It needs both network and SSH policy permission. If chosen, follow [Tailscale SSH's instructions](https://tailscale.com/docs/features/tailscale-ssh) and complete any browser re-authentication it requests. Do not change a `check` rule to `accept` merely to make phone login easier. Ordinary SSH over Tailscale remains a separate supported choice.

Review [device-key expiry](https://tailscale.com/docs/features/access-control/key-expiry) before travelling. Re-authentication or a deliberate, device-specific expiry exception for a trusted unattended computer is an owner decision; disabling expiry on every device is unnecessary. Keep a recovery route for a computer that becomes unreachable.

#### Start the terminal, then reconnect from the laptop

The examples use an illustrative desktop account `sam`, computer name `study-desktop`, and project `~/Projects/Curriculum`. Substitute the values established during setup. Terminal commands go into a shell; commands beginning with `^` go into the Agent conversation.

At the desktop, from a normal terminal outside tmux:

```sh
axis "$HOME/Projects/Curriculum" --agent codex --access subscription
```

Choose `claude` instead if that is your configured included provider. If no session exists, the launcher starts one. Send `Start Axis` if the Agent has not booted Axis yet, then use `^resume` for an existing project. Note the project and Session shown in the startup banner.

To leave the terminal running, hold Ctrl and press `b`, release them, then press `d`. This is tmux's default detach shortcut. It leaves the desktop terminal session available for another connection. See the [tmux guide](https://github.com/tmux/tmux/wiki/Getting-Started#attaching-and-detaching).

On the laptop, enable the approved private-network connection and open its terminal:

```sh
ssh sam@study-desktop
```

After login, the next commands run on the desktop, not on the laptop:

```sh
axis ls
axis "$HOME/Projects/Curriculum" --agent codex --access subscription
```

Use the same project path and, for a declared role, the same `--role` and `--surface` values as the original launch. The existing terminal and conversation should return. Repeating the command reattaches to that session; changing `--agent` or `--access` on an attach does not replace or reconfigure its running agent. `axis .` names the shell's current directory; `axis` alone prints its help and is not a session picker.

Check that the project and conversation are the ones you left before sending work. If a new startup appears unexpectedly, check the computer, account and path, and whether the old terminal ended. Do not start another provider process in a new tmux window merely to reconnect. Two attached screens can both type into the same agent, so leave only the screen you are using attached when practical.

#### Connect from the phone

Use an SSH client approved for your phone. [Termius](https://docs.termius.com/organize-and-connect-to-hosts/connecting-to-a-server) provides a mobile host form; its [Starter plan](https://www.termius.com/pricing) currently includes SSH and SFTP with a local vault. Paid cloud synchronization is not needed for this procedure. Confirm current features on your device before choosing it. Android users can also use [ConnectBot](https://connectbot.org/).

1. Turn on the approved private network. Tailscale documents a [single active VPN limit on iOS and Android](https://tailscale.com/docs/reference/faq/other-vpns); follow organizational policy if another VPN is required.
2. Add a host in the SSH app with the desktop's private address, SSH port and the same desktop account. Use the authentication prepared for that device and verify the host identity. A Tailscale address can be used if its [MagicDNS name](https://tailscale.com/docs/features/magicdns) does not resolve.
3. Connect to the desktop shell, then run the same `axis` command used on the laptop. Keep this manual step until reconnecting works. An optional startup command can then use that exact command, if the client's available features support it.
4. Make Ctrl, Esc and arrow keys available in the client's keyboard controls. Use Ctrl-b, then `d`, to detach before closing the app. Lock the phone and use the client's app lock where available: this connection grants access to the desktop account.

A phone may suspend or close its terminal connection in the background. Reconnect and attach again; success depends on the desktop session still existing. Client background features can help but are not a persistence guarantee. Termius describes its [mobile background and keyboard options](https://termius.com/blog/8-tips-for-using-ai-agents-on-mobile-in-termius).

#### Disconnecting, saving and stopping

| What you intend | What to do | What remains |
| --- | --- | --- |
| Leave this screen and return to the same running terminal | Detach with Ctrl-b, then `d`; reconnect and run the same `axis` command | The desktop process can remain running |
| Keep a durable checkpoint | Send `^save` and read its result | A Snapshot and reported local/remote checkpoint; Main remains active |
| End Main deliberately | Send `^shutdown`, wait for its stopped report, then exit the CLI if appropriate | Saved project records; that Axis session stops serving |
| Move work to a different computer or project copy | Complete the [serialized handoff](#portability), then start there and use `^resume` | Continuity from project files, subject to the reported transfer and environment checks |

Closing an SSH connection is not an Axis shutdown, and `^save` does not release Main's lease. Exiting the agent or killing its tmux session is not a substitute for a graceful `^shutdown`. When graceful shutdown is unavailable, use the existing [terminal retirement procedure](#terminal-sessions-and-model-access) as the owner; retirement fences Axis authority and does not prove that an operating-system process was terminated.

Reattaching the same terminal does not create another Axis session. Starting another conversation does: it goes through normal admission and may become Auxiliary beside the live Main. A declared role remains fixed for its session; reconnecting never promotes it. An old conversation whose lease was replaced cannot recover authority merely because its terminal survived.

**Your remote console and WhatsApp are different surfaces.** SSH into your own terminal gives you control of that existing desktop conversation and the underlying account. A WhatsApp chat through OpenClaw is a separate session with its own configured role, sender checks and limits; it does not attach to tmux. Keep shared chats on their configured restricted route and use [OpenClaw setup](#openclaw-setup) for them. Axis role guidance is not a replacement for operating-system access control; do not give colleagues your owner console credentials.

#### What can interrupt the work

There are separate limits:

- **Computer and terminal:** tmux can keep terminal programs through a client disconnect. It cannot preserve a live process through a desktop reboot, shutdown or process failure. Host policy may also end user processes after logout.
- **Provider access:** a running terminal does not remove login requirements, usage limits or a provider refusal. Use only verified included subscription access for this route. An unavailable allowance is a reason to pause or return later, not to switch to a paid API key or add `--allow-api`.
- **Axis authority and work limits:** a surviving process does not renew a lost Main lease, change a role, extend a deadline or authorize more work. Agreed task limits and required approval prompts still apply while you are away. tmux is not a scheduler or proof that work is progressing.

Before relying on remote access, agree how long the authoritative computer should stay awake and powered. Apple's [sleep settings](https://support.apple.com/en-euro/guide/mac-help/mchle41a6ccd/mac) vary by model and power source; preventing sleep uses more power, and “Wake for network access” is not proof that this remote path will work. Use an approved, bounded availability arrangement instead of blanket system-wide sleep changes.

After a reboot, restore network access and login first, then start the Axis terminal again and use `^resume`. A provider's conversation-history feature may help, but does not revive the old tmux process or supersede fresh Axis admission. Post-reboot reachability depends on encryption unlock, login and the installed network service. Tailscale's [Mac variant table](https://tailscale.com/docs/concepts/macos-variants) says the normal Mac apps do not run before login; its [unattended guide](https://tailscale.com/docs/how-to/run-unattended) distinguishes Linux and Windows behavior. Do not assume an unattended restart will recover remotely.

#### Optional Mosh and terminal adjustments

Plain SSH plus tmux is sufficient for reconnecting. [Mosh](https://mosh.org/) can improve interaction across network changes and lag. It starts through SSH, then uses UDP; it needs compatible client and server software and a permitted UDP path. Add it only after SSH works and its separate setup is approved. In a Mosh shell, run the same `axis` command. If it fails or is unavailable, return to ordinary SSH. Mosh does not add reboot recovery, model access or Axis authority.

Start with tmux defaults. If a small screen, scrolling or special key causes trouble, consult the [tmux manual](https://man.openbsd.org/tmux.1) for the installed version and the client's keyboard guide. Avoid applying a whole replacement configuration just for remote access. Detaching an unused screen often resolves confusing sizing; key combinations such as Shift+Enter still depend on both terminal and agent support.

#### Troubleshooting

| Symptom | First useful check |
| --- | --- |
| Desktop cannot be reached | Check power, sleep, private-network login, device expiry and the intended network. If another phone VPN is required, ask IT about an approved route. |
| Name fails but the desktop is online | Check MagicDNS or try the desktop's actual Tailscale address. |
| Network responds but SSH fails | Check the SSH service, selected account, authentication and access rules. A network ping does not prove SSH is working. Do not disable host-key verification or open a public router port as a shortcut. |
| `axis`, Python, tmux or the agent is not found | Check the same desktop account and its SSH environment. Ask the installer to make the approved executables available there; the Axis wrapper does not add Homebrew directories to `PATH`. |
| `axis ls` shows no session | Check the account and whether the desktop rebooted or the agent exited. A new terminal needs ordinary Axis startup and `^resume`. |
| tmux reports a nested session | Detach to the ordinary desktop/SSH shell before running the `axis` command again. |
| A fresh launch requests provider login | Complete the provider's supported sign-in yourself, locally if necessary. Keychain or login state may differ over SSH. Do not copy tokens into prompts or fall back to paid access. |
| Axis reports a replaced session or a different live Main | Follow the reported startup/recovery procedure; a surviving terminal is not authority to resume writes. |
| A phone reconnects but text is small or keys differ | Detach the other screen, check the client's keyboard controls and use the agent's documented multiline-input method. |

Before travel, perform one harmless reconnect check while you can recover locally: start an Axis terminal, note its project and Session, detach, connect from the laptop and phone, and confirm the same conversation returns. Check the intended remote network as well as home Wi-Fi. Test a reboot only during a planned maintenance window after saving and stopping work. These are checks for your setup, not a claim that this guide has tested your devices.

### Verify a Download (Advanced)

Every official GitHub Release includes two files: [`axis-project.zip`](https://github.com/AxisWorkflow/axis/releases/latest/download/axis-project.zip), which contains Axis, and [`axis-project.zip.sha256`](https://github.com/AxisWorkflow/axis/releases/latest/download/axis-project.zip.sha256), its detached SHA-256 checksum. The checksum is separate on purpose: a file inside the ZIP cannot carry the ZIP's own hash without changing the ZIP and invalidating that hash. Download both files from the **Assets** section of the [same latest release](https://github.com/AxisWorkflow/axis/releases/latest) before comparing them.

On macOS:

```sh
shasum -a 256 -c axis-project.zip.sha256
```

On Linux:

```sh
sha256sum -c axis-project.zip.sha256
```

Either command should report `axis-project.zip: OK`. On Windows PowerShell, run `(Get-FileHash .\axis-project.zip -Algorithm SHA256).Hash.ToLower()` and compare the result with the first value in `axis-project.zip.sha256`. A checksum confirms that the ZIP matches the file published beside it and catches corruption or a mismatched download; it is not a digital signature, so the official GitHub Release remains the source of trust. Verification is optional for ordinary Quick Start.

## Agents and Models

### Capabilities

Main Agent eligibility is deliberately not a degradable Capability: Axis requires a standard-capability model and the entry-point protocol stops before startup when that is not established. Smaller models remain available as bounded Subagents. This instruction-level gate makes the support policy explicit; organizations needing hard enforcement should also restrict approved Main models in the host or launcher.

At Session Start, Axis records the Main model's name and detects six **Host facts:** whether the host can spawn Subagents, run them in parallel, run shell commands, reach a local model, whether the folder appears cloud-synced, and the current storage profile (`atomic`, `serialized`, or `unknown`). Some platforms cannot spawn; Main Agent then performs all work serially. Only `atomic` together with `Storage Policy=auto` permits parallel writers and the lock protocol; the other profiles use one writer. The persistent `Storage Policy=single-writer` Setting is a safety ceiling for a location or project you never want treated as concurrently writable. There is deliberately no setting that can force atomicity.

Each feature declares the Capabilities it needs in a small table in [Rules > Capabilities](/_Axis/Rules/Capabilities.md). When a Capability is missing, the feature should degrade gracefully and be logged so you can audit it. **CX Subagents** normally run in an isolated context, and degrade to a labelled, non-isolated in-context review when spawning is unavailable. Detection re-checks at runtime (a failed spawn downgrades `host-spawn`), and if a detected value is ever wrong, just tell your Agent in chat - it will correct the Flag.

### Auxiliary Agents

A project has exactly ONE Main Agent. An additional live session without a different declared role becomes an **Auxiliary Agent**, providing continuing access within a limited scope. An agent that boots beside a live Main (one active within the last hour, judged by measured activity, never inferred from mere presence) steps down automatically, announces the live Main's identity and its measured age, and serves within a deliberately additive boundary:

- **Read and answer.** It reads the project (never `_Axis/Secrets/`) and answers questions - the Tracking timeline makes "what is going on right now?" a one-read answer, Subagents included.
- **Append.** `^note`, `^idea`, its own Logs and Tracking lines, a Status report, a clearly-labelled in-context review.
- **Create new documents** in content areas, each opening with a provenance stamp naming its author and moment - visible, attributable, reversible.
- **Proposal Teams.** It may create its own scoped Team and spawn permitted native members. Each member works in its own Team workspace and messages, returns to Auxiliary, and Auxiliary submits immutable deliverables to Main for acceptance.
- **Never** edit shared project content, touch `_Axis/` doctrine, change the Plan or Tasks, open Secrets, or spawn outside that proposal-Team scope.

Auxiliary is instructed to make only additive, attributable contributions. Optional host hooks enforce part of that boundary; they do not sandbox a compromised agent or remove its operating-system access. Credentials that require technical isolation need host permissions or storage outside the workspace. An Auxiliary never becomes Main and keeps its role for the session's life; no chat command changes a role. To make another session Main, end the live Main from a terminal in the project folder with `python3 _Axis/Resources/axis-roles.py retire` (it shows that session's recent activity and asks you to type `RETIRE`), then open a new session, which becomes Main by the normal rule. Live rehearsals covered specific hosts and versions, and deterministic tests cover the protocols and their failure schedules; neither proves that every host or model follows them. Channel delivery and GUI behavior remain limited by the evidence described below.

**When the other session has gone quiet.** A new conversation takes over a Main session that has been idle long enough, so you never have to clean up after a chat you simply left. How long depends on your Permissions setting: 24 hours at `Restricted`, 7 at `Default` and 3 at `Autonomous`. Idle for less than that (but over an hour), the new conversation asks you first and recommends taking over; say no and it joins as an Auxiliary Agent. Taking over clears the old session's record, together with any session record over 24 hours old, and the greeting tells you what was cleared. If you later type into the old conversation, it notices its record is gone, stops and asks you instead of writing.

### Returning to an old chat

A WhatsApp or other persistent chat can remain open after its Axis session has ended. Axis explains when its Main lease was replaced and stays read-only. You can ask it to start a fresh Axis session in the same chat: it loads the current rules, gets a new identity, and joins as Auxiliary if another Main is active. It never recreates the old lease or takes over an active Main. A changed installed Axis version also requires fresh startup. Takeovers retain who removed which Main, the recorded host, idle time and authorization; unknown historical details are labelled unverified. No background heartbeat or account change is required.

### Assistants, Group Agents and Observers

Beyond Main and Auxiliary, you can give a surface (a terminal, a chat or a channel) one of three declared roles. Started with `axis --role`, none of them can become Main: the startup helpers refuse it. A declaration placed only in an agent's own settings is followed by instruction only: in Axis's live tests Codex ignored it in 2 of 7 runs and started as Main. Start a surface that must never be Main with `axis --role`, or set `AXIS_ROLE` and `AXIS_SURFACE` in the host's environment settings (Claude Code's `env` setting, Codex's `shell_environment_policy`); then the startup helpers refuse Main whatever the model does. The launcher is the tested path.

- **Assistant** - your own agent: it reads the project and answers, keeps its own notes, ideas and drafts, and asks Main for anything else. It never touches the Plan, Tasks, Settings, Follow-Ups or Secrets, and it asks you before sending any message beyond its own replies.
- **Group Agent** - serves you and the people you name on a shared chat. It reads only the folders you list for that surface, never your Secrets, Instructions, Memos or records, and has no web or messaging tools. A colleague's request becomes an answer or a request to Main unless you adopt it.
- **Observer** - read-only within the folders you list; it writes nothing, not even a session record. Stop it by removing its binding.

To set one up, tell Main in this project, for example "declare my laptop terminal as an Assistant". Main adds the surface to your surface table (`_Axis/SURFACES.md`), with the folders a Group Agent or Observer may read, and logs the change. Then start the surface with the declaration `Axis role: Assistant; surface: laptop` in the agent's standing configuration, or from a terminal with `axis --agent claude --role Assistant --surface laptop`. On Claude Code the launcher also passes the declaration and the role's tool limits and withholds MCP connectors from a Group Agent or Observer, and the guardrails hook (`^install guardrails`, which the launcher requires for those two roles) enforces the role's limits and read scope, and refuses Git changes from any declared role (reading history still works; Main commits); elsewhere the limits hold through the role's instructions. A Group Agent or Observer never lists your Memos or reads your whole surface table; admission returns only its own declaration and folders. `^memos` there sends you to Main. On OpenClaw the `axis-guardrails` plugin re-adds each listed agent's role guidance to its system prompt on every run, so the guidance survives compaction. A declaration without a matching row gets a one-line notice and no service. Changes take effect at the surface's next session. Existing OpenClaw chats keep their current roles; nothing reassigns them automatically.

### An Axis Team of Agents and its Jobs

An Axis Team of Agents has a shared charter, a separate Team Leader and named workers. Every teammate can discuss, challenge and help any other teammate directly. Each has a folder for their own drafts and published revisions, and can read everyone else's work. Main reviews proposed changes, resolves conflicts and integrates them into the shared project. Teams organize collaboration; Messages retain its exchanges; Jobs record exactly what is authorized, its limits, attempts and outcome. A team can recover with a different leader or provider from these files.

An [Assignment](/_Axis/GLOSSARY.md#messages-and-delivery) is a type of [Message](/_Axis/GLOSSARY.md#messages-and-delivery) giving an agent a specific part of a [Job](/_Axis/GLOSSARY.md#coordination-and-jobs). One landing-page review Job might have separate Assignments for mobile layout and accessibility. Assignments live in Messages; Jobs retain the overall authorized work and limits. The [Glossary](/_Axis/GLOSSARY.md) also defines Submissions, receipts, admission, attempts, schedule occurrences and the supporting-record terms.

Axis uses one explicitly active writer placement. Moving a copy, changing Main or letting activation expire requires reactivation after the previous placement stops; this does not reset Job budgets.

Use `^team create` to define the objective, leader/members, outputs, validator and limits. `^team status`, `pause`, `resume` and `stop` show or control it. `^jobs` lists bounded work; `^jobs show <ID>` explains authority, limits, attempts and remaining validation. `^board` combines current agent activity with these views. A pause stops new dispatch; a stop may leave workers reaching a safe checkpoint, and Axis reports any unconfirmed stop.

Legacy records without `limits.budget` keep the helper defaults of a 60-minute Job, 3 rounds, 12 total agent starts and concurrency 3. For new work, explicitly select native money/runtime policy: an agreed monetary ceiling and/or total runtime covering preparation, worker execution, Main review and final records. Launch, round, retry and Message counts are telemetry on that path; actual concurrency, authority, host and project constraints still apply. Existing records are never silently converted. See [Coordination Manual > Native money/runtime budgets](/_Axis/Resources/Coordination-Manual.md#native-moneyruntime-budgets) for policy, charge evidence and cumulative extensions. Completion still requires validation and Main acceptance.

If an agreed budget or deadline is reached, Axis preserves the work, pauses the affected operation and asks for an extension. A limit alone does not mean the task failed. Existing authorization continues to cover its included review and finalization; a worker target does not silently shorten that grant. After approval, work resumes from the saved result with prior usage still counted. Legacy execution cutoffs permit retained-result acceptance while original authority remains valid. Native review and completion stay inside the cumulative monetary/runtime grant; actual exhaustion requires the needed extension, while evidence capture and reconciliation remain available.

Without a supported launcher, Main prepares bounded prompt envelopes and you open separate sessions, then return their results for validation. For file deliverables, Main captures the files as result attachments with checked sizes and hashes; naming a path or reporting success is insufficient. The optional `coordination.py capture-result` helper preserves the assigned worker identity and checks its file scope. Capture does not accept the work: Main must still validate it. The manual procedure remains available without Python, a provider CLI, tmux or a scheduler. Axis does not silently turn Main into its own independent leader or reviewer.

When a teammate changes or withdraws a claim others rely on, it sends a [position notice](/_Axis/GLOSSARY.md#messages-and-delivery) that must reach every affected teammate, and older copies show what replaced them. At each phase boundary the leader or Main reads the [Team checkpoint](/_Axis/GLOSSARY.md#messages-and-delivery): who published what, which reviews and questions are still open, current positions and the next actions, all derived from the Team's own records. A replacement leader starts from it instead of repeating a round.

The checked Team inbox can wait for substantive answers or observation receipts separately and return compact previews; complete Messages remain readable. The optional included route needs a trusted Host integration to verify actual access, and retains durable partial output plus uncertain process state. An explicitly selected closing contract records readiness, release, optional acknowledgment, own result and DONE. These records do not themselves prove process termination, release capacity, settle charges or accept work. See the [Coordination Manual](/_Axis/Resources/Coordination-Manual.md#compact-observation-and-purpose-specific-waits) and [Checked Session](/_Axis/Resources/Checked-Session.md#selected-closing-tools) for the usable tools and manual fallback.

### Team setup and recovery

Team infrastructure supplies identity, direct communication, owned workspaces, lifecycle and recovery. A collaboration plan selects how members work: delegation, assistance, pairing, independent assessment, deliberation, stress testing or a custom combination. Main recommends a method from the objective and asks only for consequential missing information. Every teammate can communicate directly within the grant; shared project integration remains Main-owned.

The optional `team-plan.py` read-only preview checks a versioned JSON plan. A charter can embed `collaboration_plan`; admission verifies the roles, actual charter concurrency and exact plan hash. Accepted method amendments retain previous revisions and in-flight disposition. Structural review coverage does not prove quality or approve execution. Python-free operation uses the same portable plan and canonical records. See [Practices > Teams] and [Practices > Collaboration].

Main's Message view separates actual Main obligations, uncertain cases and retained peer history. Closed Teams do not erase outstanding Main questions/results. Capacity explanations separate recorded active/reserved/uncertain attempts and policy scopes; unverified host capacity remains explicit. Neither a stale view nor an administrative close proves a process ended. These mechanisms assume cooperating writers on qualified local storage and do not certify distributed or multi-user access control.

### Scheduling

`^schedule create` previews an exact schedule: local and UTC time, timezone, action, authority, expiry, resource limits and output. `list`, `show`, `pause`, `resume`, `retire` and `due` inspect/control it. A timer proposes work; it cannot approve it. Without a configured trigger, schedules are evaluated at manual/checkpoint turns and do not wake a sleeping machine.

The baseline supports one-time, daily/weekly calendar, elapsed fixed-rate/completion-relative intervals and verified events. Unsupported recurrence is reported. Defaults skip nonexistent daylight-saving times, select the first repeated time, coalesce missed occurrences to one within expiry, and queue at most one while work is active. Unknown clock changes and external effects are held for reconciliation. Only classified safe failures get at most two retries inside the same deadline. Duplicate triggers do not admit another occurrence; Axis does not promise exactly-once external effects.

Scheduled child-project supervision initially reports status/inspection only. Recurring child starts or changes require a separately approved standing mandate. Reminders continue to mean things you must do, independently of executable schedules.

### Long conversations and compaction

When a conversation grows long, the AI tool may compact it into a summary and drop much of what the Agent read at startup. Axis tells every Agent to treat that summary as a hint: before it answers again it reloads the files its role needs, keeps any hold or limit you set, and does not take an earlier approval for a push, publication, spending or deletion from the summary alone. You need do nothing for this. If an Agent seems to have forgotten an Axis rule after a long session, ask it to run its per-turn check and reload; starting a fresh session is always safe.

On Claude Code and Codex you can also add an optional hook with `^install context hooks`; Axis shows the exact change to the tool's settings file and asks before writing it. The hook reminds a resumed or compacted session of its identity and role straight away. On Codex it also gives the startup rules back after a compaction; they stay in the conversation, so each later request carries about 9,000 more input tokens until the next compaction, and the preview states the figure for your project. On Gemini CLI, Copilot CLI, Cursor, Devin and OpenCode the same command adds a smaller hook that only records each compaction, so Axis knows to check its guidance; those tools do not let a hook speak to the Agent after a compaction. The Antigravity CLI and Grok Build have no such hook: there the entry file and the per-turn check carry recovery, and recovery after a compaction has not been observed on either. `_Axis/Resources/Host-Channels.md` lists what each tool supports and when that was last checked. Remove a hook through the same preview and approval process. Axis preserves modified or unknown OpenCode plugins; for a known plugin it saves and verifies the contents and permissions before replacement or removal, so recovery also remains possible after an interruption. A full `^audit` lists the known hook paths and matching releases. The release that installed a hook is reported only when an installation record proves it; otherwise it stays unknown. Axis helpers on Claude Code run without your own CLAUDE.md files; the Task each helper receives carries what it must follow.

### Sessions, delivery and migration

The baseline adapter supports on-demand startup. Warm or managed residency requires a separately supported host integration and explicit opt-in; the baseline does not provide persistent residency. The optional `axis` launcher shows exact project/session bindings and uses verified adapter operations. A surviving terminal, PID or provider conversation cannot restore an expired Axis lease. Unsupported attach/notify/stop operations keep the manual route available.

A [Submission](/_Axis/GLOSSARY.md#messages-and-delivery) presents information to your Main for consideration. `_Axis/Submissions/` is the only incoming submission queue; only receiving Main processes it. Messages is the communication and audit trail for teams, other agents and projects. Authorized local agents can record Messages directly. A child project's Result can arrive as a Submission and retain its Result meaning; receiving it does not validate the work.

Coordination records and Submissions begin with an ordinary Subject and readable Markdown. A labelled JSON payload and checksum at the end support validation; the system checks that readable content and payload agree. Original submissions remain visible under `Submissions/_received/`, linked to the receiving Message. Subject-first indexes and details continue to work without YAML frontmatter or Obsidian metadata ingestion.

When an update finds the older Requests queue, it moves the entries to Submissions while preserving exact contents and outcomes. Main processes those migrated entries afterward. Work already accepted remains done, referred work keeps its Task link, and historical archives remain unchanged. Migration never executes old contents; interrupted moves and collisions require recovery against the retained plan. After new-format writes, downgrade requires reviewed export/reconciliation.

### Coordinating Agents

Agents can timestamp, append and verify their activity line in one command. If tracking was missed, Main reports the gap as retrospective; it does not invent an earlier action or completion time. Before launching a separate session, Main checks that its temporary-file location stays inside the assigned project; this does not change your persistent host settings or replace sandbox protections.

When several agents work on one project - Main, Auxiliary agents on channels, Subagents it spawns, even agents from different tools - each keeps a short running diary in `_Axis/Tracking/`, creating its own file on the first append if needed. Before starting a piece of work an agent writes an INTENT line naming what it is about to do and which Tasks or files it will touch; along the way it adds STATUS lines; it can ASK another agent (or Main, or anyone) a question and receive a REPLY; and just before it finishes it writes DONE with the outcome. Because each agent writes only its own file, this works on any storage and with any tool that can read and write files.

At each checkpoint - a new turn, before changing a shared file, before starting or returning from a Subagent - every agent reads what the others have posted since it last looked. That is how it notices a question addressed to it, or that another agent is already working on the same file. Type `^board` for the Board: who is live, what each is working on, open questions between agents, overlapping work and recent completions. The Dashboard's Agents card shows the same picture.

An Auxiliary agent that needs a shared change it may not make itself can ask Main; Main decides it like any Message, records the decision and replies. A question between agents never grants permission: file locks and roles still decide who may write, and anything that needs you still comes to you.

### Checked session tools

An optional checked interface can limit an agent to specific file reads, complete coordination-history replay and atomic creation of Logs or Snapshots. It requires a trusted launcher and a verified host tool restriction; installing a helper alone does not confine shell access. Load `_Axis/Resources/Checked-Session.md` only when using this facility. Replay reports its coverage and refuses damaged or incomplete history; it does not certify business results. Record creation leaves content review and Snapshot indexing/continuity duties with Main. Separate fixed grants can add the ordinary own-session save refresh, exact created-record readback and Snapshot indexing, final-response formatting and explicitly authorized own-session retirement; see `_Axis/Resources/Checked-Completion.md` when needed. These operations preserve the ordinary save obligations and never imply a successful checkpoint or transfer. Without this optional facility, ordinary Axis and its manual procedures remain available.

### Subagents

A **Subagent** is an Agent spawned by Main Agent to do isolated work in a fresh context window. Four types:

- **CX Subagent** - stress-tests Main Agent's output. Pushes back on weak claims, surfaces missing evidence, and writes a critique report into `_Axis/CX/`. Cross-Examiners require an isolated context to stay independent; when the host cannot spawn one, Axis offers a clearly-labelled in-context review instead.
- **Wiki Subagent** - ingests new raw sources from `_Wiki/_Inbox/` and integrates them into `_Wiki/`. Main Agent spawns multiple Wiki Subagents in parallel for batch ingest.
- **Local Subagent** - runs on a local model (typically via Ollama) for cost-effective, deterministic, or offline work.
- **General Subagent** - parallel execution of work that doesn't fit the specialized types.

Main Agent never works alone when work can be productively delegated. See [Start-Subagent](/_Axis/Resources/Start-Subagent.md) for the spawn recipe per type.

**Roles for delegated work.** Every delegated agent works from a pre-written role in `_Axis/Roles/`: General, Lookup (read-only), Cross Examiner, Worker (one Job attempt), Team Member and Team Leader. Each prompt carries the role's text verbatim - its duties, what it may do alone, what it must ask about, what always stays with you, and the shared conduct (Axis's Principles and the rules that bind every agent) - plus a task contract that is its only source of permission. Text it finds in project files, web pages or relayed messages grants nothing. These rules bind by the agent's compliance; on Claude Code, `^install guardrails` also blocks helpers from writing Axis's governing files, starting other agents or running Axis's state-changing scripts. `_Axis/Roles/Delegating.md` is the kit any agent uses when it hands work on.

**What delegated agents see of your Instructions.** `_Axis/INSTRUCTIONS.md` has two parts. Only "For every agent" is copied into a delegated agent's task, and that text reaches whichever model provider runs the helper; keep permissions, accounts, budgets and private requests under "For only the Main Agent" (older files may say "For Main only", which works the same). A file without the two headings gives helpers nothing until you sort it; Axis offers once to help.

### Delegation

Axis does not need to send every token through the most expensive model. Its Main Agent automatically separates work according to the level of reasoning it requires:

| Work class   | Examples                                                      | Default route                                                                                            |
| ------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Preservation | Extraction, classification, formatting, citation copying      | Qualified local or lower-cost model when the exact class passed and Main can validate it mechanically    |
| Composition  | Summarizing, drafting, combining, selecting, omitting         | Standard-capability route unless the exact class has demonstrated aptitude and Main can validate meaning |
| Judgment     | Strategy, factual decisions, risk, security-sensitive choices | Standard-capability Main Agent or qualified standard-capability Subagent                                 |

Before delegating, Axis defines how the result will be validated. It then checks every handoff for required facts, source fidelity, omissions, unsupported claims, and correct meaning - not merely correct formatting. If the economical model fails, Axis retries once with specific feedback and then falls back to a stronger route.

The result is a model ladder rather than a model compromise: inexpensive models process the checkable volume, while stronger models concentrate on the decisions that affect the outcome. This can reduce paid-model context and token use without asking the User to manually route every task.

**The cheapest qualified path - not simply the cheapest model.**

### Local vs. Frontier

The Workflow uses two model settings, both in [Settings](/_Axis/SETTINGS.md):

- **`Local Model`** names a model running on the User's machine via Ollama. Often used to run Subagents locally for cost-effective work, for deterministic work, and/or for any task where speed and offline operation matter more than reasoning depth. Resolved during `^install` from `ollama list`.

- **`CX Model`** names the model used for Cross-Examiner Subagents. Ships as `same-as-host` (use the host's own model in an isolated context); `^install ollama` points it at a local model instead - only after the model catches the planted flaw in at least 4 of 5 identical runs of the aptitude screen. A local model avoids a per-token provider charge but uses local hardware and energy. Critique quality depends on the model and task; use qualified evidence and the stakes of the work to choose the route.

**What a small model can and cannot drive.** Small models are supported only as bounded Subagents: Main supplies the complete input, permits no direct file access, validates an explicit output contract, retries once, and falls back when validation fails. Multi-sample class scores can qualify a particular model, quantization, runtime, and machine for extraction, classification, constrained drafting, citation preservation, or similar low-stakes work without inferring aptitude across classes. A missing or failed matching score keeps the work on a stronger path. Small models do not run Session Start, maintain Axis records, ingest Wiki sources, handle secrets, or make security-sensitive trust decisions; prompt-injection performance is diagnostic and never relaxes those restrictions.

## OpenClaw Integration

### Running Axis on OpenClaw

[OpenClaw](https://openclaw.ai) is the wildly popular open-source gateway that connects an AI agent to the messaging apps you already use - WhatsApp, Telegram, Discord, Slack, iMessage, and two dozen more - and keeps it running around the clock: message it from your phone, wake it on a schedule, let it work while you sleep. One gateway can run several isolated agents, each with its own workspace and its own background sub-agents.

Axis uses OpenClaw as a **thin harness**, not as a second project brain. The integration keeps the things a Markdown workflow cannot provide by itself - channels, verified sender routing, agent/session lifecycle, directed messaging, cron triggers, and the runtime tools needed to operate the project. Axis owns identity, instructions, memory, project knowledge, Messages, and every canonical record.

The two meet at one file: OpenClaw injects the workspace's `AGENTS.md`, and that starts the ordinary Axis entry protocol. Point one OpenClaw agent workspace at one Axis Project and its roles, leases, records, Commands, and supervision become available through the connected channel.

#### How Axis and OpenClaw Fit Together


| OpenClaw keeps | Axis owns |
| --- | --- |
| WhatsApp and other channels, pairing, allowlists, routing, and bindings | Agent instructions, role doctrine, and behavior |
| Agent/session launching, tracking, stopping, and restarting | Personality and stance through `_Axis/MINDSET.md` |
| Directed session-message delivery | Persistent memory through Notes and project files |
| Explicit cron jobs and scheduled wakeups | Portable schedule intent and supervision policy |
| Operational transcripts and same-session compaction | Messages as the authoritative inter-agent message |
| The required filesystem/runtime tool substrate | Capability detection and graceful degradation |

OpenClaw must retain enough operational session state to route a turn, continue a live conversation, compact a long context, and control an Agent. That is not Axis memory. It remains bounded Host mechanics and is never a source of project truth.

- **One agent, one project.** Give each OpenClaw agent its own Axis Project folder. On startup it becomes that project's Main Agent, unless a standing declaration or another live Main makes it an Auxiliary Agent. Markers, leases, and file locks preserve the same one-Main boundary used on every other Host.
- **Role stays Axis-owned.** A standing role declaration takes effect at the next boot, and no session changes its own role. OpenClaw display metadata, transcripts, and configuration cannot reassign it mid-session.
- **Groups with other people.** Admission does not yet check who sent the first message, so an allowlisted colleague's first message in a project group can start the session that becomes Main. To reduce the risk, declare each group Auxiliary in its own group entry with the line `Axis role: Auxiliary; surface: {name}`, reset the group's session, and keep Main in your own direct chat. The group session still has Main's tools, but no chat command can make it Main. A 3.10 declaration that names External keeps working as Auxiliary. The entry may instead name Assistant, Group Agent or Observer, each with its row in your surface table ([Assistants, Group Agents and Observers](#assistants-group-agents-and-observers)); those three are untested on an installed OpenClaw group. [Practices > OpenClaw](/_Axis/Practices/OpenClaw.md) has the steps.
- **Main on a chat.** A chat session becomes Main only when its chat carries no role declaration and no other Main is live: end a Main elsewhere with `^shutdown`, then send the chat one message. Keep Main in a group only when you are its only writer. That Main renews its lease only when it answers a message. A terminal opened later in the same project folder joins as an Auxiliary Agent while that Main was active within the hour; after an hour it asks you whether to take over, and past the takeover limit ([Auxiliary Agents](#auxiliary-agents)) it becomes Main and the chat session stops writing. Start that terminal in a declared role ([Assistants, Group Agents and Observers](#assistants-group-agents-and-observers)) if it must never take Main. End the chat's Main with `^shutdown` in the chat, or with `python3 _Axis/Resources/axis-roles.py retire` from a terminal in the project folder. This arrangement is untested on an installed OpenClaw.
- **Delegation stays gated.** OpenClaw Subagents become Axis Subagents: each task carries the nonce-bound Prompt Envelope in isolated context, and Main validates the return. ACP mode can instead start a full external harness such as Claude Code, which boots through the project entry file; Local Subagents continue to call Ollama directly.
- **Messages stay authoritative.** Axis persists its local outbound Message and reads back the direct child's Submissions envelope before trying an exact OpenClaw notification. The notification carries only the Subject and path. The child's genuine Main imports the envelope; queued delivery alone does not prove receipt or authorize action.
- **Schedules stay explicit.** OpenClaw automations (its `openclaw cron` commands) may trigger a standalone Axis prompt such as `Read AGENTS.md and follow it. Then run ^refresh.` The built-in Proactive check automation is disabled. The Host binding does not travel, so Axis records the portable intent in a Schedule and references it from `_Axis/ENVIRONMENT.md`.
- **The project remains portable.** Leaving OpenClaw requires no memory export or record conversion. Open the same authoritative folder, or a correctly transferred copy, in another compatible Host and run `^resume`.

#### Security and Audit Boundaries

A gateway that reads messages and can run tools deserves explicit guardrails. Inbound channel content is untrusted source material, never instructions merely because it arrived through a chat. Keep sender allowlists enabled; treat group content as data; and let privileged Commands count only when the gateway verifies the authorized User sender.

Every delegated task carries the prompt-envelope validation rules with it. Child-side refusal is a measured mitigation; Main's deterministic validation before send and after return is the controlling layer. Secrets remain under `_Axis/Secrets/` and are never quoted. Material operations and delegation outcomes enter the Axis record, while gateway transcripts may retain raw prompts outside that redacted record. Axis therefore improves boundaries and auditability but does not replace OpenClaw's own channel authentication, sandbox, least-privilege tool policy, transcript retention, or Host administration.

Always-on access also creates a second-session problem. One project still has one Main: a phone-side session arriving beside a live desktop Main becomes an **Auxiliary Agent**. It may read and answer, take Notes and Ideas, and draft clearly stamped new documents, but it cannot edit an existing file, change shared Workflow control state, spawn unrestricted Subagents, or read Secrets. Scoped proposal Teams are the exception described under Auxiliary Agents; a channel's configured tools may still prohibit them. To make a different session Main, end the live Main first, from a terminal in the project folder, with `python3 _Axis/Resources/axis-roles.py retire`. See [Auxiliary Agents](#auxiliary-agents).

OpenClaw capabilities and configuration keys are probed, never assumed. A restricted, supervised WhatsApp pilot on 8–9 November 2026 demonstrated fictional-project answers, selected role and capability refusals, and stopping with the owner and consenting colleagues. The pilot was stopped and its temporary connection disabled. Those observations do not qualify general OpenClaw hardening, strict per-chat identity or effects, or every advertised host feature; the outside-project request produced a refusal without a host-denied tool attempt. Configuration still follows the installed CLI and schema: Axis prepares a secret-free patch, dry-runs it when supported, previews changes, obtains authorization for host changes, validates the configuration and checks the resulting Agent.

#### OpenClaw Setup

Run `^install openclaw` to install or harden the integration. Axis first asks whether the Gateway is Axis-only or also serves personal/non-Axis agents. An Axis-only Gateway may use its current profile; a mixed Gateway should use a dedicated `axis` profile so the stripped-down policy cannot change unrelated agents. A dedicated profile may require its own port, service, channel credentials, and login, so Axis previews that scope before creating it.

The hardening keeps `AGENTS.md` injection and disables the competing layers:

- Persona and bootstrap files such as `SOUL.md`, `IDENTITY.md`, `USER.md`, and `BOOTSTRAP.md`.
- `MEMORY.md`, `memory/`, embedding search, cross-conversation recall, memory plugins, active memory, session-memory capture, the automatic memory flush (it writes into the project folder), and dreaming.
- OpenClaw bootstrap hooks that run `BOOT.md` or inject extra non-Axis context. Operational command-audit and compaction-notice hooks may remain because they do not supply project instructions or semantic memory.
- The Proactive check automation, standing intents, self-learning skills (learned skills bypass the skills allowlist), default skills, and unrestricted `tools.profile: full` access, which onboarding grants by default.
- Open cross-agent access: by default every session can read other agents' transcripts and every agent can message every other. Axis narrows visibility so a session sees only itself and its own helpers, never your direct chat, and allows messaging only between exact Axis agents.
- Nested Subagents (limited to one level), OpenClaw's prompt that tells a main session to prefer hidden helpers, swarm, and unneeded browser/web, media, memory, and plugin-management tools.

The explicit Axis tool surface retains filesystem/runtime access, agent and session control, messaging, cron, status, and User interaction. Extra tools are opt-in per Project. Required channel and model-provider plugins stay enabled; Axis never disables all plugins or adds a broad plugin allowlist merely to silence a warning.

Do not create OpenClaw persona or memory files for an Axis agent. Put standing project guidance in `_Axis/INSTRUCTIONS.md`, conversational stance in `_Axis/MINDSET.md`, User/project facts in the owning project records, and persistent memory in Axis Notes. Channel display metadata may still provide a name or avatar, but it supplies no behavior, memory, role, or authority.

If legacy persona or memory files already exist, Axis checks only their existence and asks before moving them intact to `_Trash/OpenClaw-Legacy/`. A leftover `TOOLS.md` matters most: OpenClaw's repair command (`openclaw doctor --fix`, which also runs during OpenClaw updates) merges it into `AGENTS.md`, which would edit the Axis entry file, so Axis moves it first and treats every repair run and update as a change you approve. It never reads them merely to harden the profile and never edits OpenClaw's SQLite state. For a previously personal or mixed installation, a fresh dedicated Axis profile is safer than trying to clean a shared memory index. The User decides whether old profile state and transcripts are archived or purged.

Run `^audit openclaw` for a read-only report. It verifies the live-schema mapping, bootstrap and memory controls, instruction-injection hooks, effective tools, the Proactive check, skills and self-learning, session visibility, exact messaging policy, Subagent depth, delegation prompt and swarm, bounded session maintenance, channel/plugin availability, schedule declarations, and legacy-file presence. The result is `Ready`, `Degraded`, or `Unverified`; the audit never logs in, restarts the Gateway, applies configuration, sends a probe, reads old memory, or deletes anything.

The User still performs the account-bound steps: approve a dedicated profile when needed, provide and link the bot phone/account, scan the channel QR code, sign the bot account in again after a logout, approve pairing, create WhatsApp groups, and send discovery and real verification messages. Axis handles schema inspection, hardening previews, validated CLI changes, exact bindings, boot probes, and portable Environment/schedule records after the corresponding approval.

See the [OpenClaw practice](/_Axis/Practices/OpenClaw.md) for the complete thin-harness contract and the [WhatsApp practice](/_Axis/Practices/WhatsApp.md) for the channel pairing procedure.



## Integrations

### Add-ons

**Cloudflare:** `^install cloudflare` reads [Cloudflare's current agent-setup instructions](https://developers.cloudflare.com/agent-setup/prompt.md) and selects the route for your agent. Axis previews the skills/plugins, MCP connection, install scope and login effects before making changes. The CLI is optional, authentication stays in the native browser, and setup does not authorize deployments, DNS or billing changes. Cloudflare is not required for Axis.

The **Axis Workflow** runs directly from markdown - you do not need to install anything else to get Axis to run, and to run well. You may find, however, that certain third-party extensions, services, and applications will work well with Axis and significantly improve its functionality.

- **Obsidian** - Main UI for User to access project files and Wiki: https://obsidian.md
- **Obsidian Web Clipper** - Capture web pages: https://obsidian.md/clipper
- **Obsidian Graph View** (built-in) - View shape of wiki: connections, hubs, orphans.
- **Obsidian Marp Plugin** - Generate markdown presentations from wiki content.
- **Obsidian Dataview Plugin** - Query frontmatter and generate tables and lists.
- **BackBlaze** - Backup with point-in-time recovery: https://www.backblaze.com
- **age** - Optional encryption for Git-carried Axis Secrets capsules: https://github.com/FiloSottile/age
- **exa** - API for AI search, crawling, and research agents: https://exa.ai/
- **Firecrawl** - Toolkit to search, scrape, interact with web: https://www.firecrawl.dev/
- **GitHub** - Hosting for version control, tracking, collaboration: https://github.com
- **QMD** - On-device search of wiki or the entire project: https://github.com/tobi/qmd
- **Cloudflare** - Host for websites and web apps: https://pages.cloudflare.com
- **OpenClaw** - Manage remote communication and agents: https://openclaw.ai
- **Ollama** - Utility to install LLMs on your local computer: https://ollama.com
- **Qwen3-VL** - The tested model family for local delegation (via Ollama).





## Trademarks

"Axis Workflow", "Axis" when used as the name of this project, and their associated logos and lockups are trademarks of Kenneth A. Younge. The "Axis Workflow" trademark application was filed in Switzerland. These are the "Marks" used in this notice. The [Axis MIT License](/_Axis/LICENSE) covers Axis-authored text, templates, and code. It does not grant rights to the Marks or automatically license the User's project. Copyright and trademark are separate: the MIT License covers copyright only and grants no trademark rights.

#### You may, without asking

- Use the Marks to refer truthfully to this project - for example, "built with the Axis Workflow", "compatible with Axis Workflow", or "a tutorial for Axis Workflow".
- Redistribute unmodified copies of this repository under the project name, with a link to the official source.
- Say that your product, service, or training works with the Axis Workflow, provided no sponsorship or endorsement is implied.

#### Please do not

- Use the Marks, or confusingly similar names, logos, or domains, as the name of a fork, product, service, company, course, or website. Give forks their own name and describe them as "based on the Axis Workflow".
- Imply sponsorship, certification, or endorsement by Kenneth A. Younge or Kenneth Younge Advisory without a written agreement.
- Alter the Marks or combine them with other names or logos.

#### Symbols and attribution

- On first prominent use in a document, write "Axis Workflow™"; after that, plain "Axis Workflow" or "Axis" is fine.
- When an attribution line is appropriate, use: "Axis Workflow™ is free and open source (MIT License), from Kenneth Younge Advisory - training and consulting at kennethyounge.com."

Questions or permission requests can be sent to [support@axisworkflow.ai](mailto:support@axisworkflow.ai).



## License

This release is licensed under the **MIT License**. Anyone may use, copy, modify, merge, publish, distribute, sublicense, and sell it, provided the copyright and permission notice stay with every copy. Releases before Version 2.00 remain under the Functional Source License (`FSL-1.1-MIT`), and each of them converts to MIT two years after it was first made available. Third-party components retain their own copyright and licenses, including the bundled Mermaid renderer. The software is MIT licensed. The Axis Workflow name and the brand assets in `_Axis/Branding/` are not; see [`_Axis/Branding/LICENSE-ASSETS.md`](/_Axis/Branding/LICENSE-ASSETS.md). The bundled Inter and IBM Plex Mono fonts are under the SIL Open Font License 1.1. See the complete [Axis License](/_Axis/LICENSE), [Contributor License Agreement and Copyright Assignment](/_Axis/CLA.md), and [Trademarks](#trademarks).



## Copyright

Copyright 2026 Kenneth A. Younge. All rights reserved except as expressly licensed.

## Topic Index

<!-- BEGIN GENERATED: topic-index -->
106 topics covered in this document, in alphabetical order. The [Help Index](/_Axis/HELPINDEX.md) lists every topic across the Axis documents with the words people use for it; in a project, `^help <topic>` searches it.

| Topic | In this manual |
| --- | --- |
| Architecture | [How Axis Works](#how-axis-works) |
| Archiving and cold storage | [Archiving policy and cold history](#archiving-policy-and-cold-history) |
| Assistants, Group Agents and Observers | [Assistants, Group Agents and Observers](#assistants-group-agents-and-observers) |
| Assurance and evidence | [How Axis Works](#how-axis-works) |
| Audit and refresh | [Tips](#tips) |
| Auxiliary Agents | [Auxiliary Agents](#auxiliary-agents) |
| Axel | [FAQ](#faq) |
| Axis Team of Agents | [An Axis Team of Agents and its Jobs](#an-axis-team-of-agents-and-its-jobs); [Team setup and recovery](#team-setup-and-recovery) |
| Backups | [File Sharing](#file-sharing) |
| Budget and cost control | [Settings](#settings); [Delegation](#delegation) |
| Capabilities and host facts | [Capabilities](#capabilities) |
| Checked session tools | [Checked session tools](#checked-session-tools) |
| Checking for newer work at startup | [Optional Startup Check](#optional-startup-check) |
| Combining and splitting projects | [Combining projects](#combining-projects) |
| Commands | [Everyday Use](#everyday-use); [Commands](#commands) |
| Context Management | [Settings](#settings) |
| Coordinating Agents and the Board | [Coordinating Agents](#coordinating-agents) |
| Copyright | [Copyright](#copyright) |
| Cross-Examination | [Tips](#tips); [Subagents](#subagents) |
| Dashboard | [Reading the Dashboard](#reading-the-dashboard) |
| Data location and privacy | [FAQ](#faq) |
| Delegated roles and authority | [Subagents](#subagents) |
| Delegation and model routing | [Delegation](#delegation) |
| Desktop to laptop and back | [Desktop → Laptop → Desktop](#desktop--laptop--desktop) |
| Directing a child project | [Directing a child project](#directing-a-child-project) |
| Directives and standing instructions | [How Axis Works](#how-axis-works); [FAQ](#faq) |
| Encrypted Secrets between computers | [Encrypted Secrets Between Computers](#encrypted-secrets-between-computers) |
| Entry files | [FAQ](#faq); [Porting between AI Platforms](#porting-between-ai-platforms) |
| Environment declarations | [Porting between AI Platforms](#porting-between-ai-platforms) |
| FAQ | [FAQ](#faq) |
| Fault Tolerance | [Settings](#settings) |
| Feedback to the Axis developers | [Sending feedback to the Axis developers](#sending-feedback-to-the-axis-developers) |
| File sharing and cloud-synced folders | [File Sharing](#file-sharing); [FAQ](#faq) |
| Flags | [Porting between AI Platforms](#porting-between-ai-platforms) |
| Folders and file layout | [Setup](#setup); [FAQ](#faq) |
| Follow-Ups | [Tips](#tips) |
| Full-folder and offline transfer | [Full-Folder and Offline Fallbacks](#full-folder-and-offline-fallbacks) |
| Git synchronization | [What the Commands Do](#what-the-commands-do); [First-Time Git Setup](#first-time-git-setup) |
| Guardrails and host hooks | [Subagents](#subagents); [Assistants, Group Agents and Observers](#assistants-group-agents-and-observers) |
| Guided project setup | [Guided project setup](#guided-project-setup) |
| Help and where to read more | [Commands](#commands) |
| Helper scripts | [FAQ](#faq) |
| Host and model compatibility | [FAQ](#faq) |
| Inbox | [Inbox](#inbox) |
| Installing Axis | [Setup](#setup) |
| Installing optional tools | [Integrations](#integrations); [Add-ons](#add-ons) |
| Jobs and their limits | [An Axis Team of Agents and its Jobs](#an-axis-team-of-agents-and-its-jobs) |
| Keeping links valid | [Keeping Links Valid](#keeping-links-valid) |
| License | [License](#license) |
| Local and frontier models | [Local vs. Frontier](#local-vs-frontier) |
| Logs | [How Axis Works](#how-axis-works) |
| Long conversations and compaction | [Long conversations and compaction](#long-conversations-and-compaction) |
| Main Agent and the one-Main rule | [Agents and Models](#agents-and-models); [Auxiliary Agents](#auxiliary-agents) |
| Maximum concurrent sessions | [Settings](#settings) |
| Memos | [Memos](#memos) |
| Messages, Assignments and Submissions | [Sessions, delivery and migration](#sessions-delivery-and-migration) |
| Messaging, starting and stopping a child project | [Supervising Child Projects](#supervising-child-projects) |
| Model access and paid API use | [Terminal sessions and model access](#terminal-sessions-and-model-access) |
| Model benchmarks and aptitude | [Local vs. Frontier](#local-vs-frontier) |
| Notes and Ideas | [Tips](#tips) |
| OpenClaw | [OpenClaw Integration](#openclaw-integration); [Running Axis on OpenClaw](#running-axis-on-openclaw); [How Axis and OpenClaw Fit Together](#how-axis-and-openclaw-fit-together) |
| OpenClaw security and group chats | [Security and Audit Boundaries](#security-and-audit-boundaries) |
| OpenClaw setup and hardening | [OpenClaw Setup](#openclaw-setup) |
| Permissions | [Settings](#settings) |
| Plan, Tasks and Initiatives | [How Axis Works](#how-axis-works); [Initiatives](#initiatives) |
| Portability | [Working Across Tools and Machines](#working-across-tools-and-machines); [Portability](#portability) |
| Principles, Rules, Practices and Resources | [How Axis Works](#how-axis-works) |
| Project file and project README | [How Axis Works](#how-axis-works); [FAQ](#faq) |
| Project identity and placement | [An Axis Team of Agents and its Jobs](#an-axis-team-of-agents-and-its-jobs) |
| Prompt envelope | [Porting between AI Platforms](#porting-between-ai-platforms) |
| Protected and hidden content | [Setup](#setup) |
| Quick start | [Getting Started](#getting-started) |
| Reminders | [Tips](#tips) |
| Remote access: disconnecting, interruptions and troubleshooting | [Disconnecting, saving and stopping](#disconnecting-saving-and-stopping); [What can interrupt the work](#what-can-interrupt-the-work); [Optional Mosh and terminal adjustments](#optional-mosh-and-terminal-adjustments); [Troubleshooting](#troubleshooting) |
| Remote access from a laptop or phone | [Remote access from a laptop or phone](#remote-access-from-a-laptop-or-phone); [Prepare once, at the desktop](#prepare-once-at-the-desktop); [Start the terminal, then reconnect from the laptop](#start-the-terminal-then-reconnect-from-the-laptop); [Connect from the phone](#connect-from-the-phone) |
| Returning to an old chat | [Returning to an old chat](#returning-to-an-old-chat) |
| Reviews and status | [Tips](#tips) |
| Save, resume and shutdown | [Tips](#tips); [What the Commands Do](#what-the-commands-do) |
| Scheduled supervision | [Supervising Child Projects](#supervising-child-projects) |
| Scheduling | [Scheduling](#scheduling) |
| Secrets and API keys | [FAQ](#faq) |
| Security model | [Security and Audit Boundaries](#security-and-audit-boundaries) |
| Settings and Profiles | [Settings](#settings) |
| Startup and the Ready banner | [How Axis Works](#how-axis-works); [Tips](#tips) |
| Stopping and retiring an Agent | [Terminal sessions and model access](#terminal-sessions-and-model-access) |
| Storage, locks and concurrent writes | [Capabilities](#capabilities) |
| Subagents | [Subagents](#subagents) |
| Subprojects | [FAQ](#faq) |
| Supervising child projects | [Supervising Child Projects](#supervising-child-projects) |
| Supervision records and targeted audits | [Supervising Child Projects](#supervising-child-projects) |
| Switching AI tools | [Porting between AI Platforms](#porting-between-ai-platforms) |
| Taking over an idle session | [Auxiliary Agents](#auxiliary-agents) |
| Terminal sessions and the launcher | [Terminal sessions and model access](#terminal-sessions-and-model-access); [The optional axis utility](#the-optional-axis-utility); [Sessions, delivery and migration](#sessions-delivery-and-migration) |
| Tips | [Tips](#tips) |
| Trademarks | [Trademarks](#trademarks) |
| Trash and undo | [What the Commands Do](#what-the-commands-do) |
| Updating an older project | [FAQ](#faq); [Wiki](#wiki); [Sessions, delivery and migration](#sessions-delivery-and-migration) |
| Updating Axis | [FAQ](#faq) |
| Updating child projects | [Supervising Child Projects](#supervising-child-projects) |
| Verifying a download | [Verify a Download (Advanced)](#verify-a-download-advanced) |
| What Axis is | [How Axis Works](#how-axis-works) |
| Wiki | [Wiki](#wiki) |
| Wiki images | [Wiki Images](#wiki-images) |
| Windows | [Setup](#setup); [FAQ](#faq) |
| Working without helper scripts | [An Axis Team of Agents and its Jobs](#an-axis-team-of-agents-and-its-jobs) |
| Write-once records | [What the Commands Do](#what-the-commands-do) |
<!-- END GENERATED: topic-index -->
