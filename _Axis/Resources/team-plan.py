#!/usr/bin/env python3
"""Portable Team collaboration plan preview. No spawning, admission or project writes.

Checks internal consistency of supplied planning data. It does not authenticate
authority, discover capabilities, verify a provider, or authorize execution.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path


PATTERNS = {
    'delegated-contributions', 'assistance', 'paired-build-review',
    'independent-assessment', 'deliberative-panel', 'challenge-stress-test',
    'custom',
}


def preview(plan):
    issues = []

    def require(condition, code):
        if not condition and code not in issues:
            issues.append(code)

    def positive(value):
        return type(value) is int and value > 0

    require(isinstance(plan, dict), 'plan-object-required')
    if issues:
        return {'consistent': False, 'issues': issues, 'dispatch_authorized': False}
    require(plan.get('schema') == 'axis.team-plan/v1', 'unsupported-schema')
    require(isinstance(plan.get('objective'), str) and bool(plan['objective'].strip()), 'missing-objective')
    require(isinstance(plan.get('pattern'), str) and plan['pattern'] in PATTERNS, 'unknown-pattern')
    require(isinstance(plan.get('revision'), str) and bool(plan['revision'].strip()), 'missing-revision')
    require(isinstance(plan.get('deliverables'), list) and bool(plan['deliverables']) and all(isinstance(d, str) and d.strip() for d in plan['deliverables']), 'missing-deliverables')
    require(isinstance(plan.get('acceptance'), str) and bool(plan['acceptance'].strip()), 'missing-acceptance')
    leader = plan.get('leader')
    require(isinstance(leader, str) and bool(leader) and leader != 'main', 'leader-must-be-separate')
    workers = plan.get('workers')
    require(isinstance(workers, list) and bool(workers) and all(isinstance(w, str) and w and w != 'main' for w in workers), 'invalid-workers')
    if 'invalid-workers' in issues:
        workers = []
    require(len(set(workers)) == len(workers) and leader not in workers and len({w.casefold() for w in workers}) == len(workers) and (not isinstance(leader, str) or leader.casefold() not in {w.casefold() for w in workers}), 'duplicate-member')
    members = workers + ([leader] if isinstance(leader, str) else [])
    participation = plan.get('participation', {})
    review = plan.get('review', {})
    synthesis = plan.get('synthesis', {})
    budget = plan.get('budget', {})
    estimates = plan.get('estimates', {})
    require('limits' not in plan, 'legacy-count-limits-not-a-budget')
    for name, value in [('participation', participation), ('review', review), ('synthesis', synthesis), ('budget', budget), ('estimates', estimates)]:
        require(isinstance(value, dict), 'invalid-' + name)
    if any(code.startswith('invalid-') and code != 'invalid-workers' for code in issues):
        return {'consistent': False, 'issues': issues, 'dispatch_authorized': False}
    mode = participation.get('mode')
    require(isinstance(mode, str) and mode in {'concurrent', 'scheduled'}, 'invalid-participation-mode')
    capacity = participation.get('declared_capacity')
    observed = participation.get('route_observed_capacity')
    require(positive(capacity), 'invalid-declared-capacity')
    required = len(members) if mode == 'concurrent' else participation.get('peak_required_slots')
    require(positive(required), 'missing-required-capacity')
    if positive(capacity) and positive(required):
        require(capacity >= required, 'insufficient-declared-capacity')
    require(observed is None or positive(observed), 'invalid-observed-capacity')
    if positive(observed) and positive(required):
        require(observed >= required, 'insufficient-observed-capacity')
    phases = plan.get('phases')
    require(isinstance(phases, list) and bool(phases) and all(isinstance(p, str) and p for p in phases), 'invalid-phases')
    if isinstance(phases, list) and phases and all(isinstance(p, str) for p in phases):
        required_through = participation.get('required_through', {})
        available_through = participation.get('available_through', {})
        require(isinstance(required_through, dict) and isinstance(available_through, dict), 'invalid-participation-periods')
        if isinstance(required_through, dict) and isinstance(available_through, dict):
            for member in members:
                needed = required_through.get(member)
                available = available_through.get(member)
                valid = needed in phases and available in phases
                require(valid, 'missing-participation-period')
                if valid:
                    require(phases.index(available) >= phases.index(needed), 'participation-ends-before-plan')
    if isinstance(phases, list) and all(isinstance(p, str) for p in phases):
        require(len(set(phases)) == len(phases), 'duplicate-phase')
    coverage = review.get('coverage')
    require(isinstance(coverage, str) and coverage in {'all-workers', 'targeted', 'none'}, 'invalid-review-coverage')
    expected_reviews = 0
    obligations = []
    if coverage == 'all-workers':
        expected_reviews = len(workers) * max(0, len(workers) - 1)
        obligations = [{'reviewer': a, 'author': b, 'response_required': True} for a in workers for b in workers if a != b]
        require(type(review.get('peers_per_worker')) is int and review['peers_per_worker'] == len(workers) - 1, 'incomplete-peer-coverage')
        require(review.get('responses_required') is True, 'missing-response-obligation')
    elif coverage == 'targeted':
        assignments = review.get('assignments', {})
        require(isinstance(assignments, dict) and bool(assignments), 'missing-review-assignments')
        if isinstance(assignments, dict):
            for source, recipients in assignments.items():
                valid = (source in members and isinstance(recipients, list)
                         and bool(recipients) and all(isinstance(r, str) and r in members and r != source for r in recipients))
                require(valid, 'invalid-review-assignment')
                if valid:
                    require(len(set(recipients)) == len(recipients), 'duplicate-review-assignment')
                    expected_reviews += len(set(recipients))
                    obligations.extend({'reviewer': source, 'author': target, 'response_required': review.get('responses_required') is True} for target in recipients)
    if isinstance(coverage, str) and coverage in {'all-workers', 'targeted'}:
        require(type(review.get('responses_required')) is bool, 'invalid-response-obligation')
    require(type(synthesis.get('member_review')) is bool, 'invalid-synthesis-review')
    require(synthesis.get('owner') in members, 'invalid-synthesis-owner')
    require(synthesis.get('acceptance_owner') == 'main', 'missing-main-acceptance')
    allowed_budget = {'max_spend_usd', 'max_runtime_minutes', 'spend_basis'}
    require(not (set(budget) - allowed_budget), 'unsupported-budget-field')
    money = budget.get('max_spend_usd')
    runtime = budget.get('max_runtime_minutes')
    def finite(v):
        try:
            return type(v) in (int, float) and math.isfinite(v)
        except OverflowError:
            return False
    require(money is not None or runtime is not None, 'missing-total-budget')
    require(money is None or (finite(money) and money >= 0), 'invalid-spend-bound')
    require(runtime is None or (finite(runtime) and runtime > 0), 'invalid-runtime-bound')
    if money is not None:
        require(isinstance(budget.get('spend_basis'), str) and budget['spend_basis'] in {'incremental-charges', 'attributed-cost'}, 'missing-cost-basis')
    # Estimates never gate readiness or become substitute budget ceilings.
    try:
        plan_digest = hashlib.sha256(json.dumps(plan, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()).hexdigest()
    except (ValueError, TypeError):
        plan_digest = None
        require(False, 'non-json-plan')
    return {
        'consistent': not issues,
        'plan_sha256': plan_digest,
        'obligations': obligations,
        'issues': issues,
        'summary': {
            'objective': plan.get('objective'), 'pattern': plan.get('pattern'),
            'workers': len(workers), 'leaders': 1, 'participants': len(members),
            'participation': mode, 'required_capacity': required,
            'declared_capacity': capacity, 'supplied_observed_capacity': observed,
            'required_directed_reviews': expected_reviews,
            'synthesis_owner': synthesis.get('owner'), 'budget': budget, 'estimates': estimates,
            'budget_stop_conditions': [name for name, value in [('total-spend', money), ('total-runtime', runtime)] if value is not None],
        },
        'dispatch_authorized': False,
        'unverified': ['actual authority', 'provider access and allowance', 'capability observations',
                       'storage and lease safety', 'runtime readiness', 'semantic quality of the plan'],
    }


def bind(plan, slots, concurrency, budget_policy=None, ceilings=None):
    """Validate a plan against actual charter roles; never grants authority."""
    result = preview(plan)
    issues = list(result['issues'])
    if not issues:
        if plan['leader'] != 'leader' or set(plan['workers'] + ['leader']) != set(slots):
            issues.append('plan-membership-mismatch')
        if type(concurrency) is not int or concurrency < result['summary']['required_capacity']:
            issues.append('plan-concurrency-mismatch')
    if not issues and budget_policy is not None:
        from decimal import Decimal
        money = budget_policy.get('money')
        runtime = budget_policy.get('runtime_seconds')
        total = ceilings or {'money_minor': money.get('ceiling_minor') if money else None, 'runtime_seconds': runtime}
        supplied = plan['budget']
        consistent = ((supplied.get('max_runtime_minutes') is None and total['runtime_seconds'] is None) or
                      (supplied.get('max_runtime_minutes') is not None and total['runtime_seconds'] is not None and
                       Decimal(str(supplied['max_runtime_minutes'])) * 60 == total['runtime_seconds']))
        if money is None:
            consistent = consistent and supplied.get('max_spend_usd') is None
        else:
            consistent = consistent and money['currency'] == 'USD' and supplied.get('max_spend_usd') is not None
            consistent = consistent and Decimal(str(supplied.get('max_spend_usd', 0))) * 100 == total['money_minor']
            consistent = consistent and supplied.get('spend_basis') == money['cost_basis']
        if not consistent: issues.append('plan-budget-summary-mismatch')
    result['issues'] = issues
    result['consistent'] = not issues
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    try:
        value = json.loads(args.plan.read_text())
        result = preview(value)
    except (OSError, ValueError, TypeError) as error:
        result = {'consistent': False, 'issues': ['unreadable-or-malformed-plan'],
                  'error_type': type(error).__name__, 'dispatch_authorized': False}
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result['consistent'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
