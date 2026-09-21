# Lock File
> **Purpose:** Coordinate short shared writes without reclaiming a live or replacement owner's lock.

## Prerequisites

Read `Storage Policy` and `host-storage` under [Practices > Flags > Reading Flags]. Only exact policy `auto` together with valid `atomic` permits this protocol. `single-writer`, missing/malformed policy, `serialized`, `unknown`, cloud-sync replicas, and independently writable clones GOTO Degraded Mode. A local probe is not distributed consensus.

## Degraded Mode

Main Agent is the sole writer to shared files; Subagents return text for Main to write. Serialize all writers and use `^save`, synchronize/reconcile, then `^resume` for handoff. Never simulate a lock with an ordinary check followed by an overwriting write. STOP the concurrent operation when the required exclusive primitive is unavailable.

## Lock Naming and Location

For `<dir>/<file>`, use the sibling directory `<dir>/<file>.lock/`, for example `_Axis/SNAPSHOTS.md.lock/`. Acquire with atomic `mkdir`. Each acquired directory contains an `OWNER` file with a fresh random nonce and the holder's Session ID. Keep the nonce in the acquiring context; a path or timestamp alone is not ownership. Plain locks have a **10 seconds** freshness window. `BATCH` additionally marks a long hold. The startup admission directory `_Axis/Flags/starting.lock/` is owned by [Claim-Session], not this ten-second protocol.

## Acquire

Step zero: READ and judge your own Marker per [Practices > Markers > The Lease]. A revoked or missing lease cannot take locks.

1. Prepare the complete write before acquiring. Attempt `mkdir <file>.lock`. On success, exclusively create `OWNER`, read it back, and retain its exact token. If ownership initialization fails, STOP without writing the target; leave the incomplete directory for quiescent recovery.
2. If acquisition fails because the path exists, read `OWNER` and `mtime`. Missing/malformed ownership or age older than 10 seconds means uncertain or stale contention: STOP the affected write and report it. Do not rename, delete, or acquire through it.
3. For a fresh lock, back off 200-300 ms and retry, at most 60 attempts (~15 seconds). A `BATCH` lock may use 240 attempts (~60 seconds), or fail fast with `batch operation in progress`.
4. Any other failure, including permission, I/O, unavailable share, or a non-directory collision, stops the affected write. Never treat it as an acquisition or an endlessly retryable collision.

## Hold

Verify the retained `OWNER` token and your lease immediately before writing. Prepare work outside the hold; do not reason, call another model, or wait for User under a lock. Keep an ordinary hold under 10 seconds. If it expires, STOP and do not continue the write or remove the directory. Expiry is a reason to investigate, never permission for another process to steal it.

## Release

1. Flush and verify the target write.
2. Re-read `OWNER` and require the retained exact token. On missing or different ownership, STOP; never remove another holder's directory by pathname.
3. Remove only your own `BATCH` if present, then `OWNER`, then the empty directory with `rmdir`. A failed removal is reported and left for recovery; never recursively remove a possibly replaced active path.

## Quiescent Recovery

Stale cleanup is permitted only during **quiescent recovery:** User or trusted host controls establish that all other writer processes have stopped, no delayed holder can resume, and new sessions, schedules, and spawns are suspended for the whole recovery. The recovering Main holds no ordinary locks. Marker age, a tombstone, and an `mtime` recheck alone do not establish these conditions.

1. Without this exclusive maintenance window, report stale contention and STOP cleanup. Preserve the lock and target.
2. During the window, re-read the exact selected directory and its ownership, then remove that abandoned lock only. Never modify the target as part of lock cleanup. Apply [Rules > HostAndMeta > Deletion Fallback] if needed while the window remains exclusive.
3. Verify removal before ending the window. Release the maintenance exclusion, then reacquire normally for any target write. STOP.

Renaming a stale path is not an ownership check: a fresh replacement may arrive between the age read and rename. No automatic rename-then-delete recovery runs beside possible writers.

## Stale-Lock Sweep

Session Start and `^refresh` inventory directories ending exactly in `.lock/`, excluding their own startup admission directory. Re-read ownership and `mtime`, report stale or malformed candidates, and leave them untouched. Never directly delete or rename a live lock name. A requested cleanup follows Quiescent Recovery only after the quiescent recovery conditions above hold. The same restriction applies to abandoned timestamp claims; age is diagnostic, never authority to reclaim them.

## Batch

Acquire normally, then exclusively create `BATCH`. Heartbeat every 5 seconds while work runs, checking the retained `OWNER` token before touching the directory. A failed heartbeat or lost ownership stops the write. A gap beyond 10 seconds requires recovery; it never permits a blind continuation. Acquire multiple locks in fixed lexicographic order, heartbeat each independently, and release in reverse order. If any acquisition fails, release only locks still owned and STOP the batch. Prepare all work before acquiring; use batches only for work that cannot fit a short hold.
