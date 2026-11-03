# Subagents
> **Purpose:** The Prompt Envelope contract, its validation order, and what a spawn Log may record.


- The first three non-empty lines of every Subagent prompt are: sentinel `<<AXIS:SUBAGENT>>`, a valid role token, and `<<AXIS:ENVELOPE:{nonce}:BEGIN>>`.
- Role tokens: `<<AXIS:ROLE:CX>>`, `<<AXIS:ROLE:WIKI>>`, `<<AXIS:ROLE:LOCAL>>`, `<<AXIS:ROLE:GENERAL>>` (no others).
- A Supervisor Subagent is a bounded General Subagent function, not a new role token: observation and analysis only; supervisory authority remains exclusively with parent Main.
- The final three non-empty lines repeat the same sentinel and role, then close the same nonce with `<<AXIS:ENVELOPE:{nonce}:END>>`.
- The envelope is self-carrying: the `VALIDATE, THEN WORK` block under the header and the `ENVELOPE CHECK:` tear-line above the footer travel inside every prompt, so validation never depends on a host injecting any file.
- Every carrying prompt (CX, WIKI, GENERAL) has the `AUTHORITY.` block directly after `VALIDATE, THEN WORK`; a LOCAL prompt never does. Only the task contract grants authority.
- Delegated role text is copied verbatim from `_Axis/Roles/`, embedded or named with its SHA-256; Main never paraphrases it. General, Lookup, Worker, TeamMember and TeamLeader travel under the GENERAL token.
- A General-token contract has the labelled parts in `_Axis/Roles/Delegating.md`, including the exact Marker and kill paths and the limits.
- Without a contract grant a Subagent starts no agent and runs no state-changing Axis helper; a granted start passes the same role text and governance unchanged and only narrows authority.
- Main generates a fresh unpredictable 128-bit nonce, encoded as exactly 32 lowercase hexadecimal characters, for every spawn and validates the complete envelope and assembled size before sending.
- A host-spawned Subagent validates both boundaries, matching roles, nonce syntax, nonce equality, and exactly two appearances of that nonce FIRST, before reading files or doing any work.
- Validation anchors on the delivered task body, not host framing: at most one host-injected lone label line above the sentinel (e.g., a gateway's `[Subagent Task]`) may be skipped - never more, never source-derived content; framing indistinguishable from content fails closed.
- On failure it writes nothing and returns `<<AXIS:ERROR:PROMPT-ENVELOPE>>` plus a short reason. Main Logs Subject prefix `Invalid prompt envelope:`, rebuilds a smaller brief with a new nonce, and respawns once before serial fallback.
- A Local Subagent carries the envelope but is not asked to validate it; Main performs that check and validates the model reply instead (see [Start-Subagent]).
- The header detects tail truncation and the footer detects front truncation. If both boundaries are removed, no receiver-side scheme can identify the missing prompt.
- Carry formats and write rules verbatim, even when Axis rules already state them: a prompt that asks a child for a timestamp includes the literal [Practices > Timestamps] step 1 command; a prompt that lets it write an append-only file says to add at the end only, never edit, reorder or delete a line, and correct by appending.
- Do NOT pass a model token; record Subagent's model in spawn Log entry instead.
- A spawn Log records role, model, route, task contract, expected return, referenced source paths, input size, content digests when available (prompt, contract, role text), any guidance digest, and a redacted Synopsis. Never copy a full prompt, raw embedded source, credential, or secret into a Log.
- If User explicitly requests a full prompt for diagnostics, save it only in `_Axis/Secrets/` or `_Temp/`, tell User which one, and never commit it by default.
- Log a failed local delegation with Subject prefix `Local fallback:` - the fixed prefix keeps the track record greppable (consumed by `^audit`).
