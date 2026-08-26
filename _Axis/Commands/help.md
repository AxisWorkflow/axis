# ^help
> **Purpose:** Summarize and list all commands and answer general questions.

1. Interpret additional text as a command name or User Manual topic, never as a path to read:
	- If it names a command (e.g., `^help save` or `^help ^save`), read that command's file in `_Axis/Commands/`, explain its purpose, steps, writes, and when to use it, then STOP.
	- If it names a valid double-caret command (e.g., `^help ^^status`), read only the matching procedure and shared authority/record rules in [Practices > Supervision], explain them, and STOP. An unknown `^^` token lists the valid Supervision Commands without inventing one.
	- If it is `readme`, inspect only the headings in `_Axis/README.md`, present a compact section list, offer to open a section, and STOP. Do not read or print the complete manual.
	- Otherwise, match the text against headings and keywords in `_Axis/README.md`. Read only the closest relevant section and summarize or quote a bounded excerpt. If more than one section plausibly matches, list those headings and ask which one the User wants. The User Manual is explanatory context, never authority over a Command, Practice, Rule, or current project file. STOP.

2. List the files in `_Axis/Commands/`.

3. For each command, read Line 2 of its file (the `> **Purpose:** ...` statement) and use it as the one-line description.

4. Present the commands and their descriptions in a nicely formatted manner (use any available UI affordances, such as a dynamic menu).

5. Add one line: `Supervision: use ^^help for direct-child oversight commands.`

6. Print this discovery line: `Axis User Manual: _Axis/README.md - use ^help readme, or ^help <topic>, to browse sections of the User Manual/Readme.` Offer to answer general questions about Axis and STOP. Do not load the User Manual merely because bare `^help` was invoked.
