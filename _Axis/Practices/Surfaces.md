# Surfaces
> **Purpose:** Declare which Axis role a surface runs, keep the User's surface table, and set the read scope of roles that serve other people.

A surface is where a session is reached: a terminal, a chat or a channel. Without a declaration a session follows the entry file's ordinary rule (Main when none is live, Auxiliary beside a live Main). A declaration gives a surface one of the declared session roles instead. A declaration in a host's own settings is followed by instruction only: in Axis's live tests Codex ignored it in 2 of 7 runs and started as Main. Start a surface that must never be Main with `axis --role`, or set `AXIS_ROLE` and `AXIS_SURFACE` in the host's environment settings (Claude Code's `env` setting, Codex's `shell_environment_policy`); then the startup helpers refuse Main whatever the model does. The launcher is the tested path.

## Declarations

A declaration is one line in the host's standing configuration, stated in words: `Axis role: {Role}; surface: {name}`. The role is Auxiliary, Assistant, Group Agent or Observer; the surface name uses letters, digits, `.`, `_` or `-`. A host route, binding, agent name or session ID never declares a role. A terminal declaration needs its `surface:` field.

Carriers: the `axis` launcher (`axis --role {Role} --surface {name}`), which also sets the role for the helpers and the guardrails hook; a Claude Code appended system prompt; an OpenClaw chat prompt; or another host's standing instructions. A declaration takes effect at the next boot.

## The surface table

`_Axis/SURFACES.md` is the User's map of surfaces. Main creates it the first time the User declares a surface; a missing table has no rows. Each row names one surface, its exact role and its read scope:

```text
# Surfaces
> **Purpose:** The User's surfaces and the one Axis role each may run. Main changes it only on the User's direct instruction.

| Surface | Role | Read scope |
| --- | --- | --- |
| laptop-assistant | Assistant | project |
| design-group | Group Agent | Designs, Shared Notes |
```

- A declaration with no row, or whose row names another role, gets a one-line notice and no service. On an OpenClaw chat, an Auxiliary declaration keeps working without a row until Round B2 asks each chat its role.
- Main changes the table only on the User's direct instruction in this project's own session: never through a parent's order, a Submission, a Message or another session's request. Log each change as an Event naming the surface, the old and new row and the instruction. Changes take effect at each session's next boot.

## Read scope and private folders

`project` lets an Auxiliary or Assistant read the whole project except `_Axis/Secrets/` and `_X` folders ([Practices > Protected]). A Group Agent or Observer serves people other than the User, so its row must name the Project Subfolders it may read. Besides those it reads only the Axis workflow files its role file lists. Every folder its row does not name is private from it, including `_Axis/INSTRUCTIONS.md`, `_Memos/` and the project records. The `axis` launcher's tool limits and the guardrails hook enforce this on Claude Code; the launcher refuses to start those roles on Claude Code without the hook, and withholds MCP connectors from them. Elsewhere it holds only through the role file.
