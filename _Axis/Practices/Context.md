# Context
> **Purpose:** Define how the Agent selects what to read from the project for each request, as set by [Settings > Context Management].

Axis stores a project as short index entries plus detail records. Context management is the choice of which of those to bring into the conversation for each request. Too little and the Agent misses a decision; too much and irrelevant text crowds the window, and the host eventually compresses it. Missing, blank or unrecognized values of the Setting mean `Default`.

## Default

Read what the Practices and Commands direct, and lazy-load detail records when a request needs them ([Directives] > Lazy-Load Context). Nothing extra is required.

## Two-Pass

For every request that depends on project records:

1. **Pass one - index only.** Work from index-level information: the entries in `_Axis/TASKS.md` and `_Axis/SNAPSHOTS.md`, the Plan, and the first line (Subject) of each Log, Note, Idea, Follow-Up and Reminder (for example `head -n 1` across a family). Do not open record bodies yet.
2. **Write the shortlist.** Name the record IDs the request needs, newest first when they may conflict. Keep it short; a shortlist that grows past about 15 records means the request should be narrowed or split.
3. **Pass two - open exactly those.** Read the shortlisted records and answer or act from them. When records disagree, the newest record wins.
4. **Widen only on evidence.** If pass two shows a missing piece, such as a record pointing to another, add that record and say so. Never bulk-read a whole family "to be safe".
5. **Skip pass one for bulk work.** When the request itself requires reading a whole family or period in full ("review every Log from August"), read it directly. An index pass adds cost and saves nothing there; in Axis's benchmark it used 13-122% more tokens on Claude for such work.

Two-Pass changes what is read, never what is required. Session Start, Rules, Practices, Commands and each Command's own mandatory reads are unchanged, and a WORM record is still read in full when it is the one being acted on.

## Choosing a value

Evidence from Axis's benchmark (synthetic projects of 1,500-5,000 records, 15- and 45-turn sessions, October 2026):
- On Claude, Two-Pass used fewer tokens than Default in 4 of 4 matched comparisons (21-56%, about 38% on long sessions), with every answer correct under both.
- On Codex it used more tokens in 3 of 4 and ran about 20% slower.
- Under heavy read-everything workloads (67-turn sessions, Phase C), Two-Pass used more tokens than Default even on Claude, and on Codex it produced the only wrong answers seen (3 of 55), so the benefit is specific to targeted, lookup-style work.

The default Directive "Suggest a Context Method" turns this into a recommendation for the model in use. Changing the Setting follows [Practices > Settings].
