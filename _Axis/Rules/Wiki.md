# Wiki
> **Purpose:** Where Library content, raw sources, and Agent bookkeeping each live.


- `_Wiki/` lives outside `_Axis/` because it is User-facing.
- Images are ALWAYS copied into `_Wiki/` on ingest - never referenced outside it - so the Library stays self-contained and shippable.
- Version control commits ONLY `_Axis/Wiki/` (the five admin files); everything under `_Wiki/_Inbox/` and `_Wiki/` is gitignored except each folder's `.gitkeep` (see README Limitations).
- `_Wiki/_Inbox/` keeps User's raw sources immutable. Inbox filing may move a file in unchanged ([Practices > Inbox]); approved absorption may add new byte-identical sources ([Practices > Merging]). Never overwrite or edit an existing raw source.
- `_Wiki/` is owned by the Agent: content pages only.
- `_Axis/Wiki/` is Agent-maintained bookkeeping, kept apart from content so graph views and shares stay clean:
	- `Input-Index.md` - catalog of raw sources in `_Wiki/_Inbox/`.
	- `Library-Index.md` - catalog of every page with a one-line summary.
	- `Library-Activity.md` - append-only log of ingests, queries, and lint passes.
	- `Library-Status.md` - append-only Library Status record - one `## [yyyy-mm-dd] {report}` section per Review report; never rewrite past sections.
	- `Library-Schema.md` - the Wiki Library schema.
- Every claim in the Wiki should cite a source.
- Wiki contradictions are flagged under `## Contradictions`, **never** auto-resolved.
