# Manifest
> **Purpose:** Define core folders and files used with Axis Workflow.

## Project

### Folders

- **`_Axis/`** - Control folder for Axis Workflow.
- **`_Axis/Secrets/`** - Secrets (keys, tokens, credentials).
- **`_Temp/`** - Scratch space for regenerable files.
- **`_Trash/`** - Deletion staging - files waiting for the next sweep.
- **`Wiki/`** - Knowledge base for project.

### Files

- **`.gitignore`** - Git exclusions.
- **`.gitattributes`** - Narrow LF text rules for Axis-owned protocol files.
- **`AGENTS.md`** - Entry-point file (AGENTS convention: Codex, etc.); master copy.
- **`CLAUDE.md`** - Entry-point file (Claude Code / Cowork); synced from `AGENTS.md`.
- **`GEMINI.md`** - Entry-point file (Gemini CLI); synced from `AGENTS.md`.
- **`README.md`** - Before setup, generated display copy of the Axis User Manual; after setup, User-owned Project README with one bounded Axis summary block.
- **`LICENSE`** - Before setup, generated display copy of the Axis FSL-1.1-MIT License; after setup, User-owned or absent. Project Setup removes only the pristine Axis copy.

## Axis

### Folders

- `_Axis/Agents/`
- `_Axis/Tracking/`
- `_Axis/Archive/`
- `_Axis/Audit/`
- `_Axis/Commands/`
- `_Axis/CX/`
- `_Axis/Dashboard/`
- `_Axis/Flags/`
- `_Axis/Followups/`
- `_Axis/Reminders/`
- `_Axis/Ideas/`
- `_Axis/Logs/`
- `_Axis/Notes/`
- `_Axis/Practices/`
- `_Axis/Rules/`
- `_Axis/Requests/`
- `_Axis/Resources/`
- `_Axis/Snapshots/`
- `_Axis/Status/`
- `_Axis/Supervision/`
- `_Axis/Tasks/`

### Files

- `_Axis/CHANGELOG.md`
- `_Axis/CLA.md` - Canonical Contributor License Agreement and Copyright Assignment.
- `_Axis/CONTRIBUTING.md` - Contribution intake policy and CLA gate.
- `_Axis/LICENSE` - Canonical FSL-1.1-MIT License and trademark notice for Axis-authored Workflow files.
- `_Axis/README.md` - Canonical Axis User Manual; explanatory and lazy-loaded during ordinary operation.
- `_Axis/DIRECTIVES.md`
- `_Axis/ENVIRONMENT.md`
- `_Axis/GLOSSARY.md`
- `_Axis/INSTRUCTIONS.md`
- `_Axis/MANIFEST.md`
- `_Axis/MINDSET.md`
- `_Axis/PLAN.md`
- `_Axis/PRACTICES.md`
- `_Axis/PRINCIPLES.md`
- `_Axis/PROJECT.md`
- `_Axis/RULES.md`
- `_Axis/SETTINGS.md`
- `_Axis/SNAPSHOTS.md`
- `_Axis/TASKS.md`

- `_Axis/Dashboard/index.html`
- `_Axis/Dashboard/mermaid-11.16.1.min.js` - pinned Mermaid renderer.
- `_Axis/Dashboard/mermaid-LICENSE.txt` - Mermaid's MIT license.
- `_Axis/Dashboard/server.py`
- `_Axis/Dashboard/plan-diagram.{mermaid|svg|png}` - optional Plan illustration.

### Practices

- `_Axis/Practices/Agents.md`
- `_Axis/Practices/Archiving.md`
- `_Axis/Practices/Commands.md`
- `_Axis/Practices/CX.md`
- `_Axis/Practices/Dashboard.md`
- `_Axis/Practices/Delegation.md`
- `_Axis/Practices/Directives.md`
- `_Axis/Practices/Flags.md`
- `_Axis/Practices/Folders.md`
- `_Axis/Practices/Followups.md`
- `_Axis/Practices/GIT.md`
- `_Axis/Practices/Ideas.md`
- `_Axis/Practices/IndexDetail.md`
- `_Axis/Practices/Logs.md`
- `_Axis/Practices/Markers.md`
- `_Axis/Practices/Mindset.md`
- `_Axis/Practices/Notes.md`
- `_Axis/Practices/OpenClaw.md`
- `_Axis/Practices/Portability.md`
- `_Axis/Practices/Planning.md`
- `_Axis/Practices/References.md`
- `_Axis/Practices/Requests.md`
- `_Axis/Practices/Reminders.md`
- `_Axis/Practices/Settings.md`
- `_Axis/Practices/Snapshots.md`
- `_Axis/Practices/Status.md`
- `_Axis/Practices/Subprojects.md`
- `_Axis/Practices/Supervision.md`
- `_Axis/Practices/Tasks.md`
- `_Axis/Practices/Protected.md`
- `_Axis/Practices/Timestamps.md`
- `_Axis/Practices/Tracking.md`
- `_Axis/Practices/Trash.md`
- `_Axis/Practices/WhatsApp.md`
- `_Axis/Practices/Wiki.md`

