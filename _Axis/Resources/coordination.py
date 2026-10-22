#!/usr/bin/env python3
"""Portable coordination records and bounded, Main-owned orchestration. Standard library only.

No provider is called here. Issuer/lease snapshots and hashes are provenance, not authentication;
this protocol assumes the existing single writer and ordinary project-file integrity. Indexes are
rebuildable views. Control decisions are immutable Messages with an explicit causal predecessor.
"""
from __future__ import annotations
import argparse
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
FAMILIES = ('Teams', 'Messages', 'Jobs', 'Schedules')
MESSAGE_KINDS = {'request', 'offer', 'assignment', 'question', 'answer', 'receipt', 'result', 'validation', 'decision', 'control', 'transfer'}
PROPOSALS = {'offer', 'question', 'answer', 'receipt', 'result'}
TERMINAL = {'succeeded', 'completed', 'failed', 'cancelled', 'expired'}
JOB_ACTIONS = {'dispatch', 'receipt', 'result', 'validate', 'attempt_failed', 'retry', 'uncertain', 'reconcile', 'round', 'pause', 'boundary', 'resume', 'cancel', 'checkpoint', 'succeed', 'fail', 'expire'}
TEAM_ACTIONS = {'start', 'bind_member', 'replace_leader', 'amend', 'pause', 'resume', 'cancel', 'complete', 'fail', 'checkpoint'}
SAFE_OPERATIONS = {'inspect', 'read', 'report', 'write', 'validate', 'coordinate', 'dispatch'}
MAX_BODY = 16 * 1024
MAX_RECORD = 131072
MAX_ATTACHMENT = 64 * 1024 * 1024


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
    need(isinstance(issuer, dict) and issuer.get('role') in {'main', 'worker'}, 'issuer')
    identity(issuer.get('session'))
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


def validate_acceptance(record):
    """Validate Main acceptance provenance; does not claim authentication."""
    _envelope(record)
    _accepted(record)
    return record['acceptance']


accepted = validate_acceptance


def _integer(value, name, low=0, high=100000):
    need(type(value) is int and low <= value <= high, 'limit-' + name)
    return value


def _limits(limits, now=None):
    need(isinstance(limits, dict), 'limits')
    limits = copy.deepcopy(limits)
    defaults = {'rounds': 3, 'launches': 12, 'concurrency': 3, 'reserve_launches': 1, 'retries': 2}
    for key, default in defaults.items():
        limits.setdefault(key, default)
        _integer(limits[key], key, 0 if key in {'reserve_launches', 'retries'} else 1)
    need(limits['reserve_launches'] < limits['launches'], 'report-reserve')
    need(limits['retries'] <= 2, 'retry-limit')
    deadline = timestamp(limits.get('deadline'))
    if now is not None:
        need(now < deadline, 'deadline')
    if 'aggregate_concurrency' in limits:
        _integer(limits['aggregate_concurrency'], 'aggregate_concurrency', 1)
    if 'aggregate_launches' in limits:
        _integer(limits['aggregate_launches'], 'aggregate_launches', 1)
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


def _initial(record):
    _accepted(record)
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
    need(isinstance(record.get('actions'), list) and record['actions'] and set(record['actions']) <= SAFE_OPERATIONS, 'actions')
    need(timestamp(limits['deadline']) <= timestamp(authority['expires']), 'mandate-deadline')
    common = {'id': record['id'], 'family': record['family'], 'head': record['id'], 'epoch': 0, 'held': False, 'holds': [], 'history': [], 'limits': limits, 'authority': copy.deepcopy(authority), 'completed_at': None}
    if record['family'] == 'Teams':
        members = copy.deepcopy(record.get('members', []))
        need(isinstance(members, list), 'members')
        slots = [m.get('slot') for m in members if isinstance(m, dict)]
        need(len(slots) == len(members) and len(set(slots)) == len(slots) and 'leader' in slots, 'leader-slot')
        for member in members:
            _attempt_token(member.get('slot'))
            if member.get('session') is not None:
                identity(member['session'])
                need(member['session'] != record['issuer']['session'], 'dedicated-leader')
        common.update(state='ready', members={m['slot']: m for m in members}, leader=next(m.get('session') for m in members if m['slot'] == 'leader'))
    else:
        common.update(state='admitted', attempts={}, active=[], launches=0, rounds=0, retry_count=0, validations=[], results=[], late_results=[], stop_unconfirmed=[], classification=None, idempotent=False)
    return common


