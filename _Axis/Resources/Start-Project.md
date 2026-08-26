# Start Project
> **Purpose:** Start a new project.

## Step 1: Choose Setup Path

1. Offer User the choice (verbatim):
   "Quick Setup? (Standard Profile, project name, and one paragraph.) ... or ... Interactive Setup? (Deep Q&A to thoroughly assess project.)"
2. If User picks Quick Setup:
	- a. Quietly update [Settings] with the Standard Profile values from [Template-Profiles], and log an Event with subject `Profile selected: Standard (Quick Setup)`.
	- b. Ask User for the project's name (< 20 chars) and one paragraph of background.
	- c. Update `_Axis/PROJECT.md`: set the name in the `# Project:` header (Line 1), fill `## Background` with the paragraph, and remove the remaining placeholder sections (User can add any of them back later).
	- d. Quietly compare the provenance stamp in `_Axis/MINDSET.md` to the Mindset Settings in `_Axis/SETTINGS.md`; regenerate via `_Axis/Resources/Draft-Mindset.md` only on a mismatch (the shipped Mindset already matches Standard).
	- e. Quietly save the Flag `_Axis/Flags/skip-wiki` (Wiki setup is deferred on Quick Setup).
	- f. Tell User in one line: the Wiki (`^wiki`), a formal Plan (`^plan`), and version control are all available later - just ask. GOTO Step 8.
3. If User picks Interactive Setup: continue with Step 2.

## Step 2: Profile

Ask User if they want to select a pre-configured Profile for the Project.

- If Yes:

	- Present Description and Examples for each Profile from `_Axis/Resources/Template-Profiles.md` to the User.

	- Ask User to select a Profile.

- If No: quietly assume User has selected the **Standard Profile**.

Finally, implement the User's selection:

- Log an Event with subject `Profile selected: {ProfileName}`.

- Update the values of [Settings] with values prescribed by [Template-Profiles].

## Step 3: Settings

Ask User if they want to now step through each Setting, and adjust them one-by-one.

- If Yes:
	- Step through each Setting in `_Axis/SETTINGS.md`.
	- Explain each setting to the User.
	- Explain the potential range of values for the setting to the User.
	- Ask User to select a value for the setting.
	- Update `_Axis/SETTINGS.md` with the new value (override previous value).

- If No: Explain that values for the selected Profile will be used.

## Step 4: Mindset

Follow `_Axis/Resources/Draft-Mindset.md` to lookup textual guidance for the selected Settings and merge them into a new behavioral Mindset.


## Step 5: Project

Ask User if they want assistance in setting up a new Project.

- If Yes:

	- Interview User until you are 95% confident you understand the complete background context for the project and what User wants to now accomplish.

	- Draft (or re-draft) `_Axis/PROJECT.md`.

- If No:

	- Ask User to complete `_Axis/PROJECT.md`.

	- Wait for User to complete the file and inform you it is ready to proceed.

	- Read User's version of `_Axis/PROJECT.md`.

	- If you have any remaining questions, and/or there are uncompleted placeholders, then go ahead and interview User until you are 95% confident you understand the complete background context for the project and what User wants to now accomplish, and update `_Axis/PROJECT.md`.

Finally, check the drafted Project once: if its primary deliverable is a software codebase, say so in one line - Axis targets knowledge and document projects, and the host's coding tools (or a coding-first editor) will serve the code itself better, while Axis manages the surrounding project (plan, decisions, notes, reports). Then continue either way and do not raise it again; whether to run Axis on a coding project is User's call.

## Step 6: Wiki

Ask User if they want to set up the Wiki.

- If Yes:
	- Follow `_Axis/Resources/Start-Wiki.md` to interview User and set up Wiki.

- If No:
	- Inform User they can ask the Agent to set up the Wiki later.
	- Save a Flag at `_Axis/Flags/skip-wiki`

## Step 7: Plan

Ask User if they want to work with you to draft a Plan to govern the Project.

- If No:
	- Log "No Plan"
	- In `_Axis/PLAN.md`, replace the placeholder body of each of the three sections with "No Plan - working from Tasks only."
	- Make a Note that there is no Formal Plan - instead, Agents only work on Tasks.

- If Yes:
	- Run the `^plan` command in `_Axis/Commands/plan.md`

## Step 8: Transfer Root Ownership

1. Quietly verify `_Axis/PROJECT.md` contains no `{{`. If any remain: on the Interactive path, return to Step 5. On the Quick Setup path, do not send User into the Interactive interview - remove or fill the leftover placeholder sections yourself, asking a single question only where content is genuinely required, then continue.
2. Follow `_Axis/Resources/Refresh-Project-README.md` in Project Setup mode. This replaces only a pristine Axis root README, preserves customized content, retains the Axis User Manual at `_Axis/README.md`, and resolves the root `LICENSE` lifecycle without choosing a license for the User.
3. Quietly write a current UTC timestamp into the Flag `_Axis/Flags/project-ready` (overwrite if present). Project Setup is not complete until the README and license ownership decision has been resolved, including a safely preserved malformed or customized root file reported to User.
4. On the Quick Setup path, GOTO Step 10. On the Interactive path, continue to Step 9.

## Step 9: Version Control and Portable Git (optional)

Version control gives the project an undo history; a private remote can also carry saved checkpoints between computers (see [Practices > GIT]).

- Read `host-shell` under [Practices > Flags > Reading Flags]. Unless it is valid `yes`, skip this step quietly.
- Quietly check whether the project is already under version control: run `git rev-parse --show-toplevel` from the project root.
	- If it returns the project root, a repository already exists - skip this step.
	- If it returns a PARENT folder and the current Project passes [Practices > Subprojects > Recognition Contract], STOP at [Practices > GIT > Decision Point and Record]: explain the three supported arrangements and ask User to choose parent-tracked, independent ignored repository, or intentional submodule. Apply, verify, and record the selected arrangement before continuing.
	- If it returns a PARENT folder but the current Project is not a recognized Subproject, warn User that this placement is outside the Axis Subproject contract and ask whether to leave it managed by the parent repository or manage it as a nested Subproject before creating its own repository.
	- If it returns nothing, ask User: "Axis can set up version control for this project, starting with a private local undo history. After that you can choose whether to connect a private remote for computer-to-computer handoff. Set it up?"
- If Yes: run the setup portion of `^git`: initialize the repository, make the first commit, then offer the optional private remote. If User connects one, explain that `^save` sends and `^resume` receives linear checkpoints automatically; only one computer may write at a time.
- If No: note that User can type `^git` at any time, and continue.

## Step 10: Wrap Up

1. Quietly verify the `project-ready` Flag is valid and the root README lifecycle from Step 8 was resolved. If either check fails, return to Step 8 and do not claim setup completed.
2. Close with a short hint card:
	- Type `^help` to list all commands.
	- The Project README is `README.md`; the Axis User Manual remains at `_Axis/README.md` and `^help readme` browses it by section.
	- Drop ordinary files anywhere in the project folder - Agents organize them into Project Subfolders; suffix a folder `_U` for Agent-read-only or `_X` to exclude it; a complete nested Axis Project anywhere in the workspace is a Subproject; Wiki sources go to immutable `Wiki/Inbox/`; keep originals outside the project when they need operating-system-enforced protection.
	- Ask for a Plan (`^plan`) or the Wiki (`^wiki`) whenever you are ready.
	- New to Axis? `^onboard` gives you a five-minute tour.
