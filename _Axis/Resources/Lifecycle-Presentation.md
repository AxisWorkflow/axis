# Lifecycle Presentation
> **Purpose:** Present a clear Axis brand banner followed by verified session details.

## Shared style

Use the two-section block below in one fenced `text` block when Markdown is available, or the same lines as plain text. The fence preserves spaces and prevents divider interpretation. The brand section uses three lines with `│`, `+`, `│`, framed by 40 `━` characters. Follow it with the session details and one closing divider. Use ordinary spaces, no color codes, emoji, mascot or invented persona. At narrow widths shorten dividers or use flowing text; never shorten an identity. If Unicode is unavailable use `-` for `━` and `|` for `│`.

Use the Project name from Line 1 of `_Axis/PROJECT.md`, the verified current project root as Folder, and the booted role as Agent. Shorten a known home prefix to `~/` only when that relationship is already verified; do not inspect private home configuration to decorate output. Show `Not set` for an unfilled Project template and `Unavailable` for an unverified folder. Never print template tokens or guess. The `Session:` row is the Session ID: retain its complete validated timestamp. Do not add a redundant identity line outside the block. Optional version metadata uses only a verified installed Changelog.

## Main startup

Only after every startup completion gate passes, emit exactly one block and immediately follow it with the normal greeting. `Ready` means the required startup preparation completed, never merely that loading began.

```text
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  │
  +   A X I S   W O R K F L O W
  │
  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  │   Status:   Ready
  │   Project:  {verified Project name}
  │   Folder:   {verified project folder}
  │   Agent:    Main
  │   Session:  {yyyy.mm.dd.hh.mm.ss.xxxZ}

  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

Only an independently validated RSI Main identity replaces the title with the spaced uppercase title for Axis RSI. Axis Workflow and Axis RSI share the same metadata and gates. A stale cache, folder or Project name alone never selects RSI. Failed startup has no Ready block or Session ID banner. Do not print a second block after overlay activation.

## Shutdown and update

After verified shutdown use the same brand and metadata structure, with `Status: Stopped`. Retain the just-ended session details before removing its live records; this is a stopped-session receipt, not a fresh Main startup. An RSI Main keeps its validated boot brand. External and Subagent shutdown use the Workflow brand and their actual role, with their own known identifier labeled `Agent ID:` instead of the Main-only `Session:` row; omit an unavailable identifier. They never acquire a Main Session ID banner.

Follow the block with `This session has stopped. Start a new session to continue.` If a Snapshot was saved, identify it immediately before the block. Successful update uses `Status: Updated and stopped`, adds the verified old and new versions, and retains the required fresh-session instruction. Never print Ready, a startup greeting or a second final-response divider after a terminal lifecycle block.

## Compact notices

Resume, External readiness, role changes and startup failures remain compact notices, not new success banners. Use `Axis Workflow | Resumed`, `Axis Workflow | External`, `Axis Workflow | Main`, or `Axis Workflow | Startup incomplete` where the owning procedure permits. Preserve the required cause, state and User decision. Fixed loading notices and machine/error tokens remain verbatim. Promotion reuses its one normal Main startup; demotion reuses External readiness.

## Final response

Before each actual final application answer, apply [Rules > Speaking] and its `TURN COMPLETE - WAITING:` boundary. Do not use the lifecycle brand block for an ordinary answer. Progress and Subagent returns have no final-response decoration. Exact-output and machine-readable contracts retain their required shape.
