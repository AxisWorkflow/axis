# References
> **Purpose:** Define the Axis Reference notation and the resolver table that maps every reference to its file.

An Axis Reference is an internal pointer to another file (and optionally a section > subsection) of the Axis Workflow. It takes the form [File], [File > Section], or [File > Section > Subsection] - single brackets NOT followed by a `(...)` path (which would make it a markdown link). Resolve every reference with the table below - there is no heuristic resolution.

## Resolver Table

| Reference | Resolves to |
| --- | --- |
| [Project] | `_Axis/PROJECT.md` |
| [Axis README] | `_Axis/README.md` |
| [Project README] | `README.md` |
| [Axis License] | `_Axis/LICENSE` |
| [Glossary] | `_Axis/GLOSSARY.md` |
| [Manifest] | `_Axis/MANIFEST.md` |
| [Practices] | `_Axis/PRACTICES.md` |
| [Practices > X] | `_Axis/Practices/{X}.md` |
| [Principles] | `_Axis/PRINCIPLES.md` |
| [Rules] | `_Axis/RULES.md` |
| [Rules > X] | `_Axis/Rules/{X}.md` |
| [Mindset] | `_Axis/MINDSET.md` |
| [Settings] | `_Axis/SETTINGS.md` |
| [Directives] | `_Axis/DIRECTIVES.md` |
| [Plan] | `_Axis/PLAN.md` |
| [Tasks] | `_Axis/TASKS.md` |
| [Snapshots] | `_Axis/SNAPSHOTS.md` |
| [Dashboard] | `_Axis/Dashboard/` |
| [Detect-Capabilities], [Resources > Detect-Capabilities] | `_Axis/Resources/Detect-Capabilities.md` |
| [Draft-Mindset], [Resources > Draft-Mindset] | `_Axis/Resources/Draft-Mindset.md` |
| [Lock-File], [Resources > Lock-File] | `_Axis/Resources/Lock-File.md` |
| [Refresh-Project-README], [Resources > Refresh-Project-README] | `_Axis/Resources/Refresh-Project-README.md` |
| [Start-Project], [Resources > Start-Project] | `_Axis/Resources/Start-Project.md` |
| [Start-External], [Resources > Start-External] | `_Axis/Resources/Start-External.md` |
| [Start-Session], [Resources > Start-Session] | `_Axis/Resources/Start-Session.md` |
| [Start-Subagent], [Resources > Start-Subagent] | `_Axis/Resources/Start-Subagent.md` |
| [Start-Wiki], [Resources > Start-Wiki] | `_Axis/Resources/Start-Wiki.md` |
| [Starting-Context], [Resources > Starting-Context] | `_Axis/Resources/Starting-Context.md` |
| [Template-LocalPrompt], [Resources > Template-LocalPrompt] | `_Axis/Resources/Template-LocalPrompt.md` |
| [Template-Mindset], [Resources > Template-Mindset] | `_Axis/Resources/Template-Mindset.md` |
| [Template-Profiles], [Resources > Template-Profiles] | `_Axis/Resources/Template-Profiles.md` |
| [Wiki > Admin > Input-Index] | `_Axis/Wiki/Input-Index.md` |
| [Wiki > Admin > Library-Index] | `_Axis/Wiki/Library-Index.md` |
| [Wiki > Admin > Library-Activity] | `_Axis/Wiki/Library-Activity.md` |
| [Wiki > Admin > Library-Status] | `_Axis/Wiki/Library-Status.md` |
| [Wiki > Admin > Library-Schema] | `_Axis/Wiki/Library-Schema.md` |

Rules of use:

- A deeper form ([File > Section] or [File > Section > Subsection]) names real headings inside the resolved file.
- [Settings > X] names the `### X` Setting inside `_Axis/SETTINGS.md`; [Practices > X] and [Rules > X] each resolve to the single-token file in their own folder, per their table rows.
- Any reference whose base form is not in this table is invalid: fix the reference, or extend the table AND the matching integrity check in the same change.
- Reference names are logical, not literal paths: [Project] resolves to `_Axis/PROJECT.md`, and the [Wiki > ...] rows resolve into `Wiki/` - the table, not the bracket text, carries the path. Never rename a reference just because a folder moved; update its row instead.

## Axis User Manual Boundary

The Axis User Manual at [Axis README] is explanatory, never operational authority. Session Start and ordinary work do not load it. Load one relevant section only when User requests it through `^help` or when the shipped Command, Practice, and Rule set leaves a genuine ambiguity and the host establishes a high-capability frontier Main Agent. External Agents and Subagents do not use the manual as a fallback. Development Mode follows its own protocol and loads the complete manual for maximal implementation context.
