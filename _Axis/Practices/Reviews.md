# Reviews
> **Purpose:** Define how to compose, save, and present Reviews (called Status Reports before Version 2.01).

Reviews follow the Index-Detail Pattern with a timestamped file in `_Axis/Reviews/`. Each report is a new, fresh, dated report; reviews are never overwritten.

The authoritative procedure for composing, formatting, saving, and presenting a Review is the `^review` command (`_Axis/Commands/review.md`). Follow it whenever a Review is needed - whether triggered by the `^review` command or by Agent's own judgment.

Axis has three ways to see where a project stands, and none substitutes for another:

- **`^status`** - a quick look ([Practices > Status]): a one-screen summary in the terminal, or a branded static web page, built fresh from the records each time. It writes no record, so it is cheap to run as often as User likes; `^status deep dive` (or any request for more) widens it.
- A Review (`^review`) - the dated record: a self-contained file that reads anywhere, needs no tooling, survives being emailed, and never changes after it is written. It carries what changed since the last Review, health-checks and Deliverable coverage. It summarizes; it does not challenge the work (that is a Cross-Examination) and it is lighter than an `^audit`.
- The Dashboard - the live view, which needs a running web server (see [Practices > Dashboard]). When User cannot run a server, the answer is `^status` (web page) or a Review, not a degraded Dashboard.

Every report carries a `## Recent Developments` section covering the span since the previous report. That is where User goes to answer "what changed while I was away", so Axis has no separate command for it - the question is answered in the two places User already looks. The report's version is the richer one: an Agent has a shell, so it can read the commit history as well as the records written and the Wiki activity. The Dashboard's version covers records only - it has no shell and cannot reach git - and windows on the last Snapshot rather than the last report.

A Review is an internal Axis record: it lives in `_Axis/Reviews/`, it is written for User and Agent, and it may carry paths, health-checks, and Axis terminology. A report User asks for on someone else's behalf - a client, a board, a funder - is not a Review. It is an ordinary work product: write it in plain language and file it in a Project Subfolder (see [Practices > Folders]). Do not derive one automatically, and do not put it in `_Axis/`.

- Use a direct, neutral tone; do NOT try to be eager, familiar, optimistic, confident, or sycophantic.
- To find the latest Review, list files in `_Axis/Reviews/` sorted desc by filename.
- Reviews are WORM after Agent has presented them to User - do not edit a prior report; if something changes, generate a new one.
