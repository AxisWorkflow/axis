# Markers
> **Purpose:** Define ephemeral activity Markers and each Agent's lease.

Markers live in `_Axis/Agents/`, named `{yyyy.mm.dd.hh.mm.ss.xxxZ}.md` under [Practices > IndexDetail]. Subjects are `Main: session`, `External: {host}` or `Subagent: {role}`. Create a Marker when activity starts; delete a Subagent's when it returns. Never use Markers for durable state: use Flags. They are ephemeral, not WORM, and gitignored. Never archive a Marker; blocked deletion follows [Rules > HostAndMeta > Deletion Fallback] by clearing or moving to `_Trash/`.

## Main Marker Shape

The canonical Main bootstrap shape is exactly four lines, with one final newline:

```text
Main: session

session: {Session ID}
host: {nonempty host}
```

Claim-Session exclusively creates and reads back this shape before Start-Session. It is never a lease-repair recipe.

## Liveness

A Marker is fresh only while `mtime` is under1 hour old. A sibling `{ID}.kill` is DEAD at any age. Every liveness scan checks that sibling, in startup, continuation, `^kill`, `^refresh` and Dashboard. At or over1 hour is dead; cleanup may delete stale Markers with a warning, without hard-blocking. Session Start only reports them. An orphan is a fresh `Subagent:` Marker with no fresh Main behind it: report the crashed-spawn evidence; `^refresh` clears it once stale.

An ordinary host close leaves a Marker to age out. Successful `^shutdown` or verified User-invoked `^update` with its required restart deletes the actor's own Marker. Main renews on each served turn, `^save`, resume and every Log write. A fresh foreign Main requires [Lock-File] coordination; ordinary startup refuses contested admission. Tracking is advisory activity, never authority.

## The Lease

READ your own Marker and check its tombstone at every turn start and immediately before every shared write or lock/identifier claim. Judge the read, THEN renew its `mtime` as a SEPARATE action. Never chain renewal to the read or use a bare `touch`: renewal never creates a Marker. The entry executes this for both Main's banner and External's minted boot record. Lock-File and Timestamps own their pre-write checks, including append-only records that take no file lock.

- A tombstone means KILLED: Log one final Event, append final Tracking, tell User on your surface and stop permanently. Later messages receive one line, no further writes.
- A Marker missing WITHOUT a tombstone means lost lease: stop writing and ask User this turn; never recreate it to continue. Re-register once only on User's word; a second disappearance in that session stops it for good.
- Only sender-verified User `^kill` writes tombstones. Graceful self-exit uses `^shutdown`. `^refresh` silently removes tombstones older than1 hour.

Only the qualified startup-state.py record operations may combine programmatic read/judgment with renewal of the validated existing file descriptor. Check exact content, inode and tombstone before and after; this cannot create a missing pathname. Turn-start Agent renewal stays SEPARATE.
