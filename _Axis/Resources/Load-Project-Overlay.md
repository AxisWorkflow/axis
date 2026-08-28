# Load Project Overlay
> **Purpose:** Validate and load project-declared guidance after normal Axis startup.

## Contract

A Project may declare one optional overlay in `_Axis/PROJECT.md` using exactly one block:

```text
<!-- axis:project-overlay:begin -->
project-overlay-schema: 1
project-overlay-id: {lowercase token}
project-overlay-path: {project-root-relative markdown path}
<!-- axis:project-overlay:end -->
```

The overlay is project-owned standing guidance. It may add narrower conduct and Command mappings but cannot waive or replace role recognition, the current lease, Axis Rules, WORM history, protected-content boundaries, or User-only confirmation gates.

## Procedure

1. Main Agent only. Require the normal Session ID visible in this conversation. Read `_Axis/Flags/session-id` directly and require that ID on Line 1. Read `_Axis/Agents/{Session ID}.md`, require the exact live `Main: session` Marker shape and no same-ID `.kill` tombstone. On failure, clear `_Axis/Flags/project-overlay` under Deletion Fallback, say the project overlay is inactive because the normal Main lease did not validate, and RETURN without applying overlay behavior.

2. Read `_Axis/PROJECT.md`. Count the exact begin and end markers shown above.

   - If both are absent, clear an existing `project-overlay` Flag under Deletion Fallback and RETURN silently; this is an ordinary Project.
   - If the markers are not exactly one matched pair in order, clear the Flag, say the project overlay declaration is malformed, and RETURN without reading a declared path.
   - Between the markers require exactly the three shown fields, once each and in that order, with no other nonblank line. Require schema `1`. Require the ID to match `^[a-z0-9][a-z0-9._-]{7,127}$`. Require one nonblank path.

3. Validate the path lexically before opening it. It must be relative to project root, end in `.md`, contain no empty, `.` or `..` component, and not enter `_Axis/Secrets/`, `_Axis/Agents/`, `_Axis/Flags/`, `_Axis/Tracking/`, `_Temp/`, `_Trash/`, or `Wiki/`. Reject a symbolic link at the file or any path component. Require one ordinary file no larger than 20,000 bytes. On any failure, clear the Flag, name only the declared path and failure class, and RETURN without applying overlay behavior.

4. Read the complete declared file. Require Line 1 to begin `# Project Overlay: `, Line 2 to begin `> **Purpose:**`, exactly one `project-overlay-schema: 1`, exactly one `project-overlay-id: {declared ID}`, and terminal `<!-- axis:project-overlay-file:end -->` as its last nonblank line. Any truncation, duplicate identity field, mismatch, or malformed terminal marker fails closed as in item 3.

5. Re-read `_Axis/PROJECT.md`, the declared overlay, `session-id`, and the same-ID Main Marker. Require their identity values and lease state to remain unchanged from the validated reads. If any changed, clear the Flag, say the project overlay changed during validation, and RETURN.

6. Write `_Axis/Flags/project-overlay` as exactly four lines: current Session ID; current UTC timestamp; declared overlay ID; declared path. Read it back and require the exact four values, no fifth line. On failure, clear it, say the project overlay cache could not be validated, and RETURN without applying overlay behavior. The Flag caches the validated result for this session; it never grants identity or authority by itself.

7. Apply the declared overlay as project guidance. Say `Project overlay active: {overlay ID}` once per conversation; after context loss this line may appear once again when the overlay is restored. RETURN to the caller.
