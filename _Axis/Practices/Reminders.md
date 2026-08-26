# Reminders
> **Purpose:** Maintain the portable, time-based queue for information Axis should surface at or after an exact instant.

A Reminder says **when to surface** information. A Task is work Agent owns; a Follow-Up is an action User owns; a Reminder is neither a scheduler nor authorization to perform another gated action. Version 1 checks at Axis activity checkpoints and makes no real-time notification claim.

## Record Contract

Open records live in `_Axis/Reminders/{created timestamp}.md`; terminal records live only in `_Axis/Archive/Reminders/{same timestamp}.md`. The creation timestamp is stable identity even when due time changes.

```
Reminder: Renew the domain registration

created: 2026.08.19.12.30.00.000Z
updated: 2026.08.19.12.30.00.000Z
due-at: 2026.09.01.07.00.00.000Z
timezone: Europe/Zurich
target: _Axis/Followups/2026.08.10.09.00.00.000Z.md
reopens: N/A
outcome: N/A

At or after the due time, remind User that the domain renewal is pending.
```

- Line 1 begins `Reminder: ` and is at most 80 characters; Line 2 is blank.
- `created:` equals the filename stem. `updated:` is an exact UTC timestamp, initially equals `created:`, and advances on every material edit.
- `due-at:` is an exact UTC Axis timestamp. `timezone:` is `UTC` or the IANA zone used for display and local-language interpretation.
- `target:` is one existing project-root-relative path or `N/A`. A path uses forward slashes, is never absolute or home-relative, contains no `..` component, and never points inside `_Axis/Secrets/` or `_X/`; the target string is portable project metadata and may be committed.
- `reopens:` is `N/A` or the exact ID of one archived Reminder.
- `outcome:` is `N/A` while open and exactly `acknowledged`, `completed`, or `cancelled` when terminal.
- The short body is standalone: it tells a human what will be surfaced and why. It contains no scheduler, channel, host, credential, external binding, or command authorization.
- Open records are mutable. Terminal records are archived and WORM.

An already-due instant is schema-valid, but creating one from a past time requires explicit User confirmation in the same instruction or a clarifying question.

## Time Semantics

`Project Time Zone` in [Settings] is an IANA zone or `Unknown`; never infer it from the current host. For local or relative language, resolve the zone offset at the due instant, clarify an ambiguous repeated wall time, reject or clarify a nonexistent skipped time, and restate local time, zone, and exact UTC before writing. If no deterministic timezone converter is available, require explicit UTC/offset confirmation.

Due state is the lexical comparison of valid UTC Axis timestamps after obtaining a trustworthy current UTC time. If current time cannot be established, say `Reminder due state unverified`; never claim none are due. Flag `updated < created`, a terminal time before creation, or an implausibly future `created:` value without silently rewriting it.

## Lifecycle

The archive destination is intentionally created on demand. Before the first terminal move, create `_Axis/Archive/Reminders/` if it is absent, then verify it is an ordinary directory inside `_Axis/Archive/`. A symlink, non-directory collision, or destination collision is an unsafe-path failure: preserve the live Reminder and stop rather than guessing.

- **Add:** deduplicate by target, meaning, and materially equal due time; mint the ID per [Practices > Timestamps]; write, read back, and Log.
- **Reschedule/snooze:** keep identity; change `due-at`, advance `updated`, verify, and Log.
- **Acknowledge:** set `outcome: acknowledged`, advance `updated`, archive unchanged after the final write, verify, and Log.
- **Complete:** apply the substantive result to its target first; set `completed`, advance, archive, verify, and Log.
- **Cancel:** add a short reason to the body; set `cancelled`, advance, archive, verify, and Log.
- **Reopen:** mint a new Reminder whose `reopens:` points to the old archived ID. Never edit archived history.

When an Axis operation deterministically completes or cancels an exact target, close every open Reminder pointing exactly to it in the same logical operation. `^refresh` may finish a crash-left closure. If a target moves to one uniquely identifiable archive path, retarget and surface it for review; if missing or ambiguous, keep the Reminder open and unhealthy rather than guessing.

A Follow-Up date never auto-creates a Reminder. Create a paired Reminder only when User asks for exact-time surfacing; then its `target:` points to the Follow-Up, its local date agrees with the Follow-Up's `due:` or that field is `N/A`, and the body does not duplicate the ask.

No recurrence syntax exists in version 1. A repeated need becomes a new Reminder after the current one is acknowledged or completed.

## Safe Writes

Under exact `Storage Policy=auto` with `host-storage=atomic`, write a complete non-record temporary sibling, read it back, then rename it to the timestamp filename. A Reminder temporary sibling always begins `.` and never ends in `.md` (for example, `.{created timestamp}.{Session ID}.partial`), so every record scan and the Dashboard ignore it even after a crash. Under `single-writer`, missing/malformed policy, `serialized`, or `unknown`, honor the sole-writer convention, use the safest available path, and require full readback. Record processing never treats temporary or malformed filenames as valid records; health views may still surface malformed residue for review. A failed mutation leaves the previous valid record authoritative.

## Surfacing and Session Checkpoint

- Session Start is silent when no Reminder is due. With due items, show a compact count and at most three Subjects; with untrusted time, show one compact unverified notice.
- Every Axis Command dispatch checks metadata for newly due Reminders before its own procedure and speaks only when an item crossed due or was created/rescheduled already due since the last trustworthy check.
- `^resume` shows due items and the nearest upcoming items; `^reminders` manages the queue; Dashboard deterministically shows current due ordering; `^status`, `^audit`, `^refresh`, and Snapshots carry their bounded views.

`_Axis/Flags/reminder-check` makes per-session deduplication durable: Line 1 is the current Session ID; Line 2 is the last trustworthy UTC check. Session Start writes it after its check. A later Command surfaces an open item when `due-at` is at or before now and either `due-at` or `updated` is after Line 2, then advances Line 2. This catches a newly crossed due time plus an already-due item created or rescheduled since the check. Creation/reschedule to an already-due time speaks in that mutation response before advancing the checkpoint. Missing, malformed, foreign-session, untrusted-time, or a Line 2 later than current trustworthy UTC causes a full check; after that full check, rewrite Line 2 with current UTC. Never preserve a future checkpoint or make a false advance.

Main Agent alone mutates Reminders. Subagents return candidates to Main; External Agents use Requests.
