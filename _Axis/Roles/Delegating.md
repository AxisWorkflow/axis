# Roles: Delegating
> **Purpose:** The delegating kit for every agent that starts another: role selection, carriers, the task contract and acceptance.

Main, a Team Leader, an Auxiliary owner of a proposal Team and a parent Main use the same kit. A delegate can only narrow the authority it received; a granted start of another agent passes the same role text and governance unchanged and is reported. [Practices > Delegation] decides whether to delegate; [Start-Subagent] builds and sends the prompt.

## Choose the role

| Role | Envelope token | Claude Code agent type | Use for |
| --- | --- | --- | --- |
| General | `GENERAL` | `axis-general` | Exploration, implementation, comparison, drafting, review, an isolated workstream |
| Lookup | `GENERAL` | `axis-lookup` | Read-only finding, extracting and copying known facts |
| CX | `CX` | `axis-cx` | Independent cross-examination under [Practices > CX] |
| Worker | `GENERAL` | none | One dispatched Job attempt or a scheduled report Job |
| TeamMember | `GENERAL` | none | A seat in an Axis Team of Agents |
| TeamLeader | `GENERAL` | none | Leading an Axis Team of Agents |
| Wiki | `WIKI` | `axis-wiki` | Wiki ingest under [Practices > Wiki] |
| Local | `LOCAL` | none | Bounded text-in / text-out work on a qualified local model, from [Template-LocalPrompt] |

The role file `_Axis/Roles/{Role}.md` holds each role's text between its `axis:role-text` markers. Wiki and Local prompts carry no role text.

## Carry the role text

- **Embedded (default).** Copy the role text verbatim into the prompt after the AUTHORITY block. Keep the assembled prompt within the route's budget: 32,768 bytes unless the route's window is known to be larger (`envelope.py check --max-bytes`).
- **File.** When embedding would exceed the budget, name the role file with its SHA-256 instead. The delegate verifies the checksum before reading it (Python, `shasum -a 256`, `sha256sum` or `openssl dgst -sha256`) and refuses a mismatch like a torn envelope. CX and Lookup helpers have no shell to check a checksum, so their role text is always embedded; split the task instead.
- **Contract copy.** For a Team member or a contract window over 30 minutes, assemble with `envelope.py assemble --save-contract`: the prompt pins a nonce-free copy of the contract. A delegate that loses sight of its envelope after compaction returns and stops; verify the copy's SHA-256 and re-send its contract in a fresh envelope to resume. Record the printed path and SHA-256 in the Marker.
- **Host-injected.** Every role file stays within 20,000 characters, so any role can ride a host that injects one file.
- Embed the role text for CX and Lookup: their Claude Code helper types have no shell to verify a checksum.
- `envelope.py check --role {Role}` compares the role text with all whitespace collapsed, so a host's indentation and wrapping pass; it checks the text against the role file on disk.

With Python, `envelope.py assemble` builds the whole prompt from a role and a contract file and writes nothing; without it, copy the role text by hand.

## Write the contract

Every General-token contract has these labelled parts, in this order. `envelope.py check --contract` checks the labels.

- `PURPOSE:` the project goal served and who benefits.
- `REQUEST:` a link to, or the verbatim text of, the User request behind the task.
- `DELIVERABLE:` the decision or artifact to return.
- `SUCCESS:` what success means in those terms.
- `CRITICAL RULES:` how critical rules apply here, for example which checks may not change.
- `CONSTRAINTS:` holds and constraints that bind, and the Working Language when it is not English.
- `SCOPE AND AUTHORITY:` read and write scope; any grant (writes, helpers, starting agents); whether host temporary space may be used, with unique names; tools that carry the User's sign-ins are off limits, even for reading, unless granted.
- `LIMITS:` the exact Marker path and its `.kill` path, time and usage limits.
- `SOURCES:` what to read, and how to ask for a missing source.
- `RETURN:` the return shape; cite your own Tracking lines by time, never by quoting identifiers.
- `DEVIATIONS:` any declared departure from the role text, such as a substituted stance, with its reason; or `none`.

Add `FOR EVERY AGENT:` with the "For every agent" part of the User's Instructions, copied by `envelope.py instructions` or by hand; an Instructions file without exactly one such heading, or with a "For only the Main Agent" (or older "For Main only") heading inside that section, contributes nothing. General, Worker, TeamMember and TeamLeader prompts carry `GOVERNANCE:` with the absolute project root, the governance list file and its SHA-256 (`envelope.py assemble` writes the list); CX and Lookup prompts need none. A Lookup prompt carries no TRACKING line: its spawner writes the Lookup's INTENT and DONE lines in its own Tracking file.

## Accept the return

Run the mechanical checks first, then judge:

1. A return containing `<<AXIS:ERROR:PROMPT-ENVELOPE>>` is a refusal: fix the prompt, rebuild with a new nonce, respawn once.
2. Every changed path is inside the contract's write scope (`git status`, `git diff --stat`); an out-of-scope write is a defect even when the rest is good.
3. No check, test or assertion was weakened or deleted unless the contract allowed it (`git diff` on tests).
4. No push, publication, spawn or governing-file change happened without a grant (`git log` and remote state, Markers, `envelope.py governance --verify`).
5. Tracking lines exist when the prompt required them; a quoted read token is a diagnostic, not proof of reading.
6. Then shape, preservation, semantic and judgment validation under [Practices > Delegation], the frame check, and whether the result delivers the decision promised.
