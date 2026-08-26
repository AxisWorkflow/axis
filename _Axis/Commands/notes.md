# ^notes
> **Purpose:** Review active Notes - surface salient guidance, renew aging facts, and archive obsolete history.

1. Read [Practices > Notes] and [Practices > Archiving]. Read the current Project, Plan, Tasks summary, and latest Snapshot needed to judge relevance.

2. Inventory `_Axis/Notes/` by filename timestamp, Line-1 Subject, size, and word count before loading bodies. Inventory archived Note filenames and Subjects without pre-loading their bodies. If there are no active Notes: report the archived count and STOP.

3. Read every active Note and classify it for this review:
	- a. `Salient` - current guidance that materially affects active work, an upcoming deadline, a live decision, or a recurring User preference.
	- b. `Current` - still accurate and useful, but not presently consequential.
	- c. `Review` - plausibly aging, ambiguous, disconnected from current work, or older than 30 days. Age is a review signal only, never proof that a Note expired.
	- d. `Superseded` - contradicted by a newer Note or replaced by current Project, Plan, Task, Setting, or Directive state.
	- e. `Obsolete` - tied to an event, deadline, assumption, or condition that demonstrably ended.

4. Resolve conflicts by subject and meaning. A newer Note takes precedence, but do not silently discard an older contradiction. Flag uncertain facts for User rather than guessing.

5. Present one concise table ordered by action need, then salience, then newest first. Show timestamp, Subject, classification, reason, and proposed action. Do not add a priority field to Note files; the review classification is derived, and a renewed timestamp is the durable signal that an old Note was revalidated.

6. Ask User which proposals to apply:
	- a. Keep - make no change.
	- b. Renew - after User confirms the content is still accurate and salient, rename the Note to a current timestamp under [Practices > Notes].
	- c. Update - create a new Note with the corrected content through `^note`; treat the old Note as superseded.
	- d. Archive - resolve the exact selected Note paths, show their destinations, and follow `^archive` from its proposal step. Require its literal `ARCHIVE` confirmation before moving anything.

7. Apply only approved renewals and updates. For every rename, prevent collisions, preserve the body, and verify the old path is absent and the new path exists. Archive only after the separate `ARCHIVE` confirmation.

8. If the resulting active count exceeds [Settings > Max Notes], follow [Practices > Archiving > Automatic Note Overflow]. Then summarize the salient Notes that should guide current work and any uncertain Note User left unresolved.

9. Log one Event for the review with counts by classification, approved actions, declined Archive proposals, and verification results. Do not copy full Note bodies into the Log. STOP.
