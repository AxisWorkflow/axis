# Delegation
> **Purpose:** Decide whether to delegate, select the least costly qualified route, define validation before spawning, and accept or reject the result.

## Responsibility

Delegation transfers execution, never authority. Main Agent remains responsible for the task, the permitted inputs, the model route, the validation, every project write, and the final result. Follow [Practices > Agents] for role and coordination rules; after choosing a route here, follow [Start-Subagent] for the operational spawn recipe.

A Subagent never writes `_Axis/Followups/`. If delegated work reveals a specific next action only User can take, the Subagent reports a Follow-Up candidate with the proposed ask and owning record in its return. Main decides whether it meets [Practices > Followups], deduplicates it, and creates the record if warranted. An External Agent uses a Request to Main for the same handoff.

Before delegating, read applicable User preferences, [Settings > Budget], [Rules > Capabilities], and any task-specific Practice. Do not delegate merely because a cheaper model or a spawn tool is available. Delegate when the expected savings, context isolation, parallelism, independent perspective, or specialized role outweighs the handoff and validation overhead.

## Classify the Work

Classify each bounded unit by the strongest kind of reasoning it requires:

- **Preservation work** extracts, classifies, reformats, or copies known values and citations without deciding what they mean. It is eligible for a qualified Local Subagent when the return can be checked mechanically against the source.
- **Composition work** summarizes, drafts, combines, selects, or omits material. It requires a matching demonstrated task-class aptitude and a semantic validator; otherwise route it to a standard-capability Subagent or keep it with Main.
- **Judgment work** determines truth, risk, security, strategy, priorities, conflicts, or what should be believed or done. Keep it with the standard-capability Main Agent or a qualified standard-capability Subagent. A small model does not become qualified for judgment because it passed a clerical task class.

When one task mixes classes, split it into bounded stages only if Main can validate the boundary between them. Otherwise route the entire unit according to its most demanding class.

## Choose the Route

Use the least costly route that is qualified for the work:

1. Main Agent directly - use when delegation adds no material value, validation would be as difficult as doing the work, the task carries high trust or authority, or no safe route is available.
2. Local Subagent - use only for bounded text-in / text-out work, with no file access, when the active model has matching evidence and Main can validate the return. A valid fingerprinted `class-score:` in [Practices > Flags] applies only to that transport, quantization, context, model, and task class:
	- `PASS` permits bounded delegation with the validator chosen below.
	- `CONDITIONAL` permits delegation only for low-stakes work with mechanical validation, the one-retry limit, and a ready fallback.
	- `FAIL` prohibits routing that class to the model.
	- A missing matching row does not establish dependable class aptitude. The five-fixture scorecard may support an explicitly low-stakes, mechanically verifiable transform, but never a claim that the class is reliable.
	- An installer default or published model recommendation is only a candidate-selection hint. It never overrides the matching per-machine class score.
	- `prompt-injection-refusal` is diagnostic only. Even `PASS` never relaxes the bans on Wiki ingest, secrets, or security-sensitive trust decisions.
3. General Subagent on a standard-capability model - use for composition, judgment support, exploration, comparison, independent review, or a context-isolated workstream that Main can supervise.
4. CX or Wiki Subagent - use only for its specialized Practice and model requirements.

Host Capability Flags determine whether the selected route can run and whether spawns may be parallel. A missing capability changes the route or makes it serial; it never lowers the required model capability.

## Define Validation Before Spawning

State the validator before writing the prompt. If Main cannot define a check strong enough to catch the likely consequential failure, do not send the work to a small model.

Choose every level the task needs:

- **Shape validation** checks markers, fields, types, counts, length, and other literal output-contract requirements.
- **Preservation validation** compares names, numbers, quotations, dates, citations, and required source facts exactly.
- **Semantic validation** checks roles, relationships, polarity, material omissions, and unsupported additions against the source. A valid output shape is not evidence that the facts have the right meaning.
- **Judgment validation** is review by Main Agent or another qualified standard-capability model against the task's decision criteria.

Define required facts, prohibited claims, acceptable omissions, source-fidelity checks, and the fallback before spawning. Main must be able to reject a fluent answer that satisfies the format while reversing who did what, inventing support, or omitting a material qualification.

## Stage Work When It Pays

A useful cost-saving pipeline is:

	source material
	→ qualified small model extracts, classifies, or preserves
	→ Main validates the structured facts
	→ standard-capability model reasons, drafts, or decides
	→ Main validates and accepts the final result

This can reduce expensive-model context by passing validated structured facts instead of all source bulk. Use it only when the source can be reduced without losing facts needed later and the saved model cost or context exceeds the routing, validation, and possible fallback cost. For a simple or one-off task, Main doing the work directly may be cheaper.

## Accept, Retry, or Fall Back

Main never blindly forwards or writes a Subagent return. Before acceptance, verify the selected shape, preservation, semantic, and judgment checks; then confirm required facts, prohibited claims, material omissions, and source fidelity.

Retry once only when the failure is correctable through specific validation feedback and the applicable recipe permits it. On a repeated failure, a failed aptitude gate, an unverified fingerprint, or an unavailable route, follow [Start-Subagent > Restrictions & Fallback] and record the required downgrade or fallback. Do not keep retrying until an answer happens to pass.

The goal is the cheapest **qualified** path, not the cheapest model. [Settings > Budget] may steer optional delegation, but it never overrides trust boundaries, model eligibility, Host Capability gates, task-class evidence, or validation.
