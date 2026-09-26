# Initiatives
> **Purpose:** Coordinate related Tasks around one optional shared outcome.

## Responsibilities

The Plan describes overall direction and priorities. An Initiative owns one shared outcome, scope, success measures, current phase, constraints, related Tasks, and next decision. A Task owns a concrete piece of execution, its requirements, status, dependencies, and results. A deliverable is an output; a phase is a stage within the Initiative, not another record level.

Initiatives are optional. Keep Plan-and-Tasks-only projects valid and allow standalone Tasks. Do not automatically convert parent Tasks or create an Initiative for every Task. User authorization governs implementation and phase boundaries; an Initiative never grants new authority by itself.

## Record format

Store Initiatives as sections of the project-owned `_Axis/INITIATIVES.md`. This is one optional mutable project document, like the Plan, not a new timestamp-named Index-Detail family. Absence or a file with no Initiative sections means none are recorded; create the file only when useful. Each section starts with `## ` followed by a unique stable lowercase key matching `[a-z][a-z0-9-]*`. Never reuse a key for another Initiative. Its heading supplies a durable link such as `_Axis/INITIATIVES.md#customer-guide`; its `name:` can change without changing identity.

Use these bare lowercase fields, once each and in this order:

```text
## customer-guide

name: Publish the customer guide
status: Active
created: 2026.05.18.22.33.24.230Z
updated: 2026.05.18.22.33.24.230Z
completed: N/A
cancelled: N/A
phase: Draft and review
```

Use valid full Axis UTC timestamps for creation and material updates; these are metadata, not new record identifiers. Status is exactly `Active`, `Blocked`, `Completed`, or `Cancelled`. Active/Blocked use `N/A` in both terminal fields. Completed uses the completion timestamp in `completed:` and `updated:`; Cancelled uses the cancellation timestamp in `cancelled:` and `updated:`. The other terminal field stays `N/A`.

Follow the fields with short `### Outcome`, `### Scope`, `### Success`, `### Constraints`, `### Tasks`, and `### Next decision` sections. Keep the shared facts here and link to them from Tasks rather than copying them. Constraints may include an agreed budget, test limits, phase boundary, or deadline; do not invent requirements the project does not need. List actual Task detail links under Tasks. Next decision states what is needed, or `None`; a User-owned blocking ask still belongs in a canonical Follow-Up linked here.

## Task membership and consistency

A Task may carry `initiative: customer-guide` in both its `_Axis/TASKS.md` entry and detail metadata. Omission, blank, or `N/A` means a standalone Task. The field contains one primary Initiative key, not a path, comma-separated list, or inferred name. Additional relationships may be ordinary body links. Existing Tasks need no new field or migration.

For a linked Task, require exactly one matching Initiative section and a reciprocal Task link in that section. Preserve membership through normal Task archiving by updating the Initiative's link in the same operation. Link maintenance preserves a terminal Initiative's status and terminal timestamps; record the path move in the archive Event. Resolve by the existing Task timestamp if its live path has moved to Archive. Do not create a new Task identity merely to change its grouping. Missing Initiative files, duplicate keys, dangling links, or conflicting membership are visible record problems; ask about ambiguous meaning rather than silently assigning work or treating it as standalone. They stop only the affected record action, not unrelated work or a valid session startup.

Use ordinary locks, readbacks, and expected-content checks for this document. On a membership change update the Task index/detail and the affected Initiative sections as one reviewed group; re-read and reconcile an interrupted partial edit before further dependent work. Keep a completed or cancelled Task's historical membership unchanged; group later work through a new Task instead. Do not infer Initiative completion from Task counts.

## Loading and lifecycle

The Plan carries only brief active Initiative summaries and links. During startup, read the normal Plan and Task index as before; do not preload `_Axis/INITIATIVES.md` or all its sections. Before working on a linked Task, load this Practice if needed and the matching Initiative section through its next level-two heading or end of file. A context loss requires reloading the relevant section before relying on its shared decisions.

Planning, status, save, resume, and refresh keep related Plan summaries, Initiative sections, and Task membership consistent. Report the outcome, current phase, material blocker, and next decision; count executable Tasks separately from Initiatives. A completed Task does not automatically complete its Initiative, and an Initiative never closes its Tasks automatically.

Complete an Initiative only after its stated outcome and success measures are verified and remaining Tasks are explicitly finished, cancelled, or reassigned. Record the evidence and result before closing it. Cancel abandoned Initiatives with a reason and disposition of open Tasks; never mark them Completed. Retain terminal sections and their stable keys in this document so historical links remain valid; omit their details from routine active summaries. Do not automatically archive or delete Initiative sections.

Preserve this whole document as project state during updates and releases. Ship only its empty template, never a project's populated Initiative sections. Older projects may leave it absent. Natural-language planning, `^plan`, and `^tasks` can manage Initiatives under their normal authority; no additional command is required.
