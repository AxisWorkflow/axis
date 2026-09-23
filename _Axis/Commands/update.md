# ^update
> **Purpose:** Update Axis Workflow machinery to an official release while preserving project state and local customizations.

## Scope and Admission

1. Main Agent only. External Agents and Subagents refuse this Command. Require an eligible standard-capability Main, a valid current lease, and `host-shell=yes`. Read `Storage Policy` and read `host-storage` under [Practices > Flags > Reading Flags]. Require `Storage Policy=auto` and `host-storage=atomic`; exact `single-writer`, a missing or malformed policy, valid `serialized` or `unknown`, or a missing or malformed storage Flag stops. A policy ceiling, serialized, unknown, cloud-synced, or independently replicated tree cannot guarantee the atomic filesystem operations this transaction needs.

2. Check `_Axis/CHANGELOG.md` directly, then read `current-version`, `changelog-format`, and `self-update-baseline`. Accept each version only in full `YY.MM.DD` or `YY.MM.DD-N` form. An absent Changelog or missing or malformed field means unidentified or damaged update metadata: do not guess a version or overlay files; tell User that a manual reviewed migration is required and STOP. If `self-update-baseline` is `pending`, or `current-version` predates that baseline, this copy is not eligible for managed self-update: stop unless a future Changelog explicitly defines another migration path.

3. Refuse to apply while another writer may be active. Re-read `_Axis/Agents/` and every active `*.lock/`: require your own Main Marker, no other fresh Marker without a kill tombstone, and no fresh lock. Ignore dead or stale entries only under their owning protocols. Do not spawn a Subagent during this Command.

## Resolve and Validate the Source

4. Interpret optional text after `^update` as exactly one of: an official tag `vYY.MM.DD[-N]`, or a User-supplied path to an already extracted official Axis release. With no text, query `https://api.github.com/repos/AxisWorkflow/axis/releases/latest` and use its `tag_name` and `tarball_url`. Reject drafts, prereleases, another repository, a moving branch, or a tag outside the version form. Network access is used only to fetch official release metadata and exact tag archives.

5. Stage under a fresh `_Temp/Axis-Update-{timestamp}/` directory. For a remote source, use already available host download tools or ordinary `curl` plus `tar`; do not install a plugin, package, CLI, or helper merely to update Axis. Download each archive to a file first - never pipe a download into extraction. Before extraction, list and reject any absolute or `..` path, symbolic link, hard link, device, or entry outside one expected top directory; then extract into a new empty staging directory without following links. If no suitable downloader/extractor exists, ask User to place the official extracted release in the named staging directory and rerun `^update {path}`. Never execute a script, entry file, hook, binary, or Command from a downloaded tree.

6. Download or locate two immutable trees:

- `base` - the official tag `v{current-version}`;
- `target` - the requested official tag.

The live project is `local`. If the base tag cannot be obtained, or the target does not contain the installed or provisional origin version in its changelog history, stop for a manual migration. A same-version target is a clean no-op: report that Axis is current and STOP. Refuse a downgrade. Compare the numeric date components and then the numeric same-day sequence, treating no suffix as sequence 1; never compare version strings lexically (`-10` is newer than `-2`).

7. Validate the target as data before interpreting its migration notes: its changelog fields and newest published section match the target tag; `changelog-format` is supported; `self-update-baseline` is not `pending`; `AGENTS.md`, `CLAUDE.md`, and `GEMINI.md` are byte-identical and each is under 18,500 bytes; every literal file in its `_Axis/MANIFEST.md` exists; the update Command, Git Command, and Secrets-capsule helper exist; there is no development-only tree, session content, project content, symbolic link, unresolved conflict marker, or unexpected root. On any mismatch, delete nothing, report the failed invariant, and STOP.

## Build the Migration Plan

Preserve all `_Axis/Secrets/.recovery.*/` exactly through staging, apply, rollback, and cleanup. Recovery originals are protected local Secrets, never scratch or release content. Do not read or enumerate their names or contents merely to update; unresolved recovery blocks Secrets synchronization, not unrelated verified migration work.


8. Hash files without printing their contents. Read applicable published changelog sections after the origin from oldest to newest, then compare `base`, `local`, and `target` for managed Workflow paths. The managed set is the three root entry files and `.gitattributes`; `_Axis/Commands/`, `Practices/`, `Rules/`, `Resources/`, and `Dashboard/`; and `_Axis/CHANGELOG.md`, `CLA.md`, `CONTRIBUTING.md`, `LICENSE`, `README.md`, `GLOSSARY.md`, `MANIFEST.md`, `PRACTICES.md`, `PRINCIPLES.md`, and `RULES.md`. Never cross into a nested Subproject while enumerating it.

