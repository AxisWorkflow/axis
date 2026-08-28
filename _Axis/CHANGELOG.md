# Changelog
> **Purpose:** Record Axis release identity and the structural migrations needed to update an existing project safely.

current-version: 26.08.28
changelog-format: 1
self-update-baseline: 26.08.19

## Contract

`current-version` is the installed Axis release and uses the full release tag without its leading `v`. `changelog-format` versions this document's update contract. `self-update-baseline` remains `pending` until the first release that ships both this file and `^update`; at that publication it becomes that release's full version.

The RSI Controller records every upgrade-relevant structural change under `Unreleased` in the same pass as the change. At publication, `^pub` moves that material into a new immutable release section, updates `current-version`, sets the baseline when still pending, and recreates the empty headings under `Unreleased`.

Published release sections use an exact `## {version}` heading and the following stable subsections. `^update` reads applicable sections from oldest to newest. Paths are project-root-relative and literal.

- `Structural Changes` - added or changed Workflow machinery and its intended ownership.
- `Project-State Migrations` - transformations of live project state; preservation requirements must be explicit.
- `Retired Paths` - obsolete paths and their replacement, if any. An updater stages retirement reversibly and never destroys a locally modified file silently.
- `Verification` - release-specific facts that must hold before the new version is committed.

Each release carries `update-impact: automatic`, `review`, or `manual`. `automatic` permits the ordinary three-way plan, preview, and confirmation when no unresolved choice remains. `review` requires every semantic choice to be surfaced and settled in the preview. `manual` forbids auto-apply: `^update` reports the applicable migration notes and stops before mutation. An unknown value also stops. The changelog guides a migration but never authorizes executing downloaded code, overwriting project state, or resolving a local customization without review.

## Unreleased

update-impact: automatic

### Structural Changes

### Project-State Migrations

### Retired Paths

### Verification

## 26.08.28

released: 2026-08-28
update-impact: review

### Structural Changes

- Added a production-safe project-overlay mechanism that runs only after ordinary Main Session Start succeeds. `_Axis/PROJECT.md` may declare one bounded overlay file; [Load-Project-Overlay] revalidates that declaration, file identity, current normal Session ID, and Main lease before writing a per-session `project-overlay` cache. The cache alone grants no role, project identity, command, or authority.
- Converted the Axis development repository to an RSI Controller project. Its overlay maps exactly `^benchmark`, `^compile`, `^eval`, `^pub`, and `^test` to development-only files while retaining the root `_Axis/` tree as the sole Controller state and WORM record plane.
- Made all three entry files use the same generic project-overlay continuation hook. Ordinary projects with no declaration remain silent and unchanged; External Agents and Subagents never load a Main overlay.
- Recast OpenClaw as an optional thin channels-and-orchestration harness. [Practices > OpenClaw] now keeps channels, exact routing, agent/session lifecycle, directed message delivery, explicit cron, operational transcripts, and required runtime tools while disabling Host persona/bootstrap files and instruction-injection hooks, semantic memory/search, memory plugins and hooks, inferred commitments, dreaming, generic heartbeat, default skills, wildcard agent messaging, and unrestricted tools.
- Added a schema-adaptive `^install openclaw` route. It distinguishes Axis-only from mixed Gateways, prefers a dedicated `axis` profile for mixed use, resolves every semantic control against the installed CLI schema, previews and dry-runs a secret-free patch, requires bounded Host-mutation approval, validates readback, and boot-probes without making OpenClaw a dependency.
- Added targeted `^audit openclaw` with `Ready`, `Degraded`, and `Unverified` outcomes. The audit reads only non-secret controls and legacy-path existence, distinguishes disabled memory from erased old state, and never authenticates, restarts, sends a probe, reads memory/persona content, or changes the Host.
- Updated WhatsApp setup to harden the selected Axis profile before pairing, preserve its required channel/provider plugins, require the narrow messaging surface for startup notices, and retire the `tools.profile: full` recommendation.

