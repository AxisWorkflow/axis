# Continue Session
> **Purpose:** Serve an already booted identity without repeating startup; recover missing context by identity.

This Resource owns identity recovery only. Normal visible Main or External boot records use the entry fast path directly. A Subagent retains its envelope/assigned identity; it never adopts a Main Flag or overlay. Never recreate a bootstrap Marker or change a live role.

## Identity recovery

Use this ladder only when the conversation is not brand-new and no own boot record is recoverable. A visible own ID uses the entry fast path. Say "Resuming session." at most ONCE per conversation.

1. Before any ladder rung, inspect `_Axis/Updates/` through `_Axis/Resources/Check-Update-Handoff.md`, before ordinary context or overlay. A pending handoff permits only its still-owned update/recovery procedure or required fresh Main consumption; otherwise STOP.
2. READ `_Axis/Flags/session-id` directly, never infer absence from a glob. Line1 `cleared` counts as absent. Before adopting or matching an existing Flag, READ `_Axis/Flags/starting` directly; Line1 neither missing, blank nor `cleared` means Session Start is incomplete. Report it and STOP without adopting, renewing or writing.
3. Take the first applicable identity result, not an age guess:
   a. If a recovered visible Session ID equals Flag Line1, Session Start already ran, even if days passed. READ and judge its exact `Main: session` Marker and tombstone; a missing Marker stops as a lost lease. Then separately refresh that Marker and the Flag. Follow [Load-Project-Overlay] when its cache is set, say "Resuming session.", and RETURN permission to serve; STOP this Resource.
   b. If a recovered visible ID differs, another session started later. Do not rerun startup. READ and judge your own Marker/tombstone, then separately refresh only that Marker. Treat shared files as contended per [Lock-File], tell User in one line, and STOP ordinary work.
   c. If no own ID can be recovered but the Flag exists, first inspect `_Axis/Agents/` for a fresh Main whose `session:` equals Flag Line1, checking tombstones and measuring age. If it shows recent activity you did not produce, do NOT adopt it. If your own Marker can be identified, read/judge it then separately renew it; otherwise write nothing. Treat shared files as contended per [Lock-File], tell User, and STOP. Otherwise read and validate the exact same-ID Main Marker, check its tombstone, then adopt Flag Line1 and separately refresh Marker and Flag. Bare absence or tombstone stops under The Lease, never creates a Marker. Load [Load-Starting-Context] for missing core context and [Load-Project-Overlay] when its cache is set. Say "Resuming session." and RETURN permission to serve without rerunning startup; STOP this Resource.
   d. Only if `session-id` is missing or `cleared`, RETURN `no completed session` to the entry; its role/admission path still detects unfinished startup and foreign Main state. STOP this Resource.

Every resumed Main must complete the same foreign-Main, update, Requests and overlay checks in the entry fast path before ordinary serving. A resumed External keeps its booted action limits and never adopts a Main Flag. No continuation prints another success banner.
