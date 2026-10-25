# References
> **Purpose:** Define Axis References and their file resolver.

Axis References point to Workflow files or sections: [File], [File > Section], [File > Section > Subsection]. Their brackets have no following `(...)` path; that would be a Markdown link. Resolve each through this table, never heuristically.

## Resolver Table

| Reference | Resolves to |
| --- | --- |
| [Project] | `_Axis/PROJECT.md` |
| [User Manual] | `_Axis/USERMANUAL.md` |
| [Specification] | `_Axis/SPECIFICATION.md` |
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
| [Initiatives] | `_Axis/INITIATIVES.md` |
| [Snapshots] | `_Axis/SNAPSHOTS.md` |
| [Dashboard] | `_Axis/Dashboard/` |
| [Detect-Capabilities], [Resources > Detect-Capabilities] | `_Axis/Resources/Detect-Capabilities.md` |
| [Draft-Mindset], [Resources > Draft-Mindset] | `_Axis/Resources/Draft-Mindset.md` |
| [Check-Remote-Freshness] | `_Axis/Resources/Check-Remote-Freshness.md` |
| [Check-Update-Handoff] | `_Axis/Resources/Check-Update-Handoff.md` |
| [Lifecycle-Presentation] | `_Axis/Resources/Lifecycle-Presentation.md` |
| [Continue-Session] | `_Axis/Resources/Continue-Session.md` |
| [Load-Starting-Context] | `_Axis/Resources/Load-Starting-Context.md` |
| [Displaced-Session], [Resources > Displaced-Session] | `_Axis/Resources/Displaced-Session.md` |
| [Claim-Session], [Resources > Claim-Session] | `_Axis/Resources/Claim-Session.md` |
| [Lock-File], [Resources > Lock-File] | `_Axis/Resources/Lock-File.md` |
| [Load-Project-Overlay], [Resources > Load-Project-Overlay] | `_Axis/Resources/Load-Project-Overlay.md` |
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

- Deeper forms name real headings in the resolved file.
- [Settings > X] names the `### X` Setting inside `_Axis/SETTINGS.md`; [Practices > X] and [Rules > X] each resolve to the single-token file in their own folder, per their table rows.
- Unlisted base forms are invalid. Fix the reference or extend this table AND its integrity check together.
- References are logical names: [Project] resolves to `_Axis/PROJECT.md`; [Wiki > ...] rows resolve into `_Axis/Wiki/`. The table supplies paths. When folders move, update the row; never rename the reference solely for that move.

## Documentation Boundary

The [User Manual] and [Specification] explain Axis; they are never operational authority. Session Start and ordinary work do not load them. Load one relevant section only on User's `^help` request, or when the shipped Commands, Practices and Rules leave a genuine ambiguity and the host establishes a high-capability frontier Main Agent. External Agents and Subagents never use them as a fallback. A validated project overlay does not change this boundary.
