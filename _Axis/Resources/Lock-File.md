# Lock File
> **Purpose:** Manage race conditions when writing to files (i.e., when you need a distributed method to lock/unlock the writing of files). Lazy-load this file when concurrent file writes are possible. Refer to this file when you encounter a `*.lock/` directory to determine how to proceed.

## Prerequisites

This protocol assumes a filesystem with the same-directory create, replace, atomic `mkdir`, and `mtime` behavior Axis needs. Read `Storage Policy` and read `host-storage` under [Practices > Flags > Reading Flags]. Only exact policy `auto` together with valid `atomic` satisfies this protocol. `single-writer`, missing/malformed policy, `serialized`, `unknown`, cloud-sync replicas, and independently writable clones GOTO Degraded Mode below. This profile is evidence about the current location, not a universal filesystem claim; a one-process probe cannot prove distributed atomicity, and no Setting can force it.

## Degraded Mode

If the prerequisites are not met, skip the lock protocol entirely and avoid parallel writes:

1. Main Agent is the sole writer to every shared file.
2. Subagents return output to Main as text; Main does the writes.
3. Only one writer runs at a time.
4. Complete `^save`, synchronize or reconcile replicas, then use `^resume` before transferring writer responsibility.

## When this matters

A "Race Condition" arises whenever more than one Agent attempts to edit or write the same file at the same time. Avoid race conditions with **per-file directory locks**. The directory-creation primitive (`mkdir`) is atomic on POSIX filesystems and on NTFS, so it works as a portable mutex without special tooling.

## Lock Naming and Location

For every target file `<dir>/<file>`, the lock is a directory at `<dir>/<file>.lock/`. The lock sits as a sibling of the file it protects - that is easy to find, easy to sweep, and impossible to confuse with another file's lock.

For example: `_Axis/SNAPSHOTS.md` → has the lock `_Axis/SNAPSHOTS.md.lock/`

Lock timeouts are always **10 seconds**. Any operation that needs longer should release and re-acquire, or use the **Batch** sub-protocol below. Granularity is **one lock per file**. If an Agent must change two files atomically together, it acquires both locks in fixed lexicographic order to avoid deadlock, and releases them in reverse order. The lock directory is empty for plain locks (the **Batch** sub-protocol adds a single `BATCH` marker). The directory itself is the lock; its modification time (`mtime`) is the only state the protocol reads.

## Acquire

Step zero, always: the lease - verify your own Marker per [Practices > Markers > The Lease] before any acquire attempt (a tombstone means the kill protocol; bare-missing means stop and ask User). Only a live lease takes locks.

1. Attempt `mkdir <file>.lock`. If it succeeds, the Agent holds the lock; proceed.
2. If `mkdir` fails because the directory already exists, read its `mtime`.
	- If lock is **fresh** (`mtime` younger than the timeout), back off (sleep 200 ms plus 0-100 ms jitter) and GOTO step 1. Give up after 60 attempts (~15 seconds), report contention, and STOP.
	- If lock is **stale** (`mtime` older than **10 seconds**), GOTO Stale-Lock Cleanup step 1, then retry from step 1.

## Hold

1. Do **not** hold a lock while reasoning, calling another model, or waiting on User.
2. Prepare work in advance and keep file locks short - always less than 10 seconds.
3. Operations can never exceed the 10 second timeout; if they do, the operation is treated as crashed and the lock becomes stale. For legitimate longer-running work, GOTO the **Batch** sub-protocol below.

## Release

1. Flush the target file's writes.
2. Remove the lock directory: `rmdir <file>.lock`.
3. If the release fails because the directory is already gone (Stale-Lock Cleanup got there first), log it and continue - the change has already been written.
4. If the removal is blocked by a host permission error, follow [Rules > HostAndMeta > Deletion Fallback]: rename the lock into `_Trash/` and continue.

## Stale-Lock Cleanup

A naive `rmdir` followed by `mkdir` is **unsafe:** two cleaners can both reap the same stale lock and both think they hold a fresh one. Therefore, use a rename-then-delete pattern, since renaming a directory to a fresh name is atomic on POSIX (and on NTFS within the same volume):

1. Read the lock directory's `mtime`.
2. If `mtime` is older than the timeout, attempt to rename the lock to `<file>.lock.stale-<now>`. Only one Agent can win this rename.
3. If the rename succeeds, `rm -rf` the renamed directory and GOTO Acquire step 1. If the delete is blocked by the host, leave the renamed directory (it no longer blocks the lock) and continue.
4. If the rename fails (another Agent claimed it, or the holder released the lock in the meantime), back off and GOTO Acquire step 1. Retry budget of 60 attempts (~15 seconds) with 200-300 ms jittered backoff; after that, report contention and STOP.

## Stale-Lock Sweep

Session Start and `^refresh` clean abandoned locks without acquiring their target files. They use the same atomic claim as Stale-Lock Cleanup, never a direct delete:

1. Enumerate directories whose names end exactly in `.lock/`; renamed `.lock.stale-*` directories are cleanup residue, not active locks.
2. Immediately re-read each lock's `mtime`. If it is 10 seconds old or younger, leave it untouched.
3. If stale, attempt one atomic rename in the same parent directory to `<file>.lock.stale-<now>-<unique>`. Only one cleaner can win. The unique suffix must distinguish concurrent sweepers.
4. If the rename fails, another process changed, released, or claimed the lock. Re-read the original path: if it still exists and is still stale, retry once with a new unique claim name. If it is fresh, gone, or the second rename also fails, leave it alone and continue to the next candidate; never delete it by name.
5. If the rename succeeds, delete only the renamed directory. If deletion is blocked, follow [Rules > HostAndMeta > Deletion Fallback] or leave the renamed directory for a later cleanup - it no longer blocks the target file.

## Batch

Standard locks have a 10-second timeout. For operations that legitimately need to hold a lock longer - for example, a Wiki Subagent rebuilding many pages in one pass, or an update that must remain atomic across multiple files - use the **Batch** sub-protocol:

1. **Acquire** normally (per Acquire above). Then write a marker file `BATCH` inside the lock directory (e.g., `_Axis/SNAPSHOTS.md.lock/BATCH`). The marker tells other Agents that this is a long-running hold and they should wait patiently.

2. **Heartbeat every 5 seconds.** While holding the lock, refresh the lock directory's `mtime` by touching it. As long as heartbeats continue, the lock stays fresh and is NOT considered stale even after the 10-second timeout. If the holder stops heartbeating for 10+ seconds (crashed, hung), the lock goes stale and is subject to Stale-Lock Cleanup.

3. **Other Agents waiting on a `BATCH`-marked lock** should extend their retry budget to ~60 seconds (240 attempts × ~250 ms) before reporting contention. If a quick failure is preferable, an Agent can instead fail fast with the message "batch operation in progress."

4. **Multi-file batches.** Acquire all required locks in fixed lexicographic order. All must succeed; if any acquire fails, release the ones already obtained and back off before retrying the whole batch. Each lock heartbeats independently while held.

5. **Release** as normal: remove the `BATCH` marker, then `rmdir` the lock.

Batch locks are an exception, not a default. Most operations are sub-second and should use plain locks. Reach for batch locks only when the work cannot be decomposed into sub-10-second steps.
