# ^inbox
> **Purpose:** Scan the project's `_Inbox/` and file what arrived.

1. Main Agent only. An External Agent lists the items it sees, writes a Request to Main under [Practices > Requests], and STOPs.

2. Load [Practices > Inbox] and list `_Inbox/`. If it holds nothing to file, say so in one line and STOP.

3. File each item under [Practices > Inbox], Log one Event for the run, and report to User in one short line. STOP.