### Project-State Migrations

- The Axis development repository adds the exact project-overlay declaration and RSI Controller file, records `project-ready`, and preserves its existing `_Axis/` project state. Ordinary User projects add no declaration and activate no overlay. `^update` preserves an existing declaration and declared project file without loading either during the update; the mandatory fresh session revalidates them.
- Retire any stale per-session `dev-mode` Flag when adopting this release. The generated ignore contract now owns `project-overlay` instead. Do not infer an overlay from `_Dev/` presence, a Flag, a repository name, or any other heuristic.
- Existing OpenClaw integrations require review. Decide whether the current Gateway is Axis-only or mixed; a mixed Gateway should move Axis agents to a dedicated profile before hardening so unrelated agents remain unchanged.
- Existing project-root `SOUL.md`, `IDENTITY.md`, `USER.md`, `MEMORY.md`, `memory/`, `DREAMS.md`, `HEARTBEAT.md`, `BOOTSTRAP.md`, and `TOOLS.md` are never read or removed automatically. With User approval, move selected paths intact to `_Trash/OpenClaw-Legacy/{timestamp}/`; User separately decides archive or purge for old OpenClaw profile state, indexes, and transcripts.

### Retired Paths

- Retired `_Dev/Commands/dev.md`, the `^dev` command, the `dev-mode` Flag, and the entry-point bypass that formerly replaced normal Session Start. The RSI Controller is now a validated post-start project overlay.
- Retired OpenClaw persona and memory files as supported Axis overlays. Axis identity, instructions, mindset, User/project facts, and durable memory now live only in the existing Axis project files and records.

### Verification

- The RSI Controller regression contract verifies fresh activation after normal Session Start, same-session continuation with full revalidation, silence in a clean non-RSI project, fail-closed malformed or mismatched declarations, exact five-command dispatch, updater preservation without execution, synchronized entry files, and zero development-only material in a production release.
- The OpenClaw Thin Harness regression contract verifies live-schema adaptation, preserved `AGENTS.md` injection, layered memory/persona shutdown, least-privilege tools, exact Request-first messaging, explicit cron with portable intent, bounded operational sessions, reversible legacy handling, targeted audit behavior, WhatsApp hardening, and the absence of any active `tools.profile: full` recommendation.

## 26.08.26-2

released: 2026-08-26
update-impact: review

### Structural Changes

- Made dependency-free operation explicit in `_Axis/README.md`: Git, Ollama, OpenClaw, `age`, POSIX shell access, Subagents, schedulers, and host messaging remain optional enhancements whose unavailable lanes preserve the canonical file workflow and unrelated core operations.
- Added relational supervision without a fourth Agent role, Project type, Setting, Flag, or relationship registry. [Practices > Supervision] infers recognized direct children from the nearest Axis ancestor, dispatches `^^help`, `^^list`, `^^status`, `^^inspect`, `^^message`, `^^start`, `^^stop`, `^^restart`, and `^^schedule`, and reserves supervisory authority to parent Main.
- Added `_Axis/Supervision/` as the twelfth Index-Detail family for WORM parent reports and material action records. The newest 30 remain active; automatic overflow and `^refresh` move older records unchanged to `_Axis/Archive/Supervision/`, while `^archive` supports an explicit smaller active window.
- Defined Supervisor Subagents as read-only General Subagents: they may observe and analyze direct children, but cannot write, message, control lifecycle, schedule, enter grandchildren or protected content, or exercise authority. Missing spawn/parallel support degrades to parent Main's serial inspection.
- Added Request-first Host acceleration: Claude cross-session messaging, Codex queues, OpenClaw session messages, and similar adapters may notify only after the canonical Request exists. No adapter is required or treated as authorization.
- Added targeted `^audit supervision` and `^audit wiki` modes alongside `^audit portability`; bare `^audit` and `^audit full` retain the complete audit.

### Project-State Migrations

