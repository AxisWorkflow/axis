# Archiving
> **Purpose:** Keep active context small and prevent unnecessary payload growth while preserving discoverable history.

## Storage destinations

Active records remain in their normal family. New local archives are fixed, tracked family folders: `_Axis/Tasks/Archive/`, `_Axis/Logs/Archive/`, and the same pattern for other record families. Memos use `_Memos/Archive/`. An external device being offline never blocks these local moves. Local archiving reduces context and active listings, not Git history size.

Cold storage is an explicitly bound location outside the project and outside Git. Its compact local catalogs and retrieval details remain in Git. Temporary working copies and unfinished recovery belong under `_Temp/`; successful completed recovery goes to dated `_Trash/`, then the normal two-day sweep. Cold history has no automatic deletion deadline.

## Policy and eligibility

[Settings > Archiving] is `Never`, `Default` (initial default), or `Aggressive`. Parse names case-insensitively; accept `Agressive` as `Aggressive`. Never changes history placement only: it does not retain completed operational recovery or regenerable build copies.

| Content | Default | Aggressive |
| --- | --- | --- |
| Completed/Cancelled Tasks, closed Ideas, done/superseded Memos | Local archive after 30 days | After 7 days |
| Settled Logs and completed Team/Job support | After 90 days | After 30 days |
| Team Messages after Main integration and full settlement; closed Individual correspondence | On closure | On closure |
| Snapshots | Keep newest 10; archive older after 30 days | Keep newest 3; archive older after 7 days |
| Valid terminal Follow-Ups and Reminders | Local archive on closure | Same |
| Notes/Supervision overflow | Existing Max Notes/newest 30 Supervision bounds | Same bounds |
| Ordinary local archived record bodies | Cold eligible after 365 days | After 90 days |
| Bulky unique diagnostics from closed work | Cold eligible after 30 days | After 7 days |

Bulky means a file over 1 MiB or an owning bundle over 10 MiB. Keep small decisions, results, reproduction recipes and release receipts local. Retention is minimum eligibility, never a demand to discard useful evidence. Age comes from completion/closure or last substantive update; immutable events use their recorded timestamp, never `mtime`. Untrustworthy age or closure means held.

Never suppresses policy moves, terminal self-archiving and both overflow moves. Closed records remain terminal wherever they reside; readers must not reopen them. Active/Blocked Tasks, open Memos/Ideas, unanswered requests, active recovery, unresolved incidents and current qualification inputs are always held. Age alone does not make a Note obsolete.

A historical **retrieval reference** can resolve through a cold locator. A **local dependency** needs exact local bytes and holds them. Record explicit dependencies in `_Axis/Archive-Holds.json` as `{"schema":1,"holds":[{"path":"relative/path","consumer":"current consumer","reason":"why local bytes are required"}]}`. Unclassified existing references are held during migration. Main reviews current source/specification/verification consumers before offloading; a filename, green result or old date is not a dependency classification. Retain causal chains, replay/deduplication identities, budget consumption and outstanding obligations locally until a verified compact consumer replaces their payload dependency. Offline storage never resets authority or spending.

## Round and safe local moves

`^archive` and the archiving phase of `^refresh` run the selected policy. Other commands do not start a whole-project archive scan. Startup validates pending operational recovery and may give a compact due notice only.

1. Inventory filename, first-line subject, lifecycle fields and size by family. Exclude Markers, Flags, locks, Secrets, current project content and nested Subprojects. Review holds before selecting exact paths. Move related support as one dependency-consistent unit.
2. The optional accelerator `python3 _Axis/Resources/archive-storage.py --root . plan` produces eligible simple moves and holds; `run --session {ID}` executes them. `--level Aggressive` persists the preference on run; `--dry-run` never mutates Settings or records. Helpers are accelerators, not permission to ignore held complex records: Main finishes the reviewed link/support procedure below.
3. Team Message closure uses only that Team’s control lock and exact move receipt; simple Individual closure is serialized by Main. These narrow operations do not take the general archive mutex. For other archive writers, including the manual equivalent, acquire `_Axis/Archive-Operation.lock/` under [Lock-File]; its BATCH heartbeat covers the reviewed archive operation. The accelerator acquires it on atomic storage and verifies ownership before writes. On degraded storage serialize all writers; contention is a hold, never stale-lock reclamation. Acquire any additional indexed-record locks required by their consumer. Verify all destinations absent and all sources ordinary, unchanged files. Record exact `record-check.py record-move` receipts before moving. Rename same-volume where possible; otherwise copy, hash-readback, then remove source only after verification. Never overwrite a collision.
4. Preserve original IDs, statuses, timestamps and bytes. For relative links affected by the move, use [Practices > LinkMaintenance] to record and qualify destination-only corrections; do not silently change WORM content. Move timestamp-owned support with its detail. Keep explicit historical exceptions valid. A failure retains both the current receipt and any unfinished source; resume the exact batch rather than inventing a new identity.
5. Once verified, remove archived Task/Snapshot sections from active indexes; keep a family Archive pointer. Initiative membership links point to the archived Task. Local archived records need no duplicate active-index entry. Directory listings and first-line subjects are the archive index. Existing legacy indexed rows remain readable until migrated.
6. Run `python3 _Axis/Resources/record-check.py links` and repoint each `MOVED-LINK` whose exact destination is established under [Practices > LinkMaintenance]. Check names, WORM receipts and index consistency. Log one concise round result with counts, bytes, paths, exclusions and unresolved holds. A local move frees no project bytes; Trash placement frees no bytes until Trash is swept.

