# Portability
> **Purpose:** Preserve truthful project continuity across models, hosts, computers, storage arrangements, and transfer methods.

Axis portability is canonical Markdown plus explicit revalidation. It does not promise identical host features, transport installed tools or authentication, reconcile simultaneous replicas, or preserve unsaved conversation state.

## State Classes

- **Canonical state** is authoritative project content inside the project folder and intended to survive supported transfers.
- **Host-local state** describes the current machine, harness, or session and is re-detected rather than transported as truth.
- **Portable intent** is durable Markdown describing what should happen when a particular host mechanism is absent.
- **External mirror** is an optional host job or presentation layer. It can accelerate delivery but never replaces the Axis record.

`_Axis/ENVIRONMENT.md` declares logical project infrastructure and fallbacks. It is tracked and portable. Current paths, bindings, accounts, health, and credential values never belong there.

## Infrastructure Inventory

The Environment file is the declaration-driven source of truth for non-portable prerequisites. Each real row has exactly these columns: `Kind`, `Infrastructure`, `Purpose / Consumer`, `Need`, `Safe Revalidation`, `Portable Fallback`, and `Re-establish`.

- `Kind` is exactly `tool`, `credential`, `authentication`, `service`, `scheduler`, `environment`, `host-integration`, or `other`.
- `Infrastructure` is a short, non-secret logical name a human can recognize: 1-60 characters with no control character, comma, equals sign, brace, slash, or backslash. It never names an account, machine, credential file, job ID, or local path.
- `Need` is `required` or `optional`. Optional means the project can continue without that item; it does not mean a currently active consumer should fail silently.
- `Safe Revalidation` is data, never a command. It is exactly one of: `tool:{portable executable name}`; `env:{variable name}`; `loopback:{literal http://localhost, http://127.0.0.1, or http://[::1] URL}`; `capability:{boolean host-* Flag}`; or `manual`. Command arguments, shell syntax, paths, redirects, remote URLs, and credential values are invalid here.
- `Portable Fallback` is a short non-secret behavior, or `None` when the consumer must wait.
- `Re-establish` is `Ask User`, one safe project-root-relative documentation/Note path, or a public HTTPS documentation URL with no user information, query, or fragment. It is guidance, never executable content.

Revalidation produces only `present`, `absent`, `unverified`, or `not-applicable` for each declared logical name:

- `present` requires a safe positive observation from the current environment.
- `absent` requires a safe negative observation. A required absent item blocks its consumer until it is restored or its declared fallback is used.
- `unverified` means Axis cannot decide safely. It is never silently upgraded to present.
- `not-applicable` is allowed only for an optional item whose named consumer is demonstrably inactive.

Run the fixed checks without exposing their evidence: an executable check discards the resolved path and all output; an environment check tests only whether the declared variable is nonempty and never reads or prints its value; a loopback URL contains no user information, query, fragment, percent encoding, or whitespace, and its probe has a two-second maximum, follows no redirects, sends no credential, and discards headers and body; a Capability check uses [Practices > Flags > Reading Flags]; and `manual` remains unverified unless current trusted host context or User explicitly confirms only the status. Never contact a remote service merely to turn `unverified` into `present`, and never infer authentication from an installed tool or config file.

Every save, resume, and changed-environment validation supplements declarations with one **bounded discovery** pass. It may inspect only the project root and one ordinary Project-Subfolder level, active Note text, already-visible host tool context, and whether `_Axis/Secrets/` has any plaintext non-placeholder entry. That output-suppressed predicate excludes `.gitkeep`, `.recipient`, `.capsule.age`, and `.binding`; public/ciphertext transport metadata alone is not credential material. Exclude `_Axis/` except that predicate and active Notes, plus Wiki, `_Temp/`, `_Trash/`, recognized Subprojects, dot-directory contents, vendor/cache/build trees, and binary contents. Look only for a fixed small set of tool manifests, credential/config filename patterns, host-integration roots, automation/workflow roots, and schedule words. Match an indicator to a declaration when unambiguous; otherwise report only category and count (or the single fact that credential material exists), never the indicator filename, secret name/value, account, local path, host job ID, or raw host inventory. Bounded discovery proposes a missing declaration; it never installs, authenticates, schedules, mutates, or grants a stronger status.

The fixed discovery vocabulary is deliberately small:

