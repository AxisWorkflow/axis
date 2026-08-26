# Timestamps
> **Purpose:** The identifier format, its uniqueness domain, and why a malformed one is a corrupt record.


- The format is `yyyy.mm.dd.hh.mm.ss.xxxZ` (ex: `2026.05.18.22.33.24.230Z`) - every field zero-padded, milliseconds always three digits, capital `Z` always present. There is no short form and no acceptable variant.
- Identifier timestamps (record filenames) are unique across the entire Project: two records never share one, in any directory, live or archived. Mint every identifier per [Practices > Timestamps] - existence check, then an atomic claim, both unconditional. Session Start is exempt (the `starting` lock already serializes it) and each Subproject is its own uniqueness domain.
- Metadata stamps (Flag bodies, `reviewed:`-style field values, times in prose) are values, not identities: mint them directly, never through the identifier procedure.
- `_Axis/Requests/` and `_Axis/Archive/Requests/` are timestamp-named but sit OUTSIDE the uniqueness domain and outside the twelve Index-Detail directories: a request is minted in the SENDER's domain, and requiring uniqueness in the receiver's would force the cross-boundary scan and claim that [Practices > Timestamps] forbids. Unique within the queue directory is enough - see [Practices > Requests > Identity].
- A malformed timestamp is a corrupt record, not a cosmetic slip: it breaks chronological sort, breaks the join between an index entry and its detail file, and hides the record from every later Agent. Two observed failure modes to guard against: dropping `.xxxZ` (producing `2026.07.27.14.05.09.md`), and naming a file after its contents instead of its time.
- If you are unsure of the current UTC time, get it with the command in [Practices > Timestamps] rather than approximating one. Never fabricate a timestamp, or any field of one, to fill the shape - `000` milliseconds because `date` would not produce them is fabrication, and so is a random three digits to make a collision less likely. Zeros at least announce that the precision is missing; invented digits assert a sort order that never happened.
- In timestamps, `yyyy` is 4-digit year, `xxx` is 3-digit milliseconds, `Z` is "Zulu" suffix.
- Fields are year.month.day.hour.minute.second.millisecond (all UTC).
- On a timestamp collision, increment the `xxx` milliseconds suffix and retry.
- Convert all timestamps into UTC (the Z at end of timestamp indicates Zulu time).
- Agents and Users working across time zones should coordinate timing in UTC.
- Files in the twelve Index-Detail directories (Tasks, Follow-Ups, Reminders, Snapshots, Logs, Notes, Ideas, CX, Audit, Status, Supervision, Agents) are named with a timestamp.
