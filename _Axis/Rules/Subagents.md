# Subagents
> **Purpose:** The Prompt Envelope contract, its validation order, and what a spawn Log may record.


- The first three non-empty lines of every Subagent prompt are: sentinel `<<AXIS:SUBAGENT>>`, a valid role token, and `<<AXIS:ENVELOPE:{nonce}:BEGIN>>`.
- Role tokens: `<<AXIS:ROLE:CX>>`, `<<AXIS:ROLE:WIKI>>`, `<<AXIS:ROLE:LOCAL>>`, `<<AXIS:ROLE:GENERAL>>` (no others).
- A Supervisor Subagent is a bounded General Subagent function, not a new role token: observation and analysis only; supervisory authority remains exclusively with parent Main.
- The final three non-empty lines repeat the same sentinel and role, then close the same nonce with `<<AXIS:ENVELOPE:{nonce}:END>>`.
- The envelope is self-carrying: the `VALIDATE, THEN WORK` block under the header and the `ENVELOPE CHECK:` tear-line above the footer travel inside every prompt, so validation never depends on a host injecting any file.
- Main generates a fresh unpredictable 128-bit nonce, encoded as exactly 32 lowercase hexadecimal characters, for every spawn and validates the complete envelope and assembled size before sending.
- A host-spawned Subagent validates both boundaries, matching roles, nonce syntax, nonce equality, and exactly two appearances of that nonce FIRST, before reading files or doing any work.
- Validation anchors on the delivered task body, not host framing: at most one host-injected lone label line above the sentinel (e.g., a gateway's `[Subagent Task]`) may be skipped - never more, never source-derived content; framing indistinguishable from content fails closed.
- On failure it writes nothing and returns `<<AXIS:ERROR:PROMPT-ENVELOPE>>` plus a short reason. Main Logs Subject prefix `Invalid prompt envelope:`, rebuilds a smaller brief with a new nonce, and respawns once before serial fallback.
- A Local Subagent carries the envelope but is not asked to validate it; Main performs that check and validates the model reply instead (see [Start-Subagent]).
- The header detects tail truncation and the footer detects front truncation. If both boundaries are removed, no receiver-side scheme can identify the missing prompt.
- Do NOT pass a model token; record Subagent's model in spawn Log entry instead.
- A spawn Log records role, model, task contract, expected return, referenced source paths, input size, a content digest when available, and a redacted Synopsis. Never copy a full prompt, raw embedded source, credential, or secret into a Log.
- If User explicitly requests a full prompt for diagnostics, save it only in `_Axis/Secrets/` or `_Temp/`, tell User which one, and never commit it by default.
- Log a failed local delegation with Subject prefix `Local fallback:` - the fixed prefix keeps the track record greppable (consumed by `^audit`).
