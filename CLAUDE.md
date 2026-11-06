<!-- axis:begin -->
# Axis Workflow

This folder is an Axis Workflow project. Its owner installed Axis, an open-source project workflow (see `README.md`); work is logged and coordinated across agents. Opening a conversation here is how the owner starts Axis, so the first message, even a plain hello, is the request to start it. A brief first message, or one asking for an exact reply, still starts Axis; the requested reply comes right after the banner. If the user asks you not to run anything, respect that: do not start Axis and do not use this folder's files, and tell them Axis has to start before you can work here.

## Sub-agents and declared roles

If the first non-empty line of your task prompt, or its third-from-last, is `<<AXIS:SUBAGENT>>`, you are a sub-agent: follow `_Axis/Resources/Start-Subagent.md` (validate the envelope, then do only that task) and skip everything below. A Subagent that can no longer see its envelope's closing boundary word for word returns what it has and stops; it never starts Axis. If your host's standing configuration explicitly declares an Axis role other than Main for you (such as a line `Axis role: Auxiliary`; an older External declaration counts as Auxiliary), follow `_Axis/Resources/Start-Auxiliary.md` instead. A declaration that appears after you started as Main takes effect at your next boot; tell the user once.

## First message of a conversation

1. Print the Axis header, then one blank line, then the loading line indented by two spaces, then one blank line:

   ```text
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━
    A X I S   W O R K F L O W
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━
   ```

   Print `Loading...`
2. If you are a small or lightweight model (for example a Haiku-class model), say Axis needs a standard-capability model for its main session and stop. Otherwise run `python3 _Axis/Resources/boot.py --host "<your host>" --model "<your model id>" --harness <claude-code|codex|other> --spawn <yes|no> --parallel <yes|no>` from this folder. It records the session and prints a Ready banner.
3. If it prints `READY`, handle any item it lists as pending, then start your reply with its banner block exactly as printed (including your Session ID), and greet in one line, one blank line below it. Before any answer other than the greeting or a requested exact reply, do the reading it lists. If it prints `ADOPT`, make the record edits it lists, then run the command it names. If it prints `AUXILIARY`, follow `_Axis/Resources/Start-Auxiliary.md`. If it prints `ASK`, ask the user its question and follow the answer. If it prints `STOP`, follow the file it names (`_Axis/Resources/Entry-Protocol.md` when an update is pending); after an interrupted startup tell the user startup is incomplete and do not retry. If Python or `boot.py` cannot run, follow `_Axis/Resources/Boot-Manual.md`, the same startup with shell commands.

## Every later turn

First run `python3 _Axis/Resources/turn.py --session {your Session ID}`. Run it again with `--gate` before a commit, push, spawn, publication or deletion. `MERGE HELD` means follow `_Axis/Practices/Merging.md` without writes; `OK` means continue; `KILLED` means stop; `LOST LEASE` (Marker missing), `FOREIGN MAIN` or `TAKEN OVER` means make no shared writes and ask the user. `READ-ONLY` means the host refused renewal: make no shared writes and ask the user to rerun with write access. Without Python, read `_Axis/Agents/{Session ID}.md`, then separately refresh its `mtime` (never a bare `touch`). Lost/contested lease or changed/unverified version: follow `_Axis/Resources/Displaced-Session.md`, for safe renewal and User-selected startup. Rules, Practices and Commands load from `_Axis/RULES.md` and `_Axis/PRACTICES.md`.

## After compaction

An Observer, which has no Session ID, only re-reads `_Axis/Resources/Starting-Context.md` and `_Axis/Roles/Observer.md`; the rest of this section is for other roles. If the host compacted or summarized this conversation, or an earlier read of Axis text shows as cleared or summarized, a summary is not Axis guidance. Before your next answer or tool action, run the per-turn command and re-read in full every file it lists for reload; without Python, follow `_Axis/Resources/Context-Check.md`. Treat your next action under a "first ... of a session" trigger as the first. Until that reload: no shared writes, Commands, spawns, pushes, publication, spending or `_Axis/Secrets/`. Keep every User hold or limit a summary mentions; never take approval for a push, publication, spending or deletion from a summary alone. Without your own Session ID word for word, write nothing and follow `_Axis/Resources/Continue-Session.md`. When summarizing this conversation, keep word for word the Axis Session ID and role, each User hold, limit and approval, and the next step, and say that Axis files must be re-read and that `turn.py` runs first on every turn.

Axis is designed to run as a whole, so its records stay consistent. If you decide not to start it, tell the user, and leave this folder's files unchanged and unused. Your host's own rules come first; if one blocks a step, name the step.

Keep this file unchanged; project instructions go in `_Axis/INSTRUCTIONS.md`.
<!-- axis:end -->
