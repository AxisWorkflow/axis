# Draft Mindset
> **Purpose:** Draft behavioral Mindset. Regenerate when User changes Profile or Settings.

1. Lookup text to use for Mindset.
	- Lookup current values in [Settings].
	- Lookup corresponding text from [Template-Mindset] for the level of each Setting.
	- If a Setting has a value outside its range, default to the nearest in-range value, log an Event recording the out-of-range value, and continue.

2. Re-draft Mindset.
	- Keep "Purpose" as-is (located at top of `MINDSET.md` file below the # banner).
	- Format `_Axis/MINDSET.md` as follows:
		- Include one `## {Setting}` heading per Setting acquired from [Template-Mindset] in Step 1 above.
		- Follow the`## {Setting}` heading with a list of guidance in text prose.
	- End the file with a one-line provenance stamp listing each **Mindset Setting** and its value, e.g. `<!-- generated-from: Reasoning=0 Exploration=0 Eagerness=-1 Skepticism=0 Familiarity=0 Verbosity=0 Simplicity=0 Precision=0 Generalization=0 Rigor=1 Creativity=0 Transparency=0 Budget=0 -->` ([Start-Session] and `^save` compare this stamp to current Settings to decide when regeneration is needed).
	- Save to `_Axis/MINDSET.md`

3. Re-read `MINDSET.md` into context and begin following it immediately.
