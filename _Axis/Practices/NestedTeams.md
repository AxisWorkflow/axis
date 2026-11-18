# Nested Teams
> **Purpose:** Commission a child Team, review its work and account for its use within an explicit delegation grant.

Load this Practice when Main issues a delegation grant, a member's contract names them as a sponsor, or a sponsor needs to operate or supervise a child Team. [Practices > Coordination] supplies the record and lock rules.

## Grant and authority

Main records `delegation` on the root Team charter. Supply `sponsors` (named member slots), `purpose`, and when needed `depth` (levels below the Team, default 1, maximum 3), `actions` and `scope` (default to the charter's). Give the Team a native budget and room for its own simultaneous work plus its child Teams. Each child keeps the original clock, routes, accounting owner and cost basis. A child can delegate only what remains inside every ancestor's grant, resource limits and depth.

The current live session bound to a named slot acts as sponsor. A grant or seat change takes effect for new work immediately. Main changes the root grant by an `amend` that supplies a narrower grant or `null`, or changes the sponsor's binding. An amendment or transfer from a previously bound sponsoring session reports a `delegation_fence`. While pending, new work below the change is held. Main or a sponsor above the changed Team reruns `fence` until the affected locks actually pass. Use [Resources > Lock-File] for a stranded lock. Lease or lock age alone never establishes that a writer stopped. A revoked grant requires a new charter for new work.

## Operate a child Team

Use `python3 _Axis/Resources/nested-team.py --root . --session SID OPERATION` with one JSON object on standard input. If the helper or qualified direct storage is unavailable, use [Resources > Coordination-Manual > Nested Teams without the helper]. Scope and resource checks apply on both paths.

1. `team`: supply `parent`, a stable `operation_key` and `charter` with subject, objective, validator, slot-only `members` including `leader`, and `limits.concurrency`. Under a monetary ceiling, state the child's share as `limits.budget.money.ceiling_minor`. A zero share permits only costs that fit zero. Supply narrower actions/paths if needed. An embedded collaboration plan names `sponsor` as acceptance owner.
2. `member`: supply `team`, `slot` and a stable `operation_key`. The operation admits and binds a Marker. Start that member only with a separate TeamMember or TeamLeader envelope on an authorized Host route. If the Host cannot start another session, give the prepared contract to Main or User to arrange it.
3. Use `event` to start the Team, `job` with the mandate and its stable key, then `event` to dispatch the Job to a bound slot with the charge basis, route and evidence. Read the result before invoking a member. A held admission or dispatch grants no start.
4. Use `message`, `inbox`, `checkpoint` and `artifact-check` for review. Members return to `sponsor`. Record the result, validation, success and completion as distinct events supported by their evidence. This is local acceptance. Main decides shared project integration.
5. Reconcile attempts and charges, then `settle`. Settle descendants first. Settlement returns proved unused resources and carries known spend forward. Return the synthesis through your own Team.

Use `replace` with `team`, `slot`, `operation_key` and a checkpoint for the leader. It stops the old member's Marker and binds a successor. Reconcile active or uncertain attempts before redispatch. A tombstone alone cannot establish process exit. `retire` stops one admitted member of your direct child Team.

After interruption use the same key and payload. Read any partial effects before continuing. An unbound Marker may be adopted after a verified retry. A completed binding returns its recorded outcome, including that it was superseded or retired when applicable. A changed payload or later unrelated change can hold the operation. Keep the original evidence and current predecessor.

A successful authorized call maintains your existing lease when eligible. `renew` does only that. A stale, missing or killed lease requires recovery through the parent, with a fenced transfer where needed.

## Supervision and limits

Main and an ancestor sponsor may stop or reconcile work, account for charges and release or settle resources within their level of authority. The direct sponsor controls admission, dispatch and local review. A pause or freeze imposed from above requires the same level or higher to lift it. After a grant ends, use only the bound-seat cleanup, recovery and accounting actions still permitted.

A pending fence, lost sponsor, narrowed grant, Main turnover, outstanding descendant or held lock stops the affected operation. Read its cause before retrying. Settle or wind down work outside the current grant and preserve unresolved liabilities.

Automatic provider routes, selected closing contracts and shared-project writes remain outside the child Team path. Use the carried Host route and ordinary result. These are workflow controls among cooperating writers. Host isolation and provider billing still require their own verification.
