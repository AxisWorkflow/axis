# Move Project Files
> **Purpose:** Move the project files from `_Axis/` to `_Config/` by hand when `boot.py` cannot. Same result and records as its step.

Load this Resource only while a project file exists in `_Axis/` or `_Axis/Flags/config-move` begins `moving`. The project files, in the order of the move: `SETTINGS.md`, `INSTRUCTIONS.md`, `MINDSET.md`, `DIRECTIVES.md`, `PROJECT.md`, `PLAN.md`, `INITIATIVES.md`, `TASKS.md`; `{NAME}` below is one of them without `.md`. Run every command from the project root.

## The look

Read-only. Run it before the claim, and again as the first act of the step.

	for n in SETTINGS INSTRUCTIONS MINDSET DIRECTIVES PROJECT PLAN INITIATIVES TASKS; do o=_Axis/$n.md; c=_Config/$n.md; bad=
	  for f in "$o" "$c"; do if [ -L "$f" ] || { [ -e "$f" ] && [ ! -f "$f" ]; }; then echo "conflict: $f is a link or not a plain file"; bad=1; fi; done
	  if [ -n "$bad" ]; then :; elif [ -f "$o" ] && [ -f "$c" ]; then if cmp -s "$o" "$c"; then echo "redundant: $o"; else echo "conflict: $o and $c differ"; fi; elif [ -f "$o" ]; then echo "move: $o"; fi
	done
	if [ -L _Config ] || { [ -e _Config ] && [ ! -d _Config ]; }; then echo "conflict: _Config is not a plain folder"; fi
	ls -a | grep -ix _config | grep -vx _Config | sed 's/^/conflict: differs from _Config only in letter case: /'
	if [ -e .git ]; then git check-ignore -- _Config/SETTINGS.md _Config/INSTRUCTIONS.md _Config/MINDSET.md _Config/DIRECTIVES.md _Config/PROJECT.md _Config/PLAN.md _Config/INITIATIVES.md _Config/TASKS.md | sed 's/^/conflict: ignored by Git: /'; fi
	sed -n 1p _Axis/Flags/config-move 2>/dev/null || true

- `move:` the file is only in `_Axis/`. `redundant:` both places hold the same bytes. No line: the file is only in `_Config/`, or in neither, which the Manifest check reports.
- `moving` as the last line: an earlier step did not finish. The step runs again even when nothing is left to move.
- `ignored by Git` counts only while a line says `move:`. Without Git there is no such test; say so in the notice.
- Any other `conflict:` line, at any time, stops the start: write nothing, tell User each path and what to do, and STOP.
	- Two copies differ: when a `Reference move` Log names `_Config/{NAME}.md` as `target` with the SHA-256 that file has now, that copy is the one in use and the `_Axis/` copy appeared later: merge what is needed into `_Config/`, then remove the `_Axis/` copy. Otherwise keep one copy and remove or rename the other.
	- A link or not a plain file: replace it with a plain file holding the content.
	- `_Config` is not a plain folder: rename or remove that entry. Letter case: rename it to `_Config`, or to another name.
	- Ignored by Git: remove the ignore rule for `_Config/`; a checkpoint would otherwise record eight deletions and no additions.

A `_Config/` that holds none of the project files is used as it is. Leave everything else in it untouched.

## Reads before the step

Start-up text names `_Config/{NAME}.md`. Until the step has moved a file, read it where this rule finds it:

	project_file() { if [ -f "_Config/$1" ] && [ -f "_Axis/$1" ] && ! cmp -s "_Config/$1" "_Axis/$1"; then echo "project file differs between _Config and _Axis: $1" >&2; return 1; fi; if [ -f "_Config/$1" ] || [ ! -f "_Axis/$1" ]; then echo "_Config/$1"; else echo "_Axis/$1"; fi; }

Two differing copies are an error, never a choice, and Settings missing at one place never mean a default. This covers the Instructions of the admitted loading batch and of Start-Session Step 1, and every Settings read before the step: the takeover limit, Tracking and Storage Policy.

## The step

Main only, under the retained startup admission, where [Start-Session] Step 2 calls it: after an update is consumed, before the Project file is read. A failure, or a conflict found only here, leaves startup incomplete: STOP, tell User, and keep the startup lock, `starting` and your Marker in place. After [Lock-File > Quiescent Recovery] the next start looks again and continues.

