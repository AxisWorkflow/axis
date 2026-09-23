# Lifecycle Presentation
> **Purpose:** Give Axis lifecycle messages one compact, readable visual style.

## Shared style

Use a horizontal rule, one bold brand/status line, a compact metadata line when needed, and a closing rule. Use a blank line before and after every horizontal rule, and a blank line after the bold title. Keep metadata on separate paragraphs so CommonMark cannot turn a closing rule into a Setext heading. Use normal Markdown flow, generous space around the block and no ASCII artwork, fixed-width box, color, emoji or host plugin. Write `Axis Workflow` for ordinary sessions and `Axis RSI` only for a validated RSI Main startup. Typography does not confer a role or authority. Read version from the validated installed Changelog; omit unavailable version metadata rather than guessing.

## Main startup

After the complete startup gate passes, emit exactly one of these blocks. Replace the example values with verified values; never print both variants. Retain the literal `Session ID:` label and complete identity. The normal greeting follows immediately.

```text
---

**Axis Workflow | Ready**

Version {version} · Main session

Session ID: {yyyy.mm.dd.hh.mm.ss.xxxZ}

---
```

For independently validated RSI identity, replace only the title with `**Axis RSI | Ready**`. A stale cache, folder name, Project name alone or unread overlay never selects RSI. Failed startup has no Ready block and no Session ID banner.

## Shutdown and update

After verified shutdown use this same compact block, with the booted role and optional retained Snapshot path in the adjacent explanation:

```text
---

**Axis Workflow | Stopped**

This session has stopped.

Start a new session to continue.

---
```

An RSI Main may retain its validated boot brand when stopping. External and Subagent shutdown use `Axis Workflow` and their role; they never acquire a Main Session ID banner. Successful update uses `**Axis Workflow | Updated and stopped**`, the verified old/new versions and the required fresh-session instruction. Do not add a second shutdown or final-response block to a terminal lifecycle block.

## Compact notices

Resume, External readiness, role changes and startup failures remain compact notices, not new success banners. Prefix the existing required disclosure with `**Axis Workflow | Resumed**`, `**Axis Workflow | External**`, `**Axis Workflow | Main**`, or `**Axis Workflow | Startup incomplete**` when the owning procedure allows formatting. Preserve cause, state and every User decision. The fixed early loading notice and exact machine/error tokens remain verbatim. Promotion reuses its one normal Main startup; demotion reuses External readiness. Neither adds another success block.

## Final response and limited renderers

An ordinary actual final answer begins with a horizontal rule and `**Final response**`, as [Rules > Speaking] specifies. This lightweight divider marks the section that ends the turn; it is never progress decoration.

For plain text or a renderer that does not support Markdown, use `--- Axis Workflow | Ready ---`, `--- Axis RSI | Ready ---`, `--- Axis Workflow | Stopped ---`, or `--- Final response ---`, followed by the same metadata and text. Keep identity unbroken even if the host wraps it. At narrow widths use flowing lines, never a fixed-width box. Do not emit raw terminal color codes or claim control of host chrome. Exact-output and machine-readable application contracts retain their required shape.