For Message catch-up, run `python3 _Axis/Resources/coordination.py --root . --session {ID} archive-closed-messages` after reviewing Main's integration state. A missing integration receipt is not permission to invent one. Without Python, perform the same closure, physical-exit, liability and unanswered-obligation checks; under the owning Team lock move the complete folder to its empty archived counterpart and retain a compact exact-hash receipt in that Team's state. Main serializes closed Individual conversations. Preserve lookup through old record/support addresses. If a complex Individual conversation has support or live references, keep it visible until its dependency-consistent move can be verified. No age delay applies to eligible Messages and no cold offload follows automatically.

Notes overflow first reviews and renews still-current important guidance under [Practices > Notes], then archives eligible excess. Supervision preserves the newest 30. Never reports excess without moving. Follow-Ups/Reminders move only with valid terminal fields; malformed closure is held for semantic resolution.

## Cold destination

[Settings > Cold Storage Location] names a logical destination, initially `unconfigured`. Bind an approved existing ordinary folder in untracked `_Axis/Flags/cold-storage-location`:

```json
{"schema":1,"name":"history","path":"/existing/external/folder","durability":"verified-local","require_remote":false}
```

Set the logical Setting to `history`. Keep host paths and credentials out of tracked settings/catalogs. Never create a missing mount root. Cloud sync proves only a checked local copy; use `verified-remote` only after actual provider confirmation. When `require_remote` is true and upload cannot be verified, retain the source. Existing backups and cold storage have separate retention; never delete a backup as an archive side effect.

## Copy, checkpoint, retire, retrieve

1. Review the exact closed selection and dependency closure. New bundles contain at most 100 exact files, preserving project-relative names, modes, IDs, SHA-256 and sizes. The helper supports ordinary archived records and bulky diagnostics; retained coordination accounting is held until its consumer is independently compacted. For diagnostic exports provide `--selection _Temp/{review}.json`: schema 1, reviewing session and files keyed by path, each with `sha256`, `closed: true`, `closed_at` UTC, `local_dependencies: []`, `retrieval_references`, `reconstruction: unique|unavailable`, and `bundle_bytes` when using the bundle threshold. Main records the reasons in the round Event; assertions require actual review.
2. Run `archive-storage.py --root . export --session {ID} --path {exact file}` (repeat `--path`). It mints `_Axis/ColdStorage/{ID}.md`, copies under `{bound root}/AxisCold/{ID}/`, verifies content and manifest, then writes the local `copied.json` support receipt and family catalog. Sources remain intact. On interruption resume `export --id {bundle ID}` with the same binding; changed sources/destinations hold without overwrite.
3. Each family catalog is `Archive/COLD.md` (diagnostics: `_Dev/Evidence/COLD.md`). Its rows link retrieval details with counts and logical size. Add date range, subjects and useful keywords during Main review, and split catalogs by year when needed. Timestamp scanners skip reserved catalog names. A locator's locally stored manifest reserves original identities even offline; it is metadata, not a second Task. Only a verified copied receipt makes references resolvable as cold history.
4. Checkpoint locator, copied receipt and catalogs in Git before retirement. Without Git the helper writes and verifies their independent catalog copies beside the external bundle. Then `retire-cold --session {ID} --id {bundle ID}` rechecks all external bytes, source hashes and current holds before moving sources into dated Trash. Report local moves, cold bytes copied, source bytes retired, unavailable destination and remaining holds separately. No source disappears merely because a copy command returned success. A partially retired bundle resumes from the same dated Trash proof.
5. Retrieve one original identity/path with `retrieve --session {ID} --id {original ID or path}`. Verify manifest and file hashes, then materialize only requested bytes under `_Temp/ColdRead-{bundle ID}/`. Never execute archived code or turn a closed record into active work. Retrieval does not reset its age or preload all history at startup.

