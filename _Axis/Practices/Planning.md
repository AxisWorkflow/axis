# Planning
> **Purpose:** Define how to draft, verify, and maintain the project Plan.

Agent should draft a Plan for every project:

- Include a high-level overview (a.k.a. an "Executive Summary").  
- Focus more on how parts fit together (less on execution details - those are in Tasks.)
- Include info-graphics, charts, and diagrams to help User understand the big picture.
- Keep the specifics of execution and implementation in Tasks - the Plan is high-level.
- When related Tasks share an outcome, optionally use [Practices > Initiatives]. Put a brief Initiative summary and link in the Plan, shared decisions in [Initiatives], and execution details in Tasks. Standalone Tasks and projects without Initiatives remain valid.
- Save Plan as `_Axis/PLAN.md` so User can inspect, approve, give feedback.
- Save the Plan illustration as `_Axis/Dashboard/plan-diagram.{mermaid|svg|png}`, overwriting any previous one, so the Dashboard renders the current diagram (see `^plan` step 7).
- Verify Plan with User before implementing.
- Revise Plan when User gives feedback or suggestions.

Planning mode is not just for preparing the Plan document. On any host harness with a "planning" mode, also use planning mode during regular work for:

- any non-trivial task that would require 3+ steps.
- a change to, or assessment of, every organizational decision.
- a change to, or assessment of, every architectural decision.
- at end of the project to verify work is ready and correct.

## Strategic requests

For a strategy, priority, portfolio or completion judgment, including a Team or Committee mandate:

- Start from `_Axis/PROJECT.md` (mission, primary users, goals), then the whole portfolio in [Initiatives] and the Tasks, not only recent work. Recent incidents are inputs, not the agenda.
- Compare at least one strong alternative outside the most recent internal work, and name the evidence that would reverse the choice.
- Deliver the choice asked for; [Directives] > Accept the Decision Promised governs acceptance.
- A narrow, authorized fix stays narrow: it needs no portfolio review.