- Add empty `_Axis/Supervision/` with `.gitkeep`. Preserve every existing local path and all child Projects; no registration or project classification is inferred or written.
- Add `_Axis/Archive/Supervision/` only on first overflow or archive. Preserve every Supervision record byte-for-byte and keep at most the newest 30 in the live directory.

### Retired Paths

### Verification

- The Dependency-Free Core regression contract verifies the optional-tool, no-Git Snapshot, manual Secrets transfer, no-scheduler, Dashboard fallback, Host Capability degradation, and portable Requests lanes; root `README.md` remains byte-identical to `_Axis/README.md` before Project Setup.
- The Supervision regression contract verifies direct-child discovery/no-grandchildren, authority and Supervisor Subagent restrictions, the nine `^^` commands, Request-before-notify delivery, lifecycle and schedule fallbacks, the 30-record archive bound, targeted audit modes, twelfth-family timestamp integrity, update preservation, release state reset, and complete worked examples in both README copies.

## 26.08.26

released: 2026-08-26
update-impact: review

### Structural Changes

- Clarified `^update` terminal behavior: the Command performs its own update-specific shutdown after verification, tells User not to run `^shutdown` separately, and ends with an explicit closed-window/new-session handoff.
- Changed production publication to expose only the newest orphan snapshot: each publish retires every prior GitHub Release and production tag, removes unexpected production branches, and verifies that only `main`, `project`, the new tag, and one release remain publicly referenced. This cannot erase existing clones, forks, third-party caches, or temporarily retained unreachable objects.
- Reorganized and reconciled the Axis User Manual, restored its tested download-verification and Dashboard field-guide contracts, and refreshed the Dashboard illustration with a versioned source under `_Axis/Resources/` and its public copy on `axisworkflow.ai`.
- Replaced the project license with FSL-1.1-MIT: Competing Use is prohibited until each version automatically converts to MIT two years after it is made available.
- Added `_Axis/CLA.md` and `_Axis/CONTRIBUTING.md`. Contributions require a recorded copyright-assignment agreement before acceptance; the assignment form includes fallback exclusive rights, patent terms, warranties, and a license back. Both files remain inside `_Axis/` so the project root stays limited to essential entry and display files.

### Project-State Migrations

- Replace the canonical `_Axis/LICENSE` with FSL-1.1-MIT and refresh a pristine pre-setup root `LICENSE`; preserve every User-owned project license after setup.
- Add `_Axis/CLA.md` and `_Axis/CONTRIBUTING.md`. These are Axis upstream contribution documents and do not govern User-created project content; do not create root contribution files. The CLA identifies Kenneth A. Younge personally as Owner, uses `kyounge@axisworkflow.ai` as his contact address, and selects the laws and courts of the Canton of Vaud, Switzerland.

### Retired Paths

### Verification

- The update preview discloses automatic shutdown before literal `UPDATE`; success releases the current lease and matching `session-id` before saying the Axis session is shut down and directing User to close the current window or terminal and start a new session.
- The canonical User Manual and root display copy are byte-identical, every internal link resolves, the Dashboard illustration source ships under `_Axis/Resources/`, and both manual copies use its canonical `axisworkflow.ai` asset URL.
- `_Axis/LICENSE` and root `LICENSE` are byte-identical FSL-1.1-MIT texts; `_Axis/CLA.md` is the sole CLA; `_Axis/CONTRIBUTING.md` blocks acceptance without a recorded agreement; no root `CLA.md` or `CONTRIBUTING.md` exists; the README makes the Competing Use restriction, two-year per-version MIT conversion, Swiss trademark origin, trademark separation, and third-party rights explicit.

## 26.08.24

released: 2026-08-24
update-impact: review

### Structural Changes

