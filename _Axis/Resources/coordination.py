#!/usr/bin/env python3
"""Portable coordination records and bounded, Main-owned orchestration. Standard library only.

No provider is called here. Issuer/lease snapshots and hashes are provenance, not authentication;
this protocol assumes one Main control authority, cooperating scoped writers and ordinary file integrity. Indexes are
rebuildable views. Control decisions are immutable Messages with an explicit causal predecessor.
"""
from __future__ import annotations
import argparse
import base64
import contextlib
from collections import OrderedDict
import copy
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
import stat
import sys
import time
import threading
import uuid
from urllib.parse import quote
sys.dont_write_bytecode = True

_SPEC = importlib.util.spec_from_file_location('axis_coordination_startup', Path(__file__).with_name('startup-state.py'))
if _SPEC is None or _SPEC.loader is None:
    raise ImportError('startup-state unavailable')
_START = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_START)
_FORMAT_SPEC = importlib.util.spec_from_file_location('axis_coordination_record', Path(__file__).with_name('coordination-record.py'))
_FORMAT = importlib.util.module_from_spec(_FORMAT_SPEC)
_FORMAT_SPEC.loader.exec_module(_FORMAT)
SCHEMA = 'axis.coordination/v1'
RUNTIME_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
COORDINATION_PROTOCOL = 2
FAMILIES = ('Teams', 'Messages', 'Jobs', 'Schedules')
MESSAGE_KINDS = {'request', 'offer', 'assignment', 'question', 'answer', 'receipt', 'result', 'validation', 'decision', 'control', 'transfer'}
PROPOSALS = {'offer', 'question', 'answer', 'receipt', 'result'}
TERMINAL = {'succeeded', 'completed', 'failed', 'cancelled', 'expired'}
JOB_ACTIONS = {'dispatch', 'receipt', 'result', 'validate', 'attempt_failed', 'retry', 'uncertain', 'reconcile', 'round', 'pause', 'boundary', 'resume', 'cancel', 'checkpoint', 'succeed', 'fail', 'expire', 'charge', 'budget_hold', 'route_boundary'}
TEAM_ACTIONS = {'start', 'bind_member', 'replace_leader', 'amend', 'pause', 'resume', 'cancel', 'complete', 'fail', 'checkpoint', 'budget_hold'}
SAFE_OPERATIONS = {'inspect', 'read', 'report', 'write', 'validate', 'coordinate', 'dispatch'}
MAX_BODY = 16 * 1024
MAX_RECORD = 131072
MAX_ATTACHMENT = 64 * 1024 * 1024
MAX_WORK_FILE = 65536
COLLABORATION = {'version': 1, 'poll_seconds': 5, 'max_messages_per_member': 200}


def workspace_token(value):
    need(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,63}', value) is not None
         and not value.endswith('.'), 'workspace-name')
    reserved = {'con', 'prn', 'aux', 'nul'} | {'com'+str(n) for n in range(1,10)} | {'lpt'+str(n) for n in range(1,10)}
    need(value.split('.')[0].casefold() not in reserved, 'workspace-name')
    return value


def collaboration(value):
    need(isinstance(value, dict) and set(value) == set(COLLABORATION), 'collaboration-policy')
    need(type(value['version']) is int and value['version'] == 1, 'collaboration-version')
    _integer(value['poll_seconds'], 'poll-seconds', 1, 60)
    _integer(value['max_messages_per_member'], 'message-limit', 1, 10000)
    return value


class CoordinationError(Exception):
    def __init__(self, code, path=''):
        self.code, self.path = code, str(path)
        super().__init__(code + (': ' + self.path if self.path else ''))


def need(condition, code, path=''):
    if not condition:
        raise CoordinationError(code, path)


def timestamp(value):
    try:
        return _START.parse_stamp(value)
    except (ValueError, TypeError, _START.Fault):
        raise CoordinationError('timestamp', value) from None


def stamp(value=None):
    return _START.stamp(value)


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
    except (TypeError, ValueError):
        raise CoordinationError('json-value') from None


def digest(value):
    """Digest canonical JSON, or the exact bytes/string supplied by the caller."""
    raw = value if isinstance(value, bytes) else value.encode('utf-8') if isinstance(value, str) else canonical(value)
    return hashlib.sha256(raw).hexdigest()


def relative(value):
    need(isinstance(value, str) and value and not value.startswith('/') and '\\' not in value and '\x00' not in value, 'unsafe-path', value)
    need(all(p not in ('', '.', '..') for p in value.split('/')), 'unsafe-path', value)
    need(not any(p.lower() == 'secrets' for p in value.split('/')), 'protected-path', value)
    return value


def identity(value):
    timestamp(value)
    return value


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        need(key not in result, 'duplicate-json-key', key)
        result[key] = value
    return result


# Cache successful parsing only, never filesystem observations or mutable records.
# Each caller still reads fresh bytes through the original no-link/size checks.
_DECODE_MAX_BYTES = 64 * 1024 * 1024
_DECODE_MAX_ENTRIES = 16384


class _DecodeState:
    def __init__(self):
        self.pid = os.getpid()
        self.lock = threading.Lock()
        self.values = OrderedDict()
        self.bytes = 0


_DECODE_STATE = _DecodeState()


def _decode(text):
    global _DECODE_STATE
    cache = _DECODE_STATE
    if cache.pid != os.getpid():
        # Never acquire a mutex inherited from another process. A local state
        # reference also keeps concurrent first reads from mixing locks/counters.
        cache = _DecodeState()
        _DECODE_STATE = cache
    with cache.lock:
        cached = cache.values.get(text)
        if cached is not None:
            cache.values.move_to_end(text)
    if cached is not None:
        return json.loads(cached[0])
    record = _decode_uncached(text)
    payload = canonical(record)
    # Include key/value storage and a conservative per-entry container allowance.
    weight = sys.getsizeof(text) + sys.getsizeof(payload) + 256
    if weight <= _DECODE_MAX_BYTES:
        with cache.lock:
            prior = cache.values.pop(text, None)
            if prior is not None:
                cache.bytes -= prior[1]
            cache.values[text] = (payload, weight)
            cache.bytes += weight
            while len(cache.values) > _DECODE_MAX_ENTRIES or cache.bytes > _DECODE_MAX_BYTES:
                _, removed = cache.values.popitem(last=False)
                cache.bytes -= removed[1]
    return record

def _decode_uncached(text):
    try:
        subject, record = _FORMAT.decode(text, MAX_RECORD)
    except (ValueError, TypeError, RecursionError) as exc:
        raise CoordinationError('record-integrity', str(exc)) from None
    need(record.get('subject') == subject, 'record-subject')
    _envelope(record)
    return record


def _envelope(record):
    need(record.get('schema') == SCHEMA and record.get('family') in FAMILIES, 'record-schema')
    identity(record.get('id')); timestamp(record.get('created'))
    try:
        need(str(uuid.UUID(record.get('project'))) == record.get('project'), 'project-id')
    except (ValueError, TypeError, AttributeError):
        raise CoordinationError('project-id') from None
    issuer = record.get('issuer')
    need(isinstance(issuer, dict) and issuer.get('role') in {'main', 'worker', 'external'}, 'issuer')
    identity(issuer.get('session'))
    if issuer.get('role') == 'external' or 'proposal_only' in record or 'proposal_control' in record: _controlled(record)
    if 'budget_amendment' in record:
        if record['family'] == 'Jobs': identity(record['budget_amendment'])
        else:
            need(record['family'] == 'Messages' and isinstance(record['budget_amendment'], dict), 'budget-amendment-shape')
            key = record['budget_amendment'].get('budget_key')
            need(isinstance(key, str) and 0 < len(key.encode()) <= 249 and '\n' not in key, 'budget-key')
    if record['family'] == 'Messages':
        need(record.get('kind') in MESSAGE_KINDS, 'message-kind')
        need(isinstance(record.get('body'), str) and len(record['body'].encode()) <= MAX_BODY, 'message-body')
        need(isinstance(record.get('data', {}), dict), 'message-data')
        need(type(record.get('epoch')) is int and record['epoch'] >= 0, 'epoch')
        timestamp(record.get('expires'))
        need(isinstance(record.get('recipient'), str) and 0 < len(record['recipient']) <= 256, 'recipient')
        need(isinstance(record.get('correlation'), str) and 0 < len(record['correlation'].encode()) <= 256, 'correlation')
        for key in ('team', 'job'):
            if record.get(key) is not None: identity(record[key])
        attachments = record.get('attachments', [])
        need(isinstance(attachments, list) and len(attachments) <= 16, 'attachments')
        for attachment in attachments:
            need(isinstance(attachment, dict), 'attachment')
            relative(attachment.get('path'))
            _integer(attachment.get('size'), 'attachment-size', 0, MAX_ATTACHMENT)
            need(re.fullmatch(r'[0-9a-f]{64}', attachment.get('sha256', '')) is not None, 'attachment-digest')


def render_record(record):
    _envelope(record)
    try:
        text = _FORMAT.render(record.get('subject'), record)
    except (ValueError, TypeError, RecursionError) as exc:
        raise CoordinationError('record-shape', str(exc)) from None
    need(len(text.encode()) <= MAX_RECORD, 'record-size')
    return text


