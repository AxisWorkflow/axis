# ^cx
> **Purpose:** Launch a Cross-Examination.

1. Determine the model to use from [Settings > CX Model].
	- If the value is `same-as-host`: use the host's own model and GOTO step 3.

2. Confirm you can reach the named CX Model, and read `host-spawn` under [Practices > Flags > Reading Flags].
	- If reachable: GOTO step 3.
	- If unreachable and the `host-spawn` Flag is `yes`: use the host's own model instead - Log the substitution, note it in the CX report header, and GOTO step 3.
	- If unreachable and `host-spawn` is anything else: inform User, suggest changing [Settings > CX Model] or running `^install`, and offer a degraded in-context review (Main simulating the CX role, per [Start-Subagent > Restrictions & Fallback]). If User accepts: perform it per [Practices > CX > Degraded Review] - one report into `_Axis/CX/`, Line 1 labelled `CX: {topic} (in-context, non-isolated)`. If User declines: Log the outcome and STOP.

3. Read `host-spawn` under [Practices > Flags > Reading Flags].
	- If `yes`: follow `_Axis/Resources/Start-Subagent.md` to spawn the CX Subagent, then STOP - the Subagent performs the Cross-Examination, not you.
	- Otherwise: ask User whether to proceed with the degraded in-context review. Log `Capability downgrade: Cross-Examination` under [Practices > Logs > Capability Downgrades], recording the invalid or absent `host-spawn` value, the User's choice, the isolated review skipped, and the User-visible loss of isolation. If Yes: perform it per [Practices > CX > Degraded Review] - one report into `_Axis/CX/`, Line 1 labelled `CX: {topic} (in-context, non-isolated)`. If No: STOP after the downgrade Log.
