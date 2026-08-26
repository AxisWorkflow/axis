# Style
> **Purpose:** Punctuation, bolding by audience, backticking, brand form, and step numbering.


- Prefer hyphen-minus (`-`) over en-dash (`–`) and em-dash (`—`) for punctuation.
- Use en-dash only for numeric ranges (e.g., `2026–2027`).
- Bolding splits by audience. Human-facing files (`_Axis/README.md`, the pre-setup root `README.md` display copy, `_Axis/PROJECT.md`, `_Axis/GLOSSARY.md`) may bold Glossary terms freely for human readability.
- Machine-facing files (all other `_Axis/` files, the entry-point files, and the Wiki stubs) do NOT bold terms of art - capitalization, Axis References, and backticked literals carry the meaning.
- In machine-facing files, reserve bold for imperative emphasis (e.g., do **not** skip), structural labels (`**Purpose:**`), definition-list leads (`- **X** - ...`), Setting names, and enumerated literals (e.g., Task Status values).
- Never bold headings or Axis References.
- Backtick every literal path, filename, command, token, and Flag name - including any raw file path that is not a markdown link or Axis Reference.
- Square brackets are reserved for Axis References and markdown links.
- The brand is `Axis Workflow`; in running prose write it out, or use the short forms `Axis` and capital-W `Workflow`. Lowercase `workflow` stays a generic word - never use it for the brand.
- The brand is never written all-caps. The all-caps form appears only inside machine tokens (`<<AXIS:SUBAGENT>>`, `<<AXIS:ROLE:...>>`, `OK-AXIS`) and the Session ID banner block in [Start-Session] (display context).
- Executable files (Commands, and the protocols in Resources) use numbered steps with explicit STOP / GOTO / skip language; narrative context lives in Practices and the README.
- Number steps at ONE level only. Nested sub-steps use hyphen-letter bullets (`- a.`, `- b.`, ...): letters cannot collide with outer step numbers in GOTO references, and bare `a.` lines are not CommonMark lists (they render as run-on paragraphs).
