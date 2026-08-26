# ^plan
> **Purpose:** Draft (or redraft) a Project Plan and harmonize it with Tasks.

1. Assess how complicated the underlying problem and objectives of the project actually are, so you can target an appropriate level of complexity for the Plan.

2. If a Plan already exists (you are updating it): assess how well the previous Plan reflected actual progress.
	- If expectations were out of sync with reality: reconsider what needs to change.
	- If the Plan was needlessly complex: look for ways to simplify.

3. Assess how the high-level Plan and the low-level Tasks fit together into a coherent whole.
	- If they conflict or do not reinforce each other: STOP, reassess, and redraft before continuing.
	- Cancel obsolete tasks (Status **Cancelled**, stamp the *Cancelled* field, leave *Completed* as `N/A`, record the reason in the detail file). Do NOT mark abandoned tasks as **Completed** - that breaks the WORM rule.
	- Draft new Tasks that fit the new Plan.

4. Draft a 1-3 paragraph Executive Summary and insert it into the `## Executive Summary` section of `_Axis/PLAN.md`.

5. Identify key stages and milestones and save them into the `## Execution Path` section of `_Axis/PLAN.md`.

6. Generate 1-5 key concerns that might hold back the project and save them into the `## Key Concerns` section of `_Axis/PLAN.md`.

7. Generate a summary illustration as a Mermaid diagram (`.mermaid`) or SVG (fall back to PNG if an image tool is available). Save it as `_Axis/Dashboard/plan-diagram.{mermaid|svg|png}`, overwriting any previous diagram - exactly one Plan diagram exists at a time, and the Dashboard renders that name - then add a link to it at the top of `_Axis/PLAN.md`.

8. Log one Event recording the Plan revision: what changed, and which Tasks were added or cancelled. STOP.