- Moved the canonical Axis User Manual from `_Axis/Resources/README.md` to `_Axis/README.md` and the canonical Axis MIT License from root `LICENSE` to `_Axis/LICENSE`. Fresh releases carry byte-identical root display copies for GitHub; Axis no longer supplies `.github/README.md` or any `.github/` content to User projects.
- Added `_Axis/Resources/Refresh-Project-README.md`. Project Setup transfers root `README.md` to User ownership and maintains one bounded public-safe summary block; `^status`, `^save`, and outgoing `^git` checkpoints refresh it without reading the Axis User Manual or overwriting User-authored content.
- Extended `^help`: `^help readme` lists User Manual sections, `^help {topic}` lazy-loads one relevant section, and bare `^help` advertises the stable `_Axis/README.md` location without loading it. Normal operation no longer depends on README content; Development Mode loads the complete manual.
- Moved the Wiki rationale into `_Axis/Practices/Wiki.md`, removing the last operational README dependency. The Axis User Manual is explanatory fallback only and cannot override Commands, Practices, Rules, or project files.

### Project-State Migrations

- Add `_Axis/README.md`, `_Axis/LICENSE`, and `_Axis/Resources/Refresh-Project-README.md`; retire `_Axis/Resources/README.md` after carrying its content into the new canonical manual.
- When `project-ready` is absent, write root `README.md` and `LICENSE` as byte-identical display copies of the new canonical Axis files. When `project-ready` is valid, preserve the User's root README, convert a pristine Axis display copy into a Project README with one `axis:project-summary` block, and refresh only that block. Preserve malformed or customized README content and surface any decision rather than overwriting it.
- When `project-ready` is valid, remove root `LICENSE` only if it is byte-identical to the base Axis license; preserve a missing or customized root license. Never choose a license for the User's project. When setup is not complete, retain the root Axis license display copy.
- Remove `.github/README.md` when it is byte-identical to the base Axis display copy. A customized `.github/README.md` is User content: preserve it and require a path-specific choice because it can override the root Project README on GitHub. Do not copy Axis development workflows into a project.

### Retired Paths

- `_Axis/Resources/README.md` - replaced by `_Axis/README.md`.
- `.github/README.md` - replaced before setup by root `README.md`; after setup the root file is the Project README.

### Verification

- A fresh release has no `.github/` directory, root `README.md` equals `_Axis/README.md`, and root `LICENSE` equals `_Axis/LICENSE`.
- Project Setup resolves README and license ownership before `project-ready`, and optional Git initialization occurs afterward so its first commit contains final project-owned root state.
- The Project README refresher is idempotent, preserves bytes outside exactly one marker pair, fails safely on malformed markers, and excludes Secrets, local paths, session state, infrastructure identifiers, and capability state.
- No production Session Start, Command, Practice, or Rule loads the Axis User Manual except explicit `^help` browsing or the bounded high-capability ambiguity fallback. Development Mode activation and continuation load the complete manual.
- The development repository retains only `.github/workflows/tests.yml` under `.github/`; release packaging rejects all `.github/` content.

## 26.08.23

released: 2026-08-23
update-impact: automatic

### Structural Changes

- Added `age` to the README Add-ons and expanded `^install` with one shared source/preview/approval/verification/rollback contract plus explicit `age` and `qmd` routes. Installation remains optional and User-approved; installing `age` alone never enables encrypted Secrets or creates a project identity.
- Made Git receipt preserve narrowly verified, noncolliding session-lifecycle WORM Logs through a strict fast-forward. This closes the desktop-laptop-desktop loop: the source computer's post-checkpoint `Shutdown by User` Log no longer forces User to discard audit evidence or reconcile histories when the laptop checkpoint returns.
- Added `_Axis/Commands/git.md` and expanded `_Axis/Practices/GIT.md` into one adaptive, ancestry-based synchronization protocol shared by `^git`, `^save`, and `^resume`. It initializes a safe local repository, offers an optional private GitHub remote, fetches before classifying, permits only linear fast-forward/push actions, and stops on divergence or substantive incoming conflicts.
- Made repository-backed `^save` automatically fetch, assess portability, seal configured Secrets, checkpoint, re-fetch, and push; made `^resume` fetch and fast-forward before reading the Snapshot, then receive Secrets and run full revalidation. Explicit handoff/shutdown/other-computer wording composes `^save` with `^shutdown`; routine save remains a nonterminal checkpoint.
- Made `^undo` history-preserving and remote-aware: confirmed recovery uses revert or a new restore commit and never reset-hard, history rewriting, or force-push.
- Added `_Axis/Resources/secrets-capsule.sh` as an optional privacy-safe `age` adapter. It keeps plaintext and its conflict binding ignored, tracks only `_Axis/Secrets/.recipient` plus `.capsule.age`, stores the private project identity outside the project, validates tree/archive safety, detects two-sided changes, and emits no secret name or value.
- Added the user-facing README `Portability` section with first-time setup, desktop-laptop-desktop, encrypted-Secrets, full-folder, offline, and conflict procedures.

