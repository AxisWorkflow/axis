# Claim Session
> **Purpose:** Commit provisional Main admission exclusively before creating Main startup artifacts.

Run after the loading notice and initial timestamp recipe, before [Start-Session]. This is first-boot admission, not lease renewal. Never use it to resurrect a missing live Marker.

Before admission, follow `_Axis/Resources/Check-Update-Handoff.md` in `inspect` phase. An incomplete or inconsistent update stops before ordinary startup; only absent/closed evidence or verified ready success may reach the normal claim. Never reclaim an update barrier to enter this boot.

Before the first claim, read [Practices > Markers > Main Marker Shape], [Practices > Timestamps], and [Practices > IndexDetail]. These are complete pre-admission inputs; do not read Main-only Start-Session yet.

## Optional local acceleration

After the preceding `inspect` result permits admission and the canonical contracts are loaded, a verified installed `_Axis/Resources/startup-state.py` may perform ordinary local admission. It requires Python3, POSIX exclusive operations, `fcntl` and existing-descriptor timestamp renewal on the authoritative local filesystem. Do not select it for a promotion contest, a confirmed serialized maintenance window, an unverified mixed update or storage without those primitives. It never grants eligibility or update approval. Missing helper/Python or an `unavailable` result before writes takes Manual admission below; missing acceleration never disables ordinary Axis.

Run `python3 _Axis/Resources/startup-state.py --root . claim --initial {entry-timestamp} --host {host-class}`. Use the exact already-minted entry timestamp and a nonempty one-line host class. No model, endpoint, configuration or additional role parameter is accepted.

- `admitted`: retain returned final Session ID, owner nonce and exact Marker path; these were exclusively written and read back. Continue Start-Session with this helper admission. The bounded batch below applies only after admission succeeds.
- `external`: no Main artifact was written. Follow Start-External with its fresh identity and required measured cause/remedy greeting.
- `error`: stop this boot with retained evidence; never switch to a path that reacquires or recreates its state. The helper is an optional accelerator, not an authority or recovery tool.

Its OWNER contains canonical JSON with schema1, kind `axis-startup-admission`, token, session, host, phase, starting_log and started_log. The last two begin null. Phases are claiming, admitted, initialized and committing; the token stays fixed. Operations serialize on the existing ordinary OWNER inode and reject a changed token/state or unsafe path. A partial OWNER update stops for reviewed recovery. This is local cooperating-writer protection, not distributed consensus or authentication against a hostile file owner.

## Manual admission

The complete original file-tool procedure below remains available without Python or the helper. A valid helper-created owner can be checked by its retained token field and exact session/state rather than comparing the JSON body to a bare nonce. Never recreate a missing owner. For a helper that becomes unavailable after admission but before initialize, retain that admission and follow the manual steps; after initialized, retain its exact Starting Log instead of writing another. A committing or malformed partial state stops for reviewed recovery. Do not auto-restart a failed operation.

1. Establish an exclusive admission primitive for this authoritative folder. On a filesystem supporting atomic `mkdir`, acquire `_Axis/Flags/starting.lock/` and exclusively create its `OWNER` file with a fresh random nonce retained in this context. Read it back. Existing, malformed, or stale admission state stops this boot; age never authorizes deletion. Other I/O or permission errors stop as errors. Recovery follows [Lock-File > Quiescent Recovery] in an established quiescent window only. If the host cannot establish exclusive creation, require a User-confirmed serialized maintenance window with other sessions, launches, and schedules stopped before proceeding through file tools; report that concurrency is unavailable. Missing shell alone is not a failure when file tools provide exclusive creation.

2. While admission is held, READ `_Axis/Flags/starting` directly. Missing, blank, or Line 1 `cleared` is absent. A remaining value means incomplete startup: release only your own admission claim and STOP for quiescent recovery. Never overwrite an unfinished startup merely because two minutes passed.

3. Re-read all foreign Main Markers and their tombstones, measuring age. If a fresh foreign Main exists on an ordinary boot, release only your own admission claim, state that Main admission was lost to that session, and follow [Start-External] with a fresh External identity. No Main Marker, startup Log, Capability Flag, or `starting` Flag is written on this branch. Main candidacy becomes a committed role only after this check. An explicitly authorized promotion re-boot may instead carry its pending contest into [Start-Session] and must satisfy `^promote` before serving work; no other exception applies.

4. Apply [Practices > Timestamps > Bootstrap Markers] to reserve the Main Session ID, using the entry recipe's timestamp as the initial candidate. Prepare the exact canonical Main Marker Shape from [Practices > Markers > Main Marker Shape] before claiming. Within the short timestamp critical section, exclusively create and read back that first Main Marker, check its tombstone, and release only the owned timestamp claim. A collision advances the candidate before it becomes the Session ID. With admission still held, write/read back `_Axis/Flags/starting` with that final ID. Its two-minute freshness remains a diagnostic and completion check, not reclaim authority.

5. Carry the admission token and verified bootstrap Marker path into [Start-Session]. Before each startup write, verify admission ownership; lost ownership stops with no further write. After completion, delete or clear your own `starting` Flag, release only your own admission claim, and verify both are absent before the banner. Release means check the retained `OWNER` token, remove it, then `rmdir`; never release an unknown owner. A failure leaves startup incomplete. STOP this resource and continue its caller.

## Admitted loading batch

After successful helper or manual admission, retrieve `_Axis/Resources/Start-Session.md`, `_Axis/Resources/Load-Starting-Context.md` and `_Axis/INSTRUCTIONS.md` together in one bounded batch when the host supports independent file reads. Keep file boundaries visible and require complete outputs; split any oversized or truncated result. This groups retrieval only: follow Start-Session's execution order, and apply standing guidance before probes. Use ordinary sequential file tools when batching is unavailable. Never preload these project instructions before admission or skip required fresh state rereads.