def read_record(path):
    """Read one regular no-symlink, single-link Markdown record (all parent components checked)."""
    path = Path(path)
    need('..' not in path.parts, 'unsafe-path', path)
    absolute = Path(os.path.abspath(path))
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        info = current.lstat()
        need(not stat.S_ISLNK(info.st_mode), 'unsafe-path', current)
        if current != absolute:
            need(stat.S_ISDIR(info.st_mode), 'unsafe-path', current)
    fd = os.open(absolute, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        raw = _START.read_fd(fd, str(path), MAX_RECORD)
    except _START.Fault as exc:
        raise CoordinationError(exc.code, exc.path) from None
    finally:
        os.close(fd)
    try:
        return _decode(raw.decode('utf-8'))
    except UnicodeError:
        raise CoordinationError('record-encoding', path) from None


def _accepted(record):
    """Validate the acceptance contract without requiring a historical Marker to survive."""
    issuer = record.get('issuer', {})
    acceptance = record.get('acceptance', {})
    sid = issuer.get('session')
    need(issuer.get('role') == 'main' and acceptance.get('session') == sid, 'unaccepted-control')
    identity(sid)
    marker = acceptance.get('marker')
    need(isinstance(marker, str), 'acceptance-marker')
    lines = marker.splitlines()
    need(len(lines) == 4 and lines[:3] == ['Main: session', '', 'session: ' + sid] and lines[3].startswith('host: ') and lines[3][6:].strip(), 'acceptance-marker')
    need(acceptance.get('marker_sha256') == digest(marker), 'acceptance-digest')
    if 'placement_activation' in acceptance:
        need(isinstance(acceptance['placement_activation'], str) and re.fullmatch(r'[0-9a-f]{32}', acceptance['placement_activation']), 'acceptance-placement')


def _controlled(record):
    """Validate a control's provenance without conflating proposal and acceptance."""
    if record.get('issuer', {}).get('role') != 'external':
        need('proposal_only' not in record and 'proposal_control' not in record, 'proposal-classification')
        return _accepted(record)
    need('acceptance' not in record, 'proposal-has-acceptance')
    proposal = record.get('proposal_control', {})
    sid = record['issuer']['session']
    need(isinstance(proposal, dict) and set(proposal) == {'version', 'owner', 'marker', 'marker_sha256', 'main', 'placement_activation'}, 'proposal-control-shape')
    need(proposal.get('version') == 1 and proposal.get('owner') == sid, 'proposal-owner')
    marker = proposal.get('marker')
    need(isinstance(marker, str) and marker.startswith('External:'), 'proposal-external-marker')
    need(proposal.get('marker_sha256') == digest(marker), 'proposal-marker-digest')
    identity(proposal.get('main'))
    need(re.fullmatch(r'[0-9a-f]{32}', proposal.get('placement_activation', '')) is not None, 'proposal-placement')
    need(record.get('proposal_only') is True, 'proposal-classification')


def validate_acceptance(record):
    """Validate Main acceptance provenance; does not claim authentication."""
    _envelope(record)
    _accepted(record)
    return record['acceptance']


accepted = validate_acceptance


def _integer(value, name, low=0, high=100000):
    need(type(value) is int and low <= value <= high, 'limit-' + name)
    return value


def _native(record):
    """An explicit versioned policy selects new semantics; absence means legacy."""
    return 'budget' in record.get('limits', {})


def _native_policy(value, now=None):
    required = {'version', 'key', 'clock_start', 'accounting_owner', 'scope', 'routes'}
    need(isinstance(value, dict) and required <= value.keys() and value.keys() <= required | {'money', 'runtime_seconds'}, 'native-budget-shape')
    need(type(value['version']) is int and value['version'] == 1, 'native-budget-version')
    need(isinstance(value['key'], str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value['key']), 'native-budget-key')
    start = timestamp(value['clock_start']); identity(value['accounting_owner'])
    if now is not None: need(start <= now, 'budget-clock-future')
    need(isinstance(value['scope'], str) and 0 < len(value['scope'].encode()) <= 4096, 'budget-scope')
    routes = value['routes']
    need(isinstance(routes, dict) and set(routes) == {'included', 'incremental'}, 'budget-routes')
    for names in routes.values():
        need(isinstance(names, list) and all(isinstance(n, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', n) for n in names), 'budget-routes')
        need(len(names) == len(set(names)), 'budget-routes')
    need(routes['included'] or routes['incremental'], 'budget-routes')
    need(not set(routes['included']).intersection(routes['incremental']), 'budget-routes')
    need('money' in value or 'runtime_seconds' in value, 'native-budget-empty')
    if 'money' in value:
        money = value['money']
        need(isinstance(money, dict) and set(money) == {'currency', 'ceiling_minor', 'cost_basis'}, 'budget-money')
        need(isinstance(money['currency'], str) and re.fullmatch(r'[A-Z]{3}', money['currency']), 'budget-currency')
        _integer(money['ceiling_minor'], 'money-minor', 0, 10**18)
        need(isinstance(money['cost_basis'], str) and 0 < len(money['cost_basis'].encode()) <= 4096, 'budget-cost-basis')
    if 'runtime_seconds' in value: _integer(value['runtime_seconds'], 'runtime-seconds', 1, 10**12)
    return copy.deepcopy(value)


def _native_charge(policy, value):
    need(isinstance(value, dict) and set(value) == {'basis', 'route', 'reserve_minor', 'evidence'}, 'budget-charge-shape')
    basis = value['basis']
    need(isinstance(basis, str) and basis in {'included', 'incremental'} and isinstance(value['route'], str) and value['route'] in policy['routes'][basis], 'budget-route-unauthorized')
    unpriced = value['reserve_minor'] is None
    if unpriced:
        need('money' not in policy and basis == 'incremental', 'budget-reservation-required')
        reserve = 0
    else:
        reserve = _integer(value['reserve_minor'], 'reserve-minor', 0, 10**18)
        need(reserve == 0 if basis == 'included' else reserve > 0, 'budget-reservation-required')
    need(isinstance(value['evidence'], str) and value['evidence'].strip(), 'budget-charge-evidence')
    return {'known_minor': 0, 'reserved_minor': reserve, 'uncertain_minor': 0, 'final': basis == 'included', 'unpriced': unpriced, 'reports': {}}


def _native_report(item, data, event):
    required = {'attempt', 'report_id', 'known_minor', 'reserved_minor', 'uncertain_minor', 'final', 'evidence'}
    need(set(data) == required, 'budget-report-shape')
    token = _attempt_token(data['report_id'])
    charge = item['charge_state']
    need(token not in charge['reports'], 'budget-report-duplicate')
    for name in ('known_minor', 'reserved_minor', 'uncertain_minor'): _integer(data[name], name, 0, 10**18)
    need(type(data['final']) is bool and isinstance(data['evidence'], str) and data['evidence'].strip(), 'budget-report-evidence')
    need(data['known_minor'] >= charge['known_minor'], 'budget-known-regression')
    need(not data['final'] or data['reserved_minor'] == data['uncertain_minor'] == 0, 'budget-final-unsettled')
    if charge['final']:
        need(data['final'] and data['reserved_minor'] == data['uncertain_minor'] == 0, 'budget-already-final')
    elif not data['final']:
        need(sum(data[k] for k in ('known_minor', 'reserved_minor', 'uncertain_minor')) >= sum(charge[k] for k in ('known_minor', 'reserved_minor', 'uncertain_minor')), 'budget-liability-regression')
    for name in ('known_minor', 'reserved_minor', 'uncertain_minor', 'final'): charge[name] = data[name]
    if data['final']: charge['unpriced'] = False
    charge['reports'][token] = {'event': event['id'], 'data': copy.deepcopy(data)}


def _limits(limits, now=None):
    need(isinstance(limits, dict), 'limits')
    limits = copy.deepcopy(limits)
    defaults = {'rounds': 3, 'launches': 12, 'concurrency': 3, 'reserve_launches': 1, 'retries': 2}
    for key, default in defaults.items():
        limits.setdefault(key, default)
        if 'budget' in limits and key != 'concurrency':
            need(type(limits[key]) is int and limits[key] >= 0, 'budget-estimate-' + key)
        else:
            _integer(limits[key], key, 0 if key in {'reserve_launches', 'retries'} else 1)
    if 'budget' in limits:
        limits['budget'] = _native_policy(limits['budget'], now)
    else:
        need(limits['reserve_launches'] < limits['launches'], 'report-reserve')
        need(limits['retries'] <= 2, 'retry-limit')
    deadline = timestamp(limits.get('deadline'))
    if now is not None:
        need(now < deadline, 'deadline')
    if 'aggregate_concurrency' in limits:
        _integer(limits['aggregate_concurrency'], 'aggregate_concurrency', 1)
    if 'aggregate_launches' in limits:
        if 'budget' in limits: need(type(limits['aggregate_launches']) is int and limits['aggregate_launches'] >= 0, 'budget-estimate-aggregate-launches')
        else: _integer(limits['aggregate_launches'], 'aggregate_launches', 1)
    limits.setdefault('usage', 'unmetered; launch/time bounds only, no hard currency cap')
    need(isinstance(limits['usage'], str) and limits['usage'].strip(), 'usage-policy')
    return limits


def _report_reserve(record, state):
    consumed = sum(a.get('purpose') in {'validation', 'checkpoint', 'report'} for a in state['attempts'].values())
    return max(0, record['limits']['reserve_launches'] - consumed)


def _remaining_reservation(record, state):
    return max(_report_reserve(record, state), record.get('reservation_launches', 1 + record['limits']['reserve_launches']) - state['launches'])


def _attempt_token(value):
    need(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', value) is not None, 'attempt')
    return value


def _bound_plan(record, *, verify=True):
    """Optional method validation; no plan is loaded on the legacy path."""
    if 'collaboration_plan' not in record:
        need('collaboration_plan_sha256' not in record, 'plan-without-content')
        return None
    spec = importlib.util.spec_from_file_location('axis_team_plan', Path(__file__).with_name('team-plan.py'))
    try:
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    except (OSError, ImportError, AttributeError) as error:
        raise CoordinationError('plan-validator-unavailable') from error
    slots = [m.get('slot') for m in record.get('members', []) if isinstance(m, dict)]
    result = module.bind(record['collaboration_plan'], slots, record['limits']['concurrency'], record['limits'].get('budget'))
    need(result['consistent'], 'collaboration-plan:' + ','.join(result['issues']))
    if verify:
        need(record.get('collaboration_plan_sha256') == result['plan_sha256'], 'plan-digest')
    return result


def _initial(record):
    _controlled(record)
    need(record['family'] in {'Teams', 'Jobs'}, 'projection-family')
    limits = _limits(record.get('limits'))
    authority = record.get('authority', {})
    timestamp(authority.get('expires'))
    relative(authority.get('ref'))
    need(re.fullmatch(r'[0-9a-f]{64}', authority.get('digest', '')) is not None, 'authority-digest')
    need(record.get('acceptance_owner') == record['issuer']['session'], 'acceptance-owner')
    need(isinstance(record.get('objective'), str) and record['objective'].strip(), 'objective')
    need(isinstance(record.get('validator'), str) and record['validator'].strip(), 'validator')
    need(isinstance(record.get('scope'), list) and record['scope'], 'scope')
    for path in record['scope']: relative(path)
    if record.get('proposal_only'):
        team_id = record['id'] if record['family'] == 'Teams' else identity(record.get('team'))
        prefix = '_Axis/Teams/' + team_id + '/members'
        need(all(p == prefix or p.startswith(prefix + '/') for p in record['scope']), 'proposal-scope')
        need(_native(record), 'proposal-native-budget-required')
    need(isinstance(record.get('actions'), list) and record['actions'] and set(record['actions']) <= SAFE_OPERATIONS, 'actions')
    need(timestamp(limits['deadline']) <= timestamp(authority['expires']), 'mandate-deadline')
    common = {'acceptance_class': 'proposal' if record.get('proposal_only') else 'accepted', 'id': record['id'], 'family': record['family'], 'head': record['id'], 'epoch': 0, 'held': False, 'holds': [], 'history': [], 'limits': limits, 'authority': copy.deepcopy(authority), 'completed_at': None}
    if record['family'] == 'Teams':
        if 'collaboration' in record: collaboration(record['collaboration'])
        members = copy.deepcopy(record.get('members', []))
        need(isinstance(members, list), 'members')
        slots = [m.get('slot') for m in members if isinstance(m, dict)]
        need(len(slots) == len(members) and len(set(slots)) == len(slots) and 'leader' in slots, 'leader-slot')
        for member in members:
            _attempt_token(member.get('slot'))
            if 'collaboration' in record: workspace_token(member['slot'])
            if member.get('session') is not None:
                identity(member['session'])
                need(member['session'] != record['issuer']['session'], 'dedicated-leader')
        if 'collaboration' in record: need(len({s.casefold() for s in slots}) == len(slots), 'member-path-alias')
        common.update(state='ready', members={m['slot']: m for m in members}, leader=next(m.get('session') for m in members if m['slot'] == 'leader'))
        plan = _bound_plan(record)
        if plan: common.update(collaboration_plan=copy.deepcopy(record['collaboration_plan']), collaboration_plan_sha256=plan['plan_sha256'])
    else:
        common.update(state='admitted', attempts={}, active=[], launches=0, rounds=0, retry_count=0, validations=[], results=[], late_results=[], stop_unconfirmed=[], classification=None, idempotent=False)
    return common


def _job_transition(state, event, record, proposals):
    action, data = event['action'], event['data']
    now = timestamp(event['at'])
    limits = state['limits']
    active = state['active']
    pending = {key for key, value in state['attempts'].items() if value.get('route_pending') is True}
    occupied = set(active) | pending
    if action == 'dispatch':
        need(state['state'] in {'admitted', 'running'}, 'dispatch-state')
        need(now < timestamp(limits['deadline']) and now < timestamp(state['authority']['expires']), 'deadline')
        attempt = _attempt_token(data.get('attempt'))
        need(attempt not in state['attempts'], 'duplicate-attempt')
        identity(data.get('session'))
        need(data['session'] != record['issuer']['session'], 'main-worker')
        slot = _attempt_token(data.get('slot'))
        need(data.get('operation') in record['actions'], 'operation-scope')
        need(not any(state['attempts'][a]['session'] == data['session'] for a in occupied), 'session-busy')
        need(len(occupied) < limits['concurrency'], 'concurrency')
        reporting = data.get('purpose') in {'validation', 'checkpoint', 'report'}
        ceiling = limits['launches'] if reporting else limits['launches'] - limits['reserve_launches']
        if not _native(record): need(state['launches'] < ceiling, 'launches')
        if data.get('retry_of'):
            prior = state['attempts'].get(data['retry_of'], {})
            need(prior.get('retry_authorized') is True and prior.get('retry_used') is not True, 'retry-not-authorized')
            need(now >= timestamp(prior['retry_after']), 'retry-backoff')
            prior['retry_used'] = True
        if 'scope' in data:
            need(isinstance(data['scope'], list) and all(any(p == base or p.startswith(base + '/') for base in record['scope']) for p in data['scope']), 'write-scope')
            for path in data['scope']:
                relative(path)
        state['attempts'][attempt] = dict(data, status='dispatch-intent', event=event['id'], epoch=event['epoch'], dispatched_at=event['at'])
        if _native(record):
            state['attempts'][attempt]['charge_state'] = _native_charge(limits['budget'], data.get('charge'))
            if 'route_request_sha256' in data:
                need(isinstance(data['route_request_sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', data['route_request_sha256']), 'route-request-digest')
                state['attempts'][attempt].update(route_pending=True, route_uncertain=False)
        active.append(attempt); state['launches'] += 1; state['state'] = 'running'
    elif action == 'route_boundary':
        need(_native(record), 'native-route-required')
        attempt = data.get('attempt'); item = state['attempts'].get(attempt)
        need(item is not None and isinstance(item.get('route_request_sha256'), str), 'route-attempt')
        need(type(data.get('confirmed')) is bool and data.get('request_sha256') == item['route_request_sha256'], 'route-boundary-binding')
        need(isinstance(data.get('evidence'), str) and data['evidence'].strip(), 'route-boundary-evidence')
        def route_record(ident, stage, kind):
            value = proposals.get(ident); need(isinstance(value, dict), 'route-record')
            _envelope(value); _accepted(value)
            detail = value.get('data', {})
            need(value['kind'] == kind and value.get('project') == record['project'] and value.get('team') == record.get('team') and value.get('job') == record['id'] and value.get('epoch') == item['epoch'], 'route-record-binding')
            need(detail.get('protocol') == 'axis.team-route/v1' and detail.get('stage') == stage and detail.get('job') == record['id'] and detail.get('attempt') == attempt and detail.get('request_sha256') == item['route_request_sha256'], 'route-record-binding')
            return value, detail
        intent, _ = route_record(data.get('intent'), 'intent', 'control')
        result, detail = route_record(data.get('result'), 'terminal-observation' if data['confirmed'] else 'result', 'result')
        need(detail.get('intent') == intent['id'], 'route-intent-binding')
        if data['confirmed']:
            original, original_data = route_record(detail.get('route_result'), 'result', 'result')
            need(original_data.get('intent') == intent['id'], 'route-original-binding')
            boundary = detail.get('boundary', {})
            need(boundary.get('verified') is True and boundary.get('group_terminal') is True and isinstance(boundary.get('evidence'), str) and boundary['evidence'].strip(), 'route-terminal-proof')
            need(detail.get('ended_at') == original_data.get('ended_at'), 'route-return-time')
            need(boundary.get('intent') == intent['id'] and boundary.get('request_sha256') == item['route_request_sha256'], 'route-boundary-identity')
            if original_data.get('recovery_observation') is True:
                need(original_data.get('ended_at') is None and detail.get('requested_result') is None and boundary.get('result') is None, 'route-interrupted-proof')
            else:
                need(boundary.get('result') == original['id'] and detail.get('requested_result', original['id']) == original['id'], 'route-boundary-identity')
        if item.get('route_boundary') == data:
            return
        need(item.get('route_pending') is True, 'route-already-terminal')
        item['route_boundary'] = copy.deepcopy(data)
        item['route_boundary_event'] = event['id']
        item['route_uncertain'] = not data['confirmed']
        if data['confirmed']:
            item['route_pending'] = False
            if attempt in active: active.remove(attempt)
            if attempt in state['stop_unconfirmed']: state['stop_unconfirmed'].remove(attempt)
            if state['state'] == 'pause-requested' and not active and not any(a.get('route_pending') for a in state['attempts'].values()): state['state'] = 'paused'
    elif action == 'charge':
        need(_native(record), 'native-budget-required')
        item = state['attempts'].get(data.get('attempt'))
        need(item is not None, 'unknown-attempt')
        _native_report(item, data, event)
    elif action in {'receipt', 'result', 'validate', 'attempt_failed', 'uncertain', 'reconcile', 'retry'}:
        attempt = data.get('attempt')
        need(attempt in state['attempts'], 'unknown-attempt')
        item = state['attempts'][attempt]
        if action == 'receipt':
            need(item['status'] in {'dispatch-intent', 'received'}, 'receipt-state')
            item['status'] = 'received'; item['receipt'] = event['id']
        elif action == 'result':
            need(item['status'] in {'dispatch-intent', 'received'} or (item['status'] == 'reconciled' and item.get('outcome') == 'performed'), 'result-state')
            result = proposals.get(data.get('message'))
            if result is not None: _envelope(result)
            need(result is not None and result.get('project') == record['project'] and result.get('kind') == 'result' and result.get('job') == record['id'], 'result-message')
            manual = result.get('data', {}).get('manual_capture') is True
            if manual:
                _accepted(result)
                need(result.get('data', {}).get('reported_session') == item['session'], 'result-issuer')
            else:
                need(result['issuer']['session'] == item['session'], 'result-issuer')
            need(result.get('epoch') == item['epoch'] and result.get('data', {}).get('attempt') == attempt, 'result-issuer')
            need(result.get('team') == record.get('team'), 'result-team')
            item.update(status='result', result=result['id']); state['results'].append(result['id'])
            if attempt in active: active.remove(attempt)
            if _native(record) and not active and not pending and state['state'] == 'pause-requested': state['state'] = 'paused'
        elif action == 'validate':
            need(item['status'] == 'result' and data.get('message') == item['result'], 'validation-result')
            need(data.get('accepted') in {True, False} and type(data.get('accepted')) is bool, 'validation-decision')
            need(isinstance(data.get('evidence'), str) and data['evidence'].strip(), 'validation-evidence')
            need(now < timestamp(state['authority']['expires']), 'authority-expired')
            item['status'] = 'validated' if data['accepted'] else 'rejected'
            item['validation'] = event['id']; state['validations'].append(event['id'])
        elif action == 'attempt_failed':
            need(item['status'] in {'dispatch-intent', 'received'}, 'failure-state')
            need(data.get('classification') in {'transient', 'capacity', 'configuration', 'authority', 'deterministic', 'transport'}, 'failure-classification')
            need(type(data.get('idempotent')) is bool, 'idempotence')
            item.update(status='failed', classification=data['classification'], idempotent=data['idempotent'], failed_at=event['at'])
            if attempt in active: active.remove(attempt)
            state.update(classification=data['classification'], idempotent=data['idempotent'])
        elif action == 'retry':
            need(item['status'] == 'failed' and item.get('classification') in {'transient', 'capacity', 'transport'} and item.get('idempotent') is True, 'unsafe-retry')
            need(not item.get('retry_authorized') and (_native(record) or state['retry_count'] < limits['retries']), 'retry-limit')
            retry_after = timestamp(data.get('after'))
            need(now <= retry_after < timestamp(limits['deadline']), 'retry-backoff')
            item.update(retry_authorized=True, retry_after=data['after']); state['retry_count'] += 1
        elif action == 'uncertain':
            need(item['status'] in {'dispatch-intent', 'received'}, 'uncertain-state')
            item['status'] = 'needs-reconciliation'; state['state'] = 'blocked'; state['classification'] = 'unknown-external-outcome'
            if _native(record):
                charge = item['charge_state']; charge['uncertain_minor'] += charge['reserved_minor']; charge['reserved_minor'] = 0
        else:
            prior_state = state['state']
            need(item['status'] == 'needs-reconciliation' and data.get('outcome') in {'not-performed', 'performed', 'failed'}, 'reconcile-state')
            need(isinstance(data.get('evidence'), str) and data['evidence'].strip(), 'reconcile-evidence')
            item.update(status='reconciled', outcome=data['outcome'], evidence=data['evidence'])
            if attempt in active: active.remove(attempt)
            if attempt in state['stop_unconfirmed']: state['stop_unconfirmed'].remove(attempt)
            if prior_state not in TERMINAL and not any(a['status'] == 'needs-reconciliation' for a in state['attempts'].values()):
                state['state'] = ('pause-requested' if active or any(a.get('route_pending') for a in state['attempts'].values()) else 'paused') if prior_state in {'paused', 'pause-requested'} else ('running' if active else 'admitted')
    elif action == 'round':
        need(state['state'] in {'admitted', 'running'} and (_native(record) or state['rounds'] < limits['rounds']), 'rounds')
        need(isinstance(data.get('progress'), str) and data['progress'].strip(), 'progress')
        state['rounds'] += 1
    elif action == 'budget_hold':
        need(_native(record) and isinstance(data.get('summary'), str) and data['summary'].strip(), 'budget-hold')
        state['checkpoint'] = dict(data); state['state'] = 'pause-requested' if active else 'paused'
    elif action == 'pause':
        need(state['state'] not in {'pause-requested', 'paused'}, 'pause-state')
        state['state'] = 'pause-requested' if active else 'paused'
    elif action == 'boundary':
        need(state['state'] in {'pause-requested', 'cancelled', 'failed', 'expired'}, 'boundary-state')
        attempt = data.get('attempt')
        need(attempt in state['attempts'] and data.get('confirmed') is True, 'boundary-confirmation')
        need(state['attempts'][attempt]['status'] != 'needs-reconciliation', 'reconciliation-required')
        state['attempts'][attempt]['status'] = 'stopped'
        if attempt in active: active.remove(attempt)
        if attempt in state['stop_unconfirmed']: state['stop_unconfirmed'].remove(attempt)
        if not active and not any(a.get('route_pending') for a in state['attempts'].values()) and state['state'] == 'pause-requested': state['state'] = 'paused'
    elif action == 'resume':
        need(state['state'] == 'paused' and not occupied, 'resume-state')
        state['state'] = 'admitted'
    elif action == 'cancel':
        state['state'] = 'cancelled'; state['stop_unconfirmed'] = sorted(occupied); state['completed_at'] = event['at']
    elif action in {'succeed', 'fail', 'expire'}:
        if action == 'succeed':
            need(not occupied and state['attempts'] and all(a['status'] in {'validated', 'stopped'} or (a['status'] == 'failed' and a.get('retry_used') is True) or (a['status'] == 'reconciled' and a.get('outcome') == 'not-performed') for a in state['attempts'].values()), 'unvalidated-output')
            need(any(a['status'] == 'validated' for a in state['attempts'].values()), 'unvalidated-output')
            need(all(isinstance(data.get(k), str) and data[k].strip() for k in ('summary', 'dissent', 'usage')), 'completion-evidence')
        if action == 'expire':
            need(now >= (timestamp(state['authority']['expires']) if _native(record) else min(timestamp(limits['deadline']), timestamp(state['authority']['expires']))), 'not-expired')
        state['state'] = {'succeed': 'succeeded', 'fail': 'failed', 'expire': 'expired'}[action]
        state['completed_at'] = event['at']; state['stop_unconfirmed'] = sorted(occupied)
        state['classification'] = data.get('classification', state['classification'])
    elif action == 'checkpoint':
        need(isinstance(data.get('summary'), str) and data['summary'].strip(), 'checkpoint-summary')
        state['checkpoint'] = dict(data)
    else:
        raise CoordinationError('unknown-action', action)


def _team_transition(state, event, record):
    action, data = event['action'], event['data']
    if action == 'start':
        need(state['state'] == 'ready' and state['leader'] is not None, 'dedicated-leader')
        state['state'] = 'running'
    elif action in {'bind_member', 'replace_leader'}:
        slot = 'leader' if action == 'replace_leader' else data.get('slot')
        need(slot in state['members'], 'member-slot')
        sid = identity(data.get('session'))
        need(sid != record['issuer']['session'] and sid != event['issuer']['session'], 'dedicated-leader')
        need(not any(m.get('session') == sid for key, m in state['members'].items() if key != slot), 'duplicate-member-session')
        if action == 'replace_leader':
            need(sid != state['leader'] and data.get('previous') == state['leader'], 'leader-predecessor')
            need(isinstance(data.get('checkpoint'), str) and data['checkpoint'].strip(), 'leader-checkpoint')
        state['members'][slot]['session'] = sid
        if slot == 'leader': state['leader'] = sid
        state['epoch'] += 1
    elif action == 'amend':
        need(data.get('inflight') in {'finish-pinned', 'cancel', 'pause'}, 'inflight-disposition')
        need(isinstance(data.get('summary'), str) and data['summary'].strip(), 'amendment')
        if 'collaboration_plan' in data:
            value = dict(record, members=list(state['members'].values()), collaboration_plan=data['collaboration_plan'],
                         collaboration_plan_sha256=data.get('collaboration_plan_sha256'))
            result = _bound_plan(value)
            state.update(collaboration_plan=copy.deepcopy(data['collaboration_plan']), collaboration_plan_sha256=result['plan_sha256'])
        # Scope/limits cannot expand through an amendment; that requires a new founding charter.
        state['epoch'] += 1; state['amendment'] = dict(data)
    elif action == 'budget_hold':
        need(_native(record) and isinstance(data.get('summary'), str) and data['summary'].strip(), 'budget-hold')
        state['checkpoint'] = dict(data); state['state'] = 'paused'
    elif action == 'pause':
        need(state['state'] in {'ready', 'running'}, 'pause-state'); state['state'] = 'paused'
    elif action == 'resume':
        need(state['state'] == 'paused', 'resume-state'); state['state'] = 'ready'
    elif action in {'cancel', 'complete', 'fail'}:
        if action == 'complete':
            need(all(isinstance(data.get(k), str) and data[k].strip() for k in ('summary', 'dissent', 'validation', 'usage')), 'completion-evidence')
        state['state'] = {'cancel': 'cancelled', 'complete': 'completed', 'fail': 'failed'}[action]
        state['completed_at'] = event['at']
    elif action == 'checkpoint':
        need(isinstance(data.get('summary'), str) and data['summary'].strip(), 'checkpoint-summary'); state['checkpoint'] = dict(data)
    else:
        raise CoordinationError('unknown-action', action)


def project_records(founding, messages, teams=None):
    """Pure causal projection. Invalid controls put the subject on hold; proposals never change state."""
    try:
        _envelope(founding); state = _initial(founding)
    except (CoordinationError, KeyError, TypeError, ValueError) as exc:
        return {'id': founding.get('id'), 'family': founding.get('family'), 'state': 'held', 'head': founding.get('id'), 'epoch': 0, 'held': True, 'holds': [getattr(exc, 'code', 'invalid-founding')], 'history': []}
    proposals = {m['id']: m for m in messages if m.get('family') == 'Messages' and 'event' not in m}
    events = []
    for message in messages:
        event = message.get('event')
        if not isinstance(event, dict) or event.get('target') != founding['id'] or event.get('family') != founding['family']:
            continue
        try:
            _envelope(message); _controlled(message)
            need(bool(message.get('proposal_only')) == bool(founding.get('proposal_only')), 'control-classification')
            if founding.get('proposal_only'):
                need(message['issuer']['session'] == founding['issuer']['session'], 'proposal-owner')
            need(message['project'] == founding['project'], 'project-mismatch')
            need(message.get('authority') == founding.get('authority'), 'authority-mismatch')
            need(message.get('kind') == {'dispatch': 'assignment', 'validate': 'validation', 'receipt': 'receipt', 'result': 'decision'}.get(event.get('action'), 'control'), 'event-kind')
            need(message.get('epoch') == event.get('epoch'), 'epoch-mismatch')
            need(message.get('job') == (founding['id'] if founding['family'] == 'Jobs' else None) and message.get('team') == (founding['id'] if founding['family'] == 'Teams' else founding.get('team')), 'event-target')
            need(event.get('action') in (JOB_ACTIONS if founding['family'] == 'Jobs' else TEAM_ACTIONS), 'unknown-action')
            need(type(event.get('epoch')) is int and event['epoch'] >= 0 and isinstance(event.get('data'), dict), 'event-shape')
            identity(event.get('predecessor')); timestamp(event.get('at'))
            events.append(dict(event, id=message['id'], issuer=message['issuer']))
        except (CoordinationError, TypeError, KeyError, ValueError) as exc:
            state['holds'].append(message.get('id', '?') + ':' + getattr(exc, 'code', 'invalid-event'))
    successors = {}
    for event in events:
        successors.setdefault(event['predecessor'], []).append(event)
    used = set()
    while state['head'] in successors:
        chain = successors[state['head']]
        if len(chain) != 1:
            state['holds'].append('fork:' + state['head']); break
        event = chain[0]
        if event['id'] in used:
            state['holds'].append('cycle:' + event['id']); break
        try:
            need(event['epoch'] == state['epoch'], 'stale-epoch')
            # Stop acknowledgments may clear uncertainty after cancellation, never reopen it.
            need(state['state'] not in TERMINAL or (_native(founding) and event['action'] in {'charge', 'route_boundary'}) or (state['state'] in {'cancelled', 'failed', 'expired'} and event['action'] in {'boundary', 'checkpoint', 'reconcile'}), 'terminal-immutable')
            if event['action'] not in {'cancel', 'pause', 'boundary', 'checkpoint', 'expire', 'reconcile', 'charge', 'budget_hold', 'route_boundary'}:
                need(timestamp(event['at']) < timestamp(state['authority']['expires']), 'authority-expired')
                # Execution cutoff does not revoke Main's still-valid authority to
                # accept retained output and close it. No dispatch or new work here.
                if event['action'] not in {'result', 'validate', 'succeed', 'complete'}:
                    need(timestamp(event['at']) < timestamp(state['limits']['deadline']), 'deadline')
            changed = copy.deepcopy(state)
            if founding['family'] == 'Jobs': _job_transition(changed, event, founding, proposals)
            else: _team_transition(changed, event, founding)
            state = changed; state['head'] = event['id']; state['history'].append(event['id']); used.add(event['id'])
        except (CoordinationError, TypeError, KeyError, ValueError) as exc:
            state['holds'].append(event['id'] + ':' + getattr(exc, 'code', 'invalid-transition')); break
    for event in events:
        if event['id'] not in used and not any(event['id'] in hold or 'fork:' in hold for hold in state['holds']):
            state['holds'].append('unreachable:' + event['id'])
    if founding['family'] == 'Jobs' and founding.get('team') and teams is not None:
        try:
            _team_context(founding, messages, teams, state)
        except (CoordinationError, TypeError, KeyError, ValueError) as exc:
            state['holds'].append(getattr(exc, 'code', 'team-context'))
    state['holds'] = sorted(set(state['holds'])); state['held'] = bool(state['holds'])
    if founding['family'] == 'Jobs':
        state['late_results'] = sorted(m['id'] for m in proposals.values() if m.get('kind') == 'result' and m.get('job') == founding['id'] and m['id'] not in state['results'])
    return state


def _team_context(founding, messages, teams, job_state):
    """Check retained charter/head/epoch/member evidence without old runtime Markers."""
    matched = [team for team in teams if team['id'] == founding['team']]
    need(len(matched) == 1, 'team-missing')
    team = matched[0]; view = project_records(team, messages)
    need(not view['held'], 'team-held')
    history = [team['id']] + view['history']
    cache = {}
    def snapshot(head):
        need(head in history, 'team-predecessor')
        if head not in cache:
            allowed = set(history[:history.index(head) + 1])
            cache[head] = project_records(team, [m for m in messages if m['id'] in allowed])
        return cache[head]
    need(_native(founding) == _native(team), 'team-budget-semantics')
    if _native(founding): need(founding['limits']['budget'] == team['limits']['budget'], 'team-budget-binding')
    admitted = snapshot(founding.get('team_head'))
    need(bool(founding.get('proposal_only')) == bool(team.get('proposal_only')), 'team-classification')
    if team.get('proposal_only'): need(founding['issuer'] == team['issuer'], 'proposal-owner')
    need(admitted['epoch'] == founding.get('team_epoch'), 'team-epoch')
    need(set(founding['actions']) <= set(team['actions']) and all(any(p == base or p.startswith(base + '/') for base in team['scope']) for p in founding['scope']), 'team-scope')
    for message in messages:
        if message['id'] not in job_state['history']: continue
        event = message['event']; data = event['data']
        if event['action'] in {'dispatch', 'result', 'validate'}:
            context = snapshot(data.get('team_head'))
            attempt = data if event['action'] == 'dispatch' else job_state['attempts'][data['attempt']]
            need(context['epoch'] == attempt.get('team_epoch'), 'team-epoch')
            need(context['members'].get(attempt['slot'], {}).get('session') == attempt['session'], 'member-binding')
            if team.get('proposal_only'):
                need(attempt.get('scope') == ['_Axis/Teams/' + team['id'] + '/members/' + attempt['slot']], 'proposal-dispatch-scope')


def allocation_module():
    spec = importlib.util.spec_from_file_location('axis_team_allocation', Path(__file__).with_name('team-allocation.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def message_paths():
    spec = importlib.util.spec_from_file_location('axis_message_paths', Path(__file__).with_name('message-paths.py'))
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


class Store:
    def __init__(self, root, session=None, clock=None):
        try:
            self.io = _START.Session(root, session) if session is not None else _START.Startup(root)
        except _START.Fault as exc:
            raise CoordinationError(exc.code, exc.path) from None
        self.root = self.io.root
        self.session = session
        self.clock = clock or (lambda: dt.datetime.now(dt.timezone.utc))
        self._last_clock = None
        self._lock = None
        self._proposal_control = None

    def _require_external(self):
        self.guard()
        need(not self.io.lease[2] and self.io.marker_body().splitlines()[0].startswith('External:'), 'external-required')
        need(self.storage_profile() == 'atomic', 'direct-storage-unavailable')
        return self.session

    def _control_guard(self):
        if self._proposal_control is None: return self.require_main()
        self._require_external()
        self._control_placement()
        if self._proposal_control.get('team'):
            self._proposal_owned(self.read('Teams', self._proposal_control['team']))
        return self.session

    def _control_placement(self):
        if self._proposal_control is None: return self.require_placement()
        self._require_external()
        placement = self._read_placement()
        return Store(self.root, placement['session']).require_placement(expected=placement['activation'])

    def _proposal_snapshot(self):
        placement = self._control_placement()
        marker = self.io.marker_body()
        return {'version': 1, 'owner': self.session, 'marker': marker, 'marker_sha256': digest(marker),
                'main': placement['session'], 'placement_activation': placement['activation']}

    def _proposal_owned(self, record):
        self._require_external(); _controlled(record)
        need(record.get('proposal_only') and record['issuer'] == {'role': 'external', 'session': self.session}, 'proposal-owner')
        need(record['proposal_control']['marker_sha256'] == digest(self.io.marker_body()), 'proposal-owner-changed')
        self.validate_authority(record['authority'])
        need(self.now() < timestamp(record['limits']['deadline']), 'proposal-expired')
        placement = self._read_placement()
        Store(self.root, placement['session']).require_placement(expected=record['proposal_control']['placement_activation'])
        return record

    @contextlib.contextmanager
    def _proposal_context(self, team=None):
        need(self._proposal_control is None, 'nested-proposal-control')
        self._require_external()
        self._proposal_control = {'team': team}
        try:
            self._control_guard()
            yield
        finally: self._proposal_control = None

    def proposal_team(self, charter):
        """Allocate a proposal-only Team; no shared project-write scope is inherited."""
        value = copy.deepcopy(charter)
        need(isinstance(value, dict) and isinstance(value.get('authority'), dict), 'proposal-charter')
        ref = value['authority'].get('ref', '')
        need(Path(ref).parent.as_posix() == '_Axis/Logs' and Path(ref).suffix == '.md', 'proposal-authority-log')
        identity(Path(ref).stem)
        need(isinstance(value.get('limits'), dict) and isinstance(value['limits'].get('budget'), dict), 'proposal-native-budget-required')
        need(value['limits']['budget'].get('accounting_owner') == self.session, 'proposal-budget-owner')
        need(isinstance(value.get('members'), list) and value['members'], 'members')
        need(all(isinstance(m, dict) and set(m) == {'slot'} for m in value['members']), 'proposal-unbound-members')
        value['scope'] = ['_Axis/Teams']  # Replaced with the newly allocated Team ID inside the atomic record callback.
        with self._proposal_context(): return self.create_team(value)

    def _proposal_member(self, sid, team, item_slot=None):
        worker = self._worker_session(sid)
        lines = worker.marker_body().splitlines()
        need(lines[:1] == ['Subagent: External proposal Team'], 'proposal-member-origin')
        for label, value in (('parent', self.session), ('proposal-team', team)):
            need([line for line in lines if line.startswith(label + ':')] == [label + ': ' + value], 'proposal-member-origin')
        if item_slot is not None:
            need([line for line in lines if line.startswith('proposal-slot:')] == ['proposal-slot: ' + item_slot], 'proposal-member-slot')
        return worker

    def proposal_member_create(self, team, slot):
        """Fresh lifecycle Marker only; this does not launch a host process."""
        workspace_token(slot)
        with self._proposal_context(team):
            view = self.project('Teams', team)
            need(not view['held'] and view['state'] in {'ready', 'running'} and slot in view['members'] and view['members'][slot].get('session') is None, 'proposal-member-bound')
            with self.locked(proposal=True):
                configured = self.io.setting('Max Concurrent Sessions')
                cap = int(configured) if isinstance(configured, str) and configured.isascii() and configured.isdigit() and 1 <= int(configured) <= 100 else 10
                live = 0
                for marker in self.path('_Axis/Agents', kind='directory').glob('*.md'):
                    identity(marker.stem)
                    checked = self.path('_Axis/Agents/' + marker.name)
                    if not checked.with_suffix('.kill').exists() and time.time() - checked.stat().st_mtime < 3600: live += 1
                need(live < cap, 'project-concurrency')
                def allocation_body(ident):
                    return ('External Team member allocation\n\nby: External Agent\nsession: ' + self.session
                            + '\nteam: ' + team + '\nslot: ' + slot + '\nrole: GENERAL\nstate: allocation-intent\n'
                            + 'Synopsis: Reserve a scoped proposal member; no host or provider has been launched.\n')
                allocation_log, _ = self.io.record('Logs', allocation_body, renew_lease=False)
                def body(sid):
                    return ('Subagent: External proposal Team\n\nparent: ' + self.session + '\nproposal-team: ' + team
                            + '\nproposal-slot: ' + slot + '\nstarted: ' + sid + '\nlog: _Axis/Logs/' + allocation_log + '.md\nreturn: External owner; Main alone accepts project integration.\n')
                sid, path = self.io.record('Agents', body, renew_lease=False)
            self.event('Teams', team, 'bind_member', {'slot': slot, 'session': sid})
            return {'session': sid, 'path': path, 'team': team, 'slot': slot, 'owner': self.session, 'allocation_log': allocation_log}

    def proposal_job(self, mandate, operation_key):
        value = copy.deepcopy(mandate); need(isinstance(value, dict), 'proposal-mandate')
        team = identity(value.get('team'))
        need(not any(k in value for k in ('schedule', 'occurrence', 'budget_amendment')), 'proposal-job-scope')
        with self._proposal_context(team):
            charter = self._proposal_owned(self.read('Teams', team))
            need(value.get('authority') == charter['authority'] or self.validate_authority(value.get('authority')) == charter['authority'], 'proposal-authority')
            return self.admit_job(value, 'external:' + self.session + ':' + operation_key)

    def proposal_event(self, family, ident, action, data=None, expected=None, epoch=None):
        need(family in {'Teams', 'Jobs'}, 'proposal-family')
        need(data is None or isinstance(data, dict), 'event-data')
        record = self._proposal_owned(self.read(family, ident))
        team = ident if family == 'Teams' else identity(record.get('team'))
        payload = copy.deepcopy(data or {})
        need(action not in {'amend', 'replace_leader', 'bind_member', 'route_boundary'}, 'proposal-control-scope')
        if action == 'dispatch':
            need('route_request_sha256' not in payload, 'proposal-native-carried-route')
            slot = workspace_token(payload.get('slot'))
            self._proposal_member(payload.get('session'), team, slot)
            expected_scope = ['_Axis/Teams/' + team + '/members/' + slot]
            need(payload.get('scope') == expected_scope, 'proposal-dispatch-scope')
        with self._proposal_context(team): return self.event(family, ident, action, payload, expected, epoch)

    def proposal_message(self, team, recipient, body, kind='question', attachments=None):
        need(kind in PROPOSALS and isinstance(body, str), 'proposal-message-kind')
        with self._proposal_context(team):
            charter = self.read('Teams', team)
            delivery = self._route(team, recipient)
            need(all(t['slot'] != 'owner' for t in delivery['recipients']), 'proposal-owner-loop')
            delivery['sender_slot'] = 'owner'
            prefix = '_Axis/Teams/' + team + '/members/'
            need(isinstance(attachments or [], list) and all(isinstance(a, dict) and str(a.get('path', '')).startswith(prefix) for a in (attachments or [])), 'proposal-attachment-scope')
            checked = self.validate_attachments(attachments or [])
            with self.locked(proposal=True):
                return self._record('Messages', {'subject': 'External Team ' + kind, 'kind': kind,
                    'recipient': recipient, 'body': body, 'team': team, 'job': None, 'epoch': self.project('Teams', team)['epoch'],
                    'expires': charter['authority']['expires'], 'correlation': team, 'authority': None,
                    'data': {}, 'delivery': delivery, 'attachments': checked})

    def proposal_inbox(self, team):
        self._proposal_owned(self.read('Teams', team))
        rows = [m for m in self.records('Messages') if m.get('team') == team
                and m.get('recipient') in {'owner', self.session}]
        return {'team': team, 'owner': self.session, 'acceptance_class': 'proposal', 'messages': rows}

    def proposal_submit(self, team, body, attachments, submission_key):
        """Durable Main-directed request; neither submission nor review accepts integration."""
        need(isinstance(body, str) and body.strip() and isinstance(submission_key, str) and submission_key.strip(), 'proposal-submission')
        with self._proposal_context(team):
            prefix = '_Axis/Teams/' + team + '/members/'
            need(isinstance(attachments, list) and all(isinstance(a, dict) and str(a.get('path', '')).startswith(prefix) and '/artifacts/' in a['path'][len(prefix):] for a in attachments), 'proposal-attachment-scope')
            checked = self.validate_attachments(attachments)
            view = self.project('Teams', team); need(not view['held'], 'team-held')
            publications = {}
            for attachment in checked:
                parts = attachment['path'][len(prefix):].split('/')
                need(len(parts) >= 4 and parts[1] == 'artifacts', 'proposal-attachment-scope')
                key = (parts[0], parts[2])
                if key not in publications:
                    publications[key] = self.artifact_check(team, key[0], key[1], _view=view)
                verified = publications[key]
                need(attachment in [verified['attachment'], *verified['manifest']['files']], 'proposal-attachment-publication')
            need(all(v['attachment'] in checked for v in publications.values()), 'proposal-manifest-required')
            value = {'team': team, 'body': body, 'attachments': checked}
            key = digest({'owner': self.session, 'team': team, 'key': submission_key})
            fingerprint = digest(value)
            with self.locked(proposal=True):
                for message in self.records('Messages'):
                    if message.get('data', {}).get('proposal_submission') == key:
                        need(message['issuer'] == {'session': self.session, 'role': 'external'} and message['data'].get('proposal_digest') == fingerprint, 'proposal-submission-conflict')
                        return {'status': 'duplicate', 'id': message['id'], 'record': message}
                charter = self.read('Teams', team)
                return self._record('Messages', {'subject': 'External Team submission for Main', 'kind': 'request', 'recipient': 'main',
                    'body': body, 'team': team, 'job': None, 'epoch': self.project('Teams', team)['epoch'],
                    'expires': charter['authority']['expires'], 'correlation': key, 'authority': None, 'attachments': checked,
                    'data': {'proposal_submission': key, 'proposal_digest': fingerprint, 'integration': 'unaccepted'}})

    def proposal_native_launch(self, team, job, slot, attempt, task, charge=None):
        """Record dispatch and return carried scope for the host's native spawn tool.

        Host invocation is explicit after this result. This is workflow enforcement,
        not an OS sandbox or a claim that a process has started or terminated.
        """
        need(isinstance(task, str) and task.strip(), 'proposal-task')
        charter = self._proposal_owned(self.read('Teams', team))
        founding = self._proposal_owned(self.read('Jobs', job))
        need(founding.get('team') == team, 'proposal-job-scope')
        member = self.project('Teams', team)['members'].get(slot, {})
        sid = member.get('session'); self._proposal_member(sid, team, slot)
        scope = '_Axis/Teams/' + team + '/members/' + slot
        data = {'attempt': attempt, 'slot': slot, 'session': sid, 'operation': 'write', 'scope': [scope]}
        if charge is not None: data['charge'] = copy.deepcopy(charge)
        nonce = secrets.token_hex(16)
        header = '<<AXIS:SUBAGENT>>\n<<AXIS:ROLE:GENERAL>>\n<<AXIS:ENVELOPE:' + nonce + ':BEGIN>>'
        footer = '<<AXIS:SUBAGENT>>\n<<AXIS:ROLE:GENERAL>>\n<<AXIS:ENVELOPE:' + nonce + ':END>>'
        spec = importlib.util.spec_from_file_location('axis_proposal_envelope', Path(__file__).with_name('envelope.py'))
        envelope = importlib.util.module_from_spec(spec); spec.loader.exec_module(envelope)
        binding = {'team': team, 'job': job, 'attempt': attempt, 'epoch': self.project('Jobs', job)['epoch']}
        expires = min(charter['authority']['expires'], founding['authority']['expires'])
        tracking = 'TRACKING: your Session ID is {assigned ID}. Append `{Current UTC timestamp} - {assigned ID} - {one-line statement}` to `_Axis/Tracking/{assigned ID}.md` - one `INTENT [{scope}] {what you will do}` line now at start, and one `DONE [{same scope}] {outcome}` line just before you return; scope names the Task IDs and paths you will touch. TIMESTAMPS: write every timestamp in UTC as `yyyy.mm.dd.hh.mm.ss.xxxZ` with real milliseconds, made by running this exact command and using what it prints: `TS=$(date -u +"%Y.%m.%d.%H.%M.%S.%3NZ"); case "$TS" in *3N*) TS=$(node -e \'console.log(new Date().toISOString().replace(/[-T:]/g,"."))\' 2>/dev/null || python3 -c \'import datetime as d;n=d.datetime.now(d.timezone.utc);print(n.strftime("%Y.%m.%d.%H.%M.%S.")+"%03dZ"%(n.microsecond//1000))\' 2>/dev/null || perl -MTime::HiRes=time -e \'my $t=time;my @g=gmtime $t;printf "%04d.%02d.%02d.%02d.%02d.%02d.%03dZ",$g[5]+1900,$g[4]+1,$g[3],$g[2],$g[1],$g[0],($t-int $t)*1000\');; esac; echo "$TS"` - never type, guess, round or reformat one. FILE CREATION: your first append may create this Tracking file if absent; never create or replace your Marker. Before any product write, append and read back INTENT; computing its timestamp alone is insufficient. With Python, `python3 _Axis/Resources/startup-state.py --root . track --session {assigned ID} --type INTENT --scope \'{scope}\' --text \'{statement}\'` performs time, append and readback in one call; use DONE on return. Substitute shell-quoted literal values, escaping embedded quotes and shell metacharacters so each scope and statement stays one argument. APPEND-ONLY: add lines at the end of the file only; never edit, reorder or delete an existing line, even your own - to correct a line, append a new line that says so. If you cannot write files or run the command, say so in your return and Main records a current-time retrospective STATUS in Main\'s own file.'.replace('{assigned ID}', sid).replace('{scope}', scope)
        if self.io.setting('Tracking') not in {'writes', 'verbose'}: tracking = ''
        elif self.io.setting('Tracking') == 'verbose': tracking += ' Plus one STATUS [{same scope}] line at each step checkpoint.'
        instructions = (envelope.VALIDATE + '\n\n'
            'You are a scoped member of an External-led proposal Team. Owner: ' + self.session + '. Session: ' + sid + '.\n'
            'Existing Marker: _Axis/Agents/' + sid + '.md; kill tombstone: _Axis/Agents/' + sid + '.kill. '
            'Never create or replace the Marker. Missing, expired or killed owner/member means stop.\n'
            'Binding: ' + canonical(binding).decode() + '. Team epoch: ' + str(self.project('Teams', team)['epoch']) + '. Slot: ' + slot + '.\n'
            'Before each operation verify own lease and live Team/Job/owner authority using CheckedTeamSession. '
            'Use write_draft and delete_draft only for ' + scope + '/work/; publish_artifact creates immutable revisions under ' + scope + '/artifacts/.\n'
            'Allowed checked tools: team_info, read_file, read_message, inbox, observe_message, send_message, read_member_file, write_draft, delete_draft, publish_artifact, track. '
            'Read all peers through read_member_file; peer and shared project files stay read-only. '
            'Use send_message for any teammate slot or team broadcast; final result goes to owner. Scoped canonical Messages and own append-only '
            '_Axis/Tracking/' + sid + '.md are explicit write exceptions. Poll inbox every ' + str(charter['collaboration']['poll_seconds']) + ' seconds while participation is valid.\n'
            'Read only task-relevant public project files explicitly granted by the spawner; never Secrets. '
            'No shared project writes, settings, indexes, role changes, provider calls, spawning, budget changes or integration. '
            'Artifact submission does not end valid discussion. External reviews proposals; only Main accepts project integration.\n'
            'Actual shared budget: ' + canonical(founding['limits']['budget']).decode() + '. '
            'Provider launches count invocations, not individual tool calls. No new phase/count budget is implied. '
            'At the actual budget/authority boundary stop and preserve evidence; never infer success, process termination, known charges or authorization from missing observations.\n'
            'This carried scope is not OS isolation; ordinary host tools are not constrained by the checked broker. '
            'Expires: ' + expires + '.\nTASK:\n' + task + '\n\n' + tracking + '\n\n' + envelope.TEARLINE)
        prompt = header + '\n\n' + instructions + '\n\n' + footer
        need(envelope.check(prompt) is None, 'proposal-envelope')
        # Retain only a redacted spawn audit; never copy the complete prompt into a Log.
        with self._proposal_context(team):
            with self.locked(proposal=True):
                def log_body(ident):
                    return ('External Team native launch prepared\n\nby: External Agent\nsession: ' + self.session
                            + '\nteam: ' + team + '\njob: ' + job + '\nmember: ' + sid
                            + '\nroute: native-host-carried-scope\nrole: GENERAL\nmodel: selected by authorized native host\n'
                            + 'task-sha256: ' + digest(task) + '\nprompt-sha256: ' + digest(prompt)
                            + '\ninput-bytes: ' + str(len(prompt.encode())) + '\nSynopsis: Prepare scoped proposal artifacts and return evidence to External owner; Main decides integration.\n')
                log_id, _ = self.io.record('Logs', log_body, renew_lease=False)
        dispatch = self.proposal_event('Jobs', job, 'dispatch', data)
        return {'status': 'dispatch-recorded-not-launched', 'dispatch': dispatch['id'], 'session': sid,
                'binding': binding, 'expires': expires, 'spawn_log': log_id,
                'workspace': scope, 'prompt': prompt,
                'route': 'native-host-carried-scope', 'isolation': 'workflow only; host sandbox governs actual filesystem access'}

    def now(self):
        value = self.clock()
        if isinstance(value, str): value = timestamp(value)
        need(isinstance(value, dt.datetime) and value.tzinfo is not None and value.utcoffset() == dt.timedelta(0), 'clock')
        if self._last_clock is not None: need(value >= self._last_clock, 'clock-rollback')
        self._last_clock = value
        return value

    def path(self, name, missing=False, kind='file'):
        relative(name)
        try:
            if not missing and name.startswith('_Axis/Messages/') and not os.path.lexists(self.root/name):
                mapped = message_paths().alias(self.root,name)
                if mapped: name = mapped
            return self.io.path(name, missing=missing, kind=kind)
        except _START.Fault as exc:
            raise CoordinationError(exc.code, exc.path) from None

    def guard(self):
        need(self.session is not None, 'session-required')
        try:
            self.io.guard()
        except _START.Fault as exc:
            raise CoordinationError(exc.code, exc.path) from None

    def storage_profile(self):
        policy = self.io.setting('Storage Policy')
        storage = (self.io.read('_Axis/Flags/host-storage', optional=True) or '').splitlines()
        cloud = (self.io.read('_Axis/Flags/host-cloud-sync', optional=True) or '').splitlines()
        return 'atomic' if policy == 'auto' and storage[:1] == ['atomic'] and cloud[:1] == ['no'] else 'serialized'

    def main_context(self):
        self.require_placement()
        return {'session': self.require_main(), 'control_epoch': self.session, 'storage': self.storage_profile()}

    def require_main(self):
        self.guard()
        need(self.io.lease[2] is True, 'main-required')
        return self.session

    @contextlib.contextmanager
    def locked(self, worker=False, *, proposal=False, team=None):
        need(not (worker and proposal), 'lock-mode')
        if proposal:
            need(self._proposal_control is not None, 'proposal-context-required')
            self._control_guard()
        elif worker:
            self.guard()
            need(not self.io.lease[2] and self.storage_profile() == 'atomic', 'direct-storage-unavailable')
        else: self.require_main()
        need(self._lock is None, 'nested-lock')
        # Main's own control file serializes shared admission; it does not exclude Teams.
        # The old global lock is a migration barrier, never silently reclaimed.
        need(not os.path.lexists(self.root/'_Axis/coordination.lock'), 'locked:legacy-writer-maintenance-required')
        need(not os.path.lexists(self.root/'_Axis/Flags/coordination-maintenance'), 'coordination-maintenance')
        if team is None and proposal: team = self._proposal_control.get('team')
        if worker: need(team is not None, 'worker-team-lock-required')
        if team is not None:
            identity(team)
            self.path('_Axis/Teams/'+team, kind='directory')
        name = '_Axis/Teams/'+team+'/control.lock' if team else '_Axis/Flags/main-control.lock'
        lock = self.path(name, missing=True, kind='directory')
        owner = canonical({'session': self.session, 'nonce': secrets.token_hex(16)}) + b'\n'
        waiting=time.monotonic()
        until = waiting + (2 if worker or proposal else 0)
        while True:
            try:
                os.mkdir(lock); break
            except FileExistsError:
                if time.monotonic() >= until: raise CoordinationError('locked', name) from None
                time.sleep(0.02)
        start = time.monotonic(); owner_path = lock / 'OWNER'
        try:
            fd = os.open(owner_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try: _START.write_fd(fd, owner)
            finally: os.close(fd)
            self._lock = (lock, owner, start, (lock.stat().st_dev, lock.stat().st_ino), 'proposal' if proposal else worker)
            self._operation_records={}
            self._record_read_count=0;self._record_read_seconds=0.0
            self._check_lock(); yield
        finally:
            self.last_lock_metrics={'scope':name,'wait_seconds':start-waiting,'hold_seconds':time.monotonic()-start,'record_scans':getattr(self,'_record_read_count',0),'record_read_seconds':getattr(self,'_record_read_seconds',0)}
            self._operation_records=None
            if self._lock is not None:
                current = self._lock; self._lock = None
                # Never remove another owner's claim, including on exceptions or expired holds.
                try:
                    info = lock.lstat()
                    if not stat.S_ISLNK(info.st_mode) and (info.st_dev, info.st_ino) == current[3] and self.io.read(name + '/OWNER') == owner.decode():
                        os.unlink(owner_path); os.rmdir(lock)
                except (OSError, _START.Fault):
                    pass

    @contextlib.contextmanager
    def control_locked(self,team=None,shared=False):
        """Main admission may guard a Team while serializing its shared decision."""
        if not shared or not team or self._proposal_control is not None:
            with self.locked(proposal=self._proposal_control is not None,team=team):yield
            return
        with self.locked():
            peer=Store(self.root,self.session,clock=self.clock)
            with peer.locked(team=team):
                self._peer_lock=peer
                try:yield
                finally:self._peer_lock=None

    def _check_lock(self):
        need(self._lock is not None, 'lock-required')
        need(hashlib.sha256(Path(__file__).read_bytes()).hexdigest()==RUNTIME_SHA256,'coordination-runtime-changed')
        lock, owner, start, ident, worker = self._lock
        if getattr(self,'_peer_lock',None) is not None:self._peer_lock._check_lock()
        need(time.monotonic() - start < 10, 'lock-expired')
        name = lock.relative_to(self.root).as_posix()
        need(not os.path.lexists(self.root/'_Axis/Flags/coordination-maintenance'), 'coordination-maintenance')
        safe = self.path(name, kind='directory'); info = safe.stat()
        need((info.st_dev, info.st_ino) == ident and self.io.read(name+'/OWNER') == owner.decode(), 'lock-owner')
        if worker == 'proposal': self._control_guard()
        elif worker:
            self.guard()
            need(not self.io.lease[2] and self.storage_profile() == 'atomic', 'direct-storage-unavailable')
        else: self.require_main()

    def _acceptance(self):
        placement = self.require_placement()
        marker = self.io.marker_body()
        return {'session': self.session, 'marker': marker, 'marker_sha256': digest(marker),
                'placement_activation': placement['activation']}

    def _physical_placement(self):
        # Recheck the complete root ancestry on every use; a Store may outlive a move.
        _START.Startup(self.root)
        flags = self.path('_Axis/Flags', kind='directory')
        return {'root': list(_START.identity(self.root.stat())),
                'flags': list(_START.identity(flags.stat()))}

    def _host_hint(self):
        """Local change detector, never proof of global identity or exclusivity."""
        path = Path(os.path.expanduser('~/.axis/instance-id'))
        try:
            current = Path(path.anchor)
            for part in path.parts[1:]:
                current /= part
                need(not current.is_symlink(), 'unsafe-instance-hint')
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try: raw = _START.read_fd(fd, str(path), 4096)
            finally: os.close(fd)
            timestamp(raw.decode().strip())
            return {'kind': 'instance', 'value': digest(raw)}
        except (OSError, UnicodeError, CoordinationError, _START.Fault):
            # Combined with physical root/file identities and a finite genuine Main
            # lease, this permits ordinary same-host CLI use without a home write.
            import getpass
            import platform
            try:
                user = getpass.getuser()
            except (OSError, KeyError):
                # Containers can run a numeric UID absent from the password database.
                user = 'uid:' + str(os.getuid())
            return {'kind': 'host', 'value': digest({'node': platform.node(),
                    'system': platform.system(), 'user': user})}

    def _read_placement(self):
        name = '_Axis/Flags/coordination-placement.json'
        path = self.path(name, missing=True)
        need(path.exists(), 'placement-inactive')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            raw = _START.read_fd(fd, name, 8192)
            after = os.fstat(fd)
            need((info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) ==
                 (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                 and len(raw) == info.st_size, 'placement-changed')
        finally: os.close(fd)
        try: value = json.loads(raw, object_pairs_hook=_unique_pairs)
        except (ValueError, UnicodeError): raise CoordinationError('placement-malformed') from None
        keys = {'schema', 'active', 'project', 'root', 'physical', 'host_hint', 'session',
                'control_epoch', 'marker_sha256', 'marker_identity', 'storage', 'issued',
                'expires', 'activation', 'file_identity', 'declaration'}
        need(isinstance(value, dict) and set(value) == keys
             and value['schema'] in {'axis.coordination-placement/v1','axis.coordination-placement/v2'}
             and type(value['active']) is bool, 'placement-malformed')
        need(isinstance(value['activation'], str) and re.fullmatch(r'[0-9a-f]{32}', value['activation']), 'placement-malformed')
        need(isinstance(value['declaration'], str) and value['declaration'] in {'first placement of newly minted project UUID',
             'single writer; previous placement inactive; serialized handoff',
             'local placement deactivated; no automatic handoff'}, 'placement-declaration')
        need(value['file_identity'] == list(_START.identity(info))
             and _START.identity(path.stat()) == _START.identity(info), 'placement-replaced')
        issued, expires = timestamp(value['issued']), timestamp(value['expires'])
        need(dt.timedelta(0) < expires - issued <= dt.timedelta(hours=24), 'placement-expiry')
        return value

    def require_placement(self, expected=None):
        """Fence each new canonical acceptance/launch against this exact local activation.

        This does not discover or lock another machine. The explicit single-writer
        declaration and serialized deactivation/handoff remain the owner's duty.
        """
        try:
            return self._require_placement(expected)
        except _START.Fault as exc:
            raise CoordinationError(exc.code, exc.path) from None

    def _require_placement(self, expected):
        self.require_main()
        value = self._read_placement()
        need(value['schema']=='axis.coordination-placement/v2','coordination-protocol-upgrade-required')
        need(value['active'], 'placement-inactive')
        need(value['project'] == self.project_id() and value['root'] == str(self.root)
             and value['physical'] == self._physical_placement()
             and value['host_hint'] == self._host_hint(), 'placement-mismatch')
        need(value['session'] == self.session and value['control_epoch'] == self.session
             and value['marker_sha256'] == digest(self.io.marker_body())
             and value['marker_identity'] == list(self.io.lease[1]), 'placement-main-changed')
        need(value['storage'] == self.storage_profile(), 'placement-context-changed')
        now = dt.datetime.now(dt.timezone.utc)
        need(timestamp(value['issued']) <= now < timestamp(value['expires']), 'placement-expired')
        need(expected is None or expected == value['activation'], 'placement-generation-changed')
        return value

    def placement_status(self):
        """Read-only inspection; stale/copied placements never acquire authority."""
        try:
            value = self._read_placement()
            if self.session is None:
                return {'status': 'unverified' if value['active'] else 'inactive', 'placement': value,
                        'reason': 'current Main verification required'}
            self.require_placement()
            return {'status': 'active', 'placement': value}
        except (CoordinationError, _START.Fault, OSError) as exc:
            return {'status': 'inactive', 'reason': getattr(exc, 'code', 'placement-io')}

    def _write_placement(self, *, active, expires, declaration):
        self.require_main()
        self._check_lock()
        name = '_Axis/Flags/coordination-placement.json'
        destination = self.path(name, missing=True)
        previous = self.io.read(name, optional=True)
        temporary_name = name + '.' + secrets.token_hex(16) + '.tmp'
        temporary = self.path(temporary_name, missing=True)
        fd = os.open(temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            now = dt.datetime.now(dt.timezone.utc)
            value = {'schema': 'axis.coordination-placement/v2', 'active': active,
                     'project': self.project_id(), 'root': str(self.root),
                     'physical': self._physical_placement(), 'host_hint': self._host_hint(),
                     'session': self.session, 'control_epoch': self.session,
                     'marker_sha256': digest(self.io.marker_body()), 'marker_identity': list(self.io.lease[1]),
                     'storage': self.storage_profile(), 'issued': stamp(now), 'expires': expires,
                     'activation': secrets.token_hex(16), 'file_identity': list(_START.identity(os.fstat(fd))),
                     'declaration': declaration}
            raw = canonical(value) + b'\n'
            _START.write_fd(fd, raw)
            os.fsync(fd)
            need(_START.read_fd(fd, name, 8192) == raw, 'placement-readback')
        finally: os.close(fd)
        try:
            self._check_lock()
            need(self.io.read(name, optional=True) == previous, 'placement-changed')
            self.path(name, missing=True)
            os.replace(temporary, destination)
            need(self._read_placement() == value, 'placement-readback')
            self._check_lock()
            return value
        finally:
            if temporary.exists(): temporary.unlink()

    def activate(self, *, single_writer=False, previous_inactive=False, expires=None):
        """Explicit serialized handoff; declarations are assertions, not remote fencing."""
        need(single_writer is True and previous_inactive is True, 'explicit-placement-declaration-required')
        with self.locked():
            now = dt.datetime.now(dt.timezone.utc)
            expires = expires or stamp(now + dt.timedelta(hours=24))
            need(now < timestamp(expires) <= now + dt.timedelta(hours=24), 'placement-expiry')
            value = self._write_placement(active=True, expires=expires,
                    declaration='single writer; previous placement inactive; serialized handoff')
            self.require_placement(expected=value['activation'])
            return {'status': 'active', 'placement': value}

    def deactivate(self):
        with self.locked():
            self.require_placement()
            value = self._write_placement(active=False,
                    expires=stamp(dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=24)),
                    declaration='local placement deactivated; no automatic handoff')
            return {'status': 'inactive', 'placement': value}

    def project_id(self):
        text = self.io.read('_Axis/PROJECT.md')
        matches = re.findall(r'^project-id: (\S+)\s*$', text, re.M)
        need(len(matches) == 1, 'project-id')
        try:
            need(str(uuid.UUID(matches[0])) == matches[0], 'project-id')
        except ValueError:
            raise CoordinationError('project-id') from None
        return matches[0]

    def initialize(self):
        """Minting a genuinely new UUID explicitly activates its first local placement.

        Existing UUIDs are never activated or reactivated by initialization.
        """
        with self.locked():
            for family in (*FAMILIES, 'Submissions'):
                path = self.path('_Axis/' + family, missing=True, kind='directory')
                if not path.exists():
                    self._check_lock(); os.mkdir(path)
            text = self.io.read('_Axis/PROJECT.md')
            matches = re.findall(r'^project-id:', text, re.M)
            if not matches:
                value = str(uuid.uuid4())
                self._replace('_Axis/PROJECT.md', text + ('' if text.endswith('\n') else '\n') + '\nproject-id: ' + value + '\n', digest(text))
                self._write_placement(active=True, expires=stamp(dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=24)), declaration='first placement of newly minted project UUID')
            return {'status': 'initialized', 'project': self.project_id(), 'families': list(FAMILIES), 'placement': self.placement_status()['status']}

    def _replace(self, name, text, expected_digest=None, limit=65536):
        self.require_main()
        need(len(text.encode()) <= limit, 'record-size')
        self._check_lock()
        destination = self.path(name, missing=True)
        old = self.io.read(name, optional=True, limit=limit)
        need((old is None and expected_digest is None) or (old is not None and digest(old) == expected_digest), 'changed', name)
        temporary_name = name + '.' + secrets.token_hex(16) + '.tmp'
        temporary = self.path(temporary_name, missing=True)
        fd = os.open(temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        try:
            _START.write_fd(fd, text.encode())
            need(_START.read_fd(fd, name, limit) == text.encode(), 'write-readback')
        finally: os.close(fd)
        try:
            self._check_lock()
            need(self.io.read(name, optional=True, limit=limit) == old, 'changed', name)
            self.path(name, missing=True)
            if old is None:
                # Exclusive creation prevents overwriting an unexpected new destination.
                fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
                try: _START.write_fd(fd, text.encode())
                finally: os.close(fd)
            else:
                os.replace(temporary, destination)
            need(self.io.read(name, limit=limit) == text, 'write-readback', name)
            if getattr(self,'_operation_records',None) is not None:self._operation_records.clear()
            self._check_lock()
        finally:
            if temporary.exists(): temporary.unlink()

    def _record(self, family, payload, worker=False):
        need(family in FAMILIES and family in _START.FAMILIES, 'family-unavailable', family)
        self.path('_Axis/' + family, kind='directory')
        self.guard()
        if not worker: self._check_lock()
        project = self.project_id()
        reserved = {'schema', 'family', 'id', 'created', 'project', 'issuer', 'acceptance', 'proposal_control', 'proposal_only'}
        need(not reserved.intersection(payload), 'reserved-fields')
        issuer = {'session': self.session, 'role': 'main' if self.io.lease[2] else 'worker'}
        acceptance = self._acceptance() if issuer['role'] == 'main' else None
        proposal = self._proposal_snapshot() if self._proposal_control else None
        if proposal is not None:
            issuer['role'] = 'external'
            need(family in {'Teams', 'Jobs', 'Messages'}, 'proposal-family')
            if family == 'Teams':
                need(self._proposal_control.get('team') is None and payload.get('acceptance_owner') == self.session, 'proposal-team-context')
                need(all(m.get('session') is None for m in payload.get('members', [])), 'proposal-unbound-members')
            elif family == 'Jobs':
                team = self._proposal_control.get('team')
                need(team is not None and payload.get('team') == team and payload.get('acceptance_owner') == self.session, 'proposal-job-scope')
                charter = self._proposal_owned(self.read('Teams', team))
                need(payload.get('authority') == charter['authority'] and not any(k in payload for k in ('schedule', 'occurrence', 'budget_amendment')), 'proposal-job-scope')
            else:
                need(payload.get('team') == self._proposal_control.get('team') and payload.get('team') is not None, 'proposal-message-scope')

        def body(value):
            result = dict(copy.deepcopy(payload), schema=SCHEMA, family=family, id=value, created=value, project=project, issuer=issuer)
            if family == 'Messages':
                result.setdefault('expires', stamp(self.now() + dt.timedelta(hours=24)))
                result.setdefault('authority', None)
                result.setdefault('attachments', [])
                if result.get('correlation') is None: result['correlation'] = value
            if acceptance is not None: result['acceptance'] = acceptance
            if proposal is not None:
                result.update(proposal_only=True, proposal_control=proposal)
                if family == 'Teams':
                    result['scope'] = ['_Axis/Teams/' + value + '/members']
                    for member in result['members']:
                        member['scope'] = ['_Axis/Teams/' + value + '/members/' + member['slot']]
                _controlled(result)
            return render_record(result)
        try:
            options = {}
            if family == 'Messages':
                options['message_directory'] = message_paths().destination(self.root, payload.get('team'))
            ident, name = self.io.record(family, body, renew_lease=False, **options)
            if getattr(self,'_operation_records',None) is not None:self._operation_records.clear()
        except _START.Fault as exc:
            raise CoordinationError(exc.code, exc.path) from None
        return {'status': 'created', 'id': ident, 'path': name, 'record': self.read(family, ident)}

    def create_record(self, family, payload):
        need(family == 'Schedules', 'use-typed-creation', family)
        with self.locked(): return self._record(family, payload)

    def replace_record(self, family, ident, payload, expected_digest):
        need(family == 'Schedules', 'immutable-record', family)
        with self.locked():
            self.require_placement()
            old = self.read(family, ident)
            need(digest(old) == expected_digest, 'changed')
            reserved = {'schema', 'family', 'id', 'created', 'project', 'issuer', 'acceptance'}
            record = {k: v for k, v in payload.items() if k not in reserved}
            record.update({k: old[k] for k in reserved})
            text = render_record(record); name = '_Axis/' + family + '/' + ident + '.md'
            self._replace(name, text, digest(self.io.read(name, limit=MAX_RECORD)), limit=MAX_RECORD)
            return {'status': 'updated', 'id': ident, 'path': name, 'record': record}

    def require_history(self):
        """Unavailable history cannot be treated as proof that work never happened."""
        archive, external = _START.archive_root(self.io)
        folder = self.path(archive, missing=True, kind='directory') if archive else external
        need(folder is not None and folder.is_dir(), 'history-unavailable')
        current = Path(folder.anchor)
        for part in folder.parts[1:]:
            current /= part
            need(not current.is_symlink() and current.is_dir(), 'unsafe-archive', current)
        # Opening and scanning fail rather than interpreting inaccessible storage as empty.
        with os.scandir(folder) as entries:
            next(entries, None)
        return folder

    def _archive_paths(self, family):
        """Only record directories: canonical families and flat legacy year folders."""
        need(family in _START.FAMILIES, 'family', family)
        try:
            archive, external = _START.archive_root(self.io)
        except (OSError, _START.Fault):
            return
        folder = self.path(archive, missing=True, kind='directory') if archive else external
        if folder is None or not folder.exists(): return
        self.require_history()
        locations = [(self.root / '_Axis' / family / 'Archive', False), (folder / family, False)]
        with os.scandir(folder) as entries:
            locations.extend((Path(entry.path), True) for entry in entries if re.fullmatch(r'[0-9]{4}', entry.name))
        for location, legacy in locations:
            if not os.path.lexists(location): continue
            info = location.lstat()
            need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), 'unsafe-archive', location)
            with os.scandir(location) as entries:
                for entry in entries:
                    if not entry.name.endswith('.md') or not _START.ID.fullmatch(entry.name[:-3]): continue
                    path = Path(entry.path)
                    info = path.lstat()
                    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unsafe-path', path)
                    # macOS cloud placeholders must be made local explicitly, not hydrated by a queue read.
                    need(not getattr(info, 'st_flags', 0) & getattr(stat, 'SF_DATALESS', 0x40000000), 'history-unavailable', path)
                    yield path, legacy

    def _archive_records(self, family, exclude=()):
        found = []
        for path, legacy in self._archive_paths(family):
            if path in exclude: continue
            try:
                record = read_record(path)
            except CoordinationError as exc:
                if exc.code == 'unsafe-path' or not legacy: raise
                with path.open('rb') as source:
                    raw = source.read(8192)
                if b'axis.coordination/' in raw: raise
                continue
            need(record['id'] == path.stem and (legacy or record['family'] == family), 'record-identity', path)
            found.append(record)
        return found

    def _message_paths(self,team=None,archived=True):
        try: yield from message_paths().paths(self.root,team=team,archived=archived)
        except ValueError as exc: raise CoordinationError(str(exc)) from None

    def records(self, family, team=None, archived=True):
        cache=getattr(self,'_operation_records',None);key=(family,team,archived)
        if cache is not None and key in cache:return copy.deepcopy(cache[key])
        started=time.monotonic()
        result=self._read_records(family,team,archived)
        if cache is not None:
            cache[key]=copy.deepcopy(result)
            self._record_read_count+=1;self._record_read_seconds+=time.monotonic()-started
        return result

    def _read_records(self, family, team=None, archived=True):
        need(family in FAMILIES, 'family', family)
        folder = self.path('_Axis/' + family, missing=True, kind='directory')
        result = []
        if folder.exists():
            candidates = self._message_paths(team,archived) if family == 'Messages' else sorted(folder.iterdir())
            for path in candidates:
                if path.name == 'Archive' and path.is_dir(): continue
                if path.name == '.gitkeep':
                    info = path.lstat()
                    need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, 'unexpected-record-file', path.name)
                    continue
                if path.is_dir() and family in {'Teams','Messages'}:
                    self.path(path.relative_to(self.root).as_posix(), kind='directory'); identity(path.name)
                    need((folder/(path.name+'.md')).is_file(), 'support-owner-missing', path.name)
                    continue
                need(path.suffix == '.md', 'unexpected-record-file', path.name)
                identity(path.stem)
                # A cooperating publisher owns its timestamp claim until the
                # exclusive record write/readback finishes. Never treat an
                # in-flight partial frame as a corrupt permanent record.
                until = time.monotonic() + 2
                while True:
                    try:
                        record = read_record(path); break
                    except CoordinationError as exc:
                        claim = self.path('_Temp/' + path.stem + '.tsclaim', missing=True, kind='directory')
                        if exc.code not in {'record-integrity', 'record-encoding'}:
                            raise
                        if not claim.exists():
                            # The publisher can finish and release its claim after
                            # our partial read but before this check. One fresh,
                            # fully validated read resolves that race. Stable
                            # corruption still raises; never loop without a claim.
                            record = read_record(path); break
                        if time.monotonic() >= until:
                            raise
                        time.sleep(0.02)
                need(record['family'] == family and record['id'] == path.stem and record['project'] == self.project_id(), 'record-identity', path)
                result.append(record)
        local_message_paths = set(self._message_paths(team,archived)) if family == 'Messages' else set()
        for record in self._archive_records(family, exclude=local_message_paths):
            if record['family'] == family and record['project'] == self.project_id():
                result.append(record)
        ids = [record['id'] for record in result]
        need(len(ids) == len(set(ids)), 'record-collision', family)
        return sorted(result, key=lambda r: r['id'])

    def read(self, family, ident):
        identity(ident); need(family in FAMILIES, 'family')
        # Inventory exact identity locations without replaying unrelated payloads.
        if family == 'Messages':
            paths = [folder/(ident+'.md') for folder in message_paths().folders(self.root)]
        else:
            paths = [self.root/'_Axis'/family/(ident+'.md'), self.root/'_Axis'/family/'Archive'/(ident+'.md')]
        paths.extend(path for path,legacy in self._archive_paths(family) if path.stem == ident)
        matches = []
        for path in dict.fromkeys(paths):
            if not os.path.lexists(path): continue
            record = read_record(path)
            if record.get('family') == family and record.get('project') == self.project_id():
                need(record['id'] == ident, 'record-identity', path); matches.append(record)
        need(len(matches) == 1, 'record-collision' if len(matches)>1 else 'record-missing', ident)
        return matches[0]

    def _authority_bytes(self, reference):
        reference = relative(reference)
        path = self.path(reference, missing=True)
        if not path.exists() and _START.ID.fullmatch(Path(reference).stem):
            family = Path(reference).parent.name
            need(Path(reference).parent.as_posix() == '_Axis/' + family and family in _START.FAMILIES, 'authority-missing', reference)
            self.require_history()
            candidates = [p for p, _ in self._archive_paths(family) if p.name == Path(reference).name]
            need(len(candidates) == 1, 'authority-missing-or-ambiguous', reference)
            path = candidates[0]
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try: return _START.read_fd(fd, reference, MAX_RECORD)
        finally: os.close(fd)

    def validate_authority(self, authority, live=True):
        need(isinstance(authority, dict), 'authority')
        value = copy.deepcopy(authority)
        expires = timestamp(value.get('expires'))
        actual = digest(self._authority_bytes(value.get('ref')))
        need(value.get('digest', actual) == actual, 'authority-changed', value.get('ref'))
        value['digest'] = actual
        if live: need(self.now() < expires, 'authority-expired')
        return value

    def _scope(self, paths):
        need(isinstance(paths, list) and paths, 'scope')
        for name in paths:
            relative(name)
            parts = name.split('/')
            for i in range(1, len(parts) + 1):
                candidate = self.root.joinpath(*parts[:i])
                if os.path.lexists(candidate):
                    info = candidate.lstat()
                    need(not stat.S_ISLNK(info.st_mode), 'unsafe-path', name)
                    if i < len(parts): need(stat.S_ISDIR(info.st_mode), 'unsafe-path', name)
                    elif stat.S_ISREG(info.st_mode): need(info.st_nlink == 1, 'unsafe-path', name)
                    else: need(stat.S_ISDIR(info.st_mode), 'unsafe-path', name)
        return paths

    def _founding(self, payload):
        value = copy.deepcopy(payload)
        need(not {'acceptance_owner', 'epoch', 'state', 'reservation_launches'}.intersection(value), 'reserved-fields')
        need(isinstance(value.get('subject'), str) and isinstance(value.get('objective'), str) and value['objective'].strip(), 'objective')
        need(isinstance(value.get('validator'), str) and value['validator'].strip(), 'validator')
        now = self.now()
        if isinstance(value.get('authority'), dict):
            value['authority'].setdefault('expires', stamp(now + dt.timedelta(hours=24)))
        value['authority'] = self.validate_authority(value.get('authority'))
        value['scope'] = self._scope(value.get('scope'))
        need(isinstance(value.get('actions'), list) and value['actions'] and set(value['actions']) <= SAFE_OPERATIONS, 'actions')
        now = self.now()
        value.setdefault('limits', {})
        need(isinstance(value['limits'], dict), 'limits')
        if 'budget' in value['limits']:
            # Authority lifetime fences work; runtime budget has its own cumulative clock.
            value['limits']['deadline'] = value['authority']['expires']
        else:
            value['limits'].setdefault('deadline', stamp(min(now + dt.timedelta(minutes=60), timestamp(value['authority']['expires']))))
        value['limits'] = _limits(value['limits'], now)
        need(timestamp(value['limits']['deadline']) <= timestamp(value['authority']['expires']), 'mandate-deadline')
        need(value.get('coordination_protocol',2)==2,'coordination-protocol')
        value['coordination_protocol']=2
        value['acceptance_owner'] = self.session
        value['reservation_launches'] = 0 if _native(value) else min(value['limits']['launches'], 1 + value['limits']['reserve_launches'])
        if _native(value): self._native_binding(value)
        return value

    def create_team(self, charter):
        with self.locked(proposal=self._proposal_control is not None):
            self._control_placement()
            charter = allocation_module().admit(self, charter)
            value = self._founding(charter)
            # Only newly admitted charters gain this contract. Historical bytes stay unchanged.
            value.setdefault('collaboration', copy.deepcopy(COLLABORATION))
            collaboration(value['collaboration'])
            members = value.get('members')
            need(isinstance(members, list) and members, 'members')
            slots = [m.get('slot') for m in members if isinstance(m, dict)]
            need(len(slots) == len(members) and len(set(slots)) == len(slots) and slots.count('leader') == 1, 'leader-slot')
            for slot in slots: workspace_token(slot)
            need(len({s.casefold() for s in slots}) == len(slots), 'member-path-alias')
            sessions = []
            for member in members:
                _attempt_token(member.get('slot'))
                if member.get('session') is not None:
                    self._worker_session(member['session']); sessions.append(member['session'])
                if 'scope' in member:
                    self._scope(member['scope'])
                    need(all(any(p == base or p.startswith(base + '/') for base in value['scope']) for p in member['scope']), 'write-scope')
            need(len(sessions) == len(set(sessions)), 'duplicate-member-session')
            for sid in sessions:self._available_team_member(sid,allocated=bool(value.get('resource_allocation')))
            need('collaboration_plan_sha256' not in value, 'reserved-plan-digest')
            plan = _bound_plan(value, verify=False)
            if plan: value['collaboration_plan_sha256'] = plan['plan_sha256']
            result = self._record('Teams', value)
            self._init_workspaces(result['id'])
            return result

    def _available_team_member(self, sid, owner=None, allocated=False):
        # Binding and Main dispatch serialize only through Main's control file.
        # Team-local dispatch can then rely on an exclusive, stable binding.
        for charter in self.records('Teams'):
            if charter['id']==owner:continue
            if not allocated and not charter.get('resource_allocation'):continue
            view=self.project('Teams',charter['id'])
            bound=any(m.get('session')==sid for m in view['members'].values())
            if not bound:continue
            if charter.get('resource_allocation'):
                need(allocation_module().settled(self,charter) is not None,'session-reserved-to-Team')
            else:
                need(not view['held'] and view['state'] in TERMINAL,'session-reserved-to-Team')
                for job in self.records('Jobs'):
                    if job.get('team')!=charter['id']:continue
                    state=self.project('Jobs',job['id'])
                    need(not state['held'] and not state['active'] and not state['stop_unconfirmed'] and
                         not any(a.get('route_pending') or a.get('route_uncertain') for a in state['attempts'].values()),'session-reserved-to-Team')
        if allocated:
            for job in self.records('Jobs'):
                if job.get('team'):continue
                state=self.project('Jobs',job['id'])
                need(not state['held'],'capacity-held')
                occupied=set(state['active'])|set(state['stop_unconfirmed'])|{a for a,v in state['attempts'].items() if v.get('route_pending') or v.get('route_uncertain')}
                need(not any(state['attempts'][a]['session']==sid for a in occupied),'session-busy')

    def _worker_session(self, sid):
        identity(sid)
        try:
            worker = _START.Session(self.root, sid); worker.guard()
        except _START.Fault as exc:
            raise CoordinationError(exc.code, exc.path) from None
        need(not worker.lease[2], 'dedicated-leader')
        return worker

    def admit_job(self, mandate, operation_key):
        need(isinstance(operation_key, str) and 0 < len(operation_key.encode()) <= 256 and '\n' not in operation_key, 'operation-key')
        with self.control_locked(team=mandate.get('team'),shared=True):
            self._control_placement()
            self.require_history()
            mandate = copy.deepcopy(mandate)
            if mandate.get('team'):
                charter = self.read('Teams', mandate['team'])
                allocation = charter.get('resource_allocation')
                if allocation and mandate.get('limits',{}).get('budget') == allocation['pool']:
                    mandate['limits']['budget'] = copy.deepcopy(charter['limits']['budget'])
            value = self._founding(mandate)
            value['operation_key'] = operation_key
            jobs = self.records('Jobs'); messages = self.records('Messages')
            for record in jobs:
                if record.get('operation_key') == operation_key:
                    compare = {k: v for k, v in record.items() if k not in {'schema', 'family', 'id', 'created', 'project', 'issuer', 'acceptance', 'acceptance_owner', 'team_epoch', 'team_head', 'proposal_only', 'proposal_control'}}
                    candidate = {k: v for k, v in value.items() if k != 'acceptance_owner'}
                    for comparison in (compare, candidate):
                        if isinstance(comparison.get('occurrence'), dict):
                            comparison['occurrence'] = {k: v for k, v in comparison['occurrence'].items() if k != 'observed'}
                    need(compare == candidate, 'admission-conflict')
                    return {'status': 'duplicate', 'id': record['id'], 'path': '_Axis/Jobs/' + record['id'] + '.md', 'record': record}
            if value.get('team'):
                team = self.project('Teams', value['team'])
                need(not team['held'] and team['state'] in {'ready', 'running'} and team['leader'], 'team-unavailable')
                charter = self.read('Teams', value['team'])
                need(set(value['actions']) <= set(charter['actions']) and all(any(p == base or p.startswith(base + '/') for base in charter['scope']) for p in value['scope']), 'team-scope')
                need(_native(value) == _native(charter), 'team-budget-semantics')
                if _native(value): need(value['limits']['budget'] == charter['limits']['budget'], 'team-budget-binding')
                for limit in (('concurrency',) if _native(value) else ('rounds', 'launches', 'concurrency')):
                    need(value['limits'][limit] <= team['limits'][limit], 'team-limit')
                need(timestamp(value['limits']['deadline']) <= timestamp(team['limits']['deadline']), 'team-limit')
                value['team_epoch'] = team['epoch']; value['team_head'] = team['head']
            if value.get('schedule'):
                identity(value['schedule'])
                for record in jobs:
                    if record.get('schedule') == value['schedule']:
                        state = project_records(record, messages)
                        need(not state['held'] and state['state'] in TERMINAL and not state['active'] and not state['stop_unconfirmed'], 'overlap')
            if value.get('team'):self._team_budget(value, jobs, messages, admission=True)
            self._reserve_admission(value, jobs, messages)
            result = self._record('Jobs', value)
            if _native(value):
                budget = self.native_budget_state(value['limits']['budget']['key'])
                if budget['reasons']:
                    state = project_records(result['record'], messages, self.records('Teams'))
                    result.update(self._persist_native_hold('Jobs', result['record'], state, messages, budget['reasons'], 'dispatch'))
            return result

    def _team_budget(self, mandate, jobs, messages, *, admission=False, action=None, data=None):
        if _native(mandate): return
        team = self.project('Teams', mandate['team'])
        need(not team['held'], 'team-held')
        spent = reserved = rounds = 0
        teams = self.records('Teams')
        for other in jobs:
            if other.get('team') != mandate['team']:continue
            view = project_records(other, messages, teams)
            need(not view['held'], 'team-held')
            spent += view['launches'];rounds += view['rounds']
            if view['state'] not in TERMINAL and (admission or other['id'] != mandate.get('id')):
                reserved += _remaining_reservation(other, view)
        if admission:
            need(spent + reserved + mandate['reservation_launches'] <= team['limits']['launches'], 'team-launch-reservation')
        elif action == 'dispatch':
            report = (data or {}).get('purpose') in {'validation', 'checkpoint', 'report'}
            need(spent + reserved + 1 + (0 if report else team['limits']['reserve_launches']) <= team['limits']['launches'], 'team-launch-limit')
        elif action == 'round':
            need(rounds < team['limits']['rounds'], 'team-round-limit')

    def _native_binding(self, mandate):
        policy = _native_policy(mandate['limits']['budget'], self.now())
        need('budget_key' not in mandate and 'budget_amendment' not in mandate, 'budget-semantics-mixed')
        matching = []
        for record in self.records('Teams') + self.records('Jobs'):
            if _native(record) and record['authority']['digest'] == mandate['authority']['digest']:
                need(allocation_module().pool_key(self,record) == allocation_module().pool_key(self,mandate), 'budget-authority-key-reuse')
            if _native(record) and record['limits']['budget'].get('key') == policy['key']:
                _controlled(record)
                if self._proposal_control: need(record.get('proposal_only') and record['acceptance_owner'] == self.session, 'proposal-budget-owner')
                need(_native_policy(record['limits']['budget']) == policy, 'budget-baseline-conflict')
                matching.append(record)
            elif not _native(record):
                need(record.get('budget_key', record['authority']['digest']) != policy['key'], 'budget-semantics-mixed')
        if not matching:
            need(policy['accounting_owner'] == self.session, 'budget-accounting-owner')
        else:
            self.native_budget_state(policy['key'])

    def native_budget_state(self, budget_key):
        """Cumulative append-only money/runtime ledger; no provider charge is inferred."""
        self.require_history()
        jobs = self.records('Jobs'); teams = self.records('Teams')
        owners = [t['id'] for t in teams if _native(t) and t['limits']['budget'].get('key') == budget_key]
        messages = self.records('Messages', team=owners[0] if len(owners)==1 else None)
        records = [r for r in teams + jobs if _native(r) and r['limits']['budget'].get('key') == budget_key]
        need(records, 'native-budget-missing')
        policy = _native_policy(records[0]['limits']['budget'])
        for record in records:
            _controlled(record)
            need(_native_policy(record['limits']['budget']) == policy, 'budget-baseline-conflict')
            self.validate_authority(record['authority'], live=False)
        ceilings = {'money_minor': policy.get('money', {}).get('ceiling_minor'), 'runtime_seconds': policy.get('runtime_seconds')}
        head = None; chain = {}; grants = {r['authority']['digest'] for r in records}
        remaining = [m for m in messages if isinstance(m.get('native_budget_extension'), dict) and m['native_budget_extension'].get('key') == budget_key]
        while remaining:
            children = [m for m in remaining if m['native_budget_extension'].get('predecessor') == head]
            need(len(children) == 1, 'budget-branch-or-gap')
            message = children[0]; _accepted(message); value = message['native_budget_extension']
            need(set(value) == {'key', 'predecessor', 'previous', 'total', 'at'}, 'native-extension-shape')
            need(message['kind'] == 'control' and message.get('event') is None and message.get('job') is None and message.get('team') is None
                 and message['recipient'] == 'budget:' + budget_key and message['correlation'] == 'budget:' + budget_key, 'native-extension-shape')
            need(value['previous'] == ceilings, 'budget-extension-previous')
            need(timestamp(value['at']) <= self.now(), 'budget-clock-rollback')
            total = self._native_extension_limits(ceilings, value['total'])
            authority = self.validate_authority(message.get('authority'), live=False)
            need(authority['digest'] not in grants and message['expires'] == authority['expires'], 'budget-extension-authority')
            self._native_approval(authority, budget_key, head, ceilings, total)
            grants.add(authority['digest']); head = message['id']; chain[head] = message
            ceilings = total; remaining.remove(message)
        totals = {'known_minor': 0, 'reserved_minor': 0, 'uncertain_minor': 0}
        attempts = unpriced = 0
        observed = timestamp(policy['clock_start'])
        for record in records:
            view = project_records(record, messages, teams)
            need(not view['held'], 'native-budget-history-held')
            for message in messages:
                if message['id'] in view['history']: observed = max(observed, timestamp(message['event']['at']))
            if record['family'] == 'Jobs':
                for item in view['attempts'].values():
                    attempts += 1; unpriced += int(item['charge_state'].get('unpriced', False))
                    for name in totals: totals[name] += item['charge_state'][name]
        need(self.now() >= observed, 'budget-clock-rollback')
        elapsed = (self.now() - timestamp(policy['clock_start'])).total_seconds()
        need(elapsed >= 0, 'budget-clock-rollback')
        base_liability = sum(totals.values())
        settled_team_cost,reserved_team_money=allocation_module().pool_totals(self,budget_key,teams)
        allocated=settled_team_cost+reserved_team_money
        totals['known_minor']+=settled_team_cost
        totals['reserved_minor']+=reserved_team_money
        liability = sum(totals.values())
        result = dict(totals, key=budget_key, policy=policy, ceilings=ceilings, head=head, extensions=chain,
                      elapsed_seconds=elapsed, attempts=attempts, unpriced_attempts=unpriced, liability_minor=liability, base_liability_minor=base_liability, allocated_minor=allocated,
                      remaining_minor=None if ceilings['money_minor'] is None else max(0, ceilings['money_minor'] - liability),
                      remaining_seconds=None if ceilings['runtime_seconds'] is None else max(0, ceilings['runtime_seconds'] - elapsed))
        if len(owners)==1:
            team=self.read('Teams',owners[0])
            if team.get('resource_allocation'):
                allocation=allocation_module().effective(self,team)
                result['ceilings']['money_minor']=allocation['money_minor']
                result['remaining_minor']=max(0,allocation['money_minor']-liability)
                result['allocation']=allocation
        result['reasons'] = self._native_reasons(result)
        if result.get('allocation',{}).get('freeze') and 'allocation-frozen' not in result['reasons']:result['reasons'].append('allocation-frozen')
        result['status'] = 'budget-held' if result['reasons'] else 'available'
        return result

    @staticmethod
    def _native_extension_limits(previous, total):
        need(isinstance(total, dict) and set(total) == {'money_minor', 'runtime_seconds'}, 'native-extension-limits')
        changed = False
        for name, old in previous.items():
            if old is None: need(total[name] is None, 'budget-extension-dimension')
            else:
                _integer(total[name], name, 0 if name == 'money_minor' else 1, 10**18 if name == 'money_minor' else 10**12)
                need(total[name] >= old, 'budget-extension-reduction')
                changed = changed or total[name] > old
        need(changed, 'budget-extension-increase')
        return copy.deepcopy(total)

    def _native_approval(self, authority, key, predecessor, previous, total):
        reference = authority['ref']
        need(Path(reference).parent.as_posix() == '_Axis/Logs' and _START.ID.fullmatch(Path(reference).stem) and reference.endswith('.md'), 'budget-authority-log')
        raw = self._authority_bytes(reference)
        need(digest(raw) == authority['digest'], 'authority-changed')
        fields = {'coordination-native-budget-key': key, 'coordination-native-budget-predecessor': predecessor or 'initial',
                  'coordination-native-budget-previous': canonical(previous).decode(), 'coordination-native-budget-total': canonical(total).decode(),
                  'coordination-native-budget-expires': authority['expires']}
        for label, value in fields.items():
            need([line for line in raw.decode('utf-8').splitlines() if line.startswith(label + ':')] == [label + ': ' + value], 'budget-approval-binding')

    def extend_native_budget(self, budget_key, predecessor, authority, *, money_minor=None, runtime_seconds=None):
        """Accept a separately approved increase without changing any Job's authority."""
        with self.locked():
            self.require_placement(); self.require_history()
            state = self.native_budget_state(budget_key)
            need(not state.get('allocation'),'use-main-team-allocation-revision')
            need(state['head'] == predecessor, 'budget-predecessor')
            total = dict(state['ceilings'])
            if money_minor is not None: total['money_minor'] = money_minor
            if runtime_seconds is not None: total['runtime_seconds'] = runtime_seconds
            self._native_extension_limits(state['ceilings'], total)
            approval = self.validate_authority(authority)
            self._native_approval(approval, budget_key, predecessor, state['ceilings'], total)
            grants = {r['authority']['digest'] for r in self.records('Teams') + self.records('Jobs') if _native(r) and r['limits']['budget']['key'] == budget_key}
            grants.update(m['authority']['digest'] for m in state['extensions'].values())
            need(approval['digest'] not in grants, 'budget-extension-authority')
            payload = {'subject': 'Cumulative budget extension: ' + budget_key[:48], 'kind': 'control', 'recipient': 'budget:' + budget_key,
                       'body': 'Main accepted the exact User extension. Prior usage, reservations, clock, work and authority remain unchanged.',
                       'team': None, 'job': None, 'correlation': 'budget:' + budget_key, 'epoch': 0, 'data': {},
                       'authority': approval, 'expires': approval['expires'],
                       'native_budget_extension': {'key': budget_key, 'predecessor': predecessor, 'previous': state['ceilings'], 'total': total, 'at': stamp(self.now())}}
            return self._record('Messages', payload)

    @staticmethod
    def _native_reasons(state, additional=0):
        reasons = ['allocation-frozen'] if state.get('allocation',{}).get('freeze') else []
        money = state['ceilings']['money_minor']; runtime = state['ceilings']['runtime_seconds']
        if money is not None:
            # A zero incremental ceiling permits explicitly included access.
            if (money > 0 and state['known_minor'] >= money) or state['liability_minor'] + additional > money:
                reasons.append('money-exhausted' if state['known_minor'] >= money else 'money-reserved')
        if runtime is not None and state['elapsed_seconds'] >= runtime: reasons.append('runtime-exhausted')
        return reasons

    def _persist_native_hold(self, family, founding, state, messages, reasons, resume_action):
        extension_required = any(r in {'money-exhausted', 'runtime-exhausted'} for r in reasons)
        if state['state'] not in {'paused', 'pause-requested'}:
            data = {'summary': ('Budget exhausted; retain work and request the required User extension once.' if extension_required else 'Budget reservation hold; retain work and reconcile charges or obtain an explicit extension.'),
                    'budget_key': founding['limits']['budget']['key'], 'reasons': reasons, 'resume_action': resume_action}
            event = {'family': family, 'target': founding['id'], 'action': 'budget_hold', 'predecessor': state['head'],
                     'epoch': state['epoch'], 'at': stamp(self.now()), 'data': data}
            payload = {'subject': 'Budget hold: ' + founding['id'], 'kind': 'control', 'recipient': founding['id'], 'body': data['summary'],
                       'team': founding['id'] if family == 'Teams' else founding.get('team'), 'job': founding['id'] if family == 'Jobs' else None,
                       'correlation': founding.get('operation_key', founding['id']), 'epoch': state['epoch'], 'data': {},
                       'authority': founding['authority'], 'expires': founding['authority']['expires'], 'event': event}
            candidate = dict(payload, schema=SCHEMA, family='Messages', id='9999.12.31.23.59.59.999Z', created='9999.12.31.23.59.59.999Z',
                             project=self.project_id(), issuer={'session': self.session, 'role': 'main'}, acceptance=self._acceptance())
            projected = project_records(founding, messages + [candidate], self.records('Teams'))
            need(not projected['held'], 'budget-hold-transition')
            result = self._record('Messages', payload); head = result['id']
        else: head = state['head']
        return {'status': 'budget-held', 'id': founding['id'], 'head': head, 'reasons': reasons, 'resume_action': resume_action,
                'budget_key': founding['limits']['budget']['key'], 'extension_required': extension_required}

    def budget_state(self, budget_key, jobs=None, messages=None):
        """Replay accepted renewals without resetting any historical launch charge."""
        need(isinstance(budget_key, str) and 0 < len(budget_key.encode()) <= 249 and '\n' not in budget_key, 'budget-key')
        jobs = self.records('Jobs') if jobs is None else jobs
        messages = self.records('Messages') if messages is None else messages
        matching = [r for r in jobs if not _native(r) and r.get('budget_key', r['authority']['digest']) == budget_key]
        original = [r for r in matching if r.get('budget_amendment') is None]
        caps = [r['limits']['aggregate_launches'] for r in original if 'aggregate_launches' in r['limits']]
        amendments = [r for r in messages if isinstance(r.get('budget_amendment'), dict) and r['budget_amendment'].get('budget_key') == budget_key]
        need(not amendments or caps, 'budget-baseline-missing')
        limit = min(caps) if caps else None
        head = None; chain = {}; used_authority = {r['authority']['digest'] for r in original}
        remaining = list(amendments)
        while remaining:
            children = [r for r in remaining if r['budget_amendment'].get('predecessor') == head]
            need(len(children) == 1, 'budget-branch-or-gap')
            record = children[0]; _accepted(record)
            value = record['budget_amendment']
            need(set(value) == {'budget_key', 'predecessor', 'previous_limit', 'aggregate_launches'}, 'budget-amendment-shape')
            need(record['kind'] == 'control' and record.get('event') is None and record.get('job') is None and record.get('team') is None and record['recipient'] == 'budget:' + budget_key and record['correlation'] == 'budget:' + budget_key, 'budget-amendment-shape')
            cap = _integer(value['aggregate_launches'], 'aggregate_launches', 1)
            need(value['previous_limit'] == limit and cap > limit, 'budget-amendment-limit')
            authority = self.validate_authority(record.get('authority'), live=False)
            need(authority['digest'] not in used_authority and record['expires'] == authority['expires'], 'budget-amendment-authority')
            self._budget_approval(authority, budget_key, head, limit, cap)
            used_authority.add(authority['digest']); head = record['id']; limit = cap
            chain[head] = record; remaining.remove(record)
        for record in matching:
            ref = record.get('budget_amendment')
            if ref is not None:
                need(ref in chain and record['authority'] == chain[ref]['authority'], 'budget-amendment-binding')
                need('aggregate_launches' in record['limits'] and record['limits']['aggregate_launches'] <= chain[ref]['budget_amendment']['aggregate_launches'], 'budget-amendment-limit')
        return {'budget_key': budget_key, 'head': head, 'aggregate_launches': limit, 'amendments': chain}

    def _budget_approval(self, authority, key, predecessor, previous, total):
        reference = authority['ref']
        need(Path(reference).parent.as_posix() == '_Axis/Logs' and _START.ID.fullmatch(Path(reference).stem) and reference.endswith('.md'), 'budget-authority-log')
        data = self._authority_bytes(reference)
        need(digest(data) == authority['digest'], 'authority-changed', reference)
        raw = data.decode('utf-8')
        fields = {'coordination-budget-key': key, 'coordination-budget-predecessor': predecessor or 'initial',
                  'coordination-budget-previous-limit': str(previous), 'coordination-budget-total-limit': str(total),
                  'coordination-budget-expires': authority['expires']}
        for label, value in fields.items():
            need([line for line in raw.splitlines() if line.startswith(label + ':')] == [label + ': ' + value], 'budget-approval-binding')

    def amend_budget(self, budget_key, predecessor, aggregate_launches, authority):
        with self.locked():
            self.require_placement(); self.require_history()
            state = self.budget_state(budget_key)
            need(state['aggregate_launches'] is not None and predecessor == state['head'], 'budget-predecessor')
            cap = _integer(aggregate_launches, 'aggregate_launches', 1)
            need(cap > state['aggregate_launches'], 'budget-amendment-limit')
            approval = self.validate_authority(authority)
            self._budget_approval(approval, budget_key, predecessor, state['aggregate_launches'], cap)
            prior = {r['authority']['digest'] for r in self.records('Jobs') if not _native(r) and r.get('budget_key', r['authority']['digest']) == budget_key}
            prior.update(r['authority']['digest'] for r in state['amendments'].values())
            need(approval['digest'] not in prior, 'budget-amendment-authority')
            payload = {'subject': 'Shared budget renewal: ' + budget_key[:50], 'kind': 'control', 'recipient': 'budget:' + budget_key,
                       'body': 'Main accepted the bound User grant. Historical launches remain charged; Job and Team limits and expiry remain unchanged.',
                       'team': None, 'job': None, 'correlation': 'budget:' + budget_key, 'epoch': 0, 'data': {},
                       'expires': approval['expires'], 'authority': approval,
                       'budget_amendment': {'budget_key': budget_key, 'predecessor': predecessor,
                                            'previous_limit': state['aggregate_launches'], 'aggregate_launches': cap}}
            return self._record('Messages', payload)

    def _budget_caps(self, mandate, jobs, messages, admission=False):
        if _native(mandate): return []
        budget = mandate.get('budget_key', mandate['authority']['digest'])
        state = self.budget_state(budget, jobs, messages)
        ref = mandate.get('budget_amendment')
        if admission and state['head'] is not None:
            need(ref == state['head'], 'budget-amendment-binding')
        if ref is not None:
            need(ref in state['amendments'] and (not admission or ref == state['head']), 'budget-amendment-binding')
            record = state['amendments'][ref]
            authority = self.validate_authority(record['authority'])
            need(mandate['authority'] == authority, 'budget-amendment-binding')
            cap = mandate['limits'].get('aggregate_launches')
            need(type(cap) is int and cap <= record['budget_amendment']['aggregate_launches'], 'budget-amendment-limit')
            return [cap] + [r['limits']['aggregate_launches'] for r in jobs
                            if not _native(r) and r.get('budget_key', r['authority']['digest']) == budget and r.get('budget_amendment') == ref]
        # Existing mandates retain their old shared cap; renewal never silently extends them.
        return [r['limits']['aggregate_launches'] for r in [mandate, *jobs]
                if not _native(r) and r.get('budget_key', r['authority']['digest']) == budget and r.get('budget_amendment') is None and 'aggregate_launches' in r['limits']]

    def _reserve_admission(self, mandate, jobs, messages):
        if _native(mandate): return
        budget = mandate.get('budget_key', mandate['authority']['digest'])
        caps = self._budget_caps(mandate, jobs, messages, admission=True)
        spent = reserved = 0
        teams = self.records('Teams')
        for record in jobs:
            if _native(record) or record.get('budget_key', record['authority']['digest']) != budget: continue
            view = project_records(record, messages, teams)
            need(not view['held'], 'budget-held')
            spent += view['launches']
            if view['state'] not in TERMINAL:
                reserved += _remaining_reservation(record, view)
        if caps:
            need(spent + reserved + mandate['reservation_launches'] <= min(caps), 'aggregate-reservation')

    def validate_attachments(self, attachments):
        need(isinstance(attachments, list) and len(attachments) <= 16, 'attachments')
        result = []
        total = 0
        for supplied in attachments:
            need(isinstance(supplied, dict), 'attachment')
            path = self.path(supplied.get('path'))
            size = path.stat().st_size
            need(size <= MAX_ATTACHMENT, 'attachment-size')
            total += size; need(total <= 4 * MAX_ATTACHMENT, 'attachments-size')
            hasher = hashlib.sha256(); fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            try:
                before = os.fstat(fd); _START.regular(before, str(path))
                count = 0
                while True:
                    chunk = os.read(fd, 1024 * 1024)
                    if not chunk: break
                    count += len(chunk); need(count <= MAX_ATTACHMENT, 'attachment-size'); hasher.update(chunk)
                after = os.fstat(fd)
                need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns) and count == size, 'attachment-changed')
            finally: os.close(fd)
            actual = {'path': supplied['path'], 'size': size, 'sha256': hasher.hexdigest()}
            need(all(supplied.get(key, value) == value for key, value in actual.items()), 'attachment-mismatch')
            result.append(actual)
        return result

    def _direct_context(self, team, job, attempt, epoch, *, writing=False):
        """Finite participation survives a submitted artifact, never a revoked mandate."""
        _attempt_token(attempt)
        need(type(epoch) is int and epoch >= 0, 'epoch')
        self.guard()
        need(not self.io.lease[2], 'worker-required')
        need(self.storage_profile() == 'atomic', 'direct-storage-unavailable')
        placement = self._read_placement()
        Store(self.root, placement['session']).require_placement(expected=placement['activation'])
        charter = self.read('Teams', identity(team))
        collaboration(charter.get('collaboration'))
        view = self.project('Teams', team)
        founding = self.read('Jobs', identity(job)); state = self.project('Jobs', job)
        need(not view['held'] and view['state'] in {'ready', 'running'}, 'team-unavailable')
        need(not state['held'] and state['state'] in {'admitted', 'running'}, 'participation-ended')
        need(founding.get('team') == team, 'worker-message-scope')
        if charter.get('proposal_only'):
            sponsor = Store(self.root, charter['acceptance_owner'], clock=self.clock)
            sponsor._require_external(); sponsor._proposal_owned(charter)
            need(founding.get('proposal_only') and founding['acceptance_owner'] == charter['acceptance_owner'], 'proposal-owner')
            need(charter['proposal_control']['placement_activation'] == placement['activation'], 'proposal-placement')
            sponsor._proposal_member(self.session, team, item_slot=None)
        else:
            need(founding['acceptance_owner'] == placement['session'] and not founding.get('proposal_only'), 'worker-message-scope')
        self.validate_authority(charter['authority']); self.validate_authority(founding['authority'])
        need(self.now() < min(timestamp(view['limits']['deadline']), timestamp(state['limits']['deadline'])), 'participation-expired')
        item = state['attempts'].get(attempt, {})
        need(item.get('session') == self.session and item.get('epoch') == epoch == state['epoch'], 'worker-message-scope')
        need(item.get('team_epoch') == view['epoch'], 'stale-epoch')
        need(item.get('status') in {'dispatch-intent', 'received', 'result', 'validated'}, 'participation-ended')
        slot = item.get('slot'); member = view['members'].get(slot, {})
        if charter.get('proposal_only'): sponsor._proposal_member(self.session, team, item_slot=slot)
        need(member.get('session') == self.session, 'member-binding')
        need('coordinate' in founding['actions'] or 'report' in founding['actions'], 'discussion-scope')
        if writing: need('write' in founding['actions'] and item.get('operation') in {'write', 'coordinate'}, 'workspace-write-scope')
        if _native(founding): need(not self.native_budget_state(founding['limits']['budget']['key'])['reasons'], 'native-budget-held')
        return charter, view, founding, state, item

    def _route(self, team, recipient):
        charter = self.read('Teams', team); view = self.project('Teams', team)
        collaboration(charter.get('collaboration'))
        need(not view['held'], 'team-unavailable')
        if recipient in {'main', 'owner', charter['acceptance_owner']}:
            need(not charter.get('proposal_only') or recipient != 'main', 'proposal-return-to-owner')
            targets = [{'slot': 'owner' if charter.get('proposal_only') else 'main', 'session': charter['acceptance_owner']}]
        else:
            need(view['state'] in {'ready', 'running'}, 'team-unavailable')
            slot = recipient[7:] if recipient.startswith('member:') else recipient
            slots = sorted(view['members']) if slot == 'team' else [slot]
            need(all(s in view['members'] for s in slots), 'worker-recipient')
            targets = [{'slot': s, 'session': view['members'][s].get('session')} for s in slots]
            need(all(t['session'] is not None for t in targets), 'recipient-unbound')
        return {'team_epoch': view['epoch'], 'recipients': targets}

    def _direct_message(self, payload):
        with self.locked(worker=True, team=payload['team']):
            charter, view, founding, state, item = self._direct_context(payload['team'], payload['job'], payload['data'].get('attempt'), payload['epoch'])
            need(payload['kind'] in PROPOSALS, 'worker-message-scope')
            expiry = min(timestamp(charter['limits']['deadline']), timestamp(founding['limits']['deadline']), timestamp(charter['authority']['expires']), timestamp(founding['authority']['expires']))
            need(self.now() < timestamp(payload['expires']) <= expiry, 'message-expiry')
            history = [m for m in self.records('Messages') if m.get('team') == payload['team']]
            observed = payload['data'].get('observed_message')
            if observed is not None:
                for prior in history:
                    if prior['issuer']['session'] == self.session and prior.get('data', {}).get('observed_message') == observed:
                        return {'status': 'duplicate', 'id': prior['id']}
            count = sum(m['issuer']['session'] == self.session for m in history)
            need(_native(charter) or count < charter['collaboration']['max_messages_per_member'], 'message-budget')
            route = self._route(payload['team'], payload['recipient'])
            route['sender_slot'] = item['slot']
            payload['delivery'] = route
            reply = payload['data'].get('reply_to')
            if reply is not None:
                original = next((m for m in history if m['id'] == identity(reply)), None)
                need(original is not None, 'reply-scope')
                need(payload['kind'] != 'receipt' or original['kind'] != 'receipt', 'no-receipt-loop')
                need(payload['correlation'] in (None, original['correlation']), 'reply-correlation')
                payload['correlation'] = original['correlation']
            root = '_Axis/Teams/' + payload['team'] + '/members/'
            need(isinstance(payload['attachments'], list), 'attachments')
            for attachment in payload['attachments']:
                need(isinstance(attachment, dict) and isinstance(attachment.get('path'), str) and attachment['path'].startswith(root), 'attachment-scope')
                parts = attachment['path'][len(root):].split('/')
                need(len(parts) >= 4 and parts[0] in view['members'] and parts[1] == 'artifacts', 'published-artifact-required')
                self.artifact_check(payload['team'], parts[0], parts[2], _view=view)
            payload['attachments'] = self.validate_attachments(payload['attachments'])
            self._check_lock()
            result = self._record('Messages', payload, worker=True)
            result['published_at'] = self.now().isoformat()
            return result

    def team_message(self, team, job, attempt, epoch, message_id):
        """Targeted full canonical read under the same Team-history access as inbox."""
        self._direct_context(team, job, attempt, epoch)
        message = self.read('Messages', identity(message_id))
        need(message.get('team') == team, 'message-team-scope')
        self.guard()
        return message

    def team_inbox(self, team, job, attempt, epoch, *, after=None, limit=20, history=False,
                   wait_for='all', reply_to=None, compact=False):
        _, view, _, _, item = self._direct_context(team, job, attempt, epoch)
        _integer(limit, 'inbox-limit', 1, 100)
        need(type(history) is bool and type(compact) is bool, 'inbox-view')
        need(isinstance(wait_for, str) and wait_for in {'all', 'answer', 'observation'}, 'inbox-wait-purpose')
        if after is not None: identity(after)
        original = None
        if reply_to is not None:
            original = self.team_message(team, job, attempt, epoch, reply_to)
            need(original.get('job') in (None, job), 'inbox-reply-assignment')
        rows = []; size = 0; more = False
        for message in self.records('Messages'):
            if message.get('team') != team or (after is not None and message['id'] <= after): continue
            delivery = message.get('delivery', {})
            addressed = {'slot': item['slot'], 'session': self.session} in delivery.get('recipients', [])
            if not history and not addressed: continue
            state = 'available'
            if delivery and delivery.get('team_epoch') != view['epoch']: state = 'stale-epoch'
            elif timestamp(message['expires']) <= self.now(): state = 'expired'
            if wait_for != 'all' or original is not None:
                if state != 'available' or message.get('job') not in (None, job): continue
                closing = message.get('data', {}).get('closing')
                release_notice = isinstance(closing, dict) and closing.get('protocol') == 'axis.closing/v1' and closing.get('action') == 'release'
                # Wake on a typed release notice; its authority must still be verified by the recipient.
                control = message['kind'] in {'control', 'decision', 'validation', 'assignment'} or 'event' in message or release_notice
                if not control:
                    if wait_for == 'answer' and message['kind'] == 'receipt': continue
                    if wait_for == 'observation' and message['kind'] != 'receipt': continue
                    if original is not None:
                        data = message.get('data', {})
                        matched = data.get('reply_to') == reply_to or data.get('observed_message') == reply_to
                        if not matched: continue
            projected = message
            if compact:
                projected = {key: message[key] for key in ('id', 'kind', 'subject', 'issuer', 'team', 'job', 'correlation', 'epoch', 'expires') if key in message}
                projected['body_preview'] = message['body'][:240]
                projected['content_omitted'] = True
                projected['attachment_count'] = len(message.get('attachments', []))
                projected['reply_to'] = message.get('data', {}).get('reply_to')
                projected['observed_message'] = message.get('data', {}).get('observed_message')
            row = {'state': state, 'message': projected}
            weight = len(canonical(row))
            if rows and (len(rows) >= limit or size + weight > MAX_RECORD): more = True; break
            rows.append(row); size += weight
        self.guard()
        result = {'messages': rows, 'next': rows[-1]['message']['id'] if rows else after,
                  'more': more, 'available_at': self.now().isoformat(), 'poll_seconds': self.read('Teams', team)['collaboration']['poll_seconds']}
        if wait_for != 'all' or reply_to is not None or compact:
            result['selection'] = {'wait_for': wait_for, 'reply_to': reply_to, 'compact': compact, 'job': job, 'history': history}
        return result

    def observe_message(self, team, job, attempt, epoch, message_id):
        _, view, _, _, item = self._direct_context(team, job, attempt, epoch)
        original = self.read('Messages', identity(message_id))
        need(original.get('team') == team and original.get('delivery', {}).get('team_epoch') == view['epoch'], 'observation-scope')
        need({'slot': item['slot'], 'session': self.session} in original['delivery']['recipients'], 'observation-recipient')
        need(original['kind'] != 'receipt', 'no-receipt-loop')
        for record in self.records('Messages'):
            if record['issuer']['session'] == self.session and record.get('data', {}).get('observed_message') == message_id:
                return {'status': 'duplicate', 'id': record['id']}
        sender = original.get('delivery', {}).get('sender_slot', 'main')
        return self.message('receipt', sender, 'Observed addressed Message.', team=team, job=job, epoch=epoch,
                            data={'attempt': attempt, 'reply_to': message_id, 'observed_message': message_id, 'observed_at': self.now().isoformat()})

    def _workspace_root(self, team, slot):
        identity(team); workspace_token(slot)
        return '_Axis/Teams/' + team + '/members/' + slot

    def _mkdirs(self, name):
        relative(name)
        current = ''
        for part in name.split('/'):
            current = current + '/' + part if current else part
            path = self.path(current, missing=True, kind='directory')
            if not path.exists(): os.mkdir(path, 0o755)
            self.path(current, kind='directory')

    def _init_workspaces(self, team):
        self._check_lock()
        charter = self.read('Teams', team); collaboration(charter.get('collaboration'))
        for member in charter['members']:
            base = self._workspace_root(team, member['slot'])
            for folder in ('work', 'artifacts'): self._mkdirs(base + '/' + folder)
        self._mkdirs('_Axis/Teams/' + team + '/shared')

    def workspace_init(self, team):
        with self.locked():
            self.require_placement(); self._init_workspaces(team)
            return {'status': 'ready', 'team': team}

    def _work_name(self, team, slot, name, area='work'):
        relative(name)
        need(all(not p.endswith(('_U', '_X')) and p.casefold() not in {'.git', '.codex', '.claude', '.gemini', '.openclaw'} for p in name.split('/')), 'protected-path')
        return self._workspace_root(team, slot) + '/' + area + '/' + name

    def _file_bytes(self, name, missing=False):
        path = self.path(name, missing=missing)
        if missing and not path.exists(): return None
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            before = os.fstat(fd)
            need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= MAX_WORK_FILE, 'workspace-file')
            raw = _START.read_fd(fd, name, MAX_WORK_FILE)
            after = os.fstat(fd)
            need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
                 (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'workspace-changed')
        finally: os.close(fd)
        self.path(name)
        return raw

    def _write_bytes(self, name, raw, expected_sha256, *, create_parents=False):
        need(isinstance(raw, bytes) and len(raw) <= MAX_WORK_FILE, 'workspace-size')
        if create_parents: self._mkdirs(str(Path(name).parent))
        before = self._file_bytes(name, missing=True)
        need((digest(before) if before is not None else None) == expected_sha256, 'workspace-changed')
        destination = self.path(name, missing=True)
        temporary = self.path(name + '.' + secrets.token_hex(16) + '.tmp', missing=True)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
        try: _START.write_fd(fd, raw); os.fsync(fd)
        finally: os.close(fd)
        try:
            self._check_lock()
            need(self._file_bytes(name, missing=True) == before, 'workspace-changed')
            self.path(name, missing=True)
            if before is None:
                os.link(temporary, destination, follow_symlinks=False); os.unlink(temporary)
            else: os.replace(temporary, destination)
            need(self._file_bytes(name) == raw, 'workspace-readback')
        finally:
            if temporary.exists(): temporary.unlink()
        return {'path': name, 'size': len(raw), 'sha256': digest(raw)}

    def workspace_write(self, team, job, attempt, epoch, path, content_base64, expected_sha256):
        with self.locked(worker=True, team=team):
            *_, item = self._direct_context(team, job, attempt, epoch, writing=True)
            name = self._work_name(team, item['slot'], path)
            try: raw = base64.b64decode(content_base64, validate=True)
            except (ValueError, TypeError): raise CoordinationError('workspace-content') from None
            return self._write_bytes(name, raw, expected_sha256, create_parents=True)

    def workspace_delete(self, team, job, attempt, epoch, path, expected_sha256):
        with self.locked(worker=True, team=team):
            *_, item = self._direct_context(team, job, attempt, epoch, writing=True)
            name = self._work_name(team, item['slot'], path)
            need(isinstance(expected_sha256, str) and digest(self._file_bytes(name)) == expected_sha256, 'workspace-changed')
            self._check_lock(); os.unlink(self.path(name))
            return {'status': 'deleted', 'path': name}

    def workspace_read(self, team, job, attempt, epoch, slot, path, revision=None):
        _, view, _, _, _ = self._direct_context(team, job, attempt, epoch)
        need(slot in view['members'], 'member-slot')
        if revision is not None:
            workspace_token(revision); self.artifact_check(team, slot, revision, _view=view)
        name = self._work_name(team, slot, path, 'work' if revision is None else 'artifacts/' + revision)
        raw = self._file_bytes(name)
        return {'path': name, 'bytes': len(raw), 'sha256': digest(raw), 'content_base64': base64.b64encode(raw).decode()}

    def artifact_publish(self, team, job, attempt, epoch, revision, paths, *, supersedes=None):
        with self.locked(worker=True, team=team):
            charter, view, founding, _, item = self._direct_context(team, job, attempt, epoch, writing=True)
            need(_native(charter) or sum(m['issuer']['session'] == self.session and m.get('team') == team for m in self.records('Messages')) < charter['collaboration']['max_messages_per_member'], 'message-budget')
            workspace_token(revision)
            # One of the Message's sixteen attachment slots pins the manifest.
            need(isinstance(paths, list) and 0 < len(paths) <= 15 and len(set(paths)) == len(paths), 'artifact-files')
            if supersedes is not None: self.artifact_check(team, item['slot'], supersedes, _view=view)
            files = {}
            for path in paths:
                need(path != '_artifact.json', 'artifact-reserved')
                files[path] = self._file_bytes(self._work_name(team, item['slot'], path))
            base = self._workspace_root(team, item['slot']) + '/artifacts/' + revision
            target = self.path(base, missing=True, kind='directory')
            need(not target.exists(), 'artifact-exists')
            os.mkdir(target)
            entries = []
            for path, raw in files.items(): entries.append(self._write_bytes(base + '/' + path, raw, None, create_parents=True))
            manifest = {'schema': 1, 'team': team, 'slot': item['slot'], 'session': self.session, 'job': job,
                        'attempt': attempt, 'epoch': epoch, 'team_epoch': view['epoch'], 'revision': revision,
                        'supersedes': supersedes, 'files': entries}
            meta = self._write_bytes(base + '/_artifact.json', canonical(manifest) + b'\n', None)
            route = self._route(team, 'team'); route['sender_slot'] = item['slot']
            publication = self._record('Messages', {'subject': 'Artifact: ' + item['slot'] + ' ' + revision,
                'kind': 'offer', 'recipient': 'team', 'body': 'Published an immutable artifact revision for peer review.',
                'team': team, 'job': job, 'epoch': epoch, 'correlation': None, 'authority': None,
                'expires': min(charter['limits']['deadline'], founding['limits']['deadline']),
                'data': {'attempt': attempt}, 'delivery': route, 'artifact_publication': meta,
                'attachments': [meta] + entries}, worker=True)
            return {'status': 'published', 'revision': revision, 'manifest': meta, 'attachments': [meta] + entries,
                    'message': publication['id'], 'published_at': self.now().isoformat()}

    def artifact_check(self, team, slot, revision, *, _view=None):
        if _view is None:
            self.require_main(); self.require_placement()
            _view = self.project('Teams', team)
            need(not _view['held'], 'team-held')
        need(slot in _view['members'], 'member-slot'); workspace_token(revision)
        base = self._workspace_root(team, slot) + '/artifacts/' + revision
        raw = self._file_bytes(base + '/_artifact.json')
        try: manifest = json.loads(raw, object_pairs_hook=_unique_pairs)
        except (ValueError, UnicodeError): raise CoordinationError('artifact-manifest') from None
        need(manifest.get('schema') == 1 and manifest.get('team') == team and manifest.get('slot') == slot and manifest.get('revision') == revision, 'artifact-manifest')
        reference = {'path': base+'/_artifact.json', 'size': len(raw), 'sha256': digest(raw)}
        publications = [m for m in self.records('Messages') if m.get('team') == team and m.get('artifact_publication', {}).get('path') == reference['path']]
        need(len(publications) == 1 and publications[0]['artifact_publication'] == reference
             and publications[0]['issuer']['session'] == manifest.get('session')
             and publications[0].get('job') == manifest.get('job'), 'artifact-publication')
        entries = manifest.get('files')
        need(isinstance(entries, list) and 0 < len(entries) <= 15, 'artifact-files')
        names = {base + '/_artifact.json'}
        for entry in entries:
            name = entry.get('path')
            need(isinstance(name, str) and name.startswith(base + '/') and name not in names, 'artifact-path')
            data = self._file_bytes(name)
            need(entry == {'path': name, 'size': len(data), 'sha256': digest(data)}, 'artifact-changed')
            names.add(name)
        actual = set()
        for directory, dirs, files in os.walk(self.path(base, kind='directory'), followlinks=False):
            for name in dirs:
                self.path(str((Path(directory)/name).relative_to(self.root)), kind='directory')
            for name in files: actual.add(str((Path(directory)/name).relative_to(self.root)))
        need(actual == names, 'artifact-membership')
        return {'status': 'verified', 'manifest': manifest, 'attachment': reference, 'publication': publications[0]['id']}

    def review_changes(self, team, proposals):
        """Read-only preflight. Main reviews and applies under ordinary project rules."""
        self.require_main(); self.require_placement()
        view = self.project('Teams', team); need(not view['held'], 'team-held')
        need(isinstance(proposals, list) and 0 < len(proposals) <= 32, 'integration-proposals')
        destinations = {}; changes = []; overlaps = set()
        for proposal in proposals:
            message = self.read('Messages', proposal['message'])
            need(message.get('team') == team and message['kind'] == 'result', 'integration-result')
            route = message.get('delivery', {})
            need(route.get('team_epoch') == view['epoch'], 'stale-epoch')
            slot = route.get('sender_slot'); revision = proposal['revision']
            artifact = self.artifact_check(team, slot, revision)
            need(message['issuer']['session'] == artifact['manifest']['session'] == view['members'][slot].get('session'), 'integration-writer')
            need(artifact['attachment'] in message['attachments'], 'integration-artifact-reference')
            self.validate_attachments(message['attachments'])
            job = self.read('Jobs', message['job'])
            state = self.project('Jobs', message['job'])
            attempt = state.get('attempts', {}).get(message.get('data', {}).get('attempt'), {})
            manifest = artifact['manifest']
            need(not state['held'] and message['job'] == manifest['job'] and message['epoch'] == manifest['epoch'] == state['epoch']
                 and message['data'].get('attempt') == manifest['attempt']
                 and manifest['team_epoch'] == view['epoch']
                 and attempt.get('session') == message['issuer']['session'] and attempt.get('slot') == slot,
                 'integration-attempt')
            need('write' in job['actions'], 'integration-scope')
            available = {entry['path']: entry for entry in artifact['manifest']['files']}
            need(isinstance(proposal['changes'], list) and 0 < len(proposal['changes']) <= 32, 'integration-changes')
            for change in proposal['changes']:
                source = self._work_name(team, slot, change['source'], 'artifacts/' + revision)
                destination = relative(change['destination'])
                need(source in available, 'integration-source')
                need(any(destination == base or destination.startswith(base+'/') for base in job['scope']), 'integration-scope')
                need(any(destination == base or destination.startswith(base+'/') for base in attempt.get('scope', [])), 'integration-scope')
                need(all(not p.endswith(('_U','_X')) and p.casefold() not in {'.git', '.codex', '.claude', '.gemini', '.openclaw'} for p in destination.split('/')), 'integration-protected')
                before = self._file_bytes(destination, missing=True)
                need((digest(before) if before is not None else None) == change['expected_sha256'], 'integration-base-changed')
                if destination in destinations: overlaps.add(destination)
                destinations[destination] = proposal['message']
                changes.append({'message': proposal['message'], 'source': source, 'destination': destination,
                                'expected_sha256': change['expected_sha256'], 'sha256': available[source]['sha256'], 'bytes': available[source]['size']})
        return {'status': 'conflict' if overlaps else 'reviewable', 'conflicts': sorted(overlaps), 'changes': changes,
                'notice': 'No project file changed. Main must review authority/content, resolve conflicts, recheck destination digests and record integration.'}

    def message(self, kind, recipient, body, *, team=None, job=None, correlation=None, epoch=0, data=None, expires=None, authority=None, attachments=None):
        need(kind in MESSAGE_KINDS and isinstance(recipient, str) and 0 < len(recipient) <= 256, 'message-kind')
        need(isinstance(body, str) and len(body.encode()) <= MAX_BODY, 'message-body')
        need(type(epoch) is int and epoch >= 0 and (data is None or isinstance(data, dict)), 'message-data')
        self.guard()
        if expires is None and team is not None and job is not None and not self.io.lease[2]:
            charter = self.read('Teams', team)
            if charter.get('collaboration'):
                expires = min(charter['limits']['deadline'], self.read('Jobs', job)['limits']['deadline'])
        expires = expires or stamp(self.now() + dt.timedelta(hours=24))
        timestamp(expires)
        need(self.io.lease[2] or authority is None, 'worker-message-authority')
        authority = self.validate_authority(authority) if authority is not None else None
        attachments = copy.deepcopy(attachments if attachments is not None else [])
        if team is not None: identity(team)
        if job is not None: identity(job)
        if correlation is not None: need(isinstance(correlation, str) and len(correlation.encode()) <= 256, 'correlation')
        subject = kind.capitalize() + ': ' + ((body.splitlines()[0].strip() if body else '') or recipient)
        if len(subject) > 80:
            # Display shortening must not manufacture a partial record identifier.
            subject = re.sub(r'\s+\S*$', '', subject[:77]).rstrip() + '...'
        payload = {'subject': subject, 'kind': kind, 'recipient': recipient, 'body': body, 'team': team, 'job': job, 'correlation': correlation, 'epoch': epoch, 'data': copy.deepcopy(data or {}), 'expires': expires, 'authority': authority, 'attachments': attachments}
        if not self.io.lease[2]:
            need(self.storage_profile() == 'atomic', 'main-mediated-capture')
            need(kind in PROPOSALS and job is not None, 'worker-message-scope')
            need(authority is None, 'worker-message-authority')
            founding = self.read('Jobs', job); state = self.project('Jobs', job)
            if founding.get('proposal_only'):
                sponsor = Store(self.root, founding['acceptance_owner'], clock=self.clock)
                sponsor._proposal_owned(founding); sponsor._proposal_member(self.session, team)
                need(recipient != 'main', 'proposal-return-to-owner')
            need(not state['held'] and team == founding.get('team'), 'worker-message-scope')
            if team is not None and self.read('Teams', team).get('collaboration'):
                # Retain late Main-directed Results under the prior capture contract,
                # without granting further discussion, workspace writes or completion.
                team_state = self.project('Teams', team)
                attempt = state['attempts'].get(payload['data'].get('attempt'), {})
                late_result = kind == 'result' and recipient in {'main', 'owner', founding['acceptance_owner']} and (
                    state['state'] not in {'admitted', 'running'} or team_state['state'] not in {'ready', 'running'}
                    or attempt.get('team_epoch') != team_state['epoch']
                    or self.now() >= min(timestamp(founding['limits']['deadline']), timestamp(team_state['limits']['deadline'])))
                if not late_result: return self._direct_message(payload)
            attempt = state['attempts'].get(payload['data'].get('attempt'), {})
            need(attempt.get('session') == self.session and attempt.get('epoch') == epoch, 'worker-message-scope')
            need(recipient in {founding['acceptance_owner'], 'main', 'leader'} or (founding.get('proposal_only') and recipient == 'owner'), 'worker-recipient')
            if team is not None:
                team_state = self.project('Teams', team)
                need(not team_state['held'] and (kind == 'result' or attempt.get('team_epoch') == team_state['epoch']), 'stale-epoch')
            need(isinstance(attachments, list), 'attachments')
            payload['attachments'] = self._result_attachments(founding, payload['data'].get('attempt'), attempt, attachments)
            # A late result is retained after cancellation/expiry; it has no control effect.
            if team is not None and self.read('Teams', team).get('collaboration'):
                with self.locked(worker=True, team=team):
                    cap = self.read('Teams', team)['collaboration']['max_messages_per_member']
                    need(_native(self.read('Teams', team)) or sum(m['issuer']['session'] == self.session and m.get('team') == team for m in self.records('Messages')) < cap, 'message-budget')
                    return self._record('Messages', payload, worker=True)
            return self._record('Messages', payload, worker=True)
        payload['attachments'] = self.validate_attachments(attachments)
        with self.locked(team=team):
            if team is not None and self.read('Teams', team).get('collaboration'):
                payload['delivery'] = self._route(team, recipient)
                payload['delivery']['sender_slot'] = 'main'
            return self._record('Messages', payload)

    def _result_attachments(self, founding, attempt_id, item, attachments):
        """Existing Job outputs or this attempt's pinned Team artifact, including late evidence."""
        need(isinstance(attachments, list), 'attachments')
        scope = item.get('scope', founding['scope']); team = founding.get('team')
        charter = self.read('Teams', team) if team is not None else {}
        for attachment in attachments:
            need(isinstance(attachment, dict) and isinstance(attachment.get('path'), str), 'attachment-scope')
            path = attachment['path']
            if any(path == base or path.startswith(base + '/') for base in scope): continue
            need(bool(charter.get('collaboration')), 'attachment-scope')
            base = self._workspace_root(team, item['slot']) + '/artifacts/'
            need(path.startswith(base) and '/' in path[len(base):], 'attachment-scope')
            view = self.project('Teams', team); need(not view['held'], 'team-held')
            artifact = self.artifact_check(team, item['slot'], path[len(base):].split('/')[0], _view=view)
            manifest = artifact['manifest']
            need(manifest['job'] == founding['id'] and manifest['attempt'] == attempt_id and manifest['session'] == item['session'], 'attachment-attempt')
        return self.validate_attachments(attachments)

    def capture_result(self, job, attempt, body, *, attachments=None):
        self.require_main()
        founding = self.read('Jobs', job); state = self.project('Jobs', job)
        item = state.get('attempts', {}).get(attempt)
        need(not state['held'] and item is not None, 'unknown-attempt')
        attachments = copy.deepcopy(attachments if attachments is not None else [])
        attachments = self._result_attachments(founding, attempt, item, attachments)
        return self.message('result', 'main', body, team=founding.get('team'), job=job,
                            correlation=founding['operation_key'], epoch=item['epoch'],
                            data={'attempt': attempt, 'manual_capture': True, 'reported_session': item['session']},
                            attachments=attachments)

    def disposition(self, message_id, outcome, reference=None):
        need(outcome in {'received', 'admitted', 'declined', 'referred', 'validated', 'rejected', 'closed'}, 'disposition')
        owner_team=self.read('Messages',message_id).get('team')
        with self.locked(team=owner_team):
            original = self.read('Messages', message_id)
            need(original['kind'] not in {'receipt', 'decision', 'validation', 'control'} and 'event' not in original, 'no-receipt-loop')
            decisions = [m for m in self.records('Messages',team=owner_team) if m.get('data', {}).get('disposition_of') == message_id]
            for decision in decisions:
                _accepted(decision)
            predecessor = message_id; previous = None; seen = set()
            while True:
                successors = [d for d in decisions if d['data'].get('predecessor') == predecessor]
                if not successors: break
                need(len(successors) == 1 and successors[0]['id'] not in seen, 'disposition-fork')
                need(previous not in {'declined', 'referred', 'validated', 'rejected', 'closed'}, 'disposition-terminal')
                decision = successors[0]; seen.add(decision['id']); predecessor = decision['id']; previous = decision['data'].get('outcome')
                need(previous in {'received', 'admitted', 'declined', 'referred', 'validated', 'rejected', 'closed'}, 'disposition')
            need(len(seen) == len(decisions), 'disposition-predecessor')
            need(previous not in {'declined', 'referred', 'validated', 'rejected', 'closed'}, 'disposition-terminal')
            if reference is not None:
                need(isinstance(reference, str) and len(reference) <= 512, 'disposition-reference')
            if outcome in {'admitted', 'referred'}: need(reference is not None, 'disposition-reference')
            payload = {'subject': 'Disposition ' + outcome + ': ' + message_id, 'kind': 'decision', 'recipient': original['issuer']['session'],
                       'body': outcome, 'team': original.get('team'), 'job': original.get('job'), 'epoch': original['epoch'],
                       'correlation': original.get('correlation'), 'data': {'disposition_of': message_id, 'outcome': outcome, 'reference': reference, 'predecessor': predecessor}}
            return self._record('Messages', payload)

    def pending_messages(self):
        messages = self.records('Messages')
        jobs = teams = None
        projections = {}
        result = []
        for message in messages:
            if message['kind'] in {'receipt', 'decision', 'validation', 'control'} or 'event' in message:
                continue
            decisions = [m for m in messages if m.get('data', {}).get('disposition_of') == message['id']]
            state = 'pending'; head = message['id']; held = False
            while True:
                successors = [m for m in decisions if m['data'].get('predecessor') == head]
                if not successors: break
                if len(successors) != 1: held = True; break
                current = successors[0]
                try:
                    _accepted(current)
                    need(current['data'].get('outcome') in {'received', 'admitted', 'declined', 'referred', 'validated', 'rejected', 'closed'}, 'disposition')
                    state = current['data']['outcome']; head = current['id']
                except CoordinationError:
                    held = True; break
            reachable = set(); cursor = message['id']
            while cursor not in reachable:
                reachable.add(cursor)
                following = [m for m in decisions if m['data'].get('predecessor') == cursor]
                if len(following) != 1: break
                cursor = following[0]['id']
            if any(m['id'] not in reachable for m in decisions): held = True
            # Main-accepted result validation resolves the underlying result proposal.
            accepted_validations = [m for m in messages if not m.get('proposal_only') and m.get('event', {}).get('action') == 'validate' and m.get('event', {}).get('data', {}).get('message') == message['id']]
            if accepted_validations and message.get('job'):
                job_id = identity(message['job'])
                if job_id not in projections:
                    if jobs is None:
                        jobs = {record['id']: record for record in self.records('Jobs')}
                        teams = self.records('Teams')
                    need(job_id in jobs, 'record-missing', job_id)
                    projections[job_id] = project_records(jobs[job_id], messages, teams)
                view = projections[job_id]
                if not view['held'] and any(m['id'] in view['validations'] for m in accepted_validations): state = 'validated'
            if held or state not in {'admitted', 'declined', 'referred', 'validated', 'rejected', 'closed'}:
                result.append({'id': message['id'], 'subject': message['subject'], 'state': 'held' if held else state, 'head': head, 'kind': message['kind']})
        return result

    def main_messages(self):
        """Classify pending communication for Main; never resolve or alter history.

        A terminal/expired mandate cannot erase an unanswered Main obligation.
        Ambiguous routing or lifecycle remains visible for reconciliation.
        """
        messages = self.records('Messages')
        records = {m['id']: m for m in messages}
        teams = {r['id']: r for r in self.records('Teams')}
        jobs = {r['id']: r for r in self.records('Jobs')}
        owners = {r['acceptance_owner'] for r in list(teams.values()) + list(jobs.values()) if not r.get('proposal_only') and isinstance(r.get('acceptance_owner'), str)}
        owners.update(m['issuer']['session'] for m in messages if m['issuer']['role'] == 'main')
        views = {}
        result = {'actionable': [], 'uncertain': [], 'other': [], 'pending_count': 0}
        for pending in self.pending_messages():
            message = records[pending['id']]
            row = dict(pending, recipient=message['recipient'], team=message.get('team'), job=message.get('job'))
            issues = []; lifecycle = []
            if pending['state'] == 'held': issues.append('disposition-held')
            for family, collection in (('team', teams), ('job', jobs)):
                ident = message.get(family)
                if ident is None: continue
                if ident not in collection:
                    issues.append(family + '-missing'); continue
                key = (family, ident)
                if key not in views: views[key] = project_records(collection[ident], messages, list(teams.values()))
                view = views[key]
                if view['held']: issues.append(family + '-held')
                lifecycle.append(family + ':' + view['state'])
            recipient = message['recipient']
            main = recipient == 'main' or recipient in owners
            if (teams.get(message.get('team')) or {}).get('proposal_only'):
                if recipient in {'owner', teams[message['team']]['acceptance_owner']}:
                    row['reason'] = 'proposal-owner-recipient'; row['classification'] = 'proposal'
                    result['other'].append(row); result['pending_count'] += 1; continue
            peer = False
            delivery = message.get('delivery')
            team = teams.get(message.get('team'))
            if delivery is not None:
                targets = delivery.get('recipients') if isinstance(delivery, dict) else None
                valid = (team is not None and isinstance(targets, list) and bool(targets)
                         and all(isinstance(t, dict) and isinstance(t.get('slot'), str)
                                 and isinstance(t.get('session'), str) for t in targets))
                if valid:
                    team_view = views.get(('team', team['id']), {})
                    valid = (type(delivery.get('team_epoch')) is int and 0 <= delivery['team_epoch'] <= team_view.get('epoch', -1)
                             and all(t['slot'] == 'main' or t['slot'] in team_view.get('members', {}) for t in targets))
                if valid:
                    slots = {t['slot'] for t in targets}
                    routed_main = 'main' in slots or any(t['session'] in owners for t in targets)
                    expected = recipient[7:] if recipient.startswith('member:') else recipient
                    valid = ((main and slots == {'main'} and routed_main and all(t['session'] == team.get('acceptance_owner') for t in targets))
                             or (not main and not routed_main and 'main' not in slots
                                 and (expected == 'team' or slots == {expected})))
                    if valid: peer = not main
                if not valid: issues.append('routing-unverified')
            elif not main and team is not None:
                slot = recipient[7:] if recipient.startswith('member:') else recipient
                view = views.get(('team', team['id']), {})
                peer = slot == 'team' or slot in view.get('members', {})
            if not main and not peer: issues.append('recipient-unclassified')
            expired = bool(message.get('expires') and self.now() >= timestamp(message['expires']))
            if expired: lifecycle.append('message:expired')
            stale = bool(team and isinstance(delivery, dict) and type(delivery.get('team_epoch')) is int
                         and delivery['team_epoch'] < views.get(('team', team['id']), {}).get('epoch', 0))
            if stale: lifecycle.append('message:prior-epoch')
            row['lifecycle'] = lifecycle or ['unscoped']
            if issues:
                row['reason'] = ','.join(sorted(set(issues))); result['uncertain'].append(row)
            elif main:
                row['reason'] = 'main-recipient'; result['actionable'].append(row)
            else:
                closed = stale or any(v.split(':', 1)[-1] in TERMINAL for v in lifecycle)
                row['reason'] = 'peer-history' if closed else 'peer-recipient'; result['other'].append(row)
            result['pending_count'] += 1
        return result

    def project(self, family, ident):
        need(family in {'Teams', 'Jobs'}, 'projection-family')
        founding = self.read(family, ident)
        team = ident if family == 'Teams' else founding.get('team')
        return project_records(founding, self.records('Messages', team=team), [self.read('Teams',team)] if family=='Jobs' and team else [])

    def event(self, family, ident, action, data=None, expected=None, epoch=None):
        need(family in {'Teams', 'Jobs'}, 'projection-family')
        need(action in (JOB_ACTIONS if family == 'Jobs' else TEAM_ACTIONS), 'unknown-action')
        need(data is None or isinstance(data, dict), 'event-data')
        owner_team = ident if family == 'Teams' else self.read(family, ident).get('team')
        shared=bool(owner_team and (not self.read('Teams',owner_team).get('resource_allocation') or family=='Teams' and action in {'replace_leader','bind_member'}))
        with self.control_locked(team=owner_team,shared=shared):
            self._control_placement()
            founding = self.read(family, ident); messages = self.records('Messages', team=owner_team)
            if owner_team:
                need(not allocation_module().settled(self,self.read('Teams',owner_team)), 'allocation-already-settled')
            if self._proposal_control is not None:
                self._proposal_owned(founding)
                owner_team = ident if family == 'Teams' else founding.get('team')
                need(self._proposal_control.get('team') == owner_team, 'proposal-owner')
                need(action not in {'amend', 'replace_leader', 'route_boundary'}, 'proposal-control-scope')
                supplied = data or {}
                if action == 'bind_member': self._proposal_member(supplied.get('session'), owner_team, supplied.get('slot'))
                if action == 'dispatch':
                    slot = workspace_token(supplied.get('slot'))
                    self._proposal_member(supplied.get('session'), owner_team, slot)
                    need('route_request_sha256' not in supplied and supplied.get('scope') == ['_Axis/Teams/' + owner_team + '/members/' + slot], 'proposal-dispatch-scope')
            state = project_records(founding, messages, self.records('Teams'))
            need(not state['held'], 'projection-held')
            if expected is not None: need(expected == state['head'], 'stale-predecessor')
            if epoch is not None: need(epoch == state['epoch'], 'stale-epoch')
            live = action not in {'cancel', 'pause', 'boundary', 'checkpoint', 'expire', 'reconcile', 'charge', 'budget_hold', 'route_boundary'}
            self.validate_authority(founding['authority'], live=live)
            payload_data = copy.deepcopy(data or {})
            if family == 'Teams' and action == 'amend' and 'collaboration_plan' in payload_data:
                need('collaboration_plan_sha256' not in payload_data, 'reserved-plan-digest')
                value = dict(founding, members=list(state['members'].values()), collaboration_plan=payload_data['collaboration_plan'])
                result = _bound_plan(value, verify=False)
                payload_data['collaboration_plan_sha256'] = result['plan_sha256']
            now = self.now()
            if state['history']:
                last = next(m for m in messages if m['id'] == state['head'])
                need(now >= timestamp(last['event']['at']), 'clock-rollback')
            if _native(founding):
                if action == 'route_boundary':
                    item = state.get('attempts', {}).get(payload_data.get('attempt'), {})
                    if item.get('route_boundary') == payload_data:
                        return {'status': 'duplicate', 'id': item['route_boundary_event']}
                if action == 'charge':
                    prior = state.get('attempts', {}).get(payload_data.get('attempt'), {}).get('charge_state', {}).get('reports', {}).get(payload_data.get('report_id'))
                    if prior is not None:
                        need(prior['data'] == payload_data, 'budget-report-conflict')
                        return {'status': 'duplicate', 'id': prior['event']}
                safe = {'cancel', 'pause', 'boundary', 'checkpoint', 'expire', 'reconcile', 'charge', 'budget_hold', 'receipt', 'result', 'attempt_failed', 'uncertain', 'route_boundary'}
                if action not in safe:
                    budget = self.native_budget_state(founding['limits']['budget']['key'])
                    additional = _native_charge(budget['policy'], payload_data.get('charge'))['reserved_minor'] if action == 'dispatch' else 0
                    reasons = self._native_reasons(budget, additional)
                    if reasons: return self._persist_native_hold(family, founding, state, messages, reasons, action)
            if family == 'Teams' and action in {'replace_leader', 'bind_member'}:
                self._worker_session(payload_data.get('session'))
                self._available_team_member(payload_data.get('session'),owner=ident,allocated=bool(founding.get('resource_allocation')))
                if founding.get('collaboration'):
                    slot = 'leader' if action == 'replace_leader' else payload_data.get('slot')
                    previous = state['members'].get(slot, {}).get('session')
                    if previous is not None and previous != payload_data.get('session'):
                        marker = self.path('_Axis/Agents/' + previous + '.md', missing=True)
                        tombstone = self.path('_Axis/Agents/' + previous + '.kill', missing=True)
                        need(not marker.exists() or tombstone.exists(), 'previous-member-unfenced')
            if family == 'Jobs' and action in {'dispatch', 'round', 'retry'}:self.require_history()
            if family == 'Jobs' and founding.get('team') and action in {'dispatch', 'round'}:
                self._team_budget(founding, self.records('Jobs'), messages, action=action, data=payload_data)
            if family == 'Jobs' and action == 'dispatch':
                self._worker_session(payload_data.get('session'))
                if not founding.get('team'):self._available_team_member(payload_data.get('session'))
                if founding.get('team'):
                    team = self.project('Teams', founding['team'])
                    need(not team['held'] and team['state'] in {'ready', 'running'}, 'team-unavailable')
                    member = team['members'].get(payload_data.get('slot'), {})
                    need(member.get('session') == payload_data.get('session'), 'member-binding')
                    team_attempts = []
                    for other in self.records('Jobs'):
                        if other.get('team') == founding['team']:
                            other_state = project_records(other, messages, self.records('Teams'))
                            need(not other_state['held'], 'team-held')
                            team_attempts.extend(other_state['attempts'][a] for a in other_state['active'])
                    need(len(team_attempts) < team['limits']['concurrency'], 'team-concurrency')
                    if payload_data.get('slot') != 'leader':
                        need(sum(a.get('slot') != 'leader' for a in team_attempts) < max(0, team['limits']['concurrency'] - 1), 'leader-slot-reserved')
                    payload_data['team_epoch'] = team['epoch']; payload_data['team_head'] = team['head']
                    if member.get('scope'):
                        paths = payload_data.get('scope', founding['scope'])
                        need(all(any(p == base or p.startswith(base + '/') for base in member['scope']) for p in paths), 'member-scope')
                self._capacity(founding, messages, payload_data)
            if family == 'Jobs' and action in {'result', 'validate'} and founding.get('team'):
                team = self.project('Teams', founding['team'])
                attempt = state['attempts'].get(payload_data.get('attempt'), {})
                need(not team['held'] and attempt.get('team_epoch') == team['epoch'], 'stale-epoch')
                payload_data['team_head'] = team['head']
            event = {'family': family, 'target': ident, 'action': action, 'predecessor': state['head'], 'epoch': state['epoch'], 'at': stamp(now), 'data': payload_data}
            payload = {'subject': family[:-1] + ' ' + action + ': ' + ident, 'kind': {'dispatch': 'assignment', 'validate': 'validation', 'receipt': 'receipt', 'result': 'decision'}.get(action, 'control'), 'recipient': ident, 'body': payload_data.get('summary', action), 'team': ident if family == 'Teams' else founding.get('team'), 'job': ident if family == 'Jobs' else None, 'correlation': founding.get('operation_key', ident), 'epoch': state['epoch'], 'data': {}, 'authority': founding['authority'], 'expires': founding['authority']['expires'], 'event': event}
            # Validate the complete transition before obtaining a globally unique immutable ID.
            candidate = dict(payload, schema=SCHEMA, family='Messages', id='9999.12.31.23.59.59.999Z', created='9999.12.31.23.59.59.999Z', project=self.project_id(), issuer={'session': self.session, 'role': 'external' if self._proposal_control else 'main'})
            if self._proposal_control: candidate.update(proposal_only=True, proposal_control=self._proposal_snapshot())
            else: candidate['acceptance'] = self._acceptance()
            projected = project_records(founding, messages + [candidate], self.records('Teams'))
            need(not projected['held'], 'transition:' + ';'.join(projected['holds']))
            return self._record('Messages', payload)

    def _capacity_view(self, founding, messages, session=None, slot=None):
        """Explain recorded occupancy and policy; no host process capacity is inferred."""
        founding_state = project_records(founding, messages, self.records('Teams'))
        if founding_state['held']:
            return {'job': founding['id'], 'status': 'held', 'blockers': ['capacity-held'],
                    'held_jobs': [founding['id']], 'occupied': None, 'holders': [],
                    'notice': 'Founding projection held; occupancy cannot be established.'}
        configured = self.io.setting('Max Concurrent Sessions')
        valid = isinstance(configured, str) and configured.isascii() and configured.isdigit() and 1 <= int(configured) <= 100
        project_cap = int(configured) if valid else 10
        policies = [{'source': 'Max Concurrent Sessions' if valid else 'default Max Concurrent Sessions',
                     'scope': 'project', 'limit': max(0, project_cap - 1), 'main_reserved': 1}]
        if 'aggregate_concurrency' in founding['limits']:
            policies.append({'source': founding['id'], 'scope': 'project', 'limit': founding['limits']['aggregate_concurrency']})
        charter=self.read('Teams',founding['team']) if founding.get('team') else None
        local_allocation=allocation_module().effective(self,charter) if charter and charter.get('resource_allocation') else None
        if local_allocation: policies = [{'source':founding['team'],'scope':'team-allocation','limit':local_allocation['slots'],'main_reserved':0}]
        holders = []; held = []; dormant = []
        teams = self.records('Teams')
        reserved_teams = {}
        if not local_allocation:
            for team in teams:
                grant = team.get('resource_allocation')
                if grant and not allocation_module().settled(self,team): reserved_teams[team['id']] = allocation_module().effective(self,team)['slots']
            for team_id,count in reserved_teams.items():
                holders.extend({'job':None,'attempt':None,'session':None,'slot':None,'team':team_id,'category':'allocated','status':'reserved-team-grant','job_state':'allocated'} for _ in range(count))
        for record in self.records('Jobs'):
            if not local_allocation and record.get('team') in reserved_teams: continue
            if local_allocation and record.get('team') != founding.get('team'): continue
            state = project_records(record, messages, teams)
            if state['held']: held.append(record['id'])
            occupied = set(state.get('active', [])) | set(state.get('stop_unconfirmed', [])) | {a for a, item in state['attempts'].items() if item.get('route_pending') is True}
            for attempt in sorted(occupied):
                item = state['attempts'][attempt]
                category = ('uncertain' if attempt in state['stop_unconfirmed'] or item['status'] == 'needs-reconciliation' or item.get('route_uncertain') is True
                            else 'reserved' if item['status'] == 'dispatch-intent' else 'active')
                holders.append({'job': record['id'], 'attempt': attempt, 'session': item['session'],
                                'slot': item['slot'], 'team': record.get('team'), 'category': category,
                                'status': item['status'], 'job_state': state['state']})
            if record['id'] != founding['id']:
                if occupied and 'aggregate_concurrency' in state['limits']:
                    policies.append({'source': record['id'], 'scope': 'project', 'limit': state['limits']['aggregate_concurrency']})
                elif not occupied and not state['held'] and state['state'] not in TERMINAL:
                    dormant.append({'job': record['id'], 'state': state['state'], 'reason': 'no-capacity-holder'})
        own = [h for h in holders if h['job'] == founding['id']]
        policies.append({'source': founding['id'], 'scope': 'job', 'limit': founding['limits']['concurrency']})
        blockers = ['capacity-held'] if held else []
        if session is not None and any(h['session'] == session for h in holders): blockers.append('session-busy')
        if any(len(holders) >= p['limit'] for p in policies if p['scope'] in {'project','team-allocation'}): blockers.append('aggregate-concurrency')
        if len(own) >= founding['limits']['concurrency']: blockers.append('concurrency')
        team_reservation = None
        if founding.get('team'):
            team = self.project('Teams', founding['team'])
            members = [h for h in holders if h['team'] == founding['team']]
            if team['held']: blockers.append('team-held')
            if len(members) >= team['limits']['concurrency']: blockers.append('team-concurrency')
            if slot is not None and slot != 'leader' and sum(h['slot'] != 'leader' for h in members) >= max(0, team['limits']['concurrency'] - 1): blockers.append('leader-slot-reserved')
            team_reservation = {'team': founding['team'], 'limit': team['limits']['concurrency'],
                                'holders': len(members), 'leader_reserved': int(not any(h['slot'] == 'leader' for h in members)),
                                'scope': 'team-only; included when occupied, never added to project holders'}
        return {'job': founding['id'], 'host_capacity': {'status': 'unverified', 'reason': 'core has no host-route capacity observation'},
                'policies': policies, 'holders': holders, 'occupied': len(holders),
                'active': sum(h['category'] == 'active' for h in holders),
                'reserved': sum(h['category'] in {'reserved','allocated'} for h in holders),
                'uncertain': sum(h['category'] == 'uncertain' for h in holders),
                'team_reservation': team_reservation, 'dormant_policies': dormant, 'held_jobs': held,
                'blockers': blockers, 'status': 'held' if blockers else 'incomplete' if team_reservation and slot is None else 'available',
                'notice': 'Recorded admission occupancy, not a live-process census or execution authority.'}

    def freeze_team_allocation(self,team,operation):
        with self.locked(team=team):
            self.require_placement()
            return allocation_module().freeze(self,team,operation)

    def revise_team_allocation(self,team,predecessor,money_minor,slots,operation,source_release=None):
        # One Main dispatcher serializes pool changes; unrelated Teams keep working.
        with self.locked():
            peer=Store(self.root,self.session,clock=self.clock)
            with peer.locked(team=team):
                self.require_placement();peer._check_lock();self._peer_lock=peer
                try:return allocation_module().revise(self,team,predecessor,money_minor,slots,operation,source_release)
                finally:self._peer_lock=None

    def settle_team_allocation(self, team, *, integrated=False):
        with self.locked(team=team):
            if self.read('Teams',team).get('resource_allocation'):result = allocation_module().settlement(self,team,integrated)
            else:result=self._message_archive_module().close_legacy(self,team,integrated)
        try: result['messages'] = self.archive_team_messages(team)
        except (ValueError,CoordinationError) as exc: result['archive_hold'] = str(exc)
        return result

    @staticmethod
    def _message_archive_module():
        spec = importlib.util.spec_from_file_location('axis_message_archive', Path(__file__).with_name('message-archive.py'))
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module);return module

    def archive_team_messages(self, team):
        identity(team);module=self._message_archive_module()
        prepared=module.prepare(self,team)
        with self.locked(team=team): result=module.archive(self,team,prepared)
        if result['status']=='archived' and prepared['tree'] is not None:
            need(module.tree(self.root/result['path'])==prepared['tree'],'archive-content-changed')
        return result

    def archive_closed_messages(self):
        self.require_main();results=[];module=self._message_archive_module()
        for team in self.records('Teams'):
            if not module.integration(self,team['id']):continue
            try:results.append(dict(team=team['id'],**self.archive_team_messages(team['id'])))
            except (CoordinationError,ValueError,OSError) as exc:results.append({'team':team['id'],'status':'held','reason':str(exc)})
        with self.locked():individual=module.individual(self)
        return {'teams':results,'individual':individual}

    def capacity_view(self, job, session=None, slot=None):
        if session is not None: identity(session)
        if slot is not None: _attempt_token(slot)
        return self._capacity_view(self.read('Jobs', identity(job)), self.records('Messages'), session, slot)

    def _capacity(self, founding, messages, dispatch):
        view = self._capacity_view(founding, messages, dispatch.get('session'), dispatch.get('slot'))
        for blocker in view['blockers']: need(False, blocker)
        launches = reserved = 0
        budget = founding.get('budget_key', founding['authority']['digest'])
        jobs = self.records('Jobs')
        launch_limits = self._budget_caps(founding, jobs, messages)
        for record in jobs:
            state = project_records(record, messages, self.records('Teams'))
            if not _native(founding) and not _native(record) and record.get('budget_key', record['authority']['digest']) == budget:
                launches += state['launches']
                if state['state'] not in TERMINAL:
                    if record['id'] != founding['id']: reserved += _remaining_reservation(record, state)
                    elif dispatch.get('purpose') not in {'validation', 'checkpoint', 'report'}: reserved += _report_reserve(record, state)
        if launch_limits: need(launches + reserved < min(launch_limits), 'aggregate-launches')

    def check(self):
        findings = []
        try:
            all_records = {family: self.records(family) for family in FAMILIES}
            ids = [r['id'] for records in all_records.values() for r in records]
            need(len(ids) == len(set(ids)), 'record-collision')
            budgets = {r.get('budget_key', r['authority']['digest']) for r in all_records['Jobs']}
            budgets.update(r['budget_amendment'].get('budget_key') for r in all_records['Messages'] if isinstance(r.get('budget_amendment'), dict))
            for budget in budgets: self.budget_state(budget, all_records['Jobs'], all_records['Messages'])
            for key in {r['limits']['budget']['key'] for r in all_records['Jobs'] + all_records['Teams'] if _native(r)}:
                self.native_budget_state(key)
            for family in ('Teams', 'Jobs'):
                for record in all_records[family]:
                    state = project_records(record, all_records['Messages'], all_records['Teams'])
                    findings.extend({'id': record['id'], 'code': hold} for hold in state['holds'])
            findings.extend({'id': message['id'], 'code': 'disposition-held'} for message in self.pending_messages() if message['state'] == 'held')
            for message in all_records['Messages']:
                if message['issuer']['role'] == 'worker' and (message['kind'] not in PROPOSALS or message.get('event') is not None):
                    findings.append({'id': message['id'], 'code': 'forged-worker-control'})
        except (CoordinationError, _START.Fault, OSError) as exc:
            findings.append({'code': getattr(exc, 'code', 'io'), 'path': getattr(exc, 'path', str(exc))})
        return {'status': 'ok' if not findings else 'held', 'findings': findings}

    def record_link(self, family, ident):
        if family == 'Messages':
            try: return quote(os.path.relpath(message_paths().resolve(self.root,ident),self.root/'_Axis').replace(os.sep,'/'),safe='/')
            except ValueError: pass
        local = self.path('_Axis/' + family + '/' + ident + '.md', missing=True)
        if local.exists():
            return family + '/' + ident + '.md'
        matches = []
        self.require_history()
        for path, _legacy in self._archive_paths(family):
            if path.stem != ident: continue
            try:
                record = read_record(path)
            except CoordinationError:
                continue
            if record['family'] == family and record['id'] == ident and record['project'] == self.project_id():
                matches.append(path)
        need(len(matches) == 1, 'index-record-location', ident)
        return quote(os.path.relpath(matches[0], self.root / '_Axis').replace(os.sep, '/'), safe='/')

    def rebuild_indexes(self):
        with self.locked():
            self.require_history()
            all_records = {family: self.records(family) for family in FAMILIES}
            result = {}
            pending = {m['id']: m for m in self.pending_messages()}
            main_view = self.main_messages()
            actionable = {m['id'] for m in main_view['actionable']}
            uncertain = {m['id'] for m in main_view['uncertain']}
            other = {m['id']: m for m in main_view['other']}
            source_digest = digest({family: [digest(r) for r in records] for family, records in all_records.items()})
            verified = stamp(self.now())
            for family, index in (('Teams', 'TEAMS'), ('Jobs', 'JOBS'), ('Messages', 'MESSAGES'), ('Schedules', 'SCHEDULES')):
                lines = ['# ' + family, '> **Purpose:** Show cached coordination state; records and accepted events are authoritative.', '', 'schema: axis.coordination-index/v1', 'verified: ' + verified, 'source-digest: ' + source_digest, 'pending-count: ' + str(len(pending) if family == 'Messages' else sum((r.get('status') not in {'retired'} if family == 'Schedules' else project_records(r, all_records['Messages'], all_records['Teams'])['state'] not in TERMINAL) for r in all_records[family])), '', '| ID | Subject | State | Head |', '| --- | --- | --- | --- |']
                rows = all_records[family]
                if family == 'Messages':
                    lines[7:7] = ['main-view: recipient-lifecycle/v1', 'main-pending-count: ' + str(len(actionable)), 'main-uncertain-count: ' + str(len(uncertain))]
                    rows = ([item for item in rows if item['id'] in actionable]
                            + [item for item in rows if item['id'] in uncertain]
                            + [item for item in rows if item['id'] in other]
                            + list(reversed([item for item in rows if item['id'] not in pending])))
                shown = 0
                byte_count = len(('\n'.join(lines)+'\n').encode())
                for record in rows:
                    if shown >= 100: break
                    if family == 'Messages':
                        state, head = (pending[record['id']]['state'], pending[record['id']]['head']) if record['id'] in pending else ('recorded', record['id'])
                        if record['id'] in actionable: state = 'main-' + state
                        elif record['id'] in uncertain: state = 'main-uncertain'
                        elif record['id'] in other: state = other[record['id']]['reason']
                    elif family == 'Schedules':
                        state, head = record.get('status', 'held'), record.get('revision') or 'incomplete'
                    else:
                        view = project_records(record, all_records['Messages'], all_records['Teams']); state = 'held' if view['held'] else view['state']; head = view['head']
                    if record.get('proposal_only') or record.get('data', {}).get('transport', {}).get('source_acceptance_class') in {'proposal', 'worker-proposal'} or (record['issuer']['role'] != 'main' and any(t.get('proposal_only') and t['id'] == record.get('team') for t in all_records['Teams'])): state = 'proposed-' + state
                    subject = record['subject'].replace('|', '\\|').replace('\n', ' ')
                    row = '| [' + record['id'] + '](' + self.record_link(family, record['id']) + ') | ' + subject + ' | ' + state + ' | ' + head + ' |'
                    size = len((row+'\n').encode())
                    if byte_count+size > 60000: break
                    lines.append(row); byte_count += size; shown += 1
                lines.extend(['', 'shown-count: ' + str(shown), 'total-count: ' + str(len(rows))])
                if shown < len(rows):
                    lines.extend(['', 'Showing ' + str(shown) + ' of ' + str(len(rows)) + ' records. Complete details remain in ' + family + '/ and the configured Archive.'])
                if family == 'Messages':
                    lines.extend(['', 'Main obligations and uncertain classifications appear first; peer pending/history remains canonical. Counts are cached hints, never authority. Recorded does not mean approved.', ''])
                text = '\n'.join(lines) + '\n'; name = '_Axis/' + index + '.md'; old = self.io.read(name, optional=True)
                self._replace(name, text, digest(old) if old is not None else None)
                result[index] = digest(text)
            return {'status': 'rebuilt', 'indexes': result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--session')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('initialize', 'identity', 'check', 'indexes', 'pending', 'main-pending', 'placement-status', 'deactivate', 'archive-closed-messages'): sub.add_parser(name)
    activation = sub.add_parser('activate')
    activation.add_argument('--single-writer', action='store_true')
    activation.add_argument('--previous-placement-inactive', action='store_true')
    activation.add_argument('--expires')
    listing = sub.add_parser('list'); listing.add_argument('family', choices=FAMILIES)
    capacity = sub.add_parser('capacity'); capacity.add_argument('job'); capacity.add_argument('--worker-session'); capacity.add_argument('--slot')
    projection = sub.add_parser('project'); projection.add_argument('family', choices=['Teams', 'Jobs']); projection.add_argument('id')
    for name in ('team', 'admit', 'message', 'event', 'disposition', 'capture-result', 'amend-budget', 'extend-native-budget', 'native-budget-state', 'team-inbox', 'team-message', 'observe-message', 'workspace-init', 'workspace-read', 'workspace-write', 'workspace-delete', 'artifact-publish', 'artifact-check', 'review-changes', 'freeze-team-allocation', 'revise-team-allocation', 'settle-team-allocation', 'archive-team-messages'):
        command = sub.add_parser(name); command.add_argument('--input', default='-')
    args = parser.parse_args(argv)
    try:
        store = Store(args.root, args.session)
        if args.command == 'initialize': result = store.initialize()
        elif args.command == 'activate': result = store.activate(single_writer=args.single_writer, previous_inactive=args.previous_placement_inactive, expires=args.expires)
        elif args.command == 'deactivate': result = store.deactivate()
        elif args.command == 'placement-status': result = store.placement_status()
        elif args.command == 'archive-closed-messages':result=store.archive_closed_messages()
        elif args.command == 'identity': result = {'project': store.project_id()}
        elif args.command == 'check': result = store.check()
        elif args.command == 'indexes': result = store.rebuild_indexes()
        elif args.command == 'pending': result = store.pending_messages()
        elif args.command == 'main-pending': result = store.main_messages()
        elif args.command == 'capacity': result = store.capacity_view(args.job, args.worker_session, args.slot)
        elif args.command == 'list': result = store.records(args.family)
        elif args.command == 'project': result = store.project(args.family, args.id)
        else:
            raw = sys.stdin.read(MAX_RECORD + 1) if args.input == '-' else store.path(args.input).read_text()
            need(len(raw.encode()) <= MAX_RECORD, 'input-size')
            value = json.loads(raw, object_pairs_hook=_unique_pairs)
            need(isinstance(value, dict), 'input-object')
            need(not any(key.startswith('_') for key in value), 'private-argument')
            if args.command in {'team-inbox', 'team-message', 'observe-message', 'workspace-init', 'workspace-read', 'workspace-write', 'workspace-delete', 'artifact-publish', 'artifact-check', 'review-changes', 'freeze-team-allocation', 'revise-team-allocation', 'settle-team-allocation', 'archive-team-messages'}:
                result = getattr(store, args.command.replace('-', '_'))(**value)
            elif args.command == 'amend-budget': result = store.amend_budget(**value)
            elif args.command == 'extend-native-budget': result = store.extend_native_budget(**value)
            elif args.command == 'native-budget-state': result = store.native_budget_state(**value)
            elif args.command == 'team': result = store.create_team(value)
            elif args.command == 'admit': result = store.admit_job(value['mandate'], value['operation_key'])
            elif args.command == 'message': result = store.message(**value)
            elif args.command == 'disposition': result = store.disposition(**value)
            elif args.command == 'capture-result': result = store.capture_result(**value)
            else: result = store.event(**value)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        if isinstance(result, dict) and result.get('status') == 'budget-held': return 3
        return 1 if isinstance(result, dict) and result.get('status') == 'held' else 0
    except (CoordinationError, _START.Fault, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'error', 'code': getattr(exc, 'code', 'input-or-io'), 'path': getattr(exc, 'path', '')}, sort_keys=True))
        return 1


if __name__ == '__main__':
    sys.exit(main())
