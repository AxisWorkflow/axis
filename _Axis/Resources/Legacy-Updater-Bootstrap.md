# Legacy Updater Bootstrap
> **Purpose:** Cross an installed updater whose allowlist predates the current checker bootstrap.

Load only when the installed engine accepts the original three-file updater boundary.

Inspect the installed engine's literal updater allowlist as data before planning step one. Released 2.07/2.08 and 3.03 engines accept only the Command, handoff contract and transaction engine. Use that original three-file bootstrap when required; never add `record-check.py` to a plan the installed engine cannot admit. After its normal pre-update checkpoint, verified installation, `finish-updater` and normal checkpoint, verify the three installed files exactly against the target. Re-read this now-installed Command.

If the checker is still older, use the newly installed and verified engine for one additional `updater_only: true` transaction changing only `_Axis/Resources/record-check.py` to its exact target bytes. Give it a distinct scoped authorization Log, durable preimages and normal pre/post checkpoints. Then verify all four updater files before planning the ordinary remaining update. There is no target-code execution before verified installation and no authority to alter other project files during either bootstrap.

If an old-checker checkpoint refuses, preserve its diagnostic and all working/index state. Load `_Axis/Resources/Legacy-Checkpoint-Recovery.md` only for the exact known compatibility cases; genuine record defects retain their normal repair procedure. The affected Main reviews any scoped maintenance repair under existing authority before mutation. Never bypass hooks or add blanket exceptions. A parent groups affected children in one repair report instead of repeatedly launching a doomed update. Clean checkpoints need no additional per-step approval.