1. Run the look again. Write `_Axis/Flags/config-move` with `moving` on Line 1 and the current UTC time on Line 2. Create `_Config/` when absent, and remove any `_Config/.{NAME}.md.tmp` an earlier run left.
2. For each `move:` file, in the order above:
	- a. **Rebase its links in place.** A link is `[text](destination)` on any line, code spans and fenced blocks included; the destination holds no space and ends at the first `)`. Leave a destination that begins with `../`, `/`, `#` or a scheme such as `https:`, and one that is the name of a project file, with or without a `#fragment`. In every other destination drop a leading `./` and put `../_Axis/` in front: `Tasks/{ID}.md` becomes `../_Axis/Tasks/{ID}.md`. In angle brackets, change the path between them. Leave reference definitions (`[label]: path`), destinations with a title or a space, and HTML `href` or `src`. Note for the notice each of those the move breaks, and each link changed inside code. Write the result to a temporary file beside the original, then `mv` it over the original. In `INSTRUCTIONS.md` change link destinations only, by this same rule, and count them for the notice; never change its words or a path it names in plain text.
	- b. **Correct old paths, in `DIRECTIVES.md` and `SETTINGS.md` only.** Change each `_Axis/{NAME}.md` of the eight to `_Config/{NAME}.md`, in text, code spans and fenced blocks alike, and nothing else. Leave one that is part of a longer path, directly after a letter, a digit, `.`, `/`, `-` or `_`, or directly before a letter, a digit, `-` or `_` (`../_Axis/TASKS.md`, `_Axis/TASKS.md-old`), and leave every link destination as 2a left it. With `d` the folder of the file and `n` its name without `.md`:

			d=_Axis; n=DIRECTIVES; e='(SETTINGS|INSTRUCTIONS|MINDSET|DIRECTIVES|PROJECT|PLAN|INITIATIVES|TASKS)\.md'; b=$(grep -oE "_Config/$e" $d/$n.md | wc -l)
			cp -p $d/$n.md $d/.$n.md.tmp && LC_ALL=C sed -E -e :a -e 's#(^|[^[:alnum:]_./-])_Axis/'"$e"'($|[^[:alnum:]_-])#\1_Config/\2.md\3#' -e ta $d/$n.md > $d/.$n.md.tmp && mv $d/.$n.md.tmp $d/$n.md && echo "$n.md: $(( $(grep -oE "_Config/$e" $d/$n.md | wc -l) - b )) corrected"

		The command does not know links: put back a change it made inside a link destination, such as after `#` or `parent:`. Keep each file's count for the notice.
	- c. **Receipt.** Take the SHA-256 of `_Axis/{NAME}.md` as it now is (`shasum -a 256`, `sha256sum` or `openssl dgst -sha256`). A `Reference move` Log that already holds this source, target and SHA-256 is used again. Otherwise run `python3 _Axis/Resources/record-check.py record-move --session {Session ID} --path _Axis/{NAME}.md --to _Config/{NAME}.md --reason 'Project files to _Config'`, or without Python write a new Log, named by the entry's timestamp command, with exactly:

			Reference move

			by: Main Agent
			session: {Session ID}

			```axis-record-receipt
			{
			  "kind": "move",
			  "reason": "Project files to _Config",
			  "schema": 1,
			  "sha256": "{SHA-256}",
			  "source": "_Axis/{NAME}.md",
			  "target": "_Config/{NAME}.md"
			}
			```

	- d. **Move, never by a hard link.** `cp -p _Axis/{NAME}.md _Config/.{NAME}.md.tmp`; confirm `_Config/{NAME}.md` is absent; `mv -n _Config/.{NAME}.md.tmp _Config/{NAME}.md`; confirm the temporary file is gone and `_Config/{NAME}.md` has the receipt's SHA-256; only then `rm _Axis/{NAME}.md`.
3. For each `redundant:` file: apply 2a and 2b (`d=_Config`) to the copy in `_Config/`, then move the old copy to `_Trash/{YYYY-MM-DD}--{NAME}.md` under the naming of [Practices > Trash]. No receipt.
4. **Repair links in editable records.** In open Tasks, open Follow-Ups, open Reminders, Notes, Ideas, the index files in `_Axis/` that carry no checksum, and live Memos (`_Memos/*.md`), change each link destination that resolves to `_Axis/{NAME}.md` so that it resolves to `_Config/{NAME}.md`, keeping its fragment: in `_Axis/Tasks/`, `../PLAN.md` becomes `../../_Config/PLAN.md`. Leave every write-once, archived, coordination or checksummed record, and every Task, Follow-Up or Reminder that is closed on disk or at the last commit: its old link resolves as a historical link, which warns and never blocks.
5. **Correct path fields.** In `blocks:` of open Follow-Ups and `target:` of open Reminders, replace each `_Axis/{NAME}.md` by `_Config/{NAME}.md`. Do not advance `updated:`.
6. **Notice, Log and checkpoint.** Tell User in one notice with the greeting: the files moved and the old copies sent to the Trash; the links changed inside code and the forms left that now break (2a); the number of link destinations adjusted in `INSTRUCTIONS.md`; the number of old paths corrected in `SETTINGS.md` and in `DIRECTIVES.md` (2b); the records repaired and fields corrected; every other mention of `_Axis/{NAME}.md` left as text inside the project files, by count and place, unchanged; each entry of `_Axis/EXCEPTIONS.md` that names a project file, to renew under [Practices > LinkMaintenance]; and that a Dashboard server started earlier must be restarted. Log one Event with Subject `Project files moved to _Config`. When this start adopted an update, the move enters the adoption checkpoint; otherwise commit it before ordinary work under [Practices > GIT > Update checkpoints]. Without Git, say that no checkpoint was made.
7. Clear `_Axis/Flags/config-move` when this start is complete, after its `Session Started` Log; a start interrupted before that runs the step again and repeats the notice.
