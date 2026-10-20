# Coordination
> **Purpose:** Operate an Axis Team of Agents and bounded Jobs under one accepting Main.

## Records and ownership

Initialize a portable `project-id:` UUID in Project metadata once. Relocation and synchronized copies retain it; an intentional fork receives a new UUID with provenance. UUIDs and hashes identify records, not people or permission. Activate one writer/dispatcher placement explicitly; Git and cloud sync are not locks. First initialization activates only a newly minted Project UUID. An existing identity, new Main, move, copy, storage change or expiry requires explicit reactivation after verifying that the previous placement is inactive.

`Teams/{ID}.md` is an immutable founding charter; `Jobs/{ID}.md` is an immutable mandate; Messages hold accepted revisions and outcomes. `Schedules/{ID}.md` is a current definition whose immutable revisions live in Messages. All IDs use [Practices > Timestamps], including Archive checks. Optional `Teams/{ID}/` folders hold outputs. A `Messages/{ID}/` support folder belongs to its same-ID Message and requires that owning detail; session dispatch retains stdout/stderr plus readable recovery receipts there. Visible `_axis-transfer-*.md` recovery claims bind Inbox transfer publication and retirement and remain with their recorded transfer evidence. Uppercase indexes are replaceable views, never authority.

Python helper `coordination.py` provides validation, persistence, projection and bounded dispatch bookkeeping. Without it, Main follows [Resources > Coordination-Manual] using the same Markdown contract. Canonical details begin with a Subject of at most 80 characters and a blank line, then a readable Markdown view, a trailing JSON payload and checksum as defined below. The payload carries `schema: axis.coordination/v1`, family, id, project, subject, created and issuer plus the family's fields. Validate exact schema and record identity; unknown schema or branching accepted successors holds the subject for reconciliation. Read only addressed/charter-authorized content.

## Readable record format

`coordination-record.py` defines the shared Subject-first format. A detail has `## Content` for the communication or objective, `## Details` for the complete labelled record, then `## Machine payload` with one sorted, two-space-indented JSON object in a JSON fence. A final `checksum-sha256:` line carries the lowercase SHA-256 of all preceding text, including Subject, readable view, payload and the blank line before the checksum. The footer itself is excluded. Encoding is UTF-8; LF is canonical, CRLF is normalized for this document check only, and bare CR is refused. Separate original-byte evidence digests are never normalized.

The JSON object is the machine-parsed representation. Before consumption, regenerate the readable representation from that object and require exact agreement with the complete normalized document, including its checksum. Nested fields are sorted and displayed as labelled lists; communication text is quoted and Markdown syntax escaped so content cannot impersonate structure. Unknown shape, duplicate keys, missing/mismatched checksums or disagreement holds the affected record. Never automatically re-stamp unexplained edits. Immutable records are revised with a new linked record; legitimate Schedule changes use their accepted revision path. No checksum authenticates a sender or grants authority.

Coordination details and new Submissions are bounded to 128 KiB of complete readable/payload text, with Message content still bounded to 16 KiB. Large output belongs in linked, size/digest-checked support. A timestamp-named support folder belongs to its detail's identity; it is not a second independently identified record. Ordinary user-editable Notes and other unrelated Markdown do not acquire a blanket checksum requirement.

## Local activation

Use `coordination.py --root PROJECT_PATH --session SID placement-status` to inspect. `activate --single-writer --previous-placement-inactive [--expires UTC_TIMESTAMP]` records an explicit serialized handoff; `deactivate` stops local canonical effects. Never assert these declarations without evidence that the other placement has stopped. A normal takeover can establish the old Main is fenced on the same physical root; a copied root cannot establish remote shutdown.

The local `Flags/coordination-placement.json` binds Project UUID, physical root, host hint, current Main/Marker, storage profile, activation generation and expiry of at most 24 hours. It is ignored by Git. Canonical acceptance, transport effects and automatic starts recheck it; a missing, stale or copied binding holds those effects while read-only inspection and ordinary work remain available. Reactivation never resets retained budgets or unknown effects. It is a local fence, not a distributed lock or remote authentication.