### Project-State Migrations

- Add `_Axis/Commands/git.md` and `_Axis/Resources/secrets-capsule.sh`; merge the two exact Secrets exceptions into `.gitignore` and the capsule binary rule into `.gitattributes`. Preserve every existing ignore/attribute rule and all plaintext Secrets.
- Existing projects remain local-only until User invokes `^git` and accepts setup. Do not create a remote, install Git/`gh`/`age`, enable encryption, or move a private identity without User approval.
- Existing plaintext `_Axis/Secrets/` remains ignored. Encrypted transport is disabled unless `.recipient` and `.capsule.age` are deliberately initialized; when enabled, preserve the gitignored `.binding` and keep the private identity outside the project.

### Retired Paths

- None.

### Verification

- Official `age`/`age-keygen` v1.3.1 passed disposable initialization, ciphertext-opacity, first-receipt, rotation, repeated-receipt, missing-identity, two-sided-conflict, external-key-placement, and output-privacy checks through the shipped helper.
- Installer doctrine routes `^install age` deterministically, uses only the official package table, verifies both binaries with a non-secret temporary round trip, and retains the separate encrypted-Secrets enablement gate; README Add-ons names the same optional role.
- A remote-ahead source clone carrying only valid, untracked, collision-free Session Start and shutdown Logs fast-forwards without modifying those Logs; malformed, colliding, linked, or non-lifecycle local files still block receipt.
- A release contains `_Axis/Commands/git.md` and `_Axis/Resources/secrets-capsule.sh`; the Manifest, README command table, `.gitignore`, `.gitattributes`, and release leakage gate agree on them.
- Git fixtures cover no-repository setup, local-only checkpoint, equal/clean, local-ahead, remote-ahead fast-forward, remote race/rejection, substantive incoming conflict, and divergence without merge/rebase/stash/reset/force.
- Encrypted-Secrets fixtures cover initialization, seal, first-clone receive, repeated receive, local-only change, two-sided conflict, missing tool/identity, unsafe tree/archive rejection, rollback-guarded replacement, and output privacy.
- `^save`, `^resume`, and `^undo` preserve their record, portability, WORM, confirmation, and one-writer contracts while using the shared Git state machine.

## 26.08.20

released: 2026-08-20
update-impact: automatic

### Structural Changes

- Made Session Start hand its original triggering message back to the entry protocol after the readiness gate, where it is served exactly once. A first-turn Command now dispatches without repetition, while response-shape requests such as `reply exactly` apply only after Axis's mandatory startup outputs and greeting.
- Made each `^save` Event part of the saved checkpoint by writing it before the repository commit, restricted Snapshot references in User-facing save responses to timestamp IDs or project-root-relative paths, and required unknown interaction metadata whenever the host has not explicitly established interactive, headless, or channel operation.
- Clarified the Git-transfer audit boundary: `^save` commits the Snapshot and Save Event together, while the later `^shutdown` Log/Tracking tail is uncommitted operational evidence that may be absent from a Git clone without losing canonical project state.
- Retired DeepSeek-R1 from routine local-model benchmarking and installation recommendations after repeated high-latency negative evidence. Qwen3-VL remains the principal full-campaign model; Qwen3 8B receives focused reruns only for plausible routes; Gemma3 remains an installation fallback rather than a routine full-campaign target. Historical scorecards and reproducible recipes remain preserved.
- Accepted the refreshed 216-sample M4 comparison. Qwen3-VL passed all eligible clerical routes on the first attempt; Qwen3 8B gained an accepted but materially slower extraction route; Gemma3 stayed narrow; DeepSeek-R1's injection regression confirmed its retirement as negative evidence.