def _job_transition(state, event, record, proposals):
    action, data = event['action'], event['data']
    now = timestamp(event['at'])
    limits = state['limits']
    active = state['active']
    if action == 'dispatch':
        need(state['state'] in {'admitted', 'running'}, 'dispatch-state')
        need(now < timestamp(limits['deadline']) and now < timestamp(state['authority']['expires']), 'deadline')
        attempt = _attempt_token(data.get('attempt'))
        need(attempt not in state['attempts'], 'duplicate-attempt')
        identity(data.get('session'))
        need(data['session'] != record['issuer']['session'], 'main-worker')
        slot = _attempt_token(data.get('slot'))
        need(data.get('operation') in record['actions'], 'operation-scope')
        need(not any(state['attempts'][a]['session'] == data['session'] for a in active), 'session-busy')
        need(len(active) < limits['concurrency'], 'concurrency')
        reporting = data.get('purpose') in {'validation', 'checkpoint', 'report'}
        ceiling = limits['launches'] if reporting else limits['launches'] - limits['reserve_launches']
        need(state['launches'] < ceiling, 'launches')
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
        active.append(attempt); state['launches'] += 1; state['state'] = 'running'
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
            need(not item.get('retry_authorized') and state['retry_count'] < limits['retries'], 'retry-limit')
            retry_after = timestamp(data.get('after'))
            need(now <= retry_after < timestamp(limits['deadline']), 'retry-backoff')
            item.update(retry_authorized=True, retry_after=data['after']); state['retry_count'] += 1
        elif action == 'uncertain':
            need(item['status'] in {'dispatch-intent', 'received'}, 'uncertain-state')
            item['status'] = 'needs-reconciliation'; state['state'] = 'blocked'; state['classification'] = 'unknown-external-outcome'
        else:
            prior_state = state['state']
            need(item['status'] == 'needs-reconciliation' and data.get('outcome') in {'not-performed', 'performed', 'failed'}, 'reconcile-state')
            need(isinstance(data.get('evidence'), str) and data['evidence'].strip(), 'reconcile-evidence')
            item.update(status='reconciled', outcome=data['outcome'], evidence=data['evidence'])
            if attempt in active: active.remove(attempt)
            if attempt in state['stop_unconfirmed']: state['stop_unconfirmed'].remove(attempt)
            if prior_state not in TERMINAL and not any(a['status'] == 'needs-reconciliation' for a in state['attempts'].values()):
                state['state'] = ('pause-requested' if active else 'paused') if prior_state in {'paused', 'pause-requested'} else ('running' if active else 'admitted')
    elif action == 'round':
        need(state['state'] in {'admitted', 'running'} and state['rounds'] < limits['rounds'], 'rounds')
        need(isinstance(data.get('progress'), str) and data['progress'].strip(), 'progress')
        state['rounds'] += 1
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
        if not active and state['state'] == 'pause-requested': state['state'] = 'paused'
    elif action == 'resume':
        need(state['state'] == 'paused' and not active, 'resume-state')
        state['state'] = 'admitted'
    elif action == 'cancel':
        state['state'] = 'cancelled'; state['stop_unconfirmed'] = list(active); state['completed_at'] = event['at']
    elif action in {'succeed', 'fail', 'expire'}:
        if action == 'succeed':
            need(not active and state['attempts'] and all(a['status'] in {'validated', 'stopped'} or (a['status'] == 'failed' and a.get('retry_used') is True) or (a['status'] == 'reconciled' and a.get('outcome') == 'not-performed') for a in state['attempts'].values()), 'unvalidated-output')
            need(any(a['status'] == 'validated' for a in state['attempts'].values()), 'unvalidated-output')
            need(all(isinstance(data.get(k), str) and data[k].strip() for k in ('summary', 'dissent', 'usage')), 'completion-evidence')
        if action == 'expire':
            need(now >= min(timestamp(limits['deadline']), timestamp(state['authority']['expires'])), 'not-expired')
        state['state'] = {'succeed': 'succeeded', 'fail': 'failed', 'expire': 'expired'}[action]
        state['completed_at'] = event['at']; state['stop_unconfirmed'] = list(active)
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
        # Scope/limits cannot expand through an amendment; that requires a new founding charter.
        state['epoch'] += 1; state['amendment'] = dict(data)
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
            _envelope(message); _accepted(message)
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
            need(state['state'] not in TERMINAL or (state['state'] in {'cancelled', 'failed', 'expired'} and event['action'] in {'boundary', 'checkpoint', 'reconcile'}), 'terminal-immutable')
            if event['action'] not in {'cancel', 'pause', 'boundary', 'checkpoint', 'expire', 'reconcile'}:
                need(timestamp(event['at']) < timestamp(state['authority']['expires']), 'authority-expired')
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
    admitted = snapshot(founding.get('team_head'))
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
    def locked(self):
        self.require_main()
        need(self._lock is None, 'nested-lock')
        name = '_Axis/coordination.lock'
        lock = self.path(name, missing=True, kind='directory')
        owner = canonical({'session': self.session, 'nonce': secrets.token_hex(16)}) + b'\n'
        try:
            os.mkdir(lock)
        except FileExistsError:
            raise CoordinationError('locked', name) from None
        start = time.monotonic(); owner_path = lock / 'OWNER'
        try:
            fd = os.open(owner_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try: _START.write_fd(fd, owner)
            finally: os.close(fd)
            self._lock = (lock, owner, start, (lock.stat().st_dev, lock.stat().st_ino))
            self._check_lock(); yield
        finally:
            if self._lock is not None:
                current = self._lock; self._lock = None
                # Never remove another owner's claim, including on exceptions or expired holds.
                try:
                    info = lock.lstat()
                    if not stat.S_ISLNK(info.st_mode) and (info.st_dev, info.st_ino) == current[3] and self.io.read(name + '/OWNER') == owner.decode():
                        os.unlink(owner_path); os.rmdir(lock)
                except (OSError, _START.Fault):
                    pass

    def _check_lock(self):
        need(self._lock is not None, 'lock-required')
        lock, owner, start, ident = self._lock
        need(time.monotonic() - start < 10, 'lock-expired')
        safe = self.path('_Axis/coordination.lock', kind='directory'); info = safe.stat()
        need((info.st_dev, info.st_ino) == ident and self.io.read('_Axis/coordination.lock/OWNER') == owner.decode(), 'lock-owner')
        self.require_main()

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
             and value['schema'] == 'axis.coordination-placement/v1'
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
        self._check_lock()
        name = '_Axis/Flags/coordination-placement.json'
        destination = self.path(name, missing=True)
        previous = self.io.read(name, optional=True)
        temporary_name = name + '.' + secrets.token_hex(16) + '.tmp'
        temporary = self.path(temporary_name, missing=True)
        fd = os.open(temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            now = dt.datetime.now(dt.timezone.utc)
            value = {'schema': 'axis.coordination-placement/v1', 'active': active,
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
            self._check_lock()
        finally:
            if temporary.exists(): temporary.unlink()

    def _record(self, family, payload, worker=False):
        need(family in FAMILIES and family in _START.FAMILIES, 'family-unavailable', family)
        self.path('_Axis/' + family, kind='directory')
        self.guard()
        if not worker: self._check_lock()
        project = self.project_id()
        reserved = {'schema', 'family', 'id', 'created', 'project', 'issuer', 'acceptance'}
        need(not reserved.intersection(payload), 'reserved-fields')
        issuer = {'session': self.session, 'role': 'main' if self.io.lease[2] else 'worker'}
        acceptance = self._acceptance() if issuer['role'] == 'main' else None
        def body(value):
            result = dict(copy.deepcopy(payload), schema=SCHEMA, family=family, id=value, created=value, project=project, issuer=issuer)
            if family == 'Messages':
                result.setdefault('expires', stamp(self.now() + dt.timedelta(hours=24)))
                result.setdefault('authority', None)
                result.setdefault('attachments', [])
                if result.get('correlation') is None: result['correlation'] = value
            if acceptance is not None: result['acceptance'] = acceptance
            return render_record(result)
        try:
            ident, name = self.io.record(family, body, renew_lease=False)
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
        need(family in FAMILIES, 'family', family)
        try:
            archive, external = _START.archive_root(self.io)
        except (OSError, _START.Fault):
            return
        folder = self.path(archive, missing=True, kind='directory') if archive else external
        if folder is None or not folder.exists(): return
        self.require_history()
        locations = [(folder / family, False)]
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

    def _archive_records(self, family):
        found = []
        for path, legacy in self._archive_paths(family):
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

    def records(self, family):
        need(family in FAMILIES, 'family', family)
        folder = self.path('_Axis/' + family, missing=True, kind='directory')
        result = []
        if folder.exists():
            for path in sorted(folder.iterdir()):
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
                record = read_record(path)
                need(record['family'] == family and record['id'] == path.stem and record['project'] == self.project_id(), 'record-identity', path)
                result.append(record)
        for record in self._archive_records(family):
            if record['family'] == family and record['project'] == self.project_id(): result.append(record)
        ids = [record['id'] for record in result]
        need(len(ids) == len(set(ids)), 'record-collision', family)
        return sorted(result, key=lambda r: r['id'])

    def read(self, family, ident):
        identity(ident)
        matches = [record for record in self.records(family) if record['id'] == ident]
        need(len(matches) == 1, 'record-missing', ident)
        return matches[0]

    def validate_authority(self, authority, live=True):
        need(isinstance(authority, dict), 'authority')
        value = copy.deepcopy(authority)
        reference = relative(value.get('ref'))
        expires = timestamp(value.get('expires'))
        path = self.path(reference, missing=True)
        if not path.exists() and _START.ID.fullmatch(Path(reference).stem):
            # Historic source links can move into the in-project Archive.
            archive = self.path('_Axis/Archive', kind='directory')
            candidates = list(archive.rglob(Path(reference).name))
            need(len(candidates) == 1, 'authority-missing', reference)
            reference = candidates[0].relative_to(self.root).as_posix(); path = self.path(reference)
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try: raw = _START.read_fd(fd, reference, MAX_RECORD)
        finally: os.close(fd)
        actual = digest(raw)
        need(value.get('digest', actual) == actual, 'authority-changed', reference)
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
        value['limits'].setdefault('deadline', stamp(min(now + dt.timedelta(minutes=60), timestamp(value['authority']['expires']))))
        value['limits'] = _limits(value['limits'], now)
        need(timestamp(value['limits']['deadline']) <= timestamp(value['authority']['expires']), 'mandate-deadline')
        value['acceptance_owner'] = self.session
        value['reservation_launches'] = min(value['limits']['launches'], 1 + value['limits']['reserve_launches'])
        return value

    def create_team(self, charter):
        with self.locked():
            self.require_placement()
            value = self._founding(charter)
            members = value.get('members')
            need(isinstance(members, list) and members, 'members')
            slots = [m.get('slot') for m in members if isinstance(m, dict)]
            need(len(slots) == len(members) and len(set(slots)) == len(slots) and slots.count('leader') == 1, 'leader-slot')
            sessions = []
            for member in members:
                _attempt_token(member.get('slot'))
                if member.get('session') is not None:
                    self._worker_session(member['session']); sessions.append(member['session'])
                if 'scope' in member:
                    self._scope(member['scope'])
                    need(all(any(p == base or p.startswith(base + '/') for base in value['scope']) for p in member['scope']), 'write-scope')
            need(len(sessions) == len(set(sessions)), 'duplicate-member-session')
            return self._record('Teams', value)

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
        with self.locked():
            self.require_placement()
            self.require_history()
            value = self._founding(mandate)
            value['operation_key'] = operation_key
            jobs = self.records('Jobs'); messages = self.records('Messages')
            for record in jobs:
                if record.get('operation_key') == operation_key:
                    compare = {k: v for k, v in record.items() if k not in {'schema', 'family', 'id', 'created', 'project', 'issuer', 'acceptance', 'acceptance_owner', 'team_epoch', 'team_head'}}
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
                for limit in ('rounds', 'launches', 'concurrency'):
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
            return self._record('Jobs', value)

    def _team_budget(self, mandate, jobs, messages, *, admission=False, action=None, data=None):
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

    def _reserve_admission(self, mandate, jobs, messages):
        budget = mandate.get('budget_key', mandate['authority']['digest'])
        caps = [mandate['limits']['aggregate_launches']] if 'aggregate_launches' in mandate['limits'] else []
        spent = reserved = 0
        teams = self.records('Teams')
        for record in jobs:
            if record.get('budget_key', record['authority']['digest']) != budget: continue
            view = project_records(record, messages, teams)
            need(not view['held'], 'budget-held')
            spent += view['launches']
            if view['state'] not in TERMINAL:
                reserved += _remaining_reservation(record, view)
            if 'aggregate_launches' in record['limits']: caps.append(record['limits']['aggregate_launches'])
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

    def message(self, kind, recipient, body, *, team=None, job=None, correlation=None, epoch=0, data=None, expires=None, authority=None, attachments=None):
        need(kind in MESSAGE_KINDS and isinstance(recipient, str) and 0 < len(recipient) <= 256, 'message-kind')
        need(isinstance(body, str) and len(body.encode()) <= MAX_BODY, 'message-body')
        need(type(epoch) is int and epoch >= 0 and (data is None or isinstance(data, dict)), 'message-data')
        self.guard()
        expires = expires or stamp(self.now() + dt.timedelta(hours=24))
        timestamp(expires)
        need(self.io.lease[2] or authority is None, 'worker-message-authority')
        authority = self.validate_authority(authority) if authority is not None else None
        attachments = copy.deepcopy(attachments if attachments is not None else [])
        if team is not None: identity(team)
        if job is not None: identity(job)
        if correlation is not None: need(isinstance(correlation, str) and len(correlation.encode()) <= 256, 'correlation')
        payload = {'subject': (kind.capitalize() + ': ' + ((body.splitlines()[0].strip() if body else '') or recipient))[:80].strip(), 'kind': kind, 'recipient': recipient, 'body': body, 'team': team, 'job': job, 'correlation': correlation, 'epoch': epoch, 'data': copy.deepcopy(data or {}), 'expires': expires, 'authority': authority, 'attachments': attachments}
        if not self.io.lease[2]:
            need(self.storage_profile() == 'atomic', 'main-mediated-capture')
            need(kind in PROPOSALS and job is not None, 'worker-message-scope')
            need(authority is None, 'worker-message-authority')
            founding = self.read('Jobs', job); state = self.project('Jobs', job)
            need(not state['held'] and team == founding.get('team'), 'worker-message-scope')
            attempt = state['attempts'].get(payload['data'].get('attempt'), {})
            need(attempt.get('session') == self.session and attempt.get('epoch') == epoch, 'worker-message-scope')
            need(recipient in {founding['acceptance_owner'], 'main', 'leader'}, 'worker-recipient')
            if team is not None:
                team_state = self.project('Teams', team)
                need(not team_state['held'] and (kind == 'result' or attempt.get('team_epoch') == team_state['epoch']), 'stale-epoch')
            need(isinstance(attachments, list), 'attachments')
            allowed_scope = attempt.get('scope', founding['scope'])
            for attachment in attachments:
                need(isinstance(attachment, dict) and isinstance(attachment.get('path'), str) and any(attachment['path'] == base or attachment['path'].startswith(base + '/') for base in allowed_scope), 'attachment-scope')
            payload['attachments'] = self.validate_attachments(attachments)
            # A late result is retained after cancellation/expiry; it has no control effect.
            return self._record('Messages', payload, worker=True)
        payload['attachments'] = self.validate_attachments(attachments)
        with self.locked(): return self._record('Messages', payload)

    def capture_result(self, job, attempt, body, *, attachments=None):
        self.require_main()
        founding = self.read('Jobs', job); state = self.project('Jobs', job)
        item = state.get('attempts', {}).get(attempt)
        need(not state['held'] and item is not None, 'unknown-attempt')
        attachments = copy.deepcopy(attachments if attachments is not None else [])
        need(isinstance(attachments, list), 'attachments')
        allowed_scope = item.get('scope', founding['scope'])
        for attachment in attachments:
            need(isinstance(attachment, dict) and isinstance(attachment.get('path'), str) and any(attachment['path'] == base or attachment['path'].startswith(base + '/') for base in allowed_scope), 'attachment-scope')
        return self.message('result', 'main', body, team=founding.get('team'), job=job,
                            correlation=founding['operation_key'], epoch=item['epoch'],
                            data={'attempt': attempt, 'manual_capture': True, 'reported_session': item['session']},
                            attachments=attachments)

    def disposition(self, message_id, outcome, reference=None):
        need(outcome in {'received', 'admitted', 'declined', 'referred', 'validated', 'rejected', 'closed'}, 'disposition')
        with self.locked():
            original = self.read('Messages', message_id)
            need(original['kind'] not in {'receipt', 'decision', 'validation', 'control'} and 'event' not in original, 'no-receipt-loop')
            decisions = [m for m in self.records('Messages') if m.get('data', {}).get('disposition_of') == message_id]
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
            accepted_validations = [m for m in messages if m.get('event', {}).get('action') == 'validate' and m.get('event', {}).get('data', {}).get('message') == message['id']]
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

    def project(self, family, ident):
        need(family in {'Teams', 'Jobs'}, 'projection-family')
        return project_records(self.read(family, ident), self.records('Messages'), self.records('Teams'))

    def event(self, family, ident, action, data=None, expected=None, epoch=None):
        need(family in {'Teams', 'Jobs'}, 'projection-family')
        need(action in (JOB_ACTIONS if family == 'Jobs' else TEAM_ACTIONS), 'unknown-action')
        need(data is None or isinstance(data, dict), 'event-data')
        with self.locked():
            self.require_placement()
            founding = self.read(family, ident); messages = self.records('Messages')
            state = project_records(founding, messages, self.records('Teams'))
            need(not state['held'], 'projection-held')
            if expected is not None: need(expected == state['head'], 'stale-predecessor')
            if epoch is not None: need(epoch == state['epoch'], 'stale-epoch')
            live = action not in {'cancel', 'pause', 'boundary', 'checkpoint', 'expire', 'reconcile'}
            self.validate_authority(founding['authority'], live=live)
            payload_data = copy.deepcopy(data or {})
            now = self.now()
            if state['history']:
                last = next(m for m in messages if m['id'] == state['head'])
                need(now >= timestamp(last['event']['at']), 'clock-rollback')
            if family == 'Teams' and action in {'replace_leader', 'bind_member'}:
                self._worker_session(payload_data.get('session'))
            if family == 'Jobs' and action in {'dispatch', 'round', 'retry'}:self.require_history()
            if family == 'Jobs' and founding.get('team') and action in {'dispatch', 'round'}:
                self._team_budget(founding, self.records('Jobs'), messages, action=action, data=payload_data)
            if family == 'Jobs' and action == 'dispatch':
                self._worker_session(payload_data.get('session'))
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
            candidate = dict(payload, schema=SCHEMA, family='Messages', id='9999.12.31.23.59.59.999Z', created='9999.12.31.23.59.59.999Z', project=self.project_id(), issuer={'session': self.session, 'role': 'main'}, acceptance=self._acceptance())
            projected = project_records(founding, messages + [candidate], self.records('Teams'))
            need(not projected['held'], 'transition:' + ';'.join(projected['holds']))
            return self._record('Messages', payload)

    def _capacity(self, founding, messages, dispatch):
        active = launches = reserved = 0
        budget = founding.get('budget_key', founding['authority']['digest'])
        configured = self.io.setting('Max Concurrent Sessions')
        project_cap = int(configured) if isinstance(configured, str) and configured.isascii() and configured.isdigit() and 1 <= int(configured) <= 100 else 10
        concurrency_limits = [max(0, project_cap - 1), founding['limits'].get('aggregate_concurrency', founding['limits']['concurrency'])]
        launch_limits = []
        if 'aggregate_launches' in founding['limits']: launch_limits.append(founding['limits']['aggregate_launches'])
        for record in self.records('Jobs'):
            state = project_records(record, messages)
            need(not state['held'], 'capacity-held')
            active += len(state['active'])
            need(not any(state['attempts'][a]['session'] == dispatch.get('session') for a in state['active']), 'session-busy')
            if record.get('budget_key', record['authority']['digest']) == budget:
                launches += state['launches']
                if state['state'] not in TERMINAL:
                    if record['id'] != founding['id']: reserved += _remaining_reservation(record, state)
                    elif dispatch.get('purpose') not in {'validation', 'checkpoint', 'report'}: reserved += _report_reserve(record, state)
                if 'aggregate_launches' in record['limits']: launch_limits.append(record['limits']['aggregate_launches'])
            if state['state'] not in TERMINAL:
                concurrency_limits.append(record['limits'].get('aggregate_concurrency', record['limits']['concurrency']))
        need(active < min(concurrency_limits), 'aggregate-concurrency')
        if launch_limits: need(launches + reserved < min(launch_limits), 'aggregate-launches')

    def check(self):
        findings = []
        try:
            all_records = {family: self.records(family) for family in FAMILIES}
            ids = [r['id'] for records in all_records.values() for r in records]
            need(len(ids) == len(set(ids)), 'record-collision')
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
            source_digest = digest({family: [digest(r) for r in records] for family, records in all_records.items()})
            verified = stamp(self.now())
            for family, index in (('Teams', 'TEAMS'), ('Jobs', 'JOBS'), ('Messages', 'MESSAGES'), ('Schedules', 'SCHEDULES')):
                lines = ['# ' + family, '> **Purpose:** Show cached coordination state; records and accepted events are authoritative.', '', 'schema: axis.coordination-index/v1', 'verified: ' + verified, 'source-digest: ' + source_digest, 'pending-count: ' + str(len(pending) if family == 'Messages' else sum((r.get('status') not in {'retired'} if family == 'Schedules' else project_records(r, all_records['Messages'], all_records['Teams'])['state'] not in TERMINAL) for r in all_records[family])), '', '| ID | Subject | State | Head |', '| --- | --- | --- | --- |']
                rows = all_records[family]
                if family == 'Messages':
                    rows = [item for item in rows if item['id'] in pending] + list(reversed([item for item in rows if item['id'] not in pending]))
                shown = 0
                byte_count = len(('\n'.join(lines)+'\n').encode())
                for record in rows:
                    if shown >= 100: break
                    if family == 'Messages':
                        state, head = (pending[record['id']]['state'], pending[record['id']]['head']) if record['id'] in pending else ('recorded', record['id'])
                    elif family == 'Schedules':
                        state, head = record.get('status', 'held'), record.get('revision') or 'incomplete'
                    else:
                        view = project_records(record, all_records['Messages'], all_records['Teams']); state = 'held' if view['held'] else view['state']; head = view['head']
                    subject = record['subject'].replace('|', '\\|').replace('\n', ' ')
                    row = '| [' + record['id'] + '](' + self.record_link(family, record['id']) + ') | ' + subject + ' | ' + state + ' | ' + head + ' |'
                    size = len((row+'\n').encode())
                    if byte_count+size > 60000: break
                    lines.append(row); byte_count += size; shown += 1
                lines.extend(['', 'shown-count: ' + str(shown), 'total-count: ' + str(len(rows))])
                if shown < len(rows):
                    lines.extend(['', 'Showing ' + str(shown) + ' of ' + str(len(rows)) + ' records. Complete details remain in ' + family + '/ and the configured Archive.'])
                if family == 'Messages':
                    lines.extend(['', 'Pending items appear first. Recorded history includes receipts, decisions and validated work; recorded does not mean approved.', ''])
                text = '\n'.join(lines) + '\n'; name = '_Axis/' + index + '.md'; old = self.io.read(name, optional=True)
                self._replace(name, text, digest(old) if old is not None else None)
                result[index] = digest(text)
            return {'status': 'rebuilt', 'indexes': result}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default='.')
    parser.add_argument('--session')
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('initialize', 'identity', 'check', 'indexes', 'pending', 'placement-status', 'deactivate'): sub.add_parser(name)
    activation = sub.add_parser('activate')
    activation.add_argument('--single-writer', action='store_true')
    activation.add_argument('--previous-placement-inactive', action='store_true')
    activation.add_argument('--expires')
    listing = sub.add_parser('list'); listing.add_argument('family', choices=FAMILIES)
    projection = sub.add_parser('project'); projection.add_argument('family', choices=['Teams', 'Jobs']); projection.add_argument('id')
    for name in ('team', 'admit', 'message', 'event', 'disposition', 'capture-result'):
        command = sub.add_parser(name); command.add_argument('--input', default='-')
    args = parser.parse_args(argv)
    try:
        store = Store(args.root, args.session)
        if args.command == 'initialize': result = store.initialize()
        elif args.command == 'activate': result = store.activate(single_writer=args.single_writer, previous_inactive=args.previous_placement_inactive, expires=args.expires)
        elif args.command == 'deactivate': result = store.deactivate()
        elif args.command == 'placement-status': result = store.placement_status()
        elif args.command == 'identity': result = {'project': store.project_id()}
        elif args.command == 'check': result = store.check()
        elif args.command == 'indexes': result = store.rebuild_indexes()
        elif args.command == 'pending': result = store.pending_messages()
        elif args.command == 'list': result = store.records(args.family)
        elif args.command == 'project': result = store.project(args.family, args.id)
        else:
            raw = sys.stdin.read(MAX_RECORD + 1) if args.input == '-' else store.path(args.input).read_text()
            need(len(raw.encode()) <= MAX_RECORD, 'input-size')
            value = json.loads(raw, object_pairs_hook=_unique_pairs)
            need(isinstance(value, dict), 'input-object')
            if args.command == 'team': result = store.create_team(value)
            elif args.command == 'admit': result = store.admit_job(value['mandate'], value['operation_key'])
            elif args.command == 'message': result = store.message(**value)
            elif args.command == 'disposition': result = store.disposition(**value)
            elif args.command == 'capture-result': result = store.capture_result(**value)
            else: result = store.event(**value)
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 1 if isinstance(result, dict) and result.get('status') == 'held' else 0
    except (CoordinationError, _START.Fault, OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({'status': 'error', 'code': getattr(exc, 'code', 'input-or-io'), 'path': getattr(exc, 'path', '')}, sort_keys=True))
        return 1


if __name__ == '__main__':
    sys.exit(main())
