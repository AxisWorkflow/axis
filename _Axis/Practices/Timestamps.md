# Timestamps
> **Purpose:** Mint identifier timestamps that are unique across the entire Project, using an existence check plus an atomic claim.

Every record in an Index-Detail directory is named by its timestamp, and that name is the record's identity (see [Practices > IndexDetail > The Name Is the Contract]). This Practice adds one guarantee on top: no identifier timestamp names two records anywhere in the Project. That uniqueness is what turns a bare timestamp into an unambiguous key - `grep -rn "{timestamp}"` from the project root finds THE record plus every cross-reference to it, with nothing to disambiguate. Timestamps are wall-clock values and time moves forward, so a collision is only ever a concurrency problem (two mints in the same millisecond), never a history problem: no one re-mints last week's value. Real milliseconds are what make that window a millisecond wide instead of a second wide - which is why step 1 goes to some trouble to get them, and why `000` is never an acceptable stand-in.

## Scope

- An identifier timestamp is one that becomes a filename in the twelve Index-Detail directories or their `_Axis/Archive/` families. Only identifiers pass through this procedure.
- Metadata stamps are values, not identities: Flag bodies and Line 2 refreshes, `reviewed:` and `completed:` field values, times quoted in prose. Mint them directly; never check or claim them.
- Session Start is exempt: the entry-point file mints the Session ID while the `starting` in-flight lock serializes startups, so two Sessions cannot mint the same ID. The ID then names the Main Marker like any other identifier.
- A rename keeps identity: archiving a record, or repairing a malformed name under `^refresh`, moves an existing identity - it is not a new mint (the existence check still guards the repaired name's destination).
- Each Subproject is its own uniqueness domain. Never scan into a nested Subproject and never claim across the parent/child boundary - separate processes may be running against each side.

## Minting an Identifier

1. Generate a candidate. Run this one command exactly and use what it prints:

		TS=$(date -u +"%Y.%m.%d.%H.%M.%S.%3NZ"); case "$TS" in *3N*) TS=$(node -e 'console.log(new Date().toISOString().replace(/[-T:]/g,"."))' 2>/dev/null || python3 -c 'import datetime as d;n=d.datetime.now(d.timezone.utc);print(n.strftime("%Y.%m.%d.%H.%M.%S.")+"%03dZ"%(n.microsecond//1000))' 2>/dev/null || perl -MTime::HiRes=time -e 'my $t=time;my @g=gmtime $t;printf "%04d.%02d.%02d.%02d.%02d.%02d.%03dZ",$g[5]+1900,$g[4]+1,$g[3],$g[2],$g[1],$g[0],($t-int $t)*1000');; esac; echo "$TS"

	BSD/macOS `date` has no `%N` and prints a literal `3N` where the milliseconds belong; the `case` catches exactly that and falls back to an interpreter that has them. Never substitute `000` for the milliseconds. Zeros are not a lower-precision timestamp, they are a fabricated field in an identifier ([Rules > Timestamps]), and they collapse every mint in the same second onto one value - measured 2026-08-06, all 30 records written that day on a macOS host ended `.000Z`, which is the entire collision risk this Practice exists to remove. If a shell runs but no interpreter answers, use `000`, treat steps 2 and 3 as load-bearing rather than routine, and Log it ONCE per session as a Capability downgrade (`Capability downgrade: timestamp precision`, per [Practices > Logs > Capability Downgrades]) with `behavior-used: zeroed milliseconds, uniqueness carried by the existence check and claim`. Never narrate it per mint - that is exactly the noise [Rules > Speaking] exists to prevent, and uniqueness holds without User's help. But DO queue ONE boot-time line, alongside the other host-capability notices Session Start delivers: a host that cannot produce milliseconds at all is something User can act on (install `node`, `python3`, or `perl`), and "would User's next action change?" is the test that decides. Measured T1, 2026-08-06: an earlier blanket ban on speaking failed its own test - the agent told User anyway, and it was RIGHT to, because the news was a host gap plus a defect in this very ladder. The Log is the durable record and `^audit` is the reader - it scans on-disk identifiers for the `.000Z` signature - so the fallback stays visible where visibility is useful, spoken once where it is actionable, and silent everywhere else.

