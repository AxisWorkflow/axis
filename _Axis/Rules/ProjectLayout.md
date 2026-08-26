# Project Layout
> **Purpose:** Where things live: reserved folders, Project Subfolders, placeholders, and what is editable.


- Project root is the folder with the entry-point files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`).
- The Workflow reserves exactly three underscore-prefixed folders - `_Axis/` (the Workflow, with `_Axis/Secrets/` and `_Axis/Wiki/` inside), `_Temp/` (regenerable scratch), `_Trash/` (deletion staging - see [Practices > Trash]) - plus the Workflow-managed `Wiki/` (with `Wiki/Inbox/`). User may ignore every underscore-prefixed folder and work through their Agent; the one exception is depositing secrets into `_Axis/Secrets/` by hand. Every other root folder is a Project Subfolder (see [Practices > Folders]).
- A Subproject is any folder carrying the Standard Setup Anchors per the recognition contract in [Practices > Subprojects]. A folder is not a Subproject merely because it carries `_Axis/` alone; a candidate that fails the contract is an incomplete candidate, not a Subproject. Parent Main Agent never creates, moves, renames, reorganizes, or deletes a Subproject without explicit User approval.
- There is no `Templates/` directory by design; every file in the repo is a working file.
- Working files may contain `{{...}}` placeholders for Agent or User to fill over time.
- When User fills in a placeholder, replace the entire `{{...}}` portion with real content.
- Remove placeholders and stubs once there is a real entry to follow.
- There is no general-purpose read-only inbound folder. Ordinary project files are readable and editable by Agents, but the in-project protection exceptions are authoritative: `_U` content is read-only, `_X` content is neither read nor written (see [Rules > ProtectedContent]), and `Wiki/Inbox/` is an immutable inbox for raw Wiki sources. Keep originals outside the project when they require operating-system-enforced protection rather than an instruction-level boundary.
- User may add or edit any file at any moment - re-read a file (check its `mtime`) before overwriting it; stale reads are how Agents clobber human work.
- Routing: source documents meant for the knowledge base go to `Wiki/Inbox/`; ordinary project content lives in Project Subfolders; a complete nested Axis Project (a Subproject) may live anywhere in the workspace.
- The placement rule: `_Temp/` holds only what the Agent could regenerate without loss - anything whose deletion would require an apology belongs in a Project Subfolder.
- Project Subfolders hold living content: updated, revised, and redistributed as the project moves.
- The Workflow's own records (Notes, Logs, Snapshots, Tasks, Follow-Ups, Reminders, Status Reports) are neither scratch nor deliverables: they stay in `_Axis/`, always.
- Project Subfolders ARE version-controlled - User can ask Agent to roll back any file. Subprojects follow an explicit version-control arrangement in [Practices > GIT]. `_Temp/`, `_Trash/`, plaintext `_Axis/Secrets/` content, Wiki content, and ephemeral session state stay out of Git by default; only the optional public recipient and encrypted Secrets capsule are tracked from that directory.
- When reading documents or images, always attempt to extract embedded text.