### Project-State Migrations

- None.

### Retired Paths

- None.

### Verification

- A fresh first-turn `^save` completes Session Start and dispatches the command once without asking User to repeat it; exact-output prompts still show mandatory startup output before the constrained application response.
- A successful repository-backed `^save` commits its Snapshot and Save Event together, reports no absolute local path, and records `interaction: unknown` unless a trusted host fact establishes a more specific mode.
- A Git clone of the saved commit can resume from canonical state without requiring a later uncommitted shutdown Event.
- Benchmark doctrine names one active full-campaign model, preserves retired negative evidence, and does not recommend DeepSeek-R1 for installation or routine retesting.
- The accepted aug20 comparison contains four complete 54-sample ledgers with matching Ollama 0.32.5, Q4_K_M, 8192-context metadata and full class/paraphrase/seed coverage.

## 26.08.19

released: 2026-08-19
update-impact: review

### Structural Changes

- Added `_Axis/CHANGELOG.md` as the canonical installed-version and forward-migration record.
- Added `_Axis/Commands/update.md` as the model-mediated, three-way updater.
- Added the installed Axis version to the Dashboard Configuration list, sourced from this file through the Dashboard's narrow read allowlist.
- Reworked the Dashboard into a conditional untitled findings card followed by coordinated faded Configuration, Mindset, and Agents cards; omitted findings entirely when none exist, moved operational notices and recent downgrade evidence into self-contained bullets without a redundant aggregate count, clarified that Reload never invokes an Agent, relocated Metrics to the header, and reduced the footer to timestamp and Reload. The working area now places a tall white Project card on the left beside distinct Ideas, Notes, Logs, Reminders, User Follow Up, and Agent Activity cards. The former Dashboard Recent Developments and combined Current Activity cards are retired; the always-visible Status Report owns the richer analysis. Plan, Tasks, and Status Report remain full-width, with only the two major section rules retained. Configuration labels and local-platform states are normalized and regrouped, and every displayed field is documented in the README.
- Renamed the Dashboard's Cloud-Safe row, clarified its concurrency meaning and the `N/A`/`Unknown` Local Platform distinction, reduced content emphasis while strengthening card titles, standardized the Plan hint, and renamed the bottom report card to Status Report.
- Moved partial-refresh indication out of Dashboard Status and into the footer as `Partial Refresh on: {timestamp}`, while retaining each card's local fallback and clearing the prefix after the next complete refresh.
- Replaced the Dashboard's floating Mermaid CDN executable with the exact vendored Mermaid 11.16.1 bundle, pinned its SHA-256 in the release contract, restricted scripts to the same origin, and retained the underlying diagram link as the failure fallback.
- Restored the user-facing installer to a one-click download-and-unzip flow. Each publication now attaches `axis-project.zip` plus a detached `axis-project.zip.sha256`; the README keeps verification optional and explains the sidecar without embedding a self-invalidating archive hash.
- Integrated update publication, documentation, manifest, session-exit, and regression contracts needed by those two primary files.
- Added `_Axis/Followups/`, `_Axis/Practices/Followups.md`, and `^followups` as the tenth Index-Detail record family: a portable User-owned queue for questions, decisions, and actions only User can complete. Integrated bounded startup and resume surfacing, Status Reports, Snapshots, Task blocking, audit/refresh, archiving, delegation, Dashboard display, update preservation, and release reset behavior.
- Added always-on portability: every `^save` now performs a bounded local assessment and writes one Snapshot Continuity block; every `^resume` revalidates it against the current environment. Added `_Axis/Practices/Portability.md`, tracked `_Axis/ENVIRONMENT.md`, five transfer modes, `atomic`/`serialized`/`unknown` storage profiles, narrow `.gitattributes`, compatibility tiers, and honest public claims.
- Added the optional, non-authoritative environment signature: one documented external `~/.axis/instance-id` plus gitignored `_Axis/Flags/environment-binding`. It detects many computer/profile, harness, interaction, storage, clone, and copy changes without recording hardware/personal identifiers or replacing resume validation.
- Added `_Axis/Reminders/`, the on-demand `_Axis/Archive/Reminders/` destination, `_Axis/Practices/Reminders.md`, and `^reminders` as the eleventh Index-Detail record family. Version 1 is portable, checkpoint-driven Markdown with exact UTC due times, target lifecycle, deterministic surfacing, a per-session `reminder-check`, Dashboard display, and no scheduler/plugin/real-time-delivery claim.
- Added durable Task `updated:` timestamps, using `Unknown` only for migrated recency that cannot be established canonically; Status, refresh, audit, and Dashboard no longer use Task-detail `mtime` as portable freshness.
- Added terminal completeness markers for the entry protocol and compiled Starting Context, with fail-closed recovery/fallback behavior, and extended packaging and cross-userland checks for the new portability surfaces.
- Hardened the portability pass after independent review: Dashboard Snapshot/Status freshness now uses durable UTC filenames; future-clock Reminder checkpoints force a full check; sensitive session/signature Flags have explicit server-denial regressions; raw environment IDs are forbidden from Tracking; and Reminder temporary siblings have a hidden non-record filename contract.
- Added the persistent `Storage Policy` safety ceiling (`auto` or `single-writer`), with no force-atomic value. Capability detection, locking, parallel delegation, Wiki batches, Reminders, updates, Dashboard Cloud-Safe, Subproject access, Status, audit, and resume now require the policy/profile conjunction.
- Expanded `_Axis/ENVIRONMENT.md` into a declaration-driven non-portable infrastructure inventory for tools, credentials, authentication, services, schedulers, environment variables, and host integrations. Every `^save`, `^resume`, and environment-change boot now uses fixed privacy-safe revalidation statuses plus bounded category-only discovery; Snapshots carry the source status, and receivers name logical restoration work without exposing secrets or host bindings.
- Strengthened changed-environment startup to compare the latest Continuity version, canonical record IDs, transfer omissions, and infrastructure delta without running a full `^resume`. Added behavioral portability fixtures for Unicode NFC/case-fold collisions, Windows-reserved/trailing names, long paths, drive/backslash forms, symbolic links, hard links, infrastructure restoration, and discovery privacy.
- Added conditional Dashboard Status notices for `absent` and `unverified` infrastructure from the newest Snapshot's bounded Continuity summary. Healthy declarations stay invisible, and malformed summaries fail to one generic notice without exposing their contents.
- Reordered the Dashboard header metrics to `{count} {label}` and renamed the saved-report metric to `Status Reports`.
- Made the Dashboard's final Status Report card persistent; an empty Status directory now renders the actionable `No Status Report yet - use ^status.` state instead of removing the section.

