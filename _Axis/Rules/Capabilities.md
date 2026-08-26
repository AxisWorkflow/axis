# Capabilities
> **Purpose:** Main Agent eligibility, the Host Capability Flags, and how features degrade when one is missing.


**Main Agent eligibility is a prerequisite, not a Capability.** Axis supports only a standard-capability model as Main Agent. The entry-point protocol checks this from system context or explicit host configuration before printing either startup output or touching project state; when standard capability is not established, it stops and tells User to select an eligible model. Small models remain supported as bounded Subagents. Organizations needing a hard technical guarantee enforce an approved-model policy in the host or launcher.

At Session Start, [Start-Session] follows [Detect-Capabilities] to record the running model and detect each Host Capability below in its own Flag (value on Line 1, UTC timestamp on Line 2). Features degrade gracefully when a Host Capability is missing; log every skip so User can audit what dropped.

- `model` - the running model's name as reported by the host; informational (the Dashboard shows it and resolves `same-as-host` with it); `unknown` when not exposed.
- `host-spawn` - the host provides a tool to spawn Subagents; set to `no` on a failed spawn (log the downgrade, continue serially).
- `host-parallel` - multiple Subagents can run at the same time.
- `host-shell` - shell commands run in a POSIX-like shell (Windows cmd/PowerShell = `no`).
- `host-local-llm` - a local model endpoint is reachable from the working environment; re-probed by `^install`. The Flag body carries the working base URL on Line 3.
- `host-cloud-sync` - the project root appears to live in a cloud-synced folder; `yes` disables parallel writes (see [Lock-File > Prerequisites]).
- `host-storage` - current location's write profile: `atomic`, `serialized`, or `unknown`; only `atomic` together with exact `Storage Policy=auto` permits parallel writers and the lock protocol.

The detection procedure (model recording, shell and endpoint probes, cloud-sync heuristics) lives in [Detect-Capabilities] - lazy-load it only when detecting; if User corrects a detected value in chat, update the Flag and log the correction.

Axis features require the following Host Capabilities:

<!-- BEGIN GENERATED: capability-contract -->
| Feature | Needs Host |
| --- | --- |
| Cross-Examination (`^cx`) | `host-spawn` |
| Parallel Subagents - any protocol spawning 2+ at once | `host-spawn` + `host-parallel` + `host-storage` = `atomic` |
| Multi-hypothesis exploration (**Skepticism** = 2) | `host-spawn` |
| Local Subagents | `host-local-llm` |
<!-- END GENERATED: capability-contract -->

**Concurrency is gated once, not per feature.** Any protocol that would run more than one Subagent at the same time - batch Wiki ingest, multi-hypothesis exploration, and anything a later feature adds - may do so only when `host-parallel` is `yes`, `host-storage` is `atomic`, and `Storage Policy` is exact `auto`. Otherwise spawn serially, blocking for each return, and log the constraint. Features inherit this gate; they do not restate it.

**Model choice still constrains Subagents.** Local or otherwise small models are suitable only for bounded work whose output Main can validate against an explicit contract. They never perform Wiki ingest, handle secrets, or make security-sensitive trust decisions. A Wiki Subagent processing untrusted sources must use a standard-capability host model; when that cannot be established, Main Agent ingests serially instead. [Practices > Delegation] applies these boundaries when selecting a route and validator.

When a required Host Capability is missing: perform the closest safe degraded alternative (e.g., Main works serially instead of spawning), Log it under [Practices > Logs > Capability Downgrades], and notify User when it materially affects results.
