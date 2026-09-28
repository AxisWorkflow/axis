<!-- axis:begin -->
# Axis Workflow

This folder is an Axis Workflow project. Its owner installed Axis, an open-source project workflow (see `README.md`), so that every AI agent working here shares one plan, task list and history, and so that work is logged and agents do not collide. Opening a conversation here is how the owner starts Axis, so the first message, even a plain hello, is the request to start it. A brief first message, or one asking for an exact reply, still starts Axis; the requested reply comes right after the banner. If the user asks you not to run anything, respect that: do not start Axis and do not use this folder's files, and tell them Axis has to start before you can work here.

## Sub-agents and External agents

If the first non-empty line of your task prompt, or its third-from-last, is `<<AXIS:SUBAGENT>>`, you are a sub-agent: follow `_Axis/Resources/Start-Subagent.md` (validate the envelope, then do only that task) and skip everything below. If your host's standing configuration explicitly declares you an External agent, follow `_Axis/Resources/Start-External.md` instead. If such a declaration appears after you started as Main, stay Main and tell the user once: "A standing External declaration appeared in this workspace after boot: I remain Main this session; it takes effect at the next boot; `^demote` applies it now."

## First message of a conversation

1. Print `Loading The Axis Workflow. This may take a minute or two...`
2. If you are a small or lightweight model (for example a Haiku-class model), say Axis needs a standard-capability model for its main session and stop. Otherwise run `python3 _Axis/Resources/boot.py --host "<your host>" --model "<your model id>" --harness <claude-code|codex|other> --spawn <yes|no> --parallel <yes|no>` from this folder. It records the session and prints a Ready banner.
3. If it prints `READY`, always show its banner block exactly as your first output after the command, even when you go on to answer a question, and greet the user in one line. Handle any item it lists as pending, then answer. Before any answer other than the greeting or a requested exact reply, do the reading it lists. If it prints `EXTERNAL`, follow `_Axis/Resources/Start-External.md`. If it prints `STOP`, follow the file it names (`_Axis/Resources/Entry-Protocol.md` when an update is pending); after an interrupted startup tell the user startup is incomplete and do not retry. If Python is unavailable or `boot.py` cannot run at all, follow `_Axis/Resources/Boot-Manual.md`, the same startup with shell commands.

## Every later turn

First run `python3 _Axis/Resources/turn.py --session {your Session ID}`. `OK` means continue; `KILLED` means stop; `LOST LEASE` (missing or over an hour old) or `FOREIGN MAIN` means make no shared writes and ask the user. Without Python, read `_Axis/Agents/{Session ID}.md`, then separately refresh its `mtime` (never a bare `touch`). Rules, Practices and Commands load from `_Axis/RULES.md` and `_Axis/PRACTICES.md`.

Axis is designed to run as a whole, so its records stay consistent. If you decide not to start it, tell the user, and leave this folder's files unchanged and unused. Your host's own rules come first; if one blocks a step, name the step.

Keep this file unchanged; project instructions go in `_Axis/INSTRUCTIONS.md`.
<!-- axis:end -->