### Project-State Migrations

- Add an empty committed `_Axis/Followups/` directory. Preserve every existing Task and its status, including **Blocked**; do not infer historical Follow-Ups, rewrite WORM records, or introduce a task-dependency graph. During the update's required review phase, offer one bounded review of current Blocked Tasks and unresolved project prose; seed only the specific User-owned actions User chooses, and seed none when User declines.
- Add the empty committed `_Axis/Reminders/` family, create `_Axis/Archive/Reminders/` on its first terminal move, and add the Portability/Reminders Practices, `^reminders`, the infrastructure-table `_Axis/ENVIRONMENT.md`, and `.gitattributes`. Preserve every existing record and never infer a Reminder from dates or prose; optionally offer a bounded User-reviewed candidate scan. If a locally customized pre-inventory Environment file exists, preserve it and migrate each dependency into a reviewed logical infrastructure row without copying any host path, account, secret name/value, or current-health claim.
- Add `Project Time Zone` as `Unknown` unless existing canonical project state establishes an IANA zone. Add `Storage Policy=auto` only when the Setting is absent; preserve an existing exact `single-writer`, never synthesize a force-atomic value, and require a fresh storage probe before any atomic claim. Add `updated:` to every existing Task from an exact canonical timestamp only; otherwise write `Unknown`, never filesystem `mtime`.
- Add gitignored `host-storage`, `reminder-check`, and `environment-binding` Flags. The first eligible Session Start may create the non-secret external `~/.axis/instance-id`; failure to access it is non-blocking. Preserve Settings values, ENVIRONMENT declarations, Dashboard customizations, Wiki, Secrets, Subprojects, and all project content.

