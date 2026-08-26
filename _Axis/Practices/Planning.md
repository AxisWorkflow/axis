# Planning
> **Purpose:** Define how to draft, verify, and maintain the project Plan.

Agent should draft a Plan for every project:

- Include a high-level overview (a.k.a. an "Executive Summary").  
- Focus more on how parts fit together (less on execution details - those are in Tasks.)
- Include info-graphics, charts, and diagrams to help User understand the big picture.
- Keep the specifics of execution and implementation in Tasks - the Plan is high-level.
- Save Plan as `_Axis/PLAN.md` so User can inspect, approve, give feedback.
- Save the Plan illustration as `_Axis/Dashboard/plan-diagram.{mermaid|svg|png}`, overwriting any previous one, so the Dashboard renders the current diagram (see `^plan` step 7).
- Verify Plan with User before implementing.
- Revise Plan when User gives feedback or suggestions.

Planning mode is not just for preparing the Plan document. On any host harness with a "planning" mode, also use planning mode during regular work for:

- any non-trivial task that would require 3+ steps.
- a change to, or assessment of, every organizational decision.
- a change to, or assessment of, every architectural decision.
- at end of the project to verify work is ready and correct.
