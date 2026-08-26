# ^backup
> **Purpose:** Back up the entire project to a User-named location outside the project folder.

1. Read `host-shell` under [Practices > Flags > Reading Flags]. If it is not valid `yes`, tell User in one line that a backup needs a confirmed shell Capability, and STOP.

2. Ask User where to save the backup archive. The destination must be OUTSIDE the project folder: a backup stored inside the project is circular - it would vanish with the project, bloat the next backup, and leak into version control. Suggest a sensible example (e.g., `~/Backups/`). Never default to any path inside the project.

3. Validate the destination: resolve it to an absolute path and confirm it is not the project root or anything beneath the project root. If it is inside the project: explain the problem and re-ask once; if the second answer is still inside, STOP. If the destination folder does not exist, confirm with User and create it.

4. Ask User whether to include plaintext `_Axis/Secrets/` content, including inside nested Subprojects. Default is EXCLUDE PLAINTEXT. Under that default, retain each `.gitkeep`, `.recipient`, and `.capsule.age` because they are placeholder/public/encrypted transport state, but exclude `.binding` and every other Secrets entry. If User opts to include plaintext, warn in one line that the archive then contains credentials in plain text. The external private identity is outside the project and never enters either backup mode.

5. Build the archive from the parent directory of the project root, naming it `{name}-{yyyy.mm.dd.hh.mm.ss.xxxZ}.tar.gz` (where `{name}` is the Project Name from Line 1 of [Project] with spaces replaced by hyphens, or the project folder name if unset; timestamp per [Rules > Timestamps]). Under the default, use a staged exclusion list or verified archive filter that works for every nested `_Axis/Secrets/`: permit only the three retained basenames above and reject every other entry from those directories. Verify the archive listing before delivery. The archive otherwise captures the entire filesystem tree, including Subprojects, independent child repositories and their local `.git` history, submodule worktrees and metadata, `Wiki/` content, `_Temp/`, and (only if User opted in) plaintext Secrets. This is broader than the parent Git repository by design.

6. Verify the archive exists, has a plausible size (`ls -lh`), and obeys the selected Secrets policy. Report the full path and size to User, and Log one Event recording the destination and whether plaintext Secrets were excluded. STOP.
