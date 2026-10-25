# Lifecycle Presentation
> **Purpose:** Present a clear Axis brand banner followed by verified session details.

## Shared style

Use the two-section block below in one fenced `text` block when Markdown is available, or the same lines as plain text. The fence preserves spaces and prevents divider interpretation. The brand section is the spaced title indented one space, directly between two lines of 27 `━` characters that start at the left margin. Follow it with a blank line, the session rows indented two spaces, a blank line and one closing divider; the Main startup block below is tighter. Use ordinary spaces, no color codes or emoji inside the block; the Main Agent introduces itself as Axel in the greeting that follows it, not inside the block. At narrow widths shorten dividers or use flowing text; never shorten an identity. If Unicode is unavailable use `-` for `━`.

The session rows appear in this order: Project, Folder, Session, Version, Context, Status, Agent. Use the Project name from Line 1 of `_Axis/PROJECT.md`, the verified current project root as Folder, and the booted role as Agent. Always show a folder inside the User's home directory as `~/` plus the rest of its path (for example `~/Axis`), using the home directory the host reports (such as `$HOME`); show any other folder in full. Never guess the home directory, and never inspect private home configuration to decorate output. Show `Not set` for an unfilled Project template and `Unavailable` for an unverified folder. Never print template tokens or guess. The `Session:` row is the Session ID: retain its complete validated timestamp. Do not add a redundant identity line outside the block. The `Version:` row shows `current-version` from the installed `_Axis/CHANGELOG.md` exactly as written (for example `1.01`); show `Unavailable` when that file is missing, unreadable or has no single valid `current-version` line. Never take the version from memory, a release page or the folder name.

## Main startup

Read Context Management from `_Axis/SETTINGS.md`. The `Context:` row shows the effective method: `Two-pass` for `Two-Pass`, otherwise `Default` for `Default`, missing, blank or unrecognized values. This display never changes the Setting.

The brand section prints first, as in the entry file, followed by one blank line and its loading notice (indented by two spaces, with one blank line after it), before any tool call, so the user sees Axis at once. Models may print other text while startup runs, so the Ready banner is repeated whole at the end. Only after every startup completion gate passes, and after any items `boot.py` lists as pending, start the reply with one block: four blank lines, the brand section, then the session rows directly under its divider and one closing divider directly under the last row, with no blank lines inside that part (`boot.py` prints exactly this block). Immediately follow it with a blank line and the normal greeting. Never print the session rows without a passed gate, and never omit them after one: they are the visible record of the Session ID. `Ready` means the session is admitted and its startup records are committed, never merely that loading began. The core reading also finishes before any answer other than the greeting or a requested exact reply.

The Ready block (the four blank lines are part of it):

```text




━━━━━━━━━━━━━━━━━━━━━━━━━━━
 A X I S   W O R K F L O W
━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Project:  {verified Project name}
  Folder:   {verified project folder}
  Session:  {yyyy.mm.dd.hh.mm.ss.xxxZ}
  Version:  {installed Axis Workflow version}
  Context:  {effective context-management method}
  Status:   Ready
  Agent:    Main
━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Only an independently validated RSI Main identity replaces the title with the spaced uppercase title for Axis RSI. Axis Workflow and Axis RSI share the same metadata and gates. A stale cache, folder or Project name alone never selects RSI. Failed startup has no Ready block or Session ID banner. Do not print a second block after overlay activation. Under Fast Boot the brand section prints before the overlay is validated and `boot.py` prints a fixed block, so both use the Workflow title; an RSI identity is announced by the overlay activation notice and applies to later presentation.

## Shutdown and update

After verified shutdown use the same brand and metadata structure, with `Status: Stopped`. Retain the just-ended session details before removing its live records; this is a stopped-session receipt, not a fresh Main startup. An RSI Main keeps its validated boot brand. External and Subagent shutdown use the Workflow brand and their actual role, with their own known identifier labeled `Agent ID:` instead of the Main-only `Session:` row; omit an unavailable identifier. They never acquire a Main Session ID banner.

Follow the block with `This session has stopped. Start a new session to continue.` If a Snapshot was saved, identify it immediately before the block. Successful update uses `Status: Updated and stopped`, adds the verified old and new versions, and retains the required fresh-session instruction. Never print Ready, a startup greeting or the final-response frame after a terminal lifecycle block.

## Compact notices

Resume, External readiness, role changes and startup failures remain compact notices, not new success banners. Use `Axis Workflow | Resumed`, `Axis Workflow | External`, `Axis Workflow | Main`, or `Axis Workflow | Startup incomplete` where the owning procedure permits. Preserve the required cause, state and User decision. Fixed loading notices and machine/error tokens remain verbatim. Promotion reuses its one normal Main startup; demotion reuses External readiness.

## Final response

Before each actual final application answer, apply [Rules > Speaking]: its Axis Workflow header and its `> READY {Folder}:` closing, using this banner's Folder value. Do not use the lifecycle brand block for an ordinary answer. Progress and Subagent returns have no final-response decoration. Exact-output and machine-readable contracts retain their required shape.
