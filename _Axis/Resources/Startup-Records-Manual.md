# Startup Records - Manual
> **Purpose:** Complete file-tool fallback for Start-Session record initialization and commit; load only when that Resource selects the manual lane.

Retain the same valid admission and exact Starting Log. Every shared Startup Artifact Contract and semantic step in Start-Session still applies. Never reacquire a missing claim or repair a WORM artifact. A partial/unknown helper state stops for reviewed recovery.

## Initialize

These are Start-Session Step2 items1,3 and4. Perform them at those numbered positions only when not already fulfilled by a successful helper receipt; item2 and all other semantic work stay in Start-Session.

1. Quietly READ `_Axis/Flags/starting` and verify it still names your admitted Session ID before separately refreshing its `mtime`. Recheck the retained admission owner first; never recreate a missing `starting`.

3. Quietly read and validate the first Main-session Marker already exclusively created by [Claim-Session] under [Practices > Timestamps > Bootstrap Markers]. It must have the exact shape above; never create, overwrite, or recreate it in this step. A Marker left by an abrupt or ordinary host close ages out (Stale after 1 hour); an explicit successful `^shutdown` deletes the actor's own Marker. Main Markers are refreshed on every served turn per [Practices > Markers > The Lease], by `^save`, and on session resume. Immediately re-read the exact path and verify all four lines, no `{Session ID}.kill` sibling, and no other fresh Marker claiming the same Session ID. On any validation failure, leave `starting` set, do not write another startup record, name the exact failed path to User, and STOP. After exact Marker validation, append the exact opening Tracking line required above unless Tracking is `off`.

4. Quietly write the exact `Session Starting` Log above and retain its exact path for Step 3. If your Session ID was minted with zeroed milliseconds because no shell or interpreter could produce them (see the entry-point file), Log a second Event in the same pass - `Capability downgrade: timestamp precision`, with the five fields from [Practices > Logs > Capability Downgrades]. Queue ONE line with the greeting naming the missing interpreters and what to install - a host-capability notice like the others in item 5, not per-mint narration ([Rules > Speaking]).

## Commit

### Phase A - Validate the startup artifacts

1. Verify the retained admission owner. READ `_Axis/Flags/starting`, then separately refresh it only if its identity matches, and READ it directly again. Line 1 must equal your Session ID and its `mtime` must be under 2 minutes. A different ID is a concurrency failure - never overwrite it.
2. READ the exact Main Marker path. Its filename and Lines 1-4 must match the Startup Artifact Contract, it must have no `.kill` sibling, and no other fresh Marker may claim this Session ID. Recheck all foreign Main Markers: any live foreign Main fails ordinary startup. Only an explicitly authorized promotion may carry a contested Main into its mandatory resolution gate; it may serve no other work until resolved.
3. READ the Tracking setting. Unless it is `off`, the exact Tracking file must exist, contain the required opening line, and every nonblank line must have a valid UTC timestamp, this Session ID, and a nonempty statement in the contract's exact separator format. At `off`, no file is required.
4. READ all seven Capability Flags. Validate every Line 1 domain, every Line 2 boot timestamp, the two-line rule, and the `host-local-llm` Line 3 exception in the contract above. Re-read `Storage Policy`: `host-storage=atomic` passes only with exact `auto`; exact `single-writer`, missing, or malformed policy requires `host-storage=serialized`.
5. READ the exact retained `Session Starting` Log path. Its filename must be a timestamp and its four lines must exactly match the contract above; never satisfy this check with a directory scan or an older Log.
6. A malformed Capability Flag may be rewritten by its owning step once; a missing or malformed bootstrap Marker fails without repair, and a missing required opening Tracking line may be appended once; then rerun Phase A from item 1. Tracking is append-only and Logs are WORM: never edit, overwrite, or delete a malformed line or Log. If any check still fails - or an append-only/WORM artifact is malformed - startup failed: do not write `session-id`, remove `starting`, print the Session ID banner, or greet. Tell User which exact path failed and STOP.
7. Only after items 1-6 pass, mint and write the exact `Session Started` Log from the contract, retain its path, and immediately READ that exact file back. On any mismatch, preserve it as WORM failure evidence, leave `starting` set, name the exact path to User, and STOP.

### Phase B - Commit readiness

1. Quietly delete `_Axis/Flags/project-overlay` if it exists. A new normal session never inherits an overlay result from an earlier session; identity was prepared as data and must be revalidated before presentation and later activation (if deletion is blocked, follow [Rules > HostAndMeta > Deletion Fallback]).
2. Write `_Axis/Flags/session-id` as exactly your Session ID on Line 1 and a current UTC timestamp on Line 2. READ it back: Line 1 must match, Line 2 must be a valid timestamp not earlier than the Session ID, and `mtime` must be under 60 seconds. On failure, leave `starting` set, do not print the banner or greet, name the path to User, and STOP.
3. Recheck admission ownership and the foreign-Main gate once more. Delete `_Axis/Flags/starting`; if deletion is blocked, follow [Rules > HostAndMeta > Deletion Fallback]. Then release only your owned admission claim per [Claim-Session]. These completion writes must be the last writes of the startup protocol before the banner. A failed release is failed startup, not success.
4. READ `_Axis/Flags/starting` again: only missing or Line 1 `cleared` passes. READ `session-id` once more and require the same valid state. Verify the admission claim was released. If any check fails, do not print the banner or greet; warn User and STOP. No startup write follows this final read-back.
