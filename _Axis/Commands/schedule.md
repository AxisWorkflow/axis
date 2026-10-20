# ^schedule
> **Purpose:** Create, inspect and control portable schedules.

1. Verify your own lease and apply the Command role gate. Support create/list/show/pause/resume/retire/due. Load [Practices > Scheduling] and [Practices > Coordination]. List/show and occurrence preview are read-only. `due` is Main-only: within active authority it can admit a deduplicated Job, but never launch workers. Main previews an exact definition before activation; require authority and explicit placement. Persist revisions before changing the current view. Due evaluation proposes occurrences; it cannot grant execution authority. Use the typed helper or manual resolved-occurrence route. Never install a host trigger, send externally or broaden child authority merely because a definition exists.

2. Report only useful state, outcomes and blockers. Log any state change under [Practices > Logs]; read-only inspection writes nothing. STOP.
