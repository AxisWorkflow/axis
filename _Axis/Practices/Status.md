# Status
> **Purpose:** Define `^status`, the daily brief and "what needs me?": quick looks built from the project's records, and how they differ from a Review and the Dashboard.

`^status` answers "where are we?" in one screen; the daily brief says what changed and what only User can do; "what needs me?" lists only the second. Each is built fresh from the project's canonical records, writes no record, and is safe to repeat. Main, an Auxiliary Agent or an Assistant gives them; a Group Agent or Observer gives none, says the project's status is for User's own sessions, and reads nothing to say so. The procedures are `_Axis/Commands/status.md` and `_Axis/Commands/brief.md`.

## What it shows

- **Short (default):** a `STATUS` title with the time between dividers; one block of labelled rows (Project, Path, Model, Context - the Context Management method; Tasks active and blocked, Follow-Up, Reminders, Agents, Version), with no Git details; then the sections Summary (the Plan's current direction), Current (Active and Blocked Tasks), Waiting on you (Follow-Ups), Reminders, Recent activity (the newest few Logs and how long ago the last Snapshot and Review were made) and Next decisions (each open Initiative's next decision). It must fit on one ordinary terminal screen.
- **Full (`^status deep dive`, or any request for more):** the same, plus more Tasks and Logs, the open Initiatives with their phase, recently completed Tasks and record counts - and, for a deep dive, the Agent's own summary of the detail records User asked about.

## What needs me

User asks in any words ("what needs me?", "anything for me?") or with `^brief me`. From the live folders only, never `Archive/`, give one list in this order:

1. open Follow-Ups in `_Axis/Followups/` (`resolved: N/A`) whose `due:` date is before today, earliest first, then oldest `raised:`;
2. open Reminders in `_Axis/Reminders/` (`outcome: N/A`) whose `due-at` has passed, earliest first; one whose `target:` is a listed Follow-Up adds "reminder due" to that line instead;
3. the other open Follow-Ups in [Practices > Followups > Ordering and Surfacing] order;
4. Memos in `_Memos/` whose first 2,000 bytes hold `- **Status:** waiting on you`, newest first.

Open with the count and the time of reading; give each line the record's Subject and its state: overdue since, due, waiting how long, or reminder due at (in the Reminder's own `timezone:`). Read only Subjects, structured fields and Memo headers, never `_Inbox/`, Submissions, Messages, Notes, Ideas, `_Axis/Secrets/` or `_X` folders, and show them as plain text: link labels without targets, no code ticks, emphasis or control characters. List at most ten lines on a terminal and five on a chat, then the number left and `^followups`. Leave out a malformed record, a linked record file or a name with an impossible date, and name it under "Not checked". Say "Nothing needs you right now." only when every source was read with a trusted clock. Without one, give each Follow-Up its recorded date, no overdue, today or age, and show Reminders as `Reminder due state unverified`. When User answers an item, Main resolves it under [Practices > Followups]; another role passes the answer to Main as a request.

## Daily brief

1. **Needs you:** the list above; five lines on a terminal, three on a chat.
2. **Since {the previous brief}:** from `_Config/TASKS.md`, Tasks completed (`completed:`), Blocked and updated (`updated:`; the index has no blocked-since time) and created (`created:`) since then; new Memos not already listed, except brief Memos; then the newest Log Subjects in `_Axis/Logs/` except the machine Subjects `Session Starting`, `Session Started`, `Shutdown by User`, `Reference move`, `Reference warnings`, `Main retired by User (axis retire)`, `Auxiliary Team member allocation`, `Auxiliary Team native launch prepared`, `Main displacement prepared` and `Capability downgrade: ...`. Three lines, then the number left.
3. **Coming up:** open Reminders due within seven days that are not attached to a listed Follow-Up; two lines.
4. **Work:** Active and Blocked Task counts, and the Blocked Task with the oldest `updated:` and its age; `updated: Unknown` is counted, not aged.
5. **Not checked:** each unreadable source or malformed record, an untrusted clock, a malformed Setting; left out when empty.

When 1-3 are empty and everything was checked, the brief is one line: "Brief for {day}: nothing needs you, and nothing changed since {time}."

### When it is shown

