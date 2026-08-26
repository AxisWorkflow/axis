# Wiki
> **Purpose:** Where Library content, raw sources, and Agent bookkeeping each live.


- `Wiki/` lives outside `_Axis/` because it is User-facing.
- Images are ALWAYS copied into `Wiki/` on ingest - never referenced outside it - so the Library stays self-contained and shippable.
- Version control commits ONLY `_Axis/Wiki/` (the five admin files); everything under `Wiki/Inbox/` and `Wiki/` is gitignored except each folder's `.gitkeep` (see README Limitations).
- `Wiki/Inbox/` is an immutable inbox for User; raw sources only - Agents never write there.
- `Wiki/` is owned by the Agent: content pages only.
- `_Axis/Wiki/` is Agent-maintained bookkeeping, kept apart from content so graph views and shares stay clean:
	- `Input-Index.md` - catalog of raw sources in `Wiki/Inbox/`.
	- `Library-Index.md` - catalog of every page with a one-line summary.
	- `Library-Activity.md` - append-only log of ingests, queries, and lint passes.
	- `Library-Status.md` - append-only Library Status record - one `## [yyyy-mm-dd] {report}` section per Review report; never rewrite past sections.
	- `Library-Schema.md` - the Wiki Library schema.
- Every claim in the Wiki should cite a source.
- Wiki contradictions are flagged under `## Contradictions`, **never** auto-resolved.
