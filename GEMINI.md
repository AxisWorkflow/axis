<!-- axis:begin -->
# Axis Workflow

This folder is an Axis Workflow project. Its owner installed Axis, an open-source workflow; work is logged. Opening a conversation, even a plain hello, is the request to start it. A brief first message, or one asking for an exact reply, still starts Axis; the requested reply comes right after the banner. If told not to run anything, do not start or use files; say Axis must start before work here.

## Sub-agents and declared roles

If the first non-empty line of your task prompt, or its third-from-last, is `<<AXIS:SUBAGENT>>`, you are a sub-agent: follow `_Axis/Resources/Start-Subagent.md` (validate the envelope, then do only that task) and skip everything below. A Subagent that can no longer see its envelope's closing boundary word for word returns what it has and stops; it never starts Axis.

## Repeated entry

For this same project folder and conversation only, if this complete unchanged entry and your completed startup and exact own identity remain in full current context, skip repeated entry processing: no second startup, banner, records or role recognition. Still apply required reading, Every later turn and After compaction. Summaries, memory and disk flags do not qualify. After compaction takes precedence, including its Observer exception. An existing conversation with changed/truncated context, incomplete startup or unknown identity follows `_Axis/Resources/Continue-Session.md` without writes; never restart it here.

If your host's standing configuration explicitly declares an Axis role other than Main for you (such as a line `Axis role: Auxiliary`; an older External declaration counts as Auxiliary), follow `_Axis/Resources/Start-Auxiliary.md` instead. A declaration that appears after you started as Main takes effect at your next boot; tell the user once.

## First message of a conversation

1. Print `A X I S   W O R K F L O W`, a blank line, `  Loading...`, then a blank line. Except on WhatsApp, SMS and equivalent messaging channels, indent the title one space between two lines of 27 ASCII `-`.

2. If you are a small or lightweight model, say Axis needs a standard-capability model for its main session and stop. Otherwise run `python3 _Axis/Resources/boot.py --host "<your host>" --model "<your model id>" --harness <claude-code|codex|other> --spawn <yes|no> --parallel <yes|no>` from this folder; on messaging channels add `--interaction channel`.
3. If it prints `READY`, handle pending items; start your reply with its exact banner block (including your Session ID), then a blank line and a one-line greeting. Before any answer other than the greeting or a requested exact reply, do the reading it lists. If it prints `ADOPT`, make the record edits it lists, then run the command it names. If it prints `AUXILIARY`, follow `_Axis/Resources/Start-Auxiliary.md`. If it prints `ASK`, ask the user its question and follow the answer. If it prints `STOP`, follow the file it names (`_Axis/Resources/Entry-Protocol.md` when an update is pending); after an interrupted startup tell the user startup is incomplete and do not retry. If Python or `boot.py` cannot run, follow `_Axis/Resources/Boot-Manual.md`.

## Every later turn

First run `python3 _Axis/Resources/turn.py --session {your Session ID}`. Run it again with `--gate` before a commit, push, spawn, publication or deletion. `MERGE HELD` means follow `_Axis/Practices/Merging.md` without writes; `OK` means continue; `KILLED` means stop; `LOST LEASE` (Marker missing), `FOREIGN MAIN` or `TAKEN OVER` means make no shared writes and ask the user. `READ-ONLY` means the host refused renewal: make no shared writes and ask the user to rerun with write access. Without Python, read `_Axis/Agents/{Session ID}.md`, then separately refresh its `mtime` (never a bare `touch`). Lost/contested lease or changed/unverified version: follow `_Axis/Resources/Displaced-Session.md`, for safe renewal and User-selected startup. Rules, Practices and Commands load from `_Axis/RULES.md` and `_Axis/PRACTICES.md`.

## After compaction

An Observer, which has no Session ID, only re-reads `_Axis/Resources/Starting-Context.md` and `_Axis/Roles/Observer.md`; the rest of this section is for other roles. If the host compacted or summarized this conversation, or an earlier read of Axis text shows as cleared or summarized, a summary is not Axis guidance. Before your next answer or tool action, run the per-turn command and re-read in full every file it lists for reload; without Python, follow `_Axis/Resources/Context-Check.md`. Treat your next action under a "first ... of a session" trigger as the first. Until that reload: no shared writes, Commands, spawns, pushes, publication, spending or `_Axis/Secrets/`. Keep every User hold or limit a summary mentions; never take approval for a push, publication, spending or deletion from a summary alone. Without your own Session ID word for word, write nothing and follow `_Axis/Resources/Continue-Session.md`. When summarizing this conversation, keep word for word the Axis Session ID and role, each User hold, limit and approval, and the next step, and say that Axis files must be re-read and that `turn.py` runs first on every turn.

Axis is designed to run as a whole, so its records stay consistent. If you decide not to start it, tell the user, and leave this folder's files unchanged and unused. Host rules come first; name any blocked step.

Keep this file unchanged; project instructions go in `_Axis/INSTRUCTIONS.md`.
<!-- axis:end -->