- `tool-manifest`: `package.json`, `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `pyproject.toml`, `requirements.txt`, `Pipfile`, `Gemfile`, `Cargo.toml`, `go.mod`, `Dockerfile`, `compose.yaml`, `compose.yml`, or `Makefile`;
- `credential-config`: root/one-level `.env` or `.env.*`, `.netrc`, `.npmrc`, `.pypirc`, or `credentials*.json` by name only;
- `host-integration`: existence only of root `.claude`, `.codex`, `.cursor`, `.gemini`, or `.vscode`;
- `host-automation`: existence only of `.github/workflows`, `.circleci`, `.gitlab-ci.yml`, `Jenkinsfile`, or `azure-pipelines.yml`;
- `schedule-intent`: at most 250 active Notes containing `cron`, `launchd`, `Task Scheduler`, `scheduled task`, or `schedule`; and
- `credential-material`: one boolean for any non-placeholder entry under `_Axis/Secrets/`.

Inspect at most 1,000 candidate filesystem entries. Hitting a bound adds `scan-truncated=1` and makes discovery `Unverified`; it never widens the scan. A false-positive indicator is a prompt to review/declaration, not evidence that infrastructure exists.

Never enumerate `PATH`, environment variables, a keychain, browser profiles, home-directory configs, global scheduler state, services, or accounts. A declared scheduler may be checked only through an already-authorized host interface for that exact logical job; otherwise it is `unverified`. Axis can therefore identify declared restoration work and useful local signals, not prove that every external dependency has been found.

## Transfer Modes

1. **Same-folder host switch:** another compatible harness opens the same authoritative folder. Canonical state stays in place; host facts are revalidated.
2. **Full-folder transfer:** a copy or restore carries project files, but not installed tools, keychains, authentication, or external jobs.
3. **Git clone to a new sole writer:** tracked state at the selected commit travels. Plaintext Secrets travel only when optional encrypted Secrets transport is configured, current, and the receiver has its external identity; otherwise they remain omitted. Wiki content, machine/session Flags, Markers, Tracking, scratch, Trash, and ignored Subprojects do not travel. The last successful repository-backed `^save` includes its Snapshot, Save Event, and current encrypted capsule when enabled, then pushes when the upstream remains linear. A later uncommitted `^shutdown` Event is post-checkpoint operational evidence and may be absent without implying canonical loss.
4. **Shared authoritative filesystem:** several systems mount one authoritative copy. Concurrency is permitted only to the extent the verified storage profile supports it.
5. **Independent writable replicas:** cloud-sync replicas or multiple live clones may diverge. Axis provides no automatic multi-writer reconciliation; use one writer, synchronize or reconcile completely, then transfer writer responsibility.

A full-folder move or Git handoff is safe only after the source Main has completed `^shutdown`; an ordinary mid-session `^save` does not release its lease. Git remotes do not transport Markers and are not distributed locks, so the receiving clone cannot prove the source Agent stopped.

## Storage Profile

Read `Storage Policy` before using or detecting `host-storage`. Exact `auto` permits detection below. Exact `single-writer`, a missing value, or a malformed value forces `host-storage=serialized`; missing or malformed policy also makes the portability result `Unverified`. The policy is a persistent one-way safety ceiling: it can prohibit concurrency but can never force `atomic`.

Under `Storage Policy=auto`, `host-storage` is re-detected each Session:

- `atomic` - same-directory create, replace, readback, and `mtime` behavior required by Axis passed locally and no replica/cloud-sync hazard was detected.
- `serialized` - only one writer may act at a time; readback and explicit writer transfer are required.
- `unknown` - the behavior cannot be established; operate as `serialized` and call the result unverified.

A one-process probe cannot prove distributed atomicity. `serialized` is a User/Agent operating convention, not mechanically enforced mutual exclusion. Lock files do not upgrade an unverified filesystem into a distributed lock service. Only the conjunction of exact `Storage Policy=auto` and valid `host-storage=atomic` permits the ordinary lock protocol or parallel writers.

When User says a location should never be treated as concurrently writable, persist `Storage Policy=single-writer`, rewrite `host-storage=serialized`, and Log the correction. Returning the policy to `auto` removes the ceiling but does not grant atomicity; a fresh successful detection must do that. No `force-atomic` value exists.

## Path and Link Portability

The portable path common subset is project-root-relative, forward-slash separated, and Unicode NFC. Flag rather than silently rename:

- absolute, home-relative, drive-prefixed, backslash-containing, empty, `.`/`..`, control-character, or NUL-bearing paths;
- components ending in a space or period, or matching Windows device names `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, or `LPT1`-`LPT9`, case-insensitively and even with an extension;
- any two paths that collide after per-component NFC normalization plus Unicode case-folding, including composed/decomposed and case-only pairs;
- a component over 240 UTF-8 bytes or a project-relative path over 240 Unicode code points; and
- every broken link, every link that escapes the project, and every required symbolic or hard link whose semantics may not survive the intended transfer.