## Team and Job admission

A charter names owning Task, objective, outputs, validator, separate leader/member slots, scope, authority, formation, limits, stop rules and resumption. Formations: survey, panel, pair, jury and split. The Team Leader is a separate standard-capability General Subagent, never the project Main. It coordinates and proposes; Main accepts shared changes and final completion. Consensus does not replace validation; retain dissent and unresolved questions.

A Job pins its objective, exact definition revision, authority, acceptance owner, targets/action classes/exclusions, validator and usage/time limits. Defaults: 60 minutes, 3 rounds, 12 total starts, at most leader plus 2 workers, authority expiry 24 hours. Count leaders, validators, retries and restarts; apply the minimum User/host/project/Team/Schedule/Job bound. High-impact actions require explicitly reviewed limits. Unknown allowance never means unlimited usage; no automatic API fallback.

## Dispatch and recovery

1. Validate Main's existing lease, qualified storage, placement, authority, expiry and User control. On non-atomic storage serialize under one Main; workers return proposals for capture.
2. Reserve shared capacity before fan-out. Persist assignment and attempt intent before invoking an allowlisted typed adapter. Each worker gets [Start-Subagent]'s nonce-bound envelope plus Team/Job/slot/epoch, scope and return contract. No shell text from a record executes.
3. Retain receipts and results, then validate before accepting. Apply only Main-accepted controls with the expected predecessor/epoch. A worker-authored control, divergent successor or missing acceptance holds the subject. Track failed attempts and uncertain effects; do not replay unknown external actions.
4. Pause stops future dispatch at a boundary; report active workers and unconfirmed cancellation. Stop requests safe checkpoints. Late results cannot reopen terminal Jobs. A changed mandate gets an explicit revision and disposition of in-flight work.
5. Replace a leader only through an accepted membership/binding event and a new epoch/session. Recover from charter, assignments, retained results and checkpoint, not private conversation. No automatic replacement unless explicitly authorized. Stop on exhausted finite limits and preserve partial work.

Team states: draft, ready, running, paused, completed, failed, cancelled. Job states: proposed, admitted, running, blocked, pause-requested, paused, succeeded, failed, cancelled, expired. Only validated outputs and Main acceptance justify success.

## Session and transfer boundaries

Distinguish desired residency (on-demand/warm/managed), observed runtime and Axis lease authority. On-demand is default. Warm context does not renew a lease; managed restart and reboot restoration need explicit opt-in. Bind Project UUID/root, Axis Session ID, exact host handle/generation, adapter/version and verified operations. Never use PID, pane title or most-recent conversation alone.

Use `session-adapters.py` or the optional `axis` launcher only for verified typed capabilities. Unsupported or uncertain operations return their limitation; retain the manual separate-session path. No process may synthesize a Main heartbeat. If no separate session exists, report the dedicated-team capability unavailable.

Inbox transfers persist prepared, copied-and-verified, destination-accepted and source-retired receipts. Keep the source until exact receiver acceptance; only its owning Main retires unchanged bytes. Hold symlinks, collisions, partial arrivals and changed bytes. Routing authority comes from User's rule, never the document. See [Practices > Messages] and [Practices > Scheduling].

An unavailable configured Archive makes historical deduplication and budget accounting unverified. Hold new Job admission, dispatch and automatic session/transfer starts until required history is available; never interpret a missing archive as an empty history. Local pause/stop and ordinary unrelated project work remain available.

Compact indexes show at most 100 rows within a 60,000-byte table budget, with exact total and pending counts and an explicit truncation notice. Messages shows pending items first, then newest recorded history. Complete immutable details remain in the family folder and configured Archive; a bounded view never discards records or changes pending state.