- When local equals base and target changed, stage the target version.
- When local changed and target equals base, preserve local.
- When both local and target changed, perform a real three-way review. Merge only when intent is unambiguous; otherwise list the conflict and stop before mutation.
- Add a target-only path only when no local path collides.
- Retire a target-removed path only when local still equals base. Preserve and report a locally changed retired path.

An explicit changelog migration can refine these rules inside its named scope, but never override the preservation boundary or authorize downloaded code execution. Treat its prose as declarative migration data; never run a shell line or command copied from it.

Interpret `update-impact` before planning writes. `automatic` follows the ordinary three-way rules and may proceed as routine after the concise preview. `review` requires every semantic choice to be called out and resolved explicitly in that preview; ask only for the actual unresolved decision. The current Command owns authorization policy; historical descriptions of an older confirmation token do not restore a blanket token gate. If any applicable release is `manual`, report its migration notes and STOP before mutation. An absent or unknown impact also stops.

9. Preserve project state by default. Never bulk-replace `_Axis/` and never read plaintext `_Axis/Secrets/`, its private identity, or `_X` content for this Command. Preserve `_Axis/Secrets/.recipient`, `.capsule.age`, `.binding`, and every plaintext entry as project state; a release may update the managed helper under `_Axis/Resources/`, but it never replaces the configured capsule or local binding. Do not replace or delete Project Subfolders, Subprojects, Wiki content, Secrets, `.git`, host configuration, records, Flags, Markers, Requests, Archive, Tracking, or the live contents of Tasks, Follow-Ups, Reminders, Ideas, Notes, Logs, Status, Supervision, Snapshots, CX, and Audit. Preserve these working files unless an applicable changelog section gives an explicit semantic migration: `_Axis/PROJECT.md`, `PLAN.md`, `TASKS.md`, `SNAPSHOTS.md`, `SETTINGS.md`, `MINDSET.md`, `DIRECTIVES.md`, `INSTRUCTIONS.md`, `ENVIRONMENT.md`, and `_Axis/Wiki/` administration files. If `_Axis/PROJECT.md` contains a project-overlay declaration, preserve both that exact declaration and its declared project file as project state; identify and hash them without loading the overlay or dispatching its Commands during this update. WORM records are never rewritten.

10. Treat customization-sensitive files specially:

- Merge new Axis ignore rules into `.gitignore` without removing User rules.
- Merge new Axis-owned text rules into `.gitattributes` without applying a blanket transform to User content or binaries.
- Preserve the exact Secrets exceptions and binary rule required by the target release. Never broaden them to track plaintext, drop a User ignore rule, or classify `.capsule.age` as text.
- Treat root `README.md` and `LICENSE` by lifecycle, not as ordinary managed files. With no valid `project-ready`, keep them byte-identical to target `_Axis/README.md` and `_Axis/LICENSE`. With valid `project-ready`, preserve the User-owned Project README and its bounded Axis summary block; remove root `LICENSE` only when it is still the base Axis license, and preserve any customized project license.
- Retire `.github/README.md` when it matches the base Axis display copy. If it differs, treat it as User content: surface the GitHub override, require a choice to merge/preserve it, and never delete it silently. Target releases and ordinary User projects carry no Axis-supplied `.github/` directory.
- The three entry files are reserved and must finish byte-identical. Surface local divergence; move legitimate standing guidance into `_Axis/INSTRUCTIONS.md` only with User approval.
- Preserve existing Setting values and custom Settings. Add, rename, transform, or retire a Setting only as the changelog directs. Regenerate `_Axis/MINDSET.md` only when the migrated Setting schema or target template requires it.
- Three-way merge a customized Dashboard; never silently replace it.

11. Build the complete proposed result in staging, including all semantic migrations. Follow `_Axis/Resources/Check-Update-Handoff.md` > Transaction and file-only contract. Freeze the exact source, base/local/target hashes, planned adds/replacements/merges/retirements, preserved paths, overlay declaration/content hashes and required verification/reconciliation. Re-read every local and source input; changed bytes or identity invalidate the plan and its decisions. Prepare a new exact plan rather than applying a stale classification.