These are portability findings, not authority to rename User content. Traverse no symbolic link during a scan. Exact Reminder targets and other structured path fields apply their stricter owning grammar in addition to this common subset.

## Always-On Save Assessment

Every `^save` runs all safe, locally observable checks before it writes the one ordinary Snapshot:

1. validate the current lease, locks, in-flight update state, Requests, and replica/storage hazards;
2. validate portability-relevant record schemas, links, timestamps, Reminder targets, and generated contracts;
3. validate `_Axis/ENVIRONMENT.md`, revalidate every declaration into the exact infrastructure status vocabulary, run bounded discovery, and identify source-side infrastructure that a receiving environment may need to restore;
4. check Workflow-relevant absolute paths, required symlinks or hard links, broken paths, case collisions/mismatches, sync-conflict copies, platform-reserved/control names, UTF-8 BOM, and CRLF in Axis structured text;
5. inventory, by bounded counts and categories, what same-folder use, a full copy, and a Git clone carry or omit; when encrypted Secrets transport is enabled, validate its tool/identity/capsule state through [Practices > GIT] without reading a name or value; and
6. note known external host state that will not travel, without reading Secrets content or mutating an external system.

Exclude regenerable vendor, cache, build, `_Temp/`, and nested Subproject trees from broad scans. Prefer deterministic anomaly-only commands whose output is empty on success; never load an unbounded file inventory into model context.

Classify the result:

- `Ready` - all required observable invariants passed and every active required infrastructure item is present.
- `Degraded` - a required or active item is absent, source-present infrastructure needs restoration, or continuity remains usable only through a declared fallback or sole-writer constraint, with concrete findings recorded.
- `Unverified` - one or more relevant facts could not be observed safely.

When known degradation and unknowns coexist, report `Degraded` and name the unverified count separately. An unavailable optional observation never prevents the Snapshot. Existing hard safety conditions still block, including a lost/contended lease, unapproved live Subagents, or canonical corruption that prevents a trustworthy checkpoint.

## Continuity Block

Every Snapshot written by `^save` contains exactly one compact `## Continuity` block:

```
## Continuity

portability-checked: {current UTC timestamp}
portability: {Ready|Degraded|Unverified}
axis-version: {current-version from _Axis/CHANGELOG.md or Unknown}
source-session: {Session ID}
harness: {normalized harness class or unknown}
interaction: {interactive|headless|channel|unknown}
storage-policy: {auto|single-writer|invalid}
storage: {atomic|serialized|unknown}
capabilities: {bounded summary of model and host-* facts}
tasks: {exact Active and Blocked Task IDs, or None}
follow-ups: {exact open Follow-Up IDs, or None}
reminders: {exact open Reminder IDs, or None}
infrastructure: {Ready|Degraded|Unverified}; declared={None or Name=present|absent|unverified|not-applicable entries, up to 20, then +N more}; undeclared-signals={bounded category counts or None}
transfer-omissions: {bounded counts/categories, including plaintext Secrets as encrypted-capsule|omitted when applicable, or None}
findings: {concise findings, or None}
```

Set `harness` and `interaction` only from explicit trusted host/system facts. A terminal TUI established as interactive is `interactive`; a noninteractive invocation established by the host is `headless`; a messaging transport is `channel`. A served User message, terminal availability, or the ability to call tools does not by itself prove interaction mode. When the mode is not explicit, write `unknown` rather than guessing.

Serialize each declaration as its exact logical name, `=`, and exact status, separated by comma-space in Environment-table order; for example, `declared={GitHub Authentication=absent, Local Preview Service=unverified}`. Use `declared={None}` when no real declaration exists. After 20 entries append one exact `+N more` token for the undisplayed count. The Dashboard may display only `absent` and `unverified` logical names from this bounded, privacy-safe field; it never reads Environment or Secrets content for infrastructure notices.

The Axis version and source Session are historical provenance, not proof that the receiving state is still current. Never include the external environment instance ID.

