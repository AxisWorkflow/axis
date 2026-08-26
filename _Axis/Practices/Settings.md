# Settings
> **Purpose:** Define how Settings are stored, changed, and overridden.

Settings (stored in `_Axis/SETTINGS.md`) hold configuration values for the project and LLM. Each Setting appears in a ### markdown section.

User can override or change a setting by:

- Asking Agent to override a setting in current context, but not save change to disk.
- Overriding a setting for a particular task by noting the change in a task description.
- Editing, saving to disk, and re-loading `_Axis/SETTINGS.md`.

Agents may propose changes to a Setting, but must apply them only with User permission.

Agent can add a new setting for just the current project by asking User for permission and reproducing the exact shape of the existing Settings:

	### {Name}

	**Description:** {what the setting controls, and how to read its values}

	**Range:** {the allowed values, or "open ended"}

	**Value:** {the value that has been set}

Keep those labels verbatim - a `### ` heading for the name, then `**Description:**`, `**Range:**`, and `**Value:**` with the colon inside the bold. The Dashboard reads every Setting by matching `**Value:**`, so a Setting written any other way is invisible to it. A Mindset Setting additionally belongs under the `## Mindset Settings` heading, and must then appear in the provenance stamp at the end of [Mindset] - regenerate via [Draft-Mindset] after adding one.

Some settings accept a value as a "Relative Adjustment". Refer to the description of the Setting to infer what "Much More", "More", "Less", and "Much Less" mean in each context. The acceptable range for a relative adjustment value is:
> 2 = Much more
> 1 = More
> 0 = No change from default
> -1 = Less
> -2 = Much less

`Project Time Zone` is an Application Setting owned by [Practices > Reminders]. It is `Unknown`, `UTC`, or a valid IANA timezone. Never replace `Unknown` merely with the current host timezone; User confirmation or existing canonical project evidence is required.

`Storage Policy` is an Application Setting owned by [Practices > Portability]. Its only valid values are `auto` and `single-writer`. Only `auto` can permit a separately verified `host-storage=atomic`; `single-writer`, a missing value, or a malformed value forces serialized behavior. It is deliberately one-way: no Setting can force an unverified filesystem to be atomic. When User changes it to `single-writer`, immediately rewrite `host-storage` to `serialized` and Log the correction. Changing it back to `auto` removes the ceiling but does not grant `atomic`; rerun the storage detection before raising the Flag.
