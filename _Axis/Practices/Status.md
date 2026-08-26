# Status Reports
> **Purpose:** Define how to compose, save, and present Status Reports.

Status Reports follow the Index-Detail Pattern with a timestamped file in `_Axis/Status/`. Each report is a new, fresh, dated report; status reports are never overwritten.

The authoritative procedure for composing, formatting, saving, and presenting a Status Report is the `^status` command (`_Axis/Commands/status.md`). Follow it whenever a Status Report is needed - whether triggered by the `^status` command or by Agent's own judgment.

A Status Report is the static view of a project: a dated, self-contained file that reads anywhere, needs no tooling, survives being emailed, and never changes after it is written. The Dashboard is the live view and requires a running web server (see [Practices > Dashboard]). The two are a pair, and neither substitutes for the other - when User cannot run a server, the answer is a Status Report, not a degraded Dashboard.

Every report carries a `## Recent Developments` section covering the span since the previous report. That is where User goes to answer "what changed while I was away", so Axis has no separate command for it - the question is answered in the two places User already looks. The report's version is the richer one: an Agent has a shell, so it can read the commit history as well as the records written and the Wiki activity. The Dashboard's version covers records only - it has no shell and cannot reach git - and windows on the last Snapshot rather than the last report.

A Status Report is an internal Axis record: it lives in `_Axis/Status/`, it is written for User and Agent, and it may carry paths, health-checks, and Axis terminology. A report User asks for on someone else's behalf - a client, a board, a funder - is not a Status Report. It is an ordinary work product: write it in plain language and file it in a Project Subfolder (see [Practices > Folders]). Do not derive one automatically, and do not put it in `_Axis/`.

- Use a direct, neutral tone; do NOT try to be eager, familiar, optimistic, confident, or sycophantic.
- To find the latest Status Report, list files in `_Axis/Status/` sorted desc by filename.
- Status Reports are WORM after Agent has presented them to User - do not edit a prior report; if something changes, generate a new one.
