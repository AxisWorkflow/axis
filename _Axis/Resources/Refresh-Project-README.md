# Refresh Project README
> **Purpose:** Create or refresh the User-owned root Project README without loading the Axis User Manual or overwriting User content.

## Ownership Boundary

`README.md` has two lifecycle states. Before Project Setup it is a byte-identical display copy of `_Axis/README.md`. After Project Setup it belongs to the User's project. Axis may update only the single bounded block below; content outside it is User-owned and must remain byte-identical.

```markdown
<!-- axis:project-summary:begin -->
{managed project synopsis}
<!-- axis:project-summary:end -->
```

The Axis User Manual remains at `_Axis/README.md`. The Axis license remains at `_Axis/LICENSE`. This procedure never reads either file for project context; compare hashes or bytes only where the lifecycle check requires it.

## Procedure

1. Run only in one of these cases: [Start-Project] is completing setup; `^status` has saved a new report; `^save` is preparing its Snapshot checkpoint; or `^git` is about to make an outgoing checkpoint. Otherwise STOP silently. Outside Project Setup, require a valid `project-ready` Flag before changing the root README.

2. Read only public-safe project sources needed for a compact synopsis:
	- `_Axis/PROJECT.md`: project name, Background, Deliverables, and Criteria.
	- `_Axis/PLAN.md`: current Objective and immediate phase or direction, when substantive.
	- `_Axis/TASKS.md`: counts by status and the current Active or Blocked subjects, without copying detail bodies.
	- The newest `_Axis/Status/{ID}.md`, when one exists: its timestamp ID and opening synopsis only.

3. Exclude Secrets, infrastructure locations, environment signatures, credentials, personal account details, Session IDs, Capability Flags, local paths, host-specific state, and record bodies. Do not invent missing facts. Keep the result useful in a private repository but safe enough that changing repository visibility would not disclose operational secrets.

4. Compose the managed block as concise durable Markdown:
	- `# {Project Name}` only when creating a new root README; never insert a second H1 into an existing customized README.
	- `## Project Summary` inside the markers, with a short description followed only by substantive available sections: `### Current Direction`, `### Deliverables`, `### Progress`, and `### Latest Status`.
	- Task progress uses compact counts plus named Active or Blocked work only when those subjects are safe and useful.
	- The Latest Status cites the project-root-relative report path. Do not add a refresh timestamp; source identity supplies recency and unchanged project state must produce byte-identical output.

5. Apply the lifecycle safely:
	- If root `README.md` is missing, create it with the Project H1 and one managed block.
	- During Project Setup, if root `README.md` is byte-identical to `_Axis/README.md`, replace that display copy with the Project H1 and managed block.
	- If exactly one well-ordered managed block exists, replace only its contents and retain every byte outside the marker lines.
	- If a customized root README has no managed block, append one after a blank line; preserve all existing content.
	- If markers are malformed, nested, repeated, reversed, or only one exists, do not edit the file. Tell User the exact structural problem and continue setup or the owning Command without claiming the Project README was refreshed.

6. Write through a same-directory temporary file and atomic rename when the host supports it. Re-read the result: require exactly one marker pair, the intended managed content between it, and byte-identical User-owned content outside it. On failure, restore the original and report the failure.

7. During Project Setup only, resolve the root license lifecycle after the README succeeds:
	- If root `LICENSE` is byte-identical to `_Axis/LICENSE`, remove it; the User's project is not automatically placed under the Axis license.
	- If root `LICENSE` is missing, leave it missing.
	- If root `LICENSE` differs, preserve it byte-for-byte as the User's chosen or customized project license.
	- Never draft, select, or replace a project license without the User's explicit request.

8. Return to the owning procedure. Do not Log separately; the owning Project Setup, Status, Save, or Git record covers the refresh. STOP.