### Retired Paths

- None.

### Verification

- `current-version`, the README version sentence and badge, the release tag, and the newest published changelog section agree exactly at publication.
- A release contains both `_Axis/CHANGELOG.md` and `_Axis/Commands/update.md`.
- The Dashboard reports the full installed version, including any same-day suffix.
- A successful update preserves project-owned state and ends the old Main session before the new Workflow boots.
- The Dashboard always shows the full-width Status Report card without a dedicated preceding divider; an empty Status directory renders the exact actionable empty state and a populated directory shows the newest synopsis.
- A release contains the Follow-Up folder, Practice, and Command; clean release state resets `_Axis/Followups/` to `.gitkeep`; update preservation includes live and archived Follow-Ups; Task statuses remain `Active`, `Blocked`, `Completed`, and `Cancelled` with no `needs:` field.
- The Dashboard server exposes live Follow-Ups but not archived records, and its User Follow Up card renders the healthy empty state plus ordered open subjects, due state, and record links.
- Every production path and empty state directory for Portability and Reminders ships; Manifest, Practices, Commands, README, Dashboard allowlists, update preservation, and release contracts agree.
- Every `^save` writes exactly one Snapshot with a valid `Ready`, `Degraded`, or `Unverified` Continuity block; every `^resume` always revalidates it without a routine receipt Log or lease destruction.
- Reminder fixtures cover valid/invalid schemas, UTC ordering, unknown and corrected-fast clocks, duplicate due times, stable identity on reschedule, terminal placement, target movement, temporary-file exclusion, and per-session surfacing deduplication. Agent-side and Dashboard tests consume the same versioned due-state vectors. No canonical Reminder contains host binding, scheduler, command-execution, or credential fields.
- Entry files remain byte-identical and below 18,500 bytes with `<!-- axis:end -->` terminal; Starting Context ends with `<!-- axis:starting-context:end -->`; Axis-owned structured text is LF and BOM-free.
- The Dashboard's separate Reminders and Agent Activity cards agree with canonical UTC/Task `updated:` semantics; server exposure remains live-only and excludes archived Reminders.
- `Storage Policy=single-writer` cannot coexist operationally with `host-storage=atomic`, acquire an ordinary lock, run parallel writers, or pass `^update`; missing/malformed policy also fails toward serialization.
- Environment declarations accept only the exact Kind/Need domains and fixed non-executable revalidation tokens; source-present/current-absent restoration deltas name only logical infrastructure. Bounded discovery emits category/count data only and never a secret/config filename, value, account, local path, raw environment-signature ID, or scheduler job ID.
- Dashboard infrastructure notices parse only the exact bounded Continuity serialization, display only absent/unverified logical names, suppress healthy names, and never request Environment or Secrets content.
- Portable path fixtures detect NFC/case-fold collisions, absolute/drive/backslash forms, reserved/trailing/control/long names, broken/escaping symbolic links, and hard links on both native and clean Linux userlands.