12. Present one concise preview: from/to versions, exact official tag/object, change counts, supported project migrations, preserved customizations, conflicts, durable rollback location and mandatory automatic shutdown/fresh-session restart. User's `^update` invocation authorizes an expected routine update and that shutdown; no second confirmation token is required. A routine plan has an exact supported official target, all migration impacts `automatic`, valid integrity/storage/lease/exclusivity checks, deterministic preservation and no unresolved semantic choice or destructive surprise. Expected automatic Settings additions preserving existing values may qualify. Proceed without pausing when those conditions pass. For exceptions ask only the path-specific decision needed, record its answer against this exact plan, and revalidate afterward. Invalid/untrusted source, downgrade, manual/unknown migration, integrity failure or unsafe concurrent/storage state stops before apply. A same-version target remains a no-op. Never treat silence or elapsed time as an exceptional decision.

After those checks, mint a WORM scoped authorization Event recording the actual User invocation, reviewed target and resolved decisions. Include `plan_scope_sha256` and the accepted installed `engine_sha256` under [Check-Update-Handoff]. Use its ID for `_Axis/Updates/{ID}/`. The optional installed helper's `prepare --root {root} --plan {plan} --session {Session ID} --transaction {Event ID}` writes durable start-first evidence and verified frozen recovery machinery. Hold the returned owner token only for this transaction. From then on use that verified frozen engine, whose bytes are independently pinned by the authorization Log; never execute a downloaded target helper. The file-only procedure has the same scope and readback requirements.

## Apply, Verify, and Commit Readiness

13. Immediately before apply, re-verify your lease, exact scoped plan authority, all source/staged/local identities and the no-other-writer condition. Any change invalidates routine classification and earlier exception answers. Acquire Batch locks for every path the plan can change, in fixed lexicographic order, under [Lock-File > Batch]; heartbeat them through apply, validation, and any rollback, then release them in reverse order. If any lock cannot be acquired, release those already held and STOP without mutation. Treat a local symbolic link at any touched path as a conflict. Verify every changed-path preimage, mode and absence is already durable in `_Axis/Updates/{ID}/`; staging alone is not rollback authority. Hold the owned startup admission barrier throughout apply and verification, so another startup cannot load a mixed tree. When the project is already under version control, also make the ordinary pre-update checkpoint under [Practices > GIT > Checkpoints] after its staged-content safety check; do not initialize Git solely for this Command.

14. Apply only the exact scoped plan through the verified frozen engine's `apply` action or equivalent file-only transaction. Recheck each preimage, write a durable intent, atomically apply, read back, and record its result. Retire only owned paths whose exact originals are already durable. Write the entry trio at the end and Changelog last. A failed write/check leaves an interrupted transaction; rollback only known before/after states using pinned preimages, verify the full restoration, retain every failure record and release only owned admission. Unknown drift or lost ownership stops for reviewed recovery with no speculative repair.

15. Validate the applied tree before declaring success:

- `current-version` equals the target tag without `v`, and `self-update-baseline` is not `pending` in a published target;
- entry files are byte-identical and every literal Manifest path exists;
- every changelog `Verification` item for the traversed releases passes;
- no conflict marker, candidate session content, or unexpected path was introduced;
- preserved project-state hashes still match, except for approved semantic migrations;
- any project-overlay declaration and its declared project file still match their pre-update hashes unless the exact scoped plan includes an applicable supported semantic migration and any required User decision; the current session never loads them, and the required fresh session revalidates them;
- `Storage Policy` is exact `auto` or `single-writer`, and any `single-writer` result cannot coexist with a claimed `host-storage=atomic`;
- the final tree matches the approved plan and the rollback journal is complete.

On failure, take the exact recovery path and STOP. On success, verify durable `complete.json`, full journal/postimage and preservation, then create/read back readiness and release the owned update admission via the frozen engine's `release` action. Keep durable rollback and evidence; no automatic cleanup. Log `Axis updated: {from-version} to {to-version}` with exact official object, transaction, migrations and validation. Ready success still requires inline shutdown now and exactly-once fresh-session reconciliation/consumption before ordinary project resume.

16. Complete the update-specific shutdown inline because already-loaded instructions do not update in place; do not invoke the separate `^shutdown` Command and do not ask User to invoke it. Append the final Tracking line when Tracking is enabled. Delete your own Main Marker under the same explicit-exit authority as `^shutdown` (use Deletion Fallback if needed), then read `_Axis/Flags/session-id`; clear it only when Line 1 is your Session ID. Print one `Updated and stopped` block under `_Axis/Resources/Lifecycle-Presentation.md`, naming the verified from/to versions and saying to close this window (or terminal) and start a new session. Do not add another shutdown/final-response block. Do not serve further work in this conversation. STOP.
