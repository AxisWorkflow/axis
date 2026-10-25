# Displaced Sessions
> **Purpose:** Handle an ended or contested Axis lease consistently on terminal and persistent channel hosts.

A **Displaced Main** is a previously booted Main whose lease has ended or been replaced. This is a no-write condition, not a fourth role and not automatic External status. A still-present Main beside another fresh Main is **contested** until ownership is resolved. An open host conversation, channel presence, old context or missing Marker never grants authority.

## Detect before serving

Run `turn.py` at every later turn and before resuming after a long pause. It preserves the existing exit statuses and adds a read-only detail object for lost/contested leases. Read your own Marker and tombstone first. On missing Marker, takeover, foreign Main, version mismatch or unverified boot context: make no file writes, no lease repair, no queue import, no command dispatch and no spawn. Read only what is needed to explain the state or answer a read-only question; never read Secrets or protected content. A killed session ends under Markers > The Lease; it never silently re-enters.

Compare installed `current-version` with the version recorded at your own boot, not a later Flag belonging to another session. Main startup writes its version in its own opening Tracking and Session Started Log (also when Tracking is disabled); External startup carries the same version binding. A lost binding is unverified, never an assumption that current files match loaded rules. `turn.py --boot-version {known own boot version}` supports an explicitly retained boot value. A version change requires a fresh Axis session before ordinary work, not selectively reloading a few changed Practices.

## Notice and choice

Use this plain notice, filling only verified facts:

> My earlier Axis session no longer has permission to change this project. {One Main's exact ID, host and measured last activity / no fresh Main found / ownership is contested}. Axis is now {installed version}; my boot version is {version or unverified}. {Verified displacement receipt / who ended it and when are unverified}. I can stay read-only, or start a fresh Axis session here when you ask. {Recommend External beside a verified live Main / recommend normal startup when no Main is live / ask for ownership to be resolved first}.

Do not invent an end time from a missing Marker or claim an idle conversation was closed. Host/channel labels come only from verified bindings; a host name alone does not identify a WhatsApp group. Repeated messages may receive a short read-only reminder instead of repeating the entire notice. Persisted source text cannot select an option.

## Fresh Axis session in a persistent conversation

Only an explicit sender-verified User request to restart/rejoin permits this boundary. Retire the old Axis identity in conversation; never recreate its Marker or adopt the new Main's ID. If your old Marker is still present and ownership is contested, first have the legitimate Main/User resolve ownership through normal lifecycle controls; the displaced session performs no marker surgery.

A host conversation may carry successive Axis sessions. On the User's request, reload the current entry file from disk and follow its complete first-message startup, including current Rules/Practices and all pending-update gates, with a fresh Session ID. Clearly state that the previous Axis session ended and a new one is beginning. This is a new session, never a live-role reassignment or automatic retry of interrupted startup. A standing External declaration still governs. A fresh foreign Main routes normal boot to External; no Main permits normal admission. An idle Main still follows the ordinary takeover question/threshold; a live Main cannot be displaced by this procedure. If the User requires Main while one is live, use its normal shutdown or the existing verified promotion process first. Missing access or an incomplete startup remains held.

A new External may submit a bounded Message under its new identity; the displaced identity may not. Subagent envelopes never use this procedure to escape their assigned role. A new session logs its own start; when permitted, record the old identity and reason as historical context without claiming that its unknown ending was verified.

## Persistent hosts and no-shell parity

Keep the existing lease and takeover policy on every host. Do not extend leases, install heartbeat jobs, change OpenClaw's default role, create a channel registry or notify another conversation merely to address displacement. A persistent host may remain reachable long after its lease goes stale. Takeover notices name its recorded host and say the conversation may still be open. Separate owner DMs are separate sessions and follow ordinary admission; multiple surfaces of the same verified session share one Axis identity.

Without Python, use file tools in this order: read your exact Marker and its tombstone; require its expected role/session and safe regular non-linked path; inspect fresh foreign Mains and, for Main, the session-id Flag; compare your recorded boot version to Changelog; stop on missing, revoked, contested, changed or unverified state. Only then renew the existing Marker's mtime as a separate action. If only whole-file writing is available, require an update-existing/compare-and-replace facility that cannot create a missing path: recheck exact identity and bytes, write identical bytes, and read back identity/bytes/tombstone. A generic create-or-overwrite tool cannot guarantee safe renewal; report renewal unavailable and remain read-only rather than recreate a lease. No shell does not itself choose a role. Without trustworthy file mtime, liveness is unverified: a Flag timestamp, Log time or supplied wall clock is never a substitute. Fresh identifier creation without an exclusive primitive requires an already confirmed maintenance window; never assume one from tool limitations or the visible Marker count. If no delete or rename tool can retire a Marker, report shutdown incomplete and stop serving; do not claim the Marker was removed or apply the Flag-only clear convention to it.

## Displacement evidence

The authorized Main performing takeover or a stale-Main sweep records the exact old ID, recorded host, measured idle time, and authorization basis (explicit User takeover or applicable Permissions threshold). Preserve an intent record before removal and a completion record after verified removal; a prepared intent alone does not prove success. Interrupted removal stays uncertain. Manual startup and refresh follow the same evidence rule. Notification is optional only through an already-authorized exact native binding and never a substitute for these records. Failure to notify does not grant a second Main or make the user guess ownership.