2. Existence check - the candidate must name nothing anywhere in the Project:

		ls _Axis/{Agents,Audit,CX,Followups,Ideas,Logs,Notes,Reminders,Snapshots,Status,Supervision,Tasks}/{candidate}.md _Axis/Archive/*/{candidate}.md 2>/dev/null

	Empty output means the value is free. If any path matches, increment the milliseconds and repeat this step. Without a shell, glob the same paths with the host's file tools.

3. Verify your lease, THEN claim the value. READ your own Marker `_Axis/Agents/{Session ID}.md` per [Practices > Markers > The Lease] before the claim: a tombstone stops you, and a bare-missing Marker is stop-and-ask. This step is the lease's executable home for RECORD writes, and it is here because every new record mints an identifier and every identifier passes through this claim - while Follow-Ups, Logs, Notes, Ideas and Status reports are new files that take no file lock, so [Lock-File > Acquire] never sees them. Measured F2, 2026-08-06: an agent tombstoned mid-task wrote four more Notes and a Tracking line after the kill, never noticing, because the only pre-write check lived on a path its writes did not take. Then claim - the Timestamp Claim, taken always, for every identifier (see Why the Claim Is Unconditional): `mkdir "_Temp/{candidate}.tsclaim"`. `mkdir` is atomic, so exactly one Agent can own a value; if it fails, another Agent is minting that exact value right now - increment the milliseconds and repeat from step 2.

4. Create the record file under the claimed name (and its index entry, when the family is index-backed).

5. Release the claim: remove `_Temp/{candidate}.tsclaim/` (if deletion is blocked, follow [Rules > HostAndMeta > Deletion Fallback]). Once the record file exists, step 2 protects the value forever - the claim is only a bridge across the create.

## Why the Claim Is Unconditional

The claim was once conditional - taken only when parallel Subagents were running or another Session might be live. That condition cannot be evaluated by the Agent it governs. An Agent that has not yet noticed a second Agent reads the condition as false and skips the claim, and those are precisely the moments when two writers race: a foreign Marker written seconds ago, a Subagent someone else spawned, an External that booted between your directory scan and your write. A guard that switches itself off whenever you are unaware of the hazard is not a guard - it is a guard that fires only when it is not needed.

So claim every identifier. The cost is one `mkdir` and one `rmdir` per record, unmeasurable beside the write they protect, and in exchange uniqueness stops depending on what the Agent happened to know. Step 2 still does the real work against records that already exist; the claim covers only the gap between checking and creating, which is the one window a scan cannot see into.

Note what the claim does NOT do: it never invents a value to dodge a collision. The loser of a race increments to the next free millisecond, so the Agent that arrived second gets the later timestamp - true ordering, preserved by construction. Randomizing a millisecond field to make collisions less likely would do the opposite: it trades an honest tie, which a reader can see is a tie, for a manufactured sort order that reads as fact and is not (see [Rules > Timestamps]).

## Stale Claims

A claim left behind by a crashed Agent goes stale like any lock: `mtime` older than 10 seconds is abandoned. Stale `*.tsclaim/` directories in `_Temp/` are swept wherever stale locks are swept (Session Start and `^refresh`). They are gitignored with the rest of `_Temp/`, and an abandoned claim never costs more than the one retry it forces.

## Duplicates Found Later

Records created before this Practice, or slipped past it, can still collide. `^audit` scans for duplicate identifier names read-only; `^refresh` repairs them with User approval: keep the older or index-linked record under the contested name, rename the other by incrementing its milliseconds to the first free value, and relink its mutable index entry when it has one. Renaming repairs identity, not content - it does not violate WORM - and a stale reference inside an old WORM record is history, not a defect.