With [Settings > Daily Brief] at `Yes` (missing or malformed means `Yes`), each session that gives the brief checks, at its first reply to a message User wrote that day, whether it is due: the project is set up (`_Axis/Flags/project-ready` holds a timestamp) and no brief was shown today. With `No` it is shown only on request; a request in any words, or `^brief`, always shows it. Days run in [Settings > Project Time Zone], or the computer's zone while that is `Unknown`. Never give a due brief on a turn a timer, a background task or another participant started, nor in an exact or machine-readable reply; the day then stays unmarked. Answer User's message first, then give the brief; for a greeting or a request for the brief, the brief is the answer. On the startup turn it replaces the open Follow-Up count and the spoken list of due Reminders; with no brief, state the count as usual.

### Shown once a day

Compose the brief first, then create `_Temp/status/brief/{yyyy-mm-dd}` for the local day without overwriting, holding `shown: {UTC timestamp}`, `session: {Session ID}` and `role: {Role}`: with the helper, or a shell no-clobber write (`set -C`), or else a check that the file is absent just before writing, accepting a rare second brief. If the file exists, another session showed today's brief: do not show it, unless it names this session and was written in this turn (then give it by hand). A brief on request creates a missing file. "Since" runs from the newest earlier file's `shown:` time, else the last 24 hours ("In the last day"). Without a trusted clock create none and give the brief only on request; when the file cannot be created, give the brief and say once that it may appear again today. The files are scratch on this computer, never written, read or deleted when `_Temp`, `_Temp/status` or the brief folder is a link; only Main deletes them, in `^refresh`, keeping the newest fourteen and never through a link; `^save` keeps them. Without Python, check for a due brief at startup and when asked.

### Daily memo

With [Settings > Daily Memo] at `Yes` (missing or malformed means `No`), Main also saves the day's brief as a Memo at its first turn that day once the project is set up, whatever [Settings > Daily Brief] says. A request for the daily memo, in any words or `^brief memo`, always writes it or updates today's. Write it under [Practices > Memos] with Subject `Daily brief {yyyy-mm-dd}`, Status `record` and the brief as its Summary (`--format memo` prints it); one with that Subject, live or archived, means today's is written. An Auxiliary Agent or Assistant sends the request to Main instead. Give one line with its link.

## Formats

- **Text** is the default, for the chat or terminal. It follows the brand's terminal rule (`_Axis/Branding/tokens/tokens.json` > `terminal`): plain text; headings bold, in brand blue only in a real terminal (standard output is a terminal, `TERM` is set and not `dumb`, `NO_COLOR` is unset), with the blue chosen for a light or dark background (`AXIS_THEME=light|dark|plain`, else `COLORFGBG`) and bold only when the background is unknown. Output shown in a chat reply carries no escape codes.
- **Web page** writes `_Temp/status/index.html`: a static, branded page using `_Axis/Branding/` (or a root `Branding/`): logo, fonts, colour tokens and stylesheet, following the operating system's light or dark theme. It lives in `_Temp/` because it is regenerable scratch, not a record; it does not refresh itself. The page ends with the brand's credit line. It never contains Secrets, local account names or anything outside the project's records.
- **Brief:** on a terminal titled `BRIEF` with the local day and time, within 80 columns and 24 lines; on a chat within 900 characters, narrowing Subjects first and never dropping "Not checked".

## Relationship to Reviews and the Dashboard

- A Review (`^review`) is the dated record, saved as a Memo in `_Memos/` ([Practices > Memos]): what changed since the last Review, health-checks, Deliverable coverage. Run it at milestones or on a schedule.
- Memos waiting on User are listed by `^status`, newest first, by name only.
- The Dashboard (`^dashboard`) is the live view and needs a local web server.
- `^status` is neither: it is the quick look between them. When User wants to keep or share what they see, suggest `^review`.

## Implementation

`_Axis/Resources/status.py` is an optional accelerator (Python 3 standard library only). For `^status` it reads `_Config/PROJECT.md`, `PLAN.md`, `TASKS.md` and `INITIATIVES.md`, `_Axis/CHANGELOG.md`, and the `_Axis/` folders `Followups/`, `Reminders/`, `Logs/`, `Snapshots/`, `Reviews/` (and pre-2.01 `Status/`), `Notes/`, `Ideas/`, `Submissions/` and `Agents/`, plus `git branch` and `git status` when Git is present; the brief and "what needs me?" read only the sources named above. Its only writes are the web page and the day files under `_Temp/status/`. Its `--view needs|brief|due|prune` exits 3 before opening any record when the session's own Marker, or an `AXIS_ROLE` that differs from it, is not a role that gives them; `prune` is Main's alone. Its text is English; in another Working Language compose from `--format json`. Without Python the Agent composes the same by hand.