## Always-On Resume Revalidation

Every `^resume`, whether or not a move is suspected:

1. after [Practices > GIT] performs any eligible strict fast-forward and encrypted-capsule receive, reads the latest Continuity block;
2. compares its Axis version, storage policy/profile, harness/interaction class, Capability summary, infrastructure declarations/statuses, canonical IDs, omissions, and findings with current state;
3. reuses Capability probes freshly validated at Session Start and reruns only stale or newly required probes;
4. revalidates schemas, links, Reminder targets, paths, case, line endings, conflict copies, and visible transfer omissions;
5. distinguishes unavailable from absent-by-design state for Git clones, full copies, same-folder switches, and replicas; and
6. reports `Ready`, `Degraded`, or `Unverified` before continuing the normal resume summary, and names every declared item that changed from source `present` to current `absent` or `unverified`, plus any currently required absent item, with its fallback and re-establishment reference.

Resume is read-mostly. Its only routine mutations are a configured strict Git fast-forward and verified encrypted-capsule receive; neither writes a receipt Log that would immediately dirty the received checkpoint. It never clears its own valid lease or a possibly live foreign Marker. Log only a new material downgrade, an approved correction, or a mutation owned by another protocol. With no shell, inspect the bounded state reachable through host file tools and mark the inaccessible remainder `Unverified`.

## Optional Environment Signature

The signature is a non-authoritative change-detection hint, never a machine identity, credential, lease, or portability prerequisite.

- The Axis-owned external file is `~/.axis/instance-id`. When host access permits, lazily create it once as one standard Axis timestamp, read it back, and never rotate it automatically.
- The project-local, gitignored `_Axis/Flags/environment-binding` stores that opaque ID on Line 1, then `harness:`, `os:`, `interaction:`, `storage:`, and `verified:` lines. Values are normalized, non-secret facts; `verified:` is an exact UTC timestamp.
- Compare the old binding before rewriting it. Missing/malformed state, an ID mismatch, or changed harness, OS, interaction, or storage triggers the **Environment-Change Validation** below.
- After that validation completes without a hard safety failure, update and read back the binding. Mention the change once with the greeting only when it changed or the validation is degraded/unverified.
- If the external file or binding cannot be accessed, continue without it. Missing or matching state never skips an explicit `^resume` revalidation.

Never use a vendor directory such as `.claude/`, `.codex/`, or `.gemini/`. Never place the raw ID in tracked state, a Snapshot, Log, Tracking line, Dashboard, or visible response. Store no hostname, username, account, serial number, MAC address, or absolute home path. Deleting `~/.axis/instance-id` intentionally resets the local hint; the next eligible project access creates a new ID and treats every old binding as an environment change.

### Environment-Change Validation

This is deliberately smaller than `^resume`: do not sweep queues or propose work during boot.

1. verify the current Main lease and absence of an unresolved independent-replica conflict;
2. compare the current storage, harness, OS, and interaction class with the old binding;
3. read the latest Snapshot Continuity block and compare its Axis version, exact Active/Blocked Task IDs, open Follow-Up and Reminder IDs, transfer omissions, infrastructure declarations, and infrastructure source statuses with current bounded metadata; expected Session-ID change alone is not a finding;
4. read `_Axis/ENVIRONMENT.md`, revalidate every declared infrastructure item without remote network, authentication, or Secrets-content access, and run the bounded discovery pass;
5. scan Axis-owned structured paths for case/NFC collisions, conflict copies, BOM/CRLF, broken required links, unsafe common-subset names, and malformed record names; and
6. classify `Ready`, `Degraded`, or `Unverified`, queueing one concise changed-environment notice that names only material continuity deltas and infrastructure to re-establish.

This delta check reads bounded metadata only: it does not load Snapshot narrative, recent Logs, queue bodies, Notes beyond the discovery match, or propose project work. Missing or malformed Continuity state becomes `Unverified`; it never suppresses startup or pretends that a full `^resume` occurred.

## Compatibility Claims

- **Rehearsed:** the exact host/model family passed the current disposable-board lifecycle battery.
- **Mechanically compatible:** prerequisites and deterministic fixtures pass, without a complete current live campaign.
- **Unverified:** evidence does not support a stronger claim.

The defensible public claim is: every successful `^save` creates a portability-assessed checkpoint, and every `^resume` automatically revalidates that checkpoint against the current environment.
