# ^brief
> **Purpose:** Show the daily brief; `^brief me` for just what needs you, `^brief memo` to also save it as a Memo.

Follow [Practices > Status > Daily brief]. A brief changes no record, so any Agent serving User (<!-- BEGIN GENERATED: role-gate brief -->Main, Auxiliary or Assistant<!-- END GENERATED: role-gate brief -->) may give it at any time, whatever [Settings > Daily Brief] says; a Group Agent or Observer says the project's status is for User's own sessions and STOPs.

1. Read User's words after `^brief`: `me`, `mine`, `waiting` or `needs me` select "what needs me?" ([Practices > Status > What needs me]); `memo` also saves the brief as a Memo; anything else shows the brief.

2. With `host-shell` valid `yes` and Python 3 available, run `python3 _Axis/Resources/status.py --root . --view {brief|needs} --session {Session ID} --surface {terminal|chat}` from the project root and show its output under [Practices > Status > Formats], on a terminal inside a fenced `text` block. Exit 3 means this session may not give it: say so and STOP. Any other nonzero exit or a traceback means step 3; never retry in a loop.

3. Without the helper, compose it by hand under [Practices > Status].

4. **Memo.** Main writes today's brief Memo under [Practices > Status > Daily memo], taking its body from `--format memo` when the helper runs, and gives one line with its link. An Auxiliary Agent or Assistant sends that request to Main under its role file and says it was sent only after the request helper prints `queued` or `already-delivered`.

5. Log one Event only when a Memo was written; a brief alone is not logged. STOP.
