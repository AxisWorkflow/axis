# ^settings
> **Purpose:** Step through and potentially adjust each setting.

1. Load `_Axis/SETTINGS.md` back into context.

2. Walk through each Setting in order. For each one:
	- a. Show User: setting name, current value, allowed range, and a one-line summary of the description.
	- b. Ask: "Adjust this Setting? (yes / no / stop review)"
	- c. If stop review: GOTO step 3.
	- d. If no: continue to the next Setting.
	- e. If yes: ask User for the new value; validate against the range (reject invalid values, explain, re-ask once); update and save `_Axis/SETTINGS.md`.

3. Log every change: name, old value, new value, and why (if a reason was given).

4. Optionally add a Note about any change with larger ramifications for the project.

5. If any **Mindset Setting** changed (the provenance stamp in `_Axis/MINDSET.md` no longer matches): follow `_Axis/Resources/Draft-Mindset.md` to regenerate the Mindset. STOP.
