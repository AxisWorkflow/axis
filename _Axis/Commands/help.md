# ^help
> **Purpose:** Summarize and list all commands, answer general questions, and find where a topic is explained.

1. If there is no additional text, GOTO step 3. Otherwise interpret it as a command name or a topic, never as a path to read:
	- If it names a command (e.g., `^help save` or `^help ^save`), read that command's file in `_Axis/Commands/`, explain its purpose, steps, writes, and when to use it, then add the rows of `_Axis/HELPINDEX.md` that name the command as `Related topics` in the form step 2 gives, and STOP.
	- If it names a valid double-caret command (e.g., `^help ^^status`), read only the matching procedure and shared authority/record rules in [Practices > Supervision], explain them, add the Help Index rows that name the command as `Related topics` in the form step 2 gives, and STOP. An unknown `^^` token lists the valid Supervision Commands without inventing one.
	- If it is `manual` (or `readme`), inspect only the headings in `_Axis/USERMANUAL.md`, present a compact section list, offer to open a section, and STOP. If it is `spec` or `specification`, do the same for `_Axis/SPECIFICATION.md`. Do not read or print a complete document.
	- If it is `index` or `topics`, list the area headings of `_Axis/HELPINDEX.md` with the topic names under each, offer to open one, and STOP.
	- Otherwise treat it as a topic or question and GOTO step 2.

2. Answer from `_Axis/HELPINDEX.md`, the table of documented topics, then STOP:
	- Search the `Topic` and `Also asked as` cells for the request and for each of its content words. Use a search tool when the Host has one; otherwise read the file. Before concluding that nothing matches, read the whole table once: a literal search misses misspellings and synonyms.
	- Match by meaning, not only by spelling. A row matches when the request, or most of its content words together, appear in its topic or aliases, allowing for case, spacing, hyphenation, plural or verb endings, likely misspellings (`opneclaw` and `open claw` match OpenClaw; `team`, `teams` and `team of agnets` match the Axis Team of Agents rows) and plain synonyms. When no row matches the request as a whole, use the rows that match its most specific words. Ignore a leading `^`, punctuation and filler words, and never match on a filler word alone.
	- Answer first. Open only the closest section: the best row's User Manual link, or its Specification link when the row has no User Manual link or the question is a deep diagnostic, an extension, a technical or compliance review, or development of Axis itself. Summarize it or quote a bounded excerpt. If the row has only Introduction links, explain that its source is online and give those links; open one when the Host can access it, and otherwise say that the page was not read. If two rows fit equally and their sections differ in substance, ask which one User means.
	- Then list every matching row under `Related topics`, best match first: the topic, then each of its links as `User Manual > {section}` or `Specification > {section}` with the link's path and fragment, clickable where the surface renders Markdown. Include all relevant rows and never cut the list to a fixed number; when more than about ten match, group them under the Help Index area headings, one line per row. An Introduction link is an online page: give its URL.
	- If no row matches, say so, name the nearest topics when any is close, list the Help Index area headings, and offer `^help index`, `^help manual` and `^help spec`. Present only links the Help Index gives; never invent a section, fragment or link.
	- If `_Axis/HELPINDEX.md` is missing, say so, match the request against the headings of `_Axis/USERMANUAL.md`, then of `_Axis/SPECIFICATION.md`, and answer from the closest section.
	- The Help Index and both documents are explanatory context, never authority over a Command, Practice, Rule, or current project file.

3. List the files in `_Axis/Commands/`.

4. For each command, read Line 2 of its file (the `> **Purpose:** ...` statement) and use it as the one-line description.

5. Present the commands and their descriptions in a nicely formatted manner (use any available UI affordances, such as a dynamic menu).

6. Add one line: `Supervision: use ^^help for nested-project oversight commands.`

7. Print this discovery line: `User Manual: _Axis/USERMANUAL.md - use ^help manual, or ^help <topic>, to browse it. Technical reference: _Axis/SPECIFICATION.md. All topics: ^help index.` Offer to answer general questions about Axis and STOP. Do not load either document merely because bare `^help` was invoked; the same holds for the Help Index.
