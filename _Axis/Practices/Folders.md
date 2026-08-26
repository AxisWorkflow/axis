# Folders
> **Purpose:** Define how Main Agent creates and manages Project Subfolders.

The project root is an open workspace. The Workflow reserves three underscore-prefixed folders - `_Axis/` (the Workflow, including `_Axis/Secrets/` for credentials and `_Axis/Wiki/` for Wiki admin), `_Temp/` (regenerable scratch), and `_Trash/` (deletion staging) - plus one Workflow-managed plain folder, `Wiki/` (the readable knowledge base, with its `Wiki/Inbox/` dropbox). The rule of thumb: User may ignore every underscore-prefixed folder entirely and work through their Agent instead - the one exception is depositing a secret file into `_Axis/Secrets/` by hand, because secrets should never transit chat. Every other folder in the project root is a Project Subfolder: ordinary content, created and organized as the work demands. A folder anywhere in the workspace that carries the Standard Setup Anchors is a Subproject - a complete nested Axis Project owned by User under [Practices > Subprojects]; the parent's Main Agent never creates, moves, renames, reorganizes, or deletes one without explicit User approval. This is what makes install "drop in the reserved folders and entry files, and go" - no content structure is imposed up front.

- Any file inside the project is readable and editable by Agents unless its name says otherwise: a trailing `_U` marks User-controlled read-only content and `_X` marks content invisible to Agents (see [Practices > Protected]). `Wiki/Inbox/` is an immutable dropbox for raw Wiki sources. Users who need technically untouchable originals keep them outside the project folder.

- Main Agent creates Project Subfolders as work is generated: when a work product has no natural home, create one with a short, clear, human-readable name (e.g., `Reports/`, `Drafts/`, `Data/`, `Research/`). Prefer a few broad Subfolders over many narrow ones. Creating a new Subfolder for new work needs no approval.

- ONLY Main Agent creates, renames, merges, splits, moves, or retires Project Subfolders. Subagents never touch folder structure - they route any folder need through Main Agent. A single structure owner prevents race conditions and contention.

- REORGANIZING existing content (rename, consolidate, divide, or move files between Subfolders) requires User approval first: propose the change, apply it only on a Yes.

- Creating or installing a Subproject (a complete anchor-carrying Axis Project nested in the workspace) also requires User approval. Before doing it, load [Practices > Subprojects] and [Practices > GIT > Decision Point and Record], ask User which repository arrangement to use, and record the applied choice.

- Log an Event when a Subfolder is created or a reorganization is applied, so the structure's history stays auditable.

- All Project Subfolders are version-controlled. Subprojects follow one of the explicit parent-tracked, independent-repository, or submodule arrangements in [Practices > GIT]. `_Temp/`, `_Trash/`, plaintext `_Axis/Secrets/` content, Wiki content, and ephemeral session state stay out of Git by default; configured encrypted Secrets transport tracks only its public recipient and ciphertext.

- Never delete a file you did not create as scratch without User confirmation (see [Rules]).
