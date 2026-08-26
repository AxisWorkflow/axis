# Ideas
> **Purpose:** Define how to record, format, and review Ideas.

Ideas are thoughts that _might_ apply to the project, but need more exploration and consideration. Ideas are precursors to elements that could eventually be incorporated into the Plan, added as a Task, included as a new **Objective**, etc.

Ideas can result from:

- brainstorming (perhaps during discussions between User and Agent)
- dreaming by a Subagent (perhaps during a scheduled loop each night)
- reflecting on the project (e.g., when User asks for a reflection or review)
- drafting a Status Report
- reviewing a Cross-Examination (perhaps as a result of Main Agent reviewing report)
- exploration by Agent when directed to explore more by [Settings > Exploration]
- spontaneous thoughts (by User or Agent) during normal course of work

Ideas follow the **Index-Detail Pattern:** name each Idea file `{yyyy.mm.dd.hh.mm.ss.xxxZ}.md`, put the Subject on Line 1 (≤ 80 chars) like every other record, then add bare `key: value` fields (the same style as `_Axis/TASKS.md`):

	subject summarizing the idea (Line 1, ≤ 80 chars)

	status: speculative, promising, concrete, or tbd
	priority: high, medium, low, or tbd
	created: yyyy.mm.dd.hh.mm.ss.xxxZ
	reviewed: yyyy.mm.dd.hh.mm.ss.xxxZ

	explanation of idea (simple plaintext or markdown)

**Example:**

	Conduct a survey

	status: promising
	priority: tbd
	created: 2026.05.18.22.33.24.230Z
	reviewed: 2026.05.28.09.13.17.122Z

	# Post-Conference Survey
	 ...
	 ...

Keep the field keys exactly `status:`, `priority:`, `created:`, and `reviewed:` - lowercase, one per line (the Dashboard reads `status:` and `priority:` from them). There is no summary file, or index file, of all ideas; a dynamic index of ideas can be constructed as needed by scanning filenames, Line-1 subjects, and the `status:` / `priority:` fields of each Idea file (see [Practices > IndexDetail]).

Periodically review Ideas (see the `^ideas` command) - updating status, adjusting priority, and archiving obsolete or absorbed Ideas as needed. When an idea is reviewed (at more than a superficial level), update its `reviewed:` timestamp, potentially re-prioritize it (`priority:`), and summarize top priorities back to User.
