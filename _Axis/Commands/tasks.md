# ^tasks
> **Purpose:** List Tasks at a glance, and optionally apply a quick update.

1. Read `_Axis/TASKS.md` (and [Practices > Tasks] if not already loaded).

2. If the command has no additional text: present the Tasks grouped by Status (**Active** and **Blocked** first, then **Completed** and **Cancelled**), each with its name, label, and age. Then STOP.

3. If the command has additional text: interpret it as an update instruction (e.g., "complete Draft-Report", "block Survey on vendor reply", "add a task to review pricing").
	- a. Restate the change you intend to make and confirm with User.
	- b. Apply it per [Practices > Tasks] - index entry and detail file together; write or advance `updated:` for every material change; respect the WORM rules for terminal Tasks.
	- c. Set `delivers:` when the task aims at a Deliverable in `_Axis/PROJECT.md`, and when closing a task that carries one, record its output paths under `## Produced` in the detail file.
	- d. When blocking a Task on an action only User can take, load [Practices > Followups] and create or reuse the canonical Follow-Up in the same pass. Keep the Task **Blocked**. Do not create a Follow-Up for a non-User dependency.
	- e. Close an exact linked Reminder when the resulting Task state deterministically completes or cancels its target; do not close a loosely related Reminder.
	- f. Log one Event for the change (one Event may cover the paired Task, Follow-Up, and Reminder mutation). STOP.
