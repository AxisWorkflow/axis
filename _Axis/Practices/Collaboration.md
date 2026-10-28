# Collaboration
> **Purpose:** Configure how Team members work together without making one method universal.

Load when selecting or changing a Team's collaboration method. [Practices > Teams] owns setup; [Practices > Coordination] owns infrastructure and authority. A method describes work, not permissions. No pattern is universally preferred.

## Choose the method

| Pattern | Useful when | Method |
| --- | --- | --- |
| Delegated contributions | Parts can be produced separately | Assign parts, name dependencies and integration reviews, assemble one result. |
| Assistance | An owner needs specialist help | Direct questions and bounded contributions; the owner integrates the help. |
| Paired build and review | A draft needs sustained checking | Builder and reviewer iterate; roles may rotate within the plan. |
| Independent assessment | Diverse initial judgments matter | Freeze initial answers before revealing them, compare assumptions, reconcile or preserve alternatives. |
| Deliberative panel | A shared decision needs collective revision | Circulate drafts, respond to reviews, revise, synthesize and review the final synthesis. |
| Challenge and stress test | Claims need adversarial scrutiny | Probe consequential assumptions and failure cases; authors respond with evidence. |
| Custom or composed | The objective spans several methods | Name phases and transitions; preserve obligations and authority when the method changes. |

Use a pattern as a starting point, then adapt it with Main judgment and guided questions only where needed. An assistance team need not conduct all-to-all debate. A committee requested to deliberate together must actually have the concurrency and participation periods that permit it.

## Plan contract

A structured `axis.team-plan/v1` document includes revision, objective, deliverables, acceptance criteria, pattern, leader slot `leader`, worker slots, phases, participation periods, review assignments, synthesis owner, Main acceptance, and the total budget with a cost basis. `estimates` is telemetry/planning only. The helper's canonical hash identifies the exact plan; the charter embeds the reviewed object. It does not read instructions from a supplied path or make arbitrary code executable.

`all-workers` review expands to every ordered pair of different workers. `targeted` assignments map each reviewer to the authors whose artifacts they review. `none` is valid when the task does not require peer review. Name whether responses and synthesis review are required. These derived obligations are structural coverage; the reviewer still must assess the actual work and significant objections. Do not manufacture disagreement to meet a count.

Members publish immutable, attributable artifact revisions through the existing workspace mechanism. Reviews cite the exact revision. Later revisions and final synthesis retain substantive objections and explain their disposition. A final-review confirmation refers to the actual final artifact; an equivalent valid causal confirmation must not fail solely because it used a different incidental Message form.

## Adaptation and recovery

The leader may refine assignments and method within delegated discretion, publish the successor plan and reason, and identify how in-flight work is treated. Formal charter plan changes use Main's existing `amend` control with a replacement `collaboration_plan`, `summary` and explicit in-flight disposition. Binding validation and the epoch fence still apply. A plan amendment cannot enlarge authority, membership, path permissions or money/runtime limits. Keep prior revisions and retained artifacts available.

When an optional tool is unavailable, use the same portable plan and canonical records manually. When execution is interrupted, retain artifact/review references and outstanding obligations; resume through reconciled session/Job state. A procedure ending, a review question or a correctable fixture defect does not independently cancel the objective. Hold only the operation whose real precondition is missing.
