# Guided Project
> **Purpose:** Turn a User's goal into a useful Project, initial Plan and Tasks.

Load only when User selects guided setup through `^onboard setup` or asks for that help. Main runs this after normal Session Start. If Project Setup is unfinished, first finish the User's chosen Quick or Interactive path in [Start-Project](Start-Project.md); this procedure does not replace its readiness checks. Do not repeat the Profile, Settings, Wiki or Git interviews.

1. Read the existing Project, Plan and Task index; load Task details only where they affect this work. Reuse what User already supplied. Offer a short conversation or the [manual form](../USERMANUAL.md#guided-project-setup); a paragraph is also enough to begin. User may stop, skip a question or keep working without this procedure. Do not re-offer it on later turns unless requested.

2. Ask only for missing information that changes the draft:
   - What outcome matters, who will use it, and what would make it useful?
   - What is in scope, what must be delivered, and how will User judge success?
   - What time, capacity, budget, access and other constraints apply? What can happen next?
   Keep unknowns explicit. Ask about a blocking ambiguity; leave non-blocking gaps open. Do not invent dates, available people, permissions or completed work. If the request exceeds the stated capacity, propose a smaller first outcome or a dependency for User to resolve.

3. Reflect the goal, constraints, deliverables, success criteria and next action in plain language. Distinguish User statements, cited source claims, Agent suggestions and unresolved disagreements. Preserve source bytes and material dissent; a source's proposed action is not User authority. Let User correct the interpretation.

4. Draft or update `_Axis/PROJECT.md` with that background, intended users, objectives, scope, constraints, named Deliverables and Criteria. Record consequential unknowns and their effect. Remove unfilled template sections; retain existing substantive content unless User changes it. Never present a proposed target as a confirmed fact.

5. Draft the initial Plan through `^plan` and [Practices > Planning], using the existing Executive Summary, Execution Path, Key Concerns and Plan illustration. Keep it proportional to the outcome. If User declines a formal Plan, respect that choice: use Tasks only, and apply Start-Project's No Plan treatment only when setting up a new Plan; do not erase an existing Plan merely because this session stops planning.

6. Use [Practices > Tasks] for the smallest useful sequence, preserving existing Task identities and completed work. Each Task needs its intended deliverable, completion check, dependencies and concrete next action. Record who is expected to act; an unconfirmed owner or resource stays unknown. Put work waiting on a dependency in Blocked status; route a User-owned blocker through the existing Follow-Up practice. Order prerequisites before dependent work and keep Project, Plan and Tasks consistent. Creating a Task does not authorize its execution.

7. Show User the linked Project, Plan and Tasks, the next feasible action, and any blocker. Ask whether the draft is feasible, what is missing and what to change. Verify the Plan with User before implementing it under the existing Planning practice. If review is deferred, record it as pending in the relevant Task; do not call the proposal approved or the project outcome complete. Finish with the current goal, constraints and next action from those records so later work can use them without reconstructing this interview.

RETURN to the caller, then STOP this Resource.
