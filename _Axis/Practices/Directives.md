# Directives
> **Purpose:** Define conditional Directives and how to draft reliable triggers.

A Directive defines behavior to follow under certain conditions. Directive may, or may not, need to be followed, unlike ordinary instructions, which always apply.

A Directive therefore needs an inferential framework (i.e., criteria) to determine when the conditions apply and when the Directive should be triggered.

The User may give you (Agent) an informal directive in a chat session (i.e., tell you to do something in certain situations). When a User gives a directive that seems important and needs to persist so it can be triggered in the future, you should record it as a new Directive in `_Axis/DIRECTIVES.md`.

Follow these principles when you draft triggers for a new Directive:

- **Focus on what matters.** You can manage only a limited number of Directives before selection accuracy degrades.

- **Draft Directives for interpretation by Agent, not User.** Triggers should be optimized for AI (embedding model and LLM semantic reasoning), not humans.

- **Minimize complexity.** Each condition in a compound trigger reduces reliability. If a trigger requires > 2 simultaneous conditions, restructure as a chain of simpler decisions.

- **Separate when from how.** The Triggers section of a Directive encodes activation conditions, whereas the Behavior section of a Directive encodes execution steps.

- **Test boundaries.** Test a new Directive with conditions that **should** trigger it, conditions that **should not** trigger it but are similar, and conditions that are ambiguous. Ask User for feedback and clarification about the triggering of the Directive for the ambiguous cases.

- **Test non-activation.** Conditional Directives are harder to evaluate than unconditional **Instructions** because non-activation can be correct (the "counterfactual blindness" problem). Therefore, test cases where condition is false and verify that the trigger correctly _does not_ fire.

## Default Directives

Every Axis version ships its default Directives twice: in the new-project template `_Axis/DIRECTIVES.md`, and in the managed `_Axis/Resources/Default-Directives.md`, which each update replaces. At startup `boot.py` appends any default Directive missing from the project's `_Axis/DIRECTIVES.md`, so existing projects receive new defaults after an update. It matches by heading, ignoring case, and never edits, reorders or removes an existing Directive. To keep a default out of a project, remove it and add the line `<!-- axis:omit-directive: {Directive name} -->` to `_Axis/DIRECTIVES.md`.
