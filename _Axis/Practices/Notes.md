# Notes
> **Purpose:** Define how to write, contextualize, renew, and archive Notes.

Notes are used for short-term reference to track/remember:

- special instructions
- ad-hoc preferences
- ad-hoc settings
- deadlines
- reminders
- facts that can go stale
- etc.

Notes have a body length limit (≤ 250 words) to economize on context. A Note carries no fields, so its filename timestamp is the only record of when its content was true - and both precedence (a newer Note wins) and active-history selection read it. Revise a Note by writing a new one that supersedes it, or by renaming it to a current timestamp; never leave revised content sitting under an old timestamp. Notes are not WORM: the User may edit one directly at any time, so treat a Note the User has touched as content whose timestamp is only approximate.

**Contextualizing Notes:**

Consider each new Note in the context of the project. If making a new Note implies something important for the project, then surface that issue immediately with the User and suggest how to incorporate it into the project.

For example, if a Note says something like:

> `Use FedEx for all shipping.`

Then think through the implications of how the project would use that information (e.g., perhaps you should check if FedEx can actually ship the size of items required for the project; or perhaps the project needs to find a specialized shipper for the over-sized items).

## Review and Salience

`^notes` reviews every active Note against the current Project, Plan, Tasks, and latest Snapshot. Its classifications are derived review findings, not fields added to the Note:

- `Salient` materially affects active work, a live decision, an upcoming deadline, or a recurring User preference.
- `Current` remains accurate and useful without presently driving work.
- `Review` may be aging, ambiguous, or disconnected from current work.
- `Superseded` has been replaced or contradicted by newer durable state.
- `Obsolete` concerns a condition that demonstrably ended.

Recency carries weight because a newer Note wins when meanings conflict. A Note older than 30 days deserves review, but age alone never expires or archives it. Renew an old Note only after confirming it is still accurate and important; the new timestamp means it was revalidated now. When its content changed, write a new Note that supersedes it and offer the old one for Archive.

Do not add numeric priority or review fields to Notes. Keep their record shape small; `^notes` orders its report by action need, salience, and recency.

## Archiving Notes

- A newer Note always overrides and/or takes precedence over an older Note.
- Renew a Note by renaming it with a current timestamp.
- If a Note is wrong or no longer accurate, write a new entry that supersedes it.
- When **Max Notes** is exceeded, move the oldest excess Notes unchanged into `_Axis/Archive/Notes/`; do not delete them.
- Before selecting overflow, check whether an old Note is still valid and important. If so, renew it with a current timestamp.
- Retain the most recent **Max Notes** in `_Axis/Notes/`. There is no time-based expiry; overflow is purely count-based.
- Sessions that do not need active Notes can set **Max Notes** to zero; all Notes then move to the Archive.
- Follow [Practices > Archiving > Automatic Note Overflow] for the safe, reversible move and User notice.
