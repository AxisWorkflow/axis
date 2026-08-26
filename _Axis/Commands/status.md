# ^status
> **Purpose:** Generate a Status Report.

1. Mint a project-unique identifier timestamp for the report per [Practices > Timestamps].

2. Review recent Status Reports, if any, to see what has changed (`ls -t _Axis/Status/ | head -3`).

3. Build the Recent Developments list - what has actually changed since the previous Status Report. The window is that report's timestamp (from item 2); if there is no previous report, use the last 14 days:
	- a. Commits since then, if the project uses git and you have a shell: `git log --since={timestamp} --oneline --stat` (see [Practices > GIT]). Summarize what changed, not every file touched.
	- b. Records written since then: new Notes, Ideas, Follow-Ups, Reminders, Logs, Snapshots, Cross-Examinations, and Audit reports, whether still live or archived. Filenames are timestamps, so no body needs reading to place a record in time; deduplicate identical live/archive identities.
	- c. Wiki activity since then: the `## [date]` entries in `_Axis/Wiki/Library-Activity.md`, plus any new report sections in `_Axis/Wiki/Library-Status.md`.
	- d. Report developments, not inventory. Group what you find into events a reader would recognise ("Issue 01 accepted after Cross-Examination", "outreach moved from 24 to 31"), and say plainly when nothing of consequence happened.
	- e. Separately collect live or archived Log Subjects beginning `Capability downgrade:` from the same window, without duplicating identical live/archive identities. For the five most recent, extract `feature`, `missing-capability`, `behavior-used`, `work-skipped`, and `user-impact`; mark any missing field as an incomplete downgrade record. An absent local endpoint without requested Local Subagent work is neutral, not a downgrade.

4. Build the Deliverable coverage table (see [Practices > Tasks > Deliverable Coverage]):
	- a. Read the **Deliverables** and **Criteria** sections of `_Axis/PROJECT.md`. If either still holds `{{` placeholders, skip to item 5 and say in the report that the project is not set up yet.
	- b. For each Deliverable, list the tasks in `_Axis/TASKS.md` whose `delivers:` field names it, with their Status.
	- c. For each of those tasks, follow its `[Details...]` link, which may resolve to live or archived Task storage, and read `## Produced` to get the paths of the work products it produced.
	- d. Mark each Deliverable **Delivered** (every task naming it is Completed and at least one path is recorded), **In progress** (some task naming it is Active or Blocked), or **Unclaimed** (no task names it).
	- e. For each Delivered item, say whether the Criteria have actually been evaluated against it. An unevaluated Deliverable is not done - do not report it as done.

5. Compose a new Status Report:
	- Begin the body with a brief synopsis: 2-3 plain sentences (roughly 50 words) that stand alone as the report's opening paragraph. The Dashboard's Status card displays exactly this paragraph, so keep it self-contained and card-sized.
	- Tailor it to the needs of the project (shape and format at your discretion).
	- Quick, scannable, one page when printed; lead with what User needs to know first.
	- Prefer prose or tight bullets; do not pad.
	- Cite specific Tasks, Snapshots, or Logs by path.
	- Put a `## Recent Developments` section built from item 3 directly after the synopsis - it is the first thing a returning reader looks for.
	- Put a `## Follow-Ups` section immediately after Recent Developments. Read [Practices > Followups], list every open item in queue order with its due state and owning path, and report queue health: malformed state, duplicate asks, or missing `blocks:` targets. Say `None open.` when healthy and empty.
	- Put a `## Reminders` section immediately after Follow-Ups. Read [Practices > Reminders], obtain trustworthy UTC, and report overdue/due counts, the nearest upcoming items, and malformed/time/target health without duplicating their bodies. Say `None open.` when healthy and empty; say due state is unverified when time is not trustworthy.
	- Put a `## Portability` section after Reminders. Read [Practices > Portability], `_Axis/ENVIRONMENT.md`, and the latest Continuity block; report `Ready`, `Degraded`, or `Unverified`, Storage Policy/profile, infrastructure health, bounded undeclared-signal categories, and only material findings. Under a compact `Infrastructure to re-establish` subheading, list each declared required absent item and each source-present item now absent/unverified with its logical name, status, fallback, and safe setup reference; say `None identified.` when healthy. Never expose secret names/values, accounts, paths, or scheduler job IDs.
	- Put a `## Capability Downgrades` section immediately after Portability. Summarize the recent Events collected in item 3e, including their User impact and Log paths; say `None recorded in this reporting window.` when there are none.
	- Include the Deliverable coverage table, and call out anything Unclaimed.
	- Consider covering: brief project description; current objectives; work in progress; challenges, risks, open questions; on-track assessment; recommendations; health-checks.

6. Run the health-checks that apply:
	- a. **Tasks current?** Every Active task has a valid exact `updated:` within the last 7 days; every Blocked task has a valid reason. `Unknown` is review-needed, never treated as fresh or stale.
	- b. **Stale locks?** No stale `*.lock/` directories.
	- c. **Wiki healthy?** `_Axis/Wiki/Library-Index.md` current; no orphaned pages; all contradictions flagged (not dropped or auto-resolved).
	- d. **Setup complete?** `_Axis/PROJECT.md` contains no `{{` placeholders.
	- e. **Deliverables claimed?** Every Deliverable in `_Axis/PROJECT.md` is named by at least one task's `delivers:` field; every Completed task with a `delivers:` value has a `## Produced` section in its detail file.
	- f. **Follow-Ups healthy?** Every live Follow-Up is open and well-shaped, every `blocks:` target exists, every terminal Follow-Up is archived, and every User-blocked Task that needs a specific User action has exactly one matching open Follow-Up.
	- g. **Reminders healthy?** Every live Reminder is open and well-shaped, due/update times are coherent, every target/reopen reference resolves, and every terminal Reminder is archived.
	- h. **Portability current?** The latest Snapshot contains one valid Continuity block, every infrastructure declaration has a current exact status, bounded discovery ran, and no unresolved storage-policy/replica, path, case/NFC, conflict-copy, link, or text-normalization finding is hidden.

7. Save the report to `_Axis/Status/{timestamp}.md` per the **Index-Detail Pattern:** Line 1 `Status: {short topic}` (≤ 80 chars); Line 2 blank; Lines 3+ body.

8. When `project-ready` is valid, follow `_Axis/Resources/Refresh-Project-README.md` so its bounded summary can cite the new report. Preserve User-authored README content; a refresh failure does not alter the WORM Status Report.

9. Log an Event that includes the path to the new report and the Project README refresh result.

10. Present to User: a clickable link to the report plus a short summary. STOP.
