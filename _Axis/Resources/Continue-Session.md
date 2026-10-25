# Continue Session
> **Purpose:** Recover the context of an already booted identity without adopting another session.

Normal visible Main or External boot records use the entry fast path. A Subagent keeps its envelope identity. Never recreate a Marker, infer identity from age, or adopt the shared session-id Flag as your own identity.

## Identity recovery

Use this procedure only for an existing conversation. Recover your exact own Session ID and role from its boot record or a verified native-session binding. A project Flag, host name, inactive Marker or absence of recent activity does not establish that a session is yours. If your identity cannot be recovered, make no writes and follow [Displaced-Session]; only an explicit User-selected fresh startup can create a new identity.

1. Inspect pending updates through [Check-Update-Handoff] before ordinary context or overlay work. An unfinished startup or update permits only its still-owned procedure; never adopt or renew another identity to finish it.
2. With Python, run `turn.py --session {own Session ID}` and honor every hold before any renewal or other write. Without Python, use [Displaced-Session] > Persistent hosts and no-shell parity: verify your exact safe Marker, tombstone, foreign Main state, Main ownership and own boot version before renewing only the existing Marker. Do not refresh the shared session-id Flag during continuation.
3. An OK result permits recovery of missing context through [Load-Starting-Context] and applicable [Load-Project-Overlay] checks. Complete update, Message and overlay checks from the entry fast path before ordinary work. A missing, changed or unverified boot version holds until a User-selected fresh session reloads current instructions.

Say "Resuming session." at most once per conversation, with no new success banner. A resumed External retains its original limits. A displaced identity stays read-only; a fresh identity follows complete current admission rather than this continuation procedure.
