# Delegation
> **Purpose:** Decide whether to delegate, select the least costly qualified route, define validation before spawning, and accept or reject the result.

## Responsibility

Delegation transfers execution, never authority. Main Agent remains responsible for the task, the permitted inputs, the model route, the validation, every project write, and the final result. Follow [Practices > Agents] for role and coordination rules; after choosing a route here, write the contract with the delegating kit in `_Axis/Roles/Delegating.md` and follow [Start-Subagent] for the operational spawn recipe.

A delegate inherits conduct through its role text; authority comes only from its task contract; instruction status comes only from its prompt and the governing files pinned in it. Irreversible external actions (publishing, pushing, spending, signing in, contacting people) are not delegable unless the contract says User granted them.

**Every author.** The same kit, contract and envelope bind every agent that starts another: Main, a Team Leader, an External owner of a proposal Team and a parent Main. A delegate can only narrow the authority it received, and a granted start passes the same role text and governance unchanged.

**Judgment ownership.** Strategic, priority, risk and acceptance judgments stay with Main; delegated judgment is advice that Main checks against sources before relying on it. Relaxing this for a named class of work needs evidence, not the existence of the mechanism.

A Subagent never writes `_Axis/Followups/`. If delegated work reveals a specific next action only User can take, the Subagent reports a Follow-Up candidate with the proposed ask and owning record in its return. Main decides whether it meets [Practices > Followups], deduplicates it, and creates the record if warranted. An External Agent uses a Message to Main for the same handoff.

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

Pick the delegated role (General, Lookup, CX, Worker, TeamMember, TeamLeader, Wiki or Local) from the table in `_Axis/Roles/Delegating.md`. When the project's Claude Code settings hold the Axis guardrails (`^install guardrails`), spawn CX, Wiki, General and Lookup Subagents as the `axis-cx`, `axis-wiki`, `axis-general` and `axis-lookup` agent types, so the hook can hold each to its folders.

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

Main never blindly forwards or writes a Subagent return. Run the acceptance checklist in `_Axis/Roles/Delegating.md`, mechanical checks first. Verify that every changed or produced path was inside the persisted attempt scope; a supporting evidence file is still a write. Accept valid in-scope artifacts separately from any scope defect, and retain the defect instead of reporting whole-run compliance. Before acceptance, verify the selected shape, preservation, semantic, and judgment checks; then confirm required facts, prohibited claims, material omissions, and source fidelity.

Retry once only when the failure is correctable through specific validation feedback and the applicable recipe permits it. On a repeated failure, a failed aptitude gate, an unverified fingerprint, or an unavailable route, follow [Start-Subagent > Restrictions & Fallback] and record the required downgrade or fallback. Do not keep retrying until an answer happens to pass.

Inside an Axis Team of Agents, acceptance has two levels: the leader reviews members' work and keeps a verbatim register of their frame challenges with dispositions; Main judges the synthesis, every challenge marked material and a stated sample of the rest. A material challenge Main rejects appears in the deliverable.

The goal is the cheapest **qualified** path, not the cheapest model. [Settings > Budget] may steer optional delegation, but it never overrides trust boundaries, model eligibility, Host Capability gates, task-class evidence, or validation.
