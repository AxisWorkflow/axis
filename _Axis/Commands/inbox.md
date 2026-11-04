# ^inbox
> **Purpose:** Scan the project's `_Inbox/` and file what arrived.

1. Main Agent only. <!-- BEGIN GENERATED: role-gate inbox -->An Auxiliary Agent, Assistant or Group Agent lists the items it sees, writes a Message to Main under [Practices > Messages], and STOPs; an Observer tells User to ask Main and STOPs.<!-- END GENERATED: role-gate inbox -->

2. Load [Practices > Inbox] and list `_Inbox/`. If it holds nothing to file, say so in one line and STOP.

3. File each item under [Practices > Inbox], Log one Event for the run, and report to User in one short line. STOP.
