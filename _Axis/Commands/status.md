# ^status
> **Purpose:** Show where the project stands on one screen; `^status web` for a branded page, `^status deep dive` for more.

Follow [Practices > Status]. `^status` is a quick look built fresh from the project's own records each time. It changes nothing, so any Agent (Main or External) may run it at any time. For a dated report that is kept, use `^review`; for the live view, `^dashboard`.

1. Read User's words after `^status` and infer two choices:
	- **Detail.** Default is short: one screen. Words asking for more - `deep dive`, `full`, `everything`, `details`, `more`, or a named area such as `tasks` or `initiatives` - select full detail, and a named area means lead with that area.
	- **Format.** Default is text in the chat or terminal. `web`, `html`, `page`, `browser` or `open` select the web page.

2. With `host-shell` valid `yes` and Python 3 available, run `python3 _Axis/Resources/status.py --root . --format {text|html} --detail {short|full}` from the project root.
	- **Text:** show its output exactly, inside a fenced `text` block so the layout holds. Add at most one or two sentences of your own below it: the thing User most needs to act on, if anything.
	- **Web page:** it writes `_Temp/status/index.html` (regenerable scratch) and prints that path. Give User the path as a clickable link, and open it in the browser when the host can. The page uses the brand package in `_Axis/Branding/`; without it the page falls back to plain styling and says nothing is missing.
	- The helper reads records only. A nonzero exit or a traceback means fall back to item 3; never retry in a loop.

3. Without the helper, compose the same summary by hand from the same sources, reading only what the chosen detail needs: Project name (Line 1 of `_Axis/PROJECT.md`) and installed version (`current-version` in `_Axis/CHANGELOG.md`); the Plan's current direction (its first paragraph); Task counts and the Active and Blocked Tasks from `_Axis/TASKS.md`; open Initiatives from `_Axis/INITIATIVES.md` when present; open Follow-Ups and Reminders (Subjects and due fields only); the newest Log Subjects (four for short, about twelve for full); the ages of the newest Snapshot and Review; and live Agents (fresh Markers without a `.kill` sibling). Lay it out like the helper: the spaced title Axis Project Status between two dividers of 40 `━`, one block of `Label:` rows in aligned columns (Project, Path, Version, As of, the Task counts, Follow-Ups, Reminders, Agents live; no Git details), then short labelled sections, and a closing divider. For the web page without Python, write the same content to `_Temp/status/index.html`, linking `../../_Axis/Branding/css/axis-brand.css` and using its `axis-root`, `axis-card` and `axis-stat` classes.

4. **Deep dive.** When User asked for more than the full helper output shows, add your own reading below it: the Plan's sections, each Active Task's detail file, each open Initiative's section, the recent Logs' bodies, and anything else User named. Keep it a summary of the records, clearly separated from the helper output; do not write a Review or a record unless User asks (then run `^review`).

5. Say nothing about the mechanics (which helper ran, which files were read) unless something failed. A missing record family is simply absent from the summary. STOP.
