# Settings and Profiles
> **Purpose:** How Profiles apply to Settings, and what an unset value means.


- When User selects a Profile, values from Profile are applied to respective Settings.
- A Setting with a value of `?` or `<unset>` has no value set - infer a value or ask User.
- The default Mindset was generated from a Standard Profile and default Settings.
- User can change language; record **Working Language** in `_Axis/SETTINGS.md`.
- Reminder local-time interpretation uses **Project Time Zone**; `Unknown` requires explicit UTC/offset confirmation and is never inferred from the host.
- **Storage Policy** is a persistent safety ceiling: only exact `auto` plus a separately verified `host-storage=atomic` permits concurrent writers. `single-writer`, missing, or malformed state never grants concurrency.
- Core Principles ship as stable defaults common to all Axis projects; User may edit them.
