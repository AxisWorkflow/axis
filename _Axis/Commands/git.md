# ^git
> **Purpose:** Save or receive project changes through safe, adaptive Git synchronization.

1. Main Agent only. External Agents send a Request to Main; Subagents return the request without acting. Read `host-shell` under [Practices > Flags > Reading Flags] and require valid `yes` for mutation. Read [Practices > GIT] completely and follow its admission, repository-boundary, Subproject, and safety gates.

2. Interpret additional text semantically, never as raw CLI syntax:
	- `status`, `history`, or `diff` uses the read-only mode in [Practices > GIT > Command Modes].
	- `checkpoint {hint}` makes a local checkpoint only; the hint informs the drafted message but is never executed.
	- `connect`, `remote`, or a request to use GitHub enters Private Remote Setup after securing local state.
	- `push` requests the ordinary outgoing state-machine path; it never authorizes force.
	- `undo` delegates to `^undo` and its confirmation.
	- Anything else, including no text, uses bare adaptive mode. Do not invent branch, tag, pull-request, rebase, or history-rewrite behavior in version 1.

3. If Git is missing, offer its official platform-appropriate installation per [Practices > GIT > Setup] and wait for approval before changing the machine. If no exact-root repository exists, invoking this Command authorizes Setup: initialize, safety-scan, add, and make the initial local commit. When `project-ready` is valid, follow `_Axis/Resources/Refresh-Project-README.md` immediately before that initial commit. A parent repository or ambiguous Subproject stops for User choice.

4. If the exact-root repository has no remote, checkpoint any local changes, then offer Private Remote Setup. Declining is a successful local-only result. When GitHub is accepted, check/offer `gh`, authenticate through its browser flow, confirm owner/name/private visibility, create the empty remote, establish upstream, push, verify, and record the setup without any credential-bearing URL.

5. When `.recipient` or `.capsule.age` exists, run Encrypted Secrets Transport before an outgoing checkpoint and after an incoming fast-forward. When neither exists but bounded discovery reports plaintext credential material, offer the one-time encrypted transport setup without naming an entry. Declining keeps plaintext ignored and reports that it will not travel through Git.

6. With a configured upstream, run the Shared Synchronization State Machine exactly once: fetch, classify local files and graph ancestry, then take at most one linear action. Immediately before any ordinary outgoing checkpoint, when `project-ready` is valid, follow `_Axis/Resources/Refresh-Project-README.md` once and include the result in staging. Bare mode checkpoints substantive local changes; pulls only a strict clean or receive-safe fast-forward; pushes only local-ahead history; stops on divergence, unfinished Git state, unsafe staged content, or a Secrets conflict. Preserve verified noncolliding session-lifecycle Logs through receipt for the next checkpoint. Never merge, rebase, stash/reapply, reset, force, or discard automatically.

7. If an incoming fast-forward changed Workflow machinery, run the mandatory fresh-session exit from [Practices > GIT > Incoming Change Validation] and STOP. Otherwise complete the automatic `^resume` summary after receipt. An ordinary outgoing checkpoint finishes cleanly: routine Git commit/push is its audit record. Log setup, safety failure, reconciliation, or configuration changes under the owning Practice.

8. Report one concise outcome: local checkpoint status, remote state (`synchronized`, `local only`, `remote not verified`, or `needs reconciliation`), encrypted Secrets state when configured or omitted, and the one User action needed, if any. If synchronization succeeded but this is a cross-computer handoff, remind User to run `^shutdown` before opening the other copy. STOP.
