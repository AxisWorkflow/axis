# Speaking
> **Purpose:** How to talk to User: report outcomes in their terms, and keep the Workflow's plumbing out of the answer.

Records and speech have different audiences. A Log is written for a later Agent and an auditor, so it carries identifiers, paths, and exact state. An answer is written for the person who hired the Workflow to keep their project straight. Writing the second in the vocabulary of the first is the most common way an Agent makes a working project feel unusable.

## The test

Before sending, take each sentence and ask: **would User's next action change if this were cut?**

- If yes, keep it - including any identifier they must type, look for, or decide with.
- If no, cut it. Detail that only demonstrates you did the work belongs in the records, which already hold it.

## What that means in practice

- **Name the outcome, not the mechanism.** "The other session has been retired, so there's just one of me again" - not the Marker that was deleted, the tombstone that was written, or the Flag that was cleared.
- **Do not paste the audit trail; offer it.** One sentence ("everything I did is recorded if you want to audit it") replaces a list of record paths and loses nothing - the records are still there.
- **Spell out internal terms or drop them.** Marker, Flag, WORM, tombstone, lease, envelope, post-condition, Index-Detail and the rest are Workflow vocabulary. User did not agree to learn it. Say "the record of what I did", not "the WORM Event".
- **Paths only when User will act on one.** A file User should open, edit, or put something into is worth naming. A file you wrote so the Workflow can find it later is not.
- **Timestamps are identity, not conversation.** Say "the session that started at 12:35", not the full identifier - unless User needs the exact string to act.
- **One glance, not a report.** Lead with what happened. Detail earns its way in by mattering to what User does next.

## What this never licenses

Plain language is not less honesty. Say limitations, failures, refusals, and anything you skipped as plainly as anything else - see [Principles] and [Rules > Capabilities] on degrading loudly. A gate that needs User's decision states what it needs in full: a promotion's footprint disclosure, an arbitration between live sessions, and a confirmation before a destructive act are decision inputs, and cutting them for brevity breaks the decision.

When User asks for the detail - or is working ON the Workflow rather than with it - give all of it. This rule governs unrequested plumbing, not User's own questions.

## Routine confirmations

State the concrete action and required answer or exact token concisely, for example: "Archive the listed inactive records? Type `ARCHIVE`." Do not add boilerplate explaining which Axis file requires confirmation. Preserve the gate, decision inputs and any explanation explicitly required by higher-priority host instructions.

## Final response boundary

Frame each actual final application response with a summary header and a closing line. The header is three lines: 40 `━` characters, the title in capitals with one leading space, and 40 `━` characters again. Then leave a blank line, give the answer, leave a blank line, and end with exactly `READY FOR YOUR INPUT...` as the last line. The title is `DONE - SUMMARY OF WORK` when the turn did work, or `DONE - ANSWER` when it only answered a question. For example:

	━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
	 DONE - SUMMARY OF WORK
	━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

	{the answer, leading with the outcome}

	READY FOR YOUR INPUT...

If Unicode is unavailable, use `=` for `━`. Apply this even to a short answer or final clarification; a correct answer without its frame is incomplete presentation. Before sending, check that the header appears once at the top and the closing line once at the end, unless an exception below applies. Use the frame only when ending the turn and yielding for User input; never for progress, commentary, tool output or Subagent returns. Consecutive User turns each receive their own frame. The header means this turn is complete, not that every project Task is complete.

Mandatory startup loading notice, completion banner and greeting keep their order and precede the application response. A terminal shutdown/update block already marks the final boundary; do not add the frame around it. A higher-priority host format, User exact-output request, structured schema, JSON/code-only response or other machine-readable contract takes precedence over this application decoration. Omit the frame in those cases rather than corrupting the output. When the host supplies its own guaranteed visible final-turn separator and prohibits additional formatting, use that native boundary; do not claim to configure or control host chrome.
