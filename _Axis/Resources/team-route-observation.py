#!/usr/bin/env python3
"""Pure observations for an owned Team route; never authority or acceptance.

Closing facts, when supplied, must come from caller-validated canonical records.
A normal process return certifies neither the Team objective nor its release.
Provider-reported cost is not evidence of incremental billing.
"""
import json
import math


def process_observation(result, *, closing=None):
    process = result.get('process') if isinstance(result, dict) else None
    if not isinstance(process, dict):
        return {'outcome': 'unknown', 'reason': 'missing-process-evidence', 'leader_terminal': False,
                'group_terminal': False, 'closing': 'unclassified'}
    code = result.get('returncode')
    reaped = process.get('leader_reaped') is True and type(code) is int
    reason = result.get('reason')
    signals = process.get('signals', [])
    cleanup = process.get('cleanup_errors', [])
    if (process.get('launched') is not True or not isinstance(signals, list) or not isinstance(cleanup, list)
            or any(not isinstance(item, dict) for item in signals + cleanup)):
        return {'outcome': 'unknown', 'reason': 'malformed-process-evidence', 'leader_terminal': False,
                'group_terminal': False, 'closing': 'unclassified'}
    forced = isinstance(signals, list) and any(isinstance(s, dict) and s.get('outcome') == 'sent' for s in signals)
    close = 'unclassified'
    if closing is not None:
        close = 'complete' if (isinstance(closing, dict) and closing.get('validated') is True
            and all(closing.get(k) is True for k in ('released', 'result', 'done'))) else 'incomplete'
    if reason == 'deadline-exceeded':
        outcome = 'deadline-terminated' if reaped else 'deadline-stop-unconfirmed'
    elif not reaped:
        outcome = 'unknown'
    elif forced or reason is not None or cleanup:
        outcome = 'supervisor-stopped'
    elif code != 0:
        outcome = 'provider-failed'
    elif close == 'incomplete':
        outcome = 'early-exit'
    elif close == 'complete':
        outcome = 'graceful-return' if process.get('group_stop_confirmed') is True else 'closing-complete-group-unconfirmed'
    else:
        outcome = 'normal-return' if process.get('group_stop_confirmed') is True else 'normal-return-group-unconfirmed'
    return {'outcome': outcome, 'reason': reason, 'returncode': code,
            'leader_terminal': reaped,
            'group_terminal': process.get('group_stop_confirmed') is True,
            'execution_terminal': reaped and process.get('group_stop_confirmed') is True,
            'capacity_released': False,
            'closing': close, 'signals': signals, 'cleanup_errors': cleanup,
            'notice': 'Process evidence is not result validation or authority to retry.'}


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError('duplicate telemetry key')
        value[key] = item
    return value


def _decode(raw):
    if not isinstance(raw, bytes) or len(raw) > 8 * 1024 * 1024:
        raise ValueError('unsupported telemetry size or type')
    text = raw.decode('utf-8', 'strict')
    if not text.strip():
        return []
    try:
        values = [json.loads(text, object_pairs_hook=_pairs)]
    except json.JSONDecodeError:
        values = [json.loads(line, object_pairs_hook=_pairs) for line in text.splitlines() if line.strip()]
    if not all(isinstance(value, dict) for value in values):
        raise ValueError('telemetry event shape')
    return values


def usage_observation(adapter, raw):
    """Normalize one terminal usage report, without summing overlapping snapshots."""
    result = {'status': 'unavailable', 'reason': 'no-terminal-usage', 'source': None,
              'input_tokens': None, 'cached_input_tokens': None, 'uncached_input_tokens': None, 'cache_creation_input_tokens': None,
              'uncached_input_basis': 'unverified-provider-semantics; no generic input-minus-cache computation',
              'output_tokens': None, 'provider_reported_cost_usd': None,
              'incremental_spend_minor': None,
              'cost_basis': 'unclassified-provider-report',
              'token_basis': 'provider fields retained separately; cache inclusion is route-specific'}
    if adapter not in {'codex', 'claude'}:
        result['reason'] = 'unsupported-route'; return result
    try:
        events = _decode(raw)
    except (ValueError, UnicodeError, OverflowError):
        result['reason'] = 'malformed-telemetry'; return result
    kind = 'turn.completed' if adapter == 'codex' else 'result'
    reports = [event for event in events if event.get('type') == kind]
    if len(reports) != 1:
        result['reason'] = 'ambiguous-terminal-usage' if reports else 'no-terminal-usage'
        return result
    report = reports[0]
    usage = report.get('usage')
    if not isinstance(usage, dict):
        return result
    result['source'] = kind
    fields = {'input_tokens': 'input_tokens', 'cached_input_tokens': 'cached_input_tokens' if adapter == 'codex' else 'cache_read_input_tokens',
              'cache_creation_input_tokens': 'cache_creation_input_tokens', 'output_tokens': 'output_tokens'}
    invalid = False
    for target, source in fields.items():
        value = usage.get(source)
        if value is not None:
            if type(value) is int and value >= 0:
                result[target] = value
            else:
                invalid = True
    cost = report.get('total_cost_usd')
    if cost is not None:
        try:
            valid_cost = type(cost) in (int, float) and math.isfinite(cost) and cost >= 0
        except OverflowError:
            valid_cost = False
        if valid_cost: result['provider_reported_cost_usd'] = cost
        else: invalid = True
    failed = (adapter == 'claude' and report.get('is_error') is not False) or any(e.get('type') in {'error', 'turn.failed'} for e in events)
    has_usage = any(result[key] is not None for key in fields)
    complete = result['input_tokens'] is not None and result['output_tokens'] is not None
    result['status'] = 'measured' if complete and not invalid and not failed else ('partial' if has_usage else 'unavailable')
    result['reason'] = ('invalid-usage-field' if invalid else 'provider-error' if failed else 'terminal-usage' if complete else 'partial-terminal-usage')
    return result
