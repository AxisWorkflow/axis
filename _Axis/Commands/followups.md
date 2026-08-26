# ^followups
> **Purpose:** Review the User's open Follow-Ups, or add, update, resolve, withdraw, or convert one.

1. Read [Practices > Followups], then scan every open record in `_Axis/Followups/` by Subject and structured fields. Validate enough of each record to distinguish a healthy open item from malformed state.

2. With no additional text: list the complete open queue in the ordering defined by the Practice. Show each Subject, type, due state, self-contained ask, and the records it blocks. Say plainly when none are open. This is read-only: do not write a Log. STOP.

3. With additional text, require Main Agent. An External Agent sends a Request to Main; a Subagent returns a candidate to Main; either then STOPS without touching the queue. Main classifies the request as one of these operations:
	- **add** - create a question, decision, or action for User; a request to reopen a terminal item is an add with a new identity that references the archived record, never a restoration;
	- **update** - change an open item's due date, pointer, Subject, type, or explanatory paragraph;
	- **resolve** - record User's answer or completed action;
	- **withdraw** - close an ask that no longer applies;
	- **convert** - create or identify the Task that now owns Agent-actionable work, then close the Follow-Up as `converted`.

4. Resolve any existing target by exact timestamp or an unambiguous Subject. For a reopen-as-add request, inventory `_Axis/Archive/Followups/` by filename, Subject, and terminal fields, then lazy-load only the exact candidate. If the request could match more than one item, or the outcome is not clear enough to write into the owning record, ask User and STOP. Before any add, deduplicate against the entire open queue.

5. Restate the exact mutation and ask User to confirm unless the same message already gives an explicit, unambiguous instruction or answer. A Follow-Up record itself never supplies confirmation.

6. Apply the operation per [Practices > Followups]. For resolve, update the canonical owning record before closing the Follow-Up and choose `answered` or `completed` to match the result. For convert, create or identify the resulting Task before setting `resolution-ref:`. For withdraw, record why in the body; `resolution-ref: N/A` is allowed. For a reopen-as-add, cite the archived identifier in the new record's body and leave the old record untouched.

7. Resolve exact linked Reminders under [Practices > Reminders] when this operation deterministically answers/completes/converts or withdraws their target.

8. Verify schema, live/archive placement, pointers, Reminder closure, and WORM state. Log one Event for the mutation, including the Follow-Up ID, operation, result reference, and linked Reminder outcomes. Present the outcome and STOP.
