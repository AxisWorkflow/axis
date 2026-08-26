# ^resume
> **Purpose:** Pick up where project left off - load latest Snapshot, Tasks, recent Logs.

1. **Receive Git state first.** Read `host-shell` under [Practices > Flags > Reading Flags]. When valid `yes` and an exact-root repository with configured upstream exists, read [Practices > GIT] and run incoming mode before reading project continuity: fetch, classify, and accept only a strict clean or receive-safe fast-forward. Receive-safe state is limited to verified ignored current-session artifacts and byte-preserved, noncolliding `Session Starting`, `Session Started`, or `Shutdown by User` WORM Logs exactly as [Practices > GIT] defines; any other substantive local change blocks receipt. Stop on divergence. If incoming Workflow machinery changed, run the required shutdown and ask User to start a fresh session. If Git, network, or authentication is unavailable, continue from the local checkpoint but carry `remote freshness: Unverified` into the summary. No repository or no remote continues locally without error.

2. **Receive configured Secrets.** After any fast-forward, and whenever encrypted Secrets transport is configured, follow [Practices > GIT > Encrypted Secrets Transport > Receive automatically]. A verified `current`, `received`, or `local-changes` state continues. Missing tool/identity, malformed/unsafe input, or conflict leaves plaintext untouched and becomes a named infrastructure/portability finding; never expose an entry name. GitHub authentication is restored separately because it is needed before the capsule can be fetched.

3. **Sweep Trash.** Quietly sweep `_Trash/` per [Practices > Trash]: delete everything except `.gitkeep`, recreate it if absent, and note the count removed below. If the host blocks deletion, remind User to empty `_Trash/` instead.

4. **Revalidate portability.** Read [Practices > Portability] and the latest Snapshot's `## Continuity` block, then run Always-On Resume Revalidation completely whether or not a move is suspected. Reuse only Capability Flags freshly validated by this Session Start. Revalidate every infrastructure declaration and run bounded discovery; compare source/current status, then list each source-present item now absent/unverified and each currently required absent item with fallback and `Re-establish` reference. Preserve your lease and never clear a possibly live foreign Marker. Classify `Ready`, `Degraded`, or `Unverified`; remain read-mostly and write no routine receipt Log.

5. Read the last entry of `_Axis/SNAPSHOTS.md` and its detail file in `_Axis/Snapshots/` if any.

6. Read `_Axis/TASKS.md` and identify Active and Blocked Tasks, including any `updated: Unknown` recency that needs review.

7. Read the Subjects of the five most recent Logs in `_Axis/Logs/`; lazy-load any body that looks decision-relevant.

8. Read [Practices > Followups] and the open queue. Include the first ten self-contained asks in its defined ordering. If more than ten are open, give the total and say `^followups` lists the complete queue.

9. Read [Practices > Reminders] and the open queue. Show due items first and the nearest upcoming items, up to ten total; report unverified time or malformed state honestly. If more remain, give the count and say `^reminders` lists the complete queue.

10. Summarize in one glance: Git/remote freshness when applicable; portability and encrypted Secrets state; infrastructure to re-establish (logical names/status only); where the project left off; what is active/blocked; Follow-Ups; due/upcoming Reminders; Trash count; and anything else unresolved. Stay quiet about unchanged healthy infrastructure beyond one `Ready` label. Never expose secret values/names, accounts, local paths, or host job IDs.

11. Propose the next 1-3 actions and wait for User direction. STOP.
