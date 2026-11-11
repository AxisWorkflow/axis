# Budget
> **Purpose:** How the Budget Setting steers discretionary spend, and the gates it cannot override.


## Budget limits and extensions

If you hit a budget constraint or deadline, preserve progress and ask for an extension rather than just failing. The only standing time exception is pre-assessed completion grace under [Practices > FaultTolerance]; spending caps, hard deadlines and expiring mandates remain strict.

**Kinds of limit.** State the kind when setting a limit; distinguish real bounds from planning figures when applying it.

- **Hard bound:** authorized spending, a User-agreed work window, mandate or lease expiry, enforced resource capacity, or a deadline explicitly marked hard. Only the authority that owns it may extend it. Preserve a checkpoint before it and hold only the affected work.
- **Deadline:** another agreed time limit. Apply only the existing pre-assessed completion grace; otherwise ask for an extension.
- **Target:** an advisory phase time, duration, count or other planning figure inside the actual bounds. A miss calls for replanning and reporting while useful work continues, not a new stop condition.
- **Forecast:** a prediction. Revise it when the expected result changes materially.

Infer the kind from the actual agreement, not the agent's preference. Treat an ambiguous agreed time limit as a deadline. Reserve time within real bounds for saving and reporting; a reserve never extends them. No label changes a scope, authority, integrity or acceptance requirement.

Preserve completed work, current usage, pending actions and uncertain effects. Pause the affected execution and ask once for the additional time or spending needed, explaining what remains. Keep the Task resumable while awaiting the answer; a budget hold alone is not failure, cancellation or completion. Carry the same request forward instead of opening duplicate approval loops.

A tool wait timeout ends that wait; it is not an additional User budget. Complete acceptance, saving and finalization already covered by the current grant. If a technical mandate accidentally prevents those steps, reconcile it under that existing authority; ask only when a real extension or unresolved decision is needed. Do not backdate events or bypass lease, integrity, Secrets or spending controls.

When User authorizes continuation, resume from retained work, record the renewed scope and limits, and preserve cumulative usage. Use a new linked mandate when an immutable expired one cannot be renewed safely. Preserve failed attempt evidence without treating it as failure of the whole Task. Continue unrelated authorized work while only one operation is held.

Budget ([Settings > Budget], a Mindset Setting on the -2..+2 scale) steers discretionary spending of time, tokens, and compute. Two rules govern it:

- **Precedence:** a specific Setting that names a decision always beats Budget's general pull. If **CX Frequency** is high on a Frugal Budget, CX still runs high; Budget governs only the decisions no specific Setting names.
- **Steering, not metering:** Budget cannot see or cap actual spend (Axis has no portable view of the User's bill or token count) - it shifts defaults and enforces the hard gates below.

The following discretionary decisions consult Budget. The numeric gates are hard rules; the rest compile into [Mindset] as disposition. Levels group as Frugal/Lean (-2/-1), Standard (0), Flexible/Unconstrained (+1/+2).

| Decision | Frugal / Lean (-2/-1) | Standard (0) | Flexible / Unconstrained (+1/+2) |
| --- | --- | --- | --- |
| Optional Subagents (non-`^cx`) | work serially; do not spawn | spawn when serial is clearly worse | spawn whenever it helps |
| Default Subagent model | prefer a local or lower-cost model when its aptitude fits the task | host's own model (`same-as-host`) | strongest available / `same-as-host` |
| Snapshot read window at Session Start (entries) | 3 | 5 | 10 |
| Snapshot length | tight milestone summary | normal summary | fuller record |
| Multi-hypothesis exploration | one hypothesis, commit | second only if the first is shaky | explore in parallel |
| Log verbosity | folds into [Settings > Transparency] | folds into Transparency | folds into Transparency |

A required Capability always wins: if `host-spawn` is `no`, no Budget level spawns Subagents (see [Rules > Capabilities]).
