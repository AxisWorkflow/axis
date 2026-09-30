# Status
> **Purpose:** Define `^status`, the quick look at where a project stands, and how it differs from a Review and the Dashboard.

`^status` answers "where are we?" in one screen. It is built fresh from the project's canonical records every time, writes no record, and is safe to run as often as User likes, by Main or External. The procedure is `_Axis/Commands/status.md`.

## What it shows

- **Short (default):** a spaced `S T A T U S` title with the time between dividers; one block of labelled rows (Project, Path, Model; Tasks active and blocked, Follow-Up, Reminders, Agents, Version), with no Git details; then the sections Summary (the Plan's current direction), Current (Active and Blocked Tasks), Waiting on you (Follow-Ups), Reminders, Recent activity (the newest few Logs and how long ago the last Snapshot and Review were made) and Next decisions (each open Initiative's next decision). It must fit on one ordinary terminal screen.
- **Full (`^status deep dive`, or any request for more):** the same, plus more Tasks and Logs, the open Initiatives with their phase, recently completed Tasks and record counts - and, for a deep dive, the Agent's own summary of the detail records User asked about.

## Formats

- **Text** is the default, for the chat or terminal. It follows the brand's terminal rule (`_Axis/Branding/tokens/tokens.json` > `terminal`): plain text; headings bold, in brand blue only in a real terminal (standard output is a terminal, `TERM` is set and not `dumb`, `NO_COLOR` is unset), with the blue chosen for a light or dark background (`AXIS_THEME=light|dark|plain`, else `COLORFGBG`) and bold only when the background is unknown. Output shown in a chat reply carries no escape codes.
- **Web page** writes `_Temp/status/index.html`: a static, branded page using `_Axis/Branding/` (or a root `Branding/`): logo, fonts, colour tokens and stylesheet, following the operating system's light or dark theme. It lives in `_Temp/` because it is regenerable scratch, not a record; it does not refresh itself. The page ends with the brand's credit line. It never contains Secrets, local account names or anything outside the project's records.

## Relationship to Reviews and the Dashboard

- A Review (`^review`, [Practices > Reviews]) is the dated record kept in `_Axis/Reviews/`: what changed since the last Review, health-checks, Deliverable coverage. Run it at milestones or on a schedule.
- The Dashboard (`^dashboard`) is the live view and needs a local web server.
- `^status` is neither: it is the quick look between them. When User wants to keep or share what they see, suggest `^review`.

## Implementation

`_Axis/Resources/status.py` is an optional, read-only accelerator (Python 3 standard library only). It reads `_Axis/PROJECT.md`, `CHANGELOG.md`, `PLAN.md`, `TASKS.md`, `INITIATIVES.md`, and the `Followups/`, `Reminders/`, `Logs/`, `Snapshots/`, `Reviews/` (and pre-2.01 `Status/`), `Notes/`, `Ideas/`, `Requests/` and `Agents/` folders, plus `git branch` and `git status` when Git is present. Its only write is the web page under `_Temp/status/`. Without Python the Agent composes the same summary by hand; nothing else changes.
