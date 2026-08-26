# Template - Local Prompt
> **Purpose:** Provide the fill-in skeleton for every Local Subagent spawn prompt after [Practices > Delegation] has selected the task and validator. Copy the template, replace the `{{...}}` placeholders, and delete unused constraint slots. The send / validate / retry procedure lives in [Start-Subagent > How to Start a Local Subagent].

Rules for filling the template:

1. ONE task per spawn. If the work has two steps, spawn twice.
2. State the task before everything else - small models weight early tokens most.
3. Embed ALL input inside the INPUT fence - the model has no file access.
4. Keep the numbered constraints to 8 or fewer, one line each.
5. Show the output shape literally inside the contract - show, do not describe.
6. Keep the whole prompt within the `num_ctx` you set (see [Start-Subagent]); estimate ~4 characters per token.
7. Generate a fresh 32-lowercase-hex envelope nonce for this spawn. A local model is not asked to confirm it, but Main validates both boundaries and size before sending.

The template (the envelope lines stay bare - no backticks or quoting):

	<<AXIS:SUBAGENT>>
	<<AXIS:ROLE:LOCAL>>
	<<AXIS:ENVELOPE:{{32-lowercase-hex nonce}}:BEGIN>>

	TASK: {{one sentence: what to produce}}

	OUTPUT CONTRACT:
	Write your answer between the two marker lines below, and write NOTHING outside them.
	=====BEGIN-OUTPUT=====
	{{a literal example of the required shape, e.g.:
	name: ...
	date: ...
	summary: ...}}
	=====END-OUTPUT=====

	CONSTRAINTS:
	1. {{constraint - one line}}
	2. {{constraint - one line}}
	3. {{delete unused slots}}

	INPUT:
	```
	{{all source material the task needs - the Subagent can read nothing else}}
	```

	<<AXIS:SUBAGENT>>
	<<AXIS:ROLE:LOCAL>>
	<<AXIS:ENVELOPE:{{same nonce}}:END>>
