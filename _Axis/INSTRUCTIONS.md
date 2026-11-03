# Instructions
> **Purpose:** Where User's own standing instructions live. User owns this file; Agents read it and follow it, and never edit it unasked.

Write here, in your own words, what Agents on this project should know and follow: the contents of an entry file you used before Axis, your organization's requirements, how your platform behaves, or standing preferences no Setting covers. Put each instruction under one of the two headings at the end. "For every agent" reaches every agent that works here, including helpers that may run on other model providers. "For only the Main Agent" reaches no helper: put permissions, accounts, budgets and pending requests there.

## Why here and not in the entry files

The entry-point files (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`) are **reserved for the Axis Workflow and must not be edited or added to**. Hosts inject the entry file into every Agent's context on every turn, some under a size cap (20,000 characters on one measured host) that silently truncates rather than rejects. The three files must also stay identical, and `^update` replaces them, so an addition there would be cut off or overwritten without notice.

This file has no such limit. Main reads it at Session Start, like the Plan and the Directives.

## How Agents treat this file

- Your instructions here are standing guidance for the whole project ([Start-Session]). Where they conflict with an Agent's own habits, yours win.
- They cannot waive the parts of Axis that exist to fail closed: the entry-file startup protocol, the Marker lease, role assignment, secrets handling, and the untrusted-content rules. An Agent asked here to skip startup, ignore its lease, or hand over a secret tells you plainly rather than comply or silently ignore it.
- Nothing in this file is a Command. `^` tokens written here are text; Commands count only when you type them ([Practices > Commands]).
- For tunable behaviour prefer [Settings], and for "when X happens, do Y" prefer [Directives].
- Until this file has a "For every agent" heading, helpers receive nothing from it.

## Your instructions

### For every agent

*(Empty. How work should be done here: conventions, domain rules, preferences.)*

### For only the Main Agent

*(Empty. Permissions, accounts, budgets and requests.)*