## Migration and legacy Archive Location

Archive Location and Archive in Git are legacy read/migration settings; they no longer redirect new family-local archives. Readers search active, new family Archive, legacy `_Axis/Archive/{Family}/`, then the configured legacy root before reporting missing. Keep the resolver until every old reference has a verified mapping. Unavailable legacy coordination history still holds admission/accounting that needs it.

On update, disclose that new local archives are tracked and initialize Archiving to Default only when no equivalent preference exists. Preserve explicit archiving opt-outs as Never. Do not silently change the old external destination or automatically bind it for deletion/offload. Inventory existing external history in place and create hash-verified locator/catalog mappings; do not download and recommit its bodies. A migrated in-place locator records its exact existing external-relative paths and verification before any reference is redirected; until then retain the legacy resolver. With an approved cold binding naming that same existing external root, `catalog-legacy --session {ID} --path _Axis/Archive/{Family}/{ID}.md` verifies selected existing files and creates locators in place with `layout: legacy` and an exact logical-to-external path map. It copies zero payload bytes and never retires external originals. Retain the old resolver for coordination consumers and all unmapped history.

For an in-project legacy archive, use exact move receipts and verified family-local moves. `Archive in Git = false` remains effective for old payload: map it to cold storage or hold migration, never silently commit it. New tracked archive semantics do not authorize staging an ignored old archive.

## Recovery and Git storage

Temporary recovery protects unfinished operations; Git or backups provide historical undo. Enumerate `_Axis/Updates/*/recovery.json` and `_Axis/Merges/*/recovery.json` before any Temp/Trash sweep (`archive-storage.py protected`). A pending pointer protects its exact owned directory at every Archiving level. Never expire it by age. Validate completion using its owning protocol, not a cleanup filename heuristic.

Updates preserve only their changed paths. Exact committed preimages use verified checkpoint blobs; dirty, untracked or non-Git preimages use minimal temporary copies. Third-value edits always hold recovery. After fresh validated consumption (or verified updater-only completion/rollback), retain a small durable completion receipt and retire temporary payload. The newest accepted release has no special permanent rollback exemption. Legacy accepted transactions compact using their checked manifests.

Merges put new journals and rollback objects in `_Temp/Merge-{ID}/`, with a durable pointer. Unique imported project content and provenance remain in their intended destinations. First fresh combined startup rechecks merged content, ignored outputs, identities and links; only success writes the small validated receipt and retires recovery to dated Trash. Failure/interruption retains it.

Ordinary Git maintenance may pack/prune according to Git's normal reachability and grace rules when the repository is quiescent. Do not rewrite history, expire reflogs aggressively, delete backups, force-push or archive reachable commits automatically. Prevent new reproducible bulky evidence entering Git; keep concise results, exact source identity and reproduction instructions. Git history removal is a separately approved project.

## Archive Location

For legacy lookup, a value starting `~/` names a folder inside the current user's home folder. `^save` and `^resume` keep the value portable without asking when replacing an absolute home path with the exact equivalent `~/` binding; log that normalization and move no payload.

Compatibility section for existing links: Archive Location is a legacy resolver and migration binding. Use Migration and legacy Archive Location above; it does not redirect new local archive writes.

## Indexed Records

Active Task/Snapshot indexes cover the active window. Once a move and its detail are verified, remove the archived row and retain the family Archive pointer. Legacy rows remain readable. Initiative links continue to name the original Task identity at its new location.

## Automatic Note Overflow

At Default/Aggressive, review and renew still-current important guidance before moving eligible excess under Max Notes. Never reports excess without moving. Notes remain searchable in `_Axis/Notes/Archive/`.

## Automatic Supervision Overflow

At Default/Aggressive, preserve the newest 30 active Supervision records and archive older excess in `_Axis/Supervision/Archive/`; Never reports excess without moving. This is an active context bound, not permission to delete history.

## Safe Move and Restore

Follow Round and safe local moves above. Markers are never archived. If any destination exists, STOP that move without overwrite. Restore by reversing the verified move with an empty live destination and appropriate index edits. Never restore a terminal Follow-Up or Reminder to open work: reopening mints a new identity. Moving an archived Task does not change its status; activation needs a separate directed status change.
