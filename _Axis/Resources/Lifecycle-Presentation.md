# Lifecycle Presentation
> **Purpose:** Present a clear Axis brand banner followed by verified session details.

## Shared style

On WhatsApp, SMS and equivalent messaging channels, begin every message with exactly three lines, without fences or dividers: `A X I S   W O R K F L O W` at the left margin, then ` > {Project name}` and ` > {folder}` (as the rows below show them), each with exactly one leading space. Then one blank line and the greeting, answer or closing notice. Show no session rows and no closing line there. Until the Project name and folder are verified (the loading notice, a failed startup), print the title line alone. Use the same opening before compact notices. Keep all startup and lifecycle gates.

On other surfaces use the two-section block below in one fenced `text` block when Markdown is available, or the same lines as plain text. The fence preserves spaces and prevents divider interpretation. Every Axis divider is exactly `- - - - - - - - - - - - - -`: 14 ASCII hyphen-minus (`-`) characters with single spaces between them, 27 characters, at the left margin. The brand section is the spaced title indented one space, directly between two dividers. The session rows follow directly under its second divider at the left margin, each label padded with spaces so that every value starts at position 11, and one closing divider sits directly under the last row. Use ordinary spaces, no color codes or emoji inside the block; the Main Agent introduces itself as Axel in the greeting that follows it, not inside the block. At narrow widths shorten dividers or use flowing text; never shorten an identity.

The session rows appear in this order: Session, Project, Folder, Model, Context, Agent, Version, Status. Use the Project name from Line 1 of `_Axis/PROJECT.md`, the verified current project root as Folder, and the booted role as Agent. Always show a folder inside the User's home directory as `~/` plus the rest of its path (for example `~/Axis`), using the home directory the host reports (such as `$HOME`); show any other folder in full. Never guess the home directory, and never inspect private home configuration to decorate output. Show `Not set` for an unfilled Project template and `Unavailable` for an unverified folder. Never print template tokens or guess. The `Session:` row is the Session ID: retain its complete validated timestamp. Do not add a redundant identity line outside the block. The `Version:` row shows `current-version` from the installed `_Axis/CHANGELOG.md` exactly as written (for example `1.01`); show `Unavailable` when that file is missing, unreadable or has no single valid `current-version` line. Never take the version from memory, a release page or the folder name. The `Model:` row shows the reported model (the `model` Flag) in readable form, for example `claude-fable-5-2` as `Fable 5.2`; show an unrecognized form unchanged and `Unknown` when none is reported.

## Main startup

Read Context Management from `_Axis/SETTINGS.md`. The `Context:` row shows the effective method: `Two-pass` for `Two-Pass`, otherwise `Default` for `Default`, missing, blank or unrecognized values. This display never changes the Setting.

The brand section prints first, as in the entry file, followed by one blank line and its loading notice (without indent, with one blank line after it), before any tool call, so the user sees Axis at once. Models may print other text while startup runs, so the Ready banner is repeated whole at the end. Only after every startup completion gate passes, and after any items `boot.py` lists as pending, use the channel form above; on other surfaces start the reply with one block: four blank lines, then the brand section, session rows and closing divider of Shared style (`boot.py` prints exactly this block). Immediately follow it with a blank line and the normal greeting. Never print the session rows without a passed gate, and never omit them after one where the surface shows them: they are the visible record of the Session ID. `Ready` means the session is admitted and its startup records are committed, never merely that loading began. The core reading also finishes before any answer other than the greeting or a requested exact reply.

The terminal Ready block (the four blank lines are part of it):

```text




- - - - - - - - - - - - - -
 A X I S   W O R K F L O W
- - - - - - - - - - - - - -
Session:  {yyyy.mm.dd.hh.mm.ss.xxxZ}
Project:  {verified Project name}
Folder:   {verified project folder}
Model:    {reported model in readable form}
Context:  {effective context-management method}
Agent:    Main
Version:  {installed Axis Workflow version}
Status:   Ready
- - - - - - - - - - - - - -
```

Only an independently validated RSI Main identity replaces the title with the spaced uppercase title for Axis RSI. Axis Workflow and Axis RSI share the same metadata and gates. A stale cache, folder or Project name alone never selects RSI. Failed startup has no Ready block or Session ID banner. Do not print a second block after overlay activation. Under Fast Boot the brand section prints before the overlay is validated and `boot.py` prints a fixed block, so both use the Workflow title; an RSI identity is announced by the overlay activation notice and applies to later presentation.

## Shutdown and update

After verified shutdown use the same surface form and row order, with `Status: Stopped`. Retain the just-ended session details before removing its live records; this is a stopped-session receipt, not a fresh Main startup. An RSI Main keeps its validated boot brand. Auxiliary and Subagent shutdown use the Workflow brand and their actual role, with their own known identifier labeled `Agent ID:` instead of the Main-only `Session:` row; omit an unavailable identifier. They never acquire a Main Session ID banner.

Follow the block with `This session has stopped. Start a new session to continue.` If a Snapshot was saved, identify it immediately before the block. Successful update uses `Status: Updated and stopped`, adds the verified old and new versions as rows directly after the `Version:` row (on messaging channels, in the notice with the status), and retains the required fresh-session instruction. Never print Ready, a startup greeting or the final-response frame after a terminal lifecycle block.

## Compact notices

Resume, Auxiliary readiness, role changes and startup failures remain compact notices, not new success banners. Use `Axis Workflow | Resumed`, `Axis Workflow | Auxiliary`, `Axis Workflow | Main`, or `Axis Workflow | Startup incomplete` where the owning procedure permits. Preserve the required cause, state and User decision. Fixed loading notices and machine/error tokens remain verbatim. Promotion reuses its one normal Main startup; demotion reuses Auxiliary readiness.

## Final response

Before each actual final application answer, apply [Rules > Speaking]: its Axis Workflow header and, on terminals, its `> READY | {Folder}:` closing using this banner's Folder value. On WhatsApp, SMS and equivalent discrete-message channels, use the three-line opening above and omit the closing. Do not use the lifecycle brand block for an ordinary answer. Progress and Subagent returns have no final-response decoration. Exact-output and machine-readable contracts retain their required shape.