### Rules

- `_Axis/Rules/Budget.md`
- `_Axis/Rules/Capabilities.md`
- `_Axis/Rules/ExternalAgents.md`
- `_Axis/Rules/HostAndMeta.md`
- `_Axis/Rules/Indices.md`
- `_Axis/Rules/MarkersFlagsAndLocks.md`
- `_Axis/Rules/ProjectLayout.md`
- `_Axis/Rules/ProtectedContent.md`
- `_Axis/Rules/RecordsAndWORM.md`
- `_Axis/Rules/ReferencesAndLinks.md`
- `_Axis/Rules/Secrets.md`
- `_Axis/Rules/SettingsAndProfiles.md`
- `_Axis/Rules/Speaking.md`
- `_Axis/Rules/Style.md`
- `_Axis/Rules/Subagents.md`
- `_Axis/Rules/Timestamps.md`
- `_Axis/Rules/UntrustedContent.md`
- `_Axis/Rules/Wiki.md`

### Commands

- `_Axis/Commands/archive.md`
- `_Axis/Commands/audit.md`
- `_Axis/Commands/backup.md`
- `_Axis/Commands/cx.md`
- `_Axis/Commands/dashboard.md`
- `_Axis/Commands/demote.md`
- `_Axis/Commands/followups.md`
- `_Axis/Commands/git.md`
- `_Axis/Commands/help.md`
- `_Axis/Commands/idea.md`
- `_Axis/Commands/ideas.md`
- `_Axis/Commands/install.md`
- `_Axis/Commands/kill.md`
- `_Axis/Commands/log.md`
- `_Axis/Commands/note.md`
- `_Axis/Commands/notes.md`
- `_Axis/Commands/onboard.md`
- `_Axis/Commands/plan.md`
- `_Axis/Commands/profile.md`
- `_Axis/Commands/promote.md`
- `_Axis/Commands/reminders.md`
- `_Axis/Commands/refresh.md`
- `_Axis/Commands/resume.md`
- `_Axis/Commands/save.md`
- `_Axis/Commands/settings.md`
- `_Axis/Commands/shutdown.md`
- `_Axis/Commands/status.md`
- `_Axis/Commands/tasks.md`
- `_Axis/Commands/trash.md`
- `_Axis/Commands/undo.md`
- `_Axis/Commands/update.md`
- `_Axis/Commands/wiki.md`

### Resources

- `_Axis/Resources/Detect-Capabilities.md`
- `_Axis/Resources/Draft-Mindset.md`
- `_Axis/Resources/Lock-File.md`
- `_Axis/Resources/Load-Project-Overlay.md`
- `_Axis/Resources/Refresh-Project-README.md`
- `_Axis/Resources/secrets-capsule.sh` - optional encrypted Secrets transport helper.
- `_Axis/Resources/Start-External.md`
- `_Axis/Resources/Start-Project.md`
- `_Axis/Resources/Start-Session.md`
- `_Axis/Resources/Start-Subagent.md`
- `_Axis/Resources/Start-Wiki.md`
- `_Axis/Resources/Starting-Context.md` - Pre-compiled starting context.
- `_Axis/Resources/Template-LocalPrompt.md`
- `_Axis/Resources/Template-Mindset.md`
- `_Axis/Resources/Template-Profiles.md`
- `_Axis/Resources/axis-dashboard-meridian.png` - Versioned User Manual illustration of the default Dashboard.

## Wiki

### Folders

- `_Axis/Wiki/` - Wiki bookkeeping by Agents (indexes, activity, status, schema).
- `Wiki/Inbox/` - Raw input sources for the project (domain subject matter).
- `Wiki/` - Collection of markdown files forming a knowledge base.

### Files

- `_Axis/Wiki/Input-Index.md`
- `_Axis/Wiki/Library-Index.md`
- `_Axis/Wiki/Library-Activity.md`
- `_Axis/Wiki/Library-Status.md`
- `_Axis/Wiki/Library-Schema.md`
