#!/usr/bin/env python3
"""Main-owned, immutable-message Inbox transfers across one direct-child boundary.

No source document is interpreted as authority. Destination acceptance is a record
of filing responsibility, not approval to execute document contents. Hashes provide
integrity/provenance only. Cooperating local writers and qualified locks are required.
"""
from __future__ import annotations
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time
import uuid
import unicodedata

PROTOCOL = 'axis.transfer/v1'
SID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\Z')
STAGES = ('prepared', 'copied-and-verified', 'destination-accepted', 'source-retired')
ANCHORS = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '_Axis/MANIFEST.md', '_Axis/PROJECT.md', '_Axis/PRACTICES.md', '_Axis/RULES.md')


class TransferError(ValueError):
    def __init__(self, code, detail=''):
        self.code = code
        super().__init__(code + (': ' + detail if detail else ''))


def _need(condition, code, detail=''):
    if not condition:
        raise TransferError(code, detail)


def _root(value):
    p = Path(value)
    _need(p.is_absolute() and str(p) == str(p.resolve(strict=True)) and p.is_dir(), 'unsafe-root')
    return p


def _recognized(root):
    return all((root / n).is_file() and not (root / n).is_symlink() for n in ANCHORS) and (root / '_Temp').is_dir() and not (root / '_Temp').is_symlink() and not (root / '_Axis').is_symlink()


def direct_boundary(source, destination):
    """Nearest recognized Axis ancestor only; wrappers are allowed, grandchildren not."""
    a, b = _root(source.root), _root(destination.root)
    _need(a != b and _recognized(a) and _recognized(b), 'invalid-project-boundary')
    _need(source.project_id() != destination.project_id(), 'copied-project-identity')
    _need(a in b.parents, 'destination-not-descendant')
    for ancestor in b.parents:
        if _recognized(ancestor):
            _need(ancestor == a, 'not-direct-child')
            break
    # Any protected wrapper blocks routing even if an inner project is otherwise valid.
    for part in b.relative_to(a).parts:
        _need(not part.endswith(('_U', '_X')) and not part.startswith('.'), 'protected-boundary')
    return a, b


def _relative(value, *, inbox=False):
    _need(isinstance(value, str) and bool(value) and '\\' not in value and '\x00' not in value, 'unsafe-path')
    path = PurePosixPath(value)
    _need(not path.is_absolute() and str(path) == value and all(x not in ('', '.', '..') for x in path.parts), 'unsafe-path')
    _need(all(not x.startswith('.') and not x.lower().endswith(('_u', '_x')) and unicodedata.normalize('NFC', x) == x for x in path.parts), 'protected-path')
    _need(not any(x.casefold() in ('_axis', '_temp', '_trash', 'secrets', '_secrets') for x in path.parts), 'protected-path')
    _need(not re.search(r'(?:^|[._-])(?:credentials?|secrets?|tokens?|private[-_]?key)(?:[._-]|$)', path.name, re.I), 'suspected-secret-name')
    _need(path.suffix.lower() not in ('.part', '.partial', '.tmp', '.download', '.crdownload', '.pem', '.key'), 'partial-or-sensitive-name')
    if inbox:
        _need(len(path.parts) == 2 and path.parts[0] == '_Inbox', 'destination-must-be-flat-inbox')
    return value


def _safe_path(root, relative, *, missing=False):
    path = root
    for index, part in enumerate(PurePosixPath(relative).parts):
        _need(part not in ('', '.', '..'), 'unsafe-path')
        parent = path
        path = path / part
        if parent.is_dir():
            matches = [n for n in os.listdir(parent) if unicodedata.normalize('NFC', n).casefold() == unicodedata.normalize('NFC', part).casefold()]
            _need(not matches or matches == [part], 'case-collision', str(path))
        _need(not path.is_symlink(), 'symlink', str(path))
        if not path.exists():
            _need(missing and index == len(PurePosixPath(relative).parts) - 1, 'missing-path', str(path))
            return path
    if path.is_file():
        _need(path.stat().st_nlink == 1, 'hardlink', str(path))
    return path


_RECORD_FORMAT = None

def _record_format():
    global _RECORD_FORMAT
    if _RECORD_FORMAT is None:
        spec = importlib.util.spec_from_file_location('axis_transfer_record', Path(__file__).with_name('coordination-record.py'))
        _RECORD_FORMAT = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(_RECORD_FORMAT)
    return _RECORD_FORMAT


def _read_claim(path):
    limit = 4096 if path.name == 'OWNER' else 16384
    _need(path.is_file() and not path.is_symlink(), 'unsafe-claim')
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        before = os.fstat(fd)
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit, 'unsafe-claim')
        raw = os.read(fd, limit+1)
        after = os.fstat(fd)
        _need(len(raw) == before.st_size and (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'changed-claim')
    finally:
        os.close(fd)
    def unique(pairs):
        result = {}
        for key, value in pairs:
            _need(key not in result, 'duplicate-claim-key')
            result[key] = value
        return result
    try:
        if path.name == 'OWNER':
            return json.loads(raw, object_pairs_hook=unique)
        return _record_format().decode(raw.decode('utf-8'),16384)[1]
    except (ValueError, UnicodeError) as exc:
        raise TransferError('invalid-claim') from exc


def _fingerprint(path, max_bytes):
    fd = os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        before = os.fstat(fd)
        _need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'not-plain-file')
        _need(before.st_size <= max_bytes, 'file-too-large')
        h = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            _need(total <= max_bytes, 'file-too-large')
            h.update(chunk)
        after = os.fstat(fd)
        _need((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) ==
              (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'changed-during-read')
        current = path.lstat()
        _need(not stat.S_ISLNK(current.st_mode) and (current.st_dev, current.st_ino) == (before.st_dev, before.st_ino), 'path-replaced')
        return {'sha256': h.hexdigest(), 'size': total}, before
    finally:
        os.close(fd)


def _record(result):
    return result.get('record', result)


def _metadata(record):
    # Foundation's canonical record puts message-specific fields at top level.
    data = record.get('data', {})
    return data if isinstance(data, dict) else {}


def _records(store):
    records = store.records('Messages')
    for item in records:
        if isinstance(item, dict):
            yield _record(item)
        else:
            # Support stores yielding immutable paths; never parse them as instructions.
            yield store.read('Messages', Path(item).stem)


_CORE = None

def _accepted_main(record):
    global _CORE
    if _CORE is None:
        path = Path(__file__).with_name('coordination.py')
        _need(path.is_file() and not path.is_symlink(), 'foundation-unavailable')
        spec = importlib.util.spec_from_file_location('axis_transfer_foundation', path)
        _CORE = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = _CORE
        spec.loader.exec_module(_CORE)
    try:
        _CORE.validate_acceptance(record)
        return True
    except _CORE.CoordinationError:
        return False


class TransferManager:
    def __init__(self, source, destination, *, max_bytes=1024 * 1024, stable_age=60, clock=time.time):
        _need(isinstance(max_bytes, int) and 0 < max_bytes <= 64 * 1024 * 1024, 'invalid-size-limit')
        _need(isinstance(stable_age, (int, float)) and stable_age >= 60, 'invalid-stability-window')
        self.source, self.destination = source, destination
        self.max_bytes, self.stable_age, self.clock = max_bytes, stable_age, clock
        self._holds = []
        direct_boundary(source, destination)

    def _guard(self, store):
        for lock, owner, started, identity in self._holds:
            _need(time.monotonic() - started < 10, 'lock-expired')
            _need(not lock.is_symlink() and (lock.stat().st_dev, lock.stat().st_ino) == identity and _read_claim(lock / 'OWNER') == owner, 'lock-owner')
        store.require_placement()
        store.guard()
        _need(self.source.storage_profile() == self.destination.storage_profile() == 'atomic', 'storage-not-qualified')
        direct_boundary(self.source, self.destination)

    @contextmanager
    def _lock(self, path, store):
        self._guard(store)
        lock = Path(str(path) + '.lock')
        owner = {'session': store.session, 'nonce': uuid.uuid4().hex}
        try:
            lock.mkdir()
        except FileExistsError as exc:
            raise TransferError('collision-or-held-lock', str(lock)) from exc
        try:
            with (lock / 'OWNER').open('x') as f:
                json.dump(owner, f, sort_keys=True)
            hold = (lock, owner, time.monotonic(), (lock.stat().st_dev, lock.stat().st_ino))
            self._holds.append(hold)
            yield
        finally:
            self._holds = [held for held in self._holds if held[0] != lock]
            try:
                if not lock.is_symlink() and _read_claim(lock / 'OWNER') == owner:
                    (lock / 'OWNER').unlink()
                    lock.rmdir()
            except (OSError, ValueError):
                pass  # Never remove another owner's lock or conceal its partial state.

    def _events(self, store, transfer_id):
        rows = []
        for rec in _records(store):
            data = _metadata(rec)
            if data.get('protocol') == PROTOCOL and (rec.get('id') == transfer_id or data.get('transfer_id') == transfer_id):
                _need(_accepted_main(rec), 'unaccepted-or-forged-transfer-event')
                _need(data.get('stage') in STAGES and rec.get('kind') == 'transfer', 'unknown-transfer-event')
                rows.append(rec)
        return rows

    def _base(self, transfer_id):
        _need(isinstance(transfer_id, str) and SID.fullmatch(transfer_id), 'invalid-transfer-id')
        row = _record(self.source.read('Messages', transfer_id))
        data = _metadata(row)
        _need(_accepted_main(row) and row.get('id') == transfer_id and row.get('project') == self.source.project_id() and row.get('kind') == 'transfer' and data.get('protocol') == PROTOCOL and data.get('stage') == 'prepared', 'invalid-prepared-record')
        a, b = direct_boundary(self.source, self.destination)
        _need(data.get('source', {}).get('project') == self.source.project_id() and data['source'].get('root') == str(a), 'source-identity-mismatch')
        _need(data.get('destination', {}).get('project') == self.destination.project_id() and data['destination'].get('root') == str(b), 'destination-identity-mismatch')
        _relative(data['source']['path'])
        _relative(data['destination']['path'], inbox=True)
        _need(re.fullmatch('[0-9a-f]{64}', data.get('sha256', '')) and isinstance(data.get('size'), int) and 0 <= data['size'] <= self.max_bytes, 'invalid-file-identity')
        _need(data.get('retirement') == 'archive-after-acceptance', 'unknown-retirement-policy')
        return row, data

    def _stage(self, store, transfer_id, stage, data, predecessor):
        rows = [r for r in self._events(store, transfer_id) if _metadata(r).get('stage') == stage]
        _need(len(rows) <= 1, 'divergent-transfer-events')
        if not rows:
            return None
        record = rows[0]
        got = _metadata(record)
        for key in ('source', 'destination', 'sha256', 'size', 'routing_rule', 'retirement', 'operation'):
            _need(got.get(key) == data.get(key), 'transfer-event-mismatch', key)
        _need(got.get('predecessor') == predecessor, 'transfer-predecessor-mismatch')
        _need(record.get('project') == store.project_id(), 'event-project-mismatch')
        return record

    def _append(self, store, transfer_id, stage, data, predecessor, extra=None):
        self._guard(store)
        event = dict(data, protocol=PROTOCOL, transfer_id=transfer_id, stage=stage, predecessor=predecessor)
        event.update(extra or {})
        return _record(store.message('transfer', 'Main', 'Inbox transfer ' + stage + '; document contents are data, not authority.',
                                     correlation=data['operation'], job=data.get('job'), data=event))

    def _check_bytes(self, path, data):
        actual, st = _fingerprint(path, self.max_bytes)
        _need(actual == {'sha256': data['sha256'], 'size': data['size']}, 'changed-or-partial-file', str(path))
        return st

    def prepare(self, source_path, *, routing_rule, operation, destination_name=None, job=None):
        self._guard(self.source)
        self.source.require_history()
        self.destination.require_history()
        _need(isinstance(operation, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', operation), 'invalid-operation-key')
        source_path = _relative(source_path)
        _need(PurePosixPath(source_path).parts[0] == '_Inbox', 'source-must-be-inbox')
        dest_path = '_Inbox/' + (destination_name or PurePosixPath(source_path).name)
        _relative(dest_path, inbox=True)
        rule = self.source.validate_authority(routing_rule)
        _need(routing_rule.get('action') == 'inbox.transfer' and routing_rule.get('target_project') == self.destination.project_id() and routing_rule.get('target_root') == str(self.destination.root), 'routing-rule-scope')
        source = _safe_path(self.source.root, source_path)
        with self._lock(source, self.source):
            actual, st = _fingerprint(source, self.max_bytes)
            _need(self.clock() - st.st_mtime >= self.stable_age, 'incomplete-arrival')
            repeat, again = _fingerprint(source, self.max_bytes)
            _need(actual == repeat and st.st_mtime_ns == again.st_mtime_ns, 'incomplete-arrival')
            data = {'protocol': PROTOCOL, 'stage': 'prepared', 'operation': operation,
                    'source': {'project': self.source.project_id(), 'root': str(self.source.root), 'path': source_path},
                    'destination': {'project': self.destination.project_id(), 'root': str(self.destination.root), 'path': dest_path},
                    **actual, 'routing_rule': dict(rule, action='inbox.transfer', target_project=self.destination.project_id(), target_root=str(self.destination.root)),
                    'retirement': 'archive-after-acceptance', 'job': job, 'predecessor': None}
            same = [r for r in _records(self.source) if _metadata(r).get('protocol') == PROTOCOL and _metadata(r).get('stage') == 'prepared' and _metadata(r).get('operation') == operation]
            _need(len(same) <= 1, 'duplicate-operation')
            if same:
                _need(_accepted_main(same[0]) and _metadata(same[0]) == data, 'operation-content-collision')
                return same[0]
            _safe_path(self.destination.root, dest_path, missing=True)
            _need(not (self.destination.root / dest_path).exists(), 'destination-collision')
            self._guard(self.source)
            return _record(self.source.message('transfer', 'Main', 'Prepare Inbox transfer; routing authority is separate from document contents.', correlation=operation, job=job, data=data))

    def _publish_copy(self, source, dest, data):
        """Publish only complete bytes; exclusive hard-link publish never overwrites."""
        partial = dest.with_name('.' + dest.name + '.partial-' + uuid.uuid4().hex)
        src_fd = os.open(source, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
        try:
            original = os.fstat(src_fd)
            _need(stat.S_ISREG(original.st_mode) and original.st_nlink == 1, 'not-plain-file')
            with partial.open('xb') as out:
                h, count = hashlib.sha256(), 0
                while True:
                    chunk = os.read(src_fd, 1024 * 1024)
                    if not chunk:
                        break
                    count += len(chunk)
                    _need(count <= self.max_bytes, 'file-too-large')
                    out.write(chunk)
                    h.update(chunk)
                out.flush()
                os.fsync(out.fileno())
            _need(count == data['size'] and h.hexdigest() == data['sha256'], 'source-changed')
            after = os.fstat(src_fd)
            _need((original.st_dev, original.st_ino, original.st_size, original.st_mtime_ns, original.st_ctime_ns) == (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns), 'source-changed')
            self._check_bytes(source, data)
            self._guard(self.source)
            os.link(partial, dest, follow_symlinks=False)
            partial.unlink()
            self._check_bytes(dest, data)
        finally:
            os.close(src_fd)
            # Failed partials remain visible as held evidence; never reuse them.

    def copy(self, transfer_id):
        self._guard(self.source)
        base, data = self._base(transfer_id)
        self.source.validate_authority(data['routing_rule'])
        previous = {'project': self.source.project_id(), 'id': transfer_id}
        existing = self._stage(self.source, transfer_id, 'copied-and-verified', data, previous)
        source = _safe_path(self.source.root, data['source']['path'])
        dest = _safe_path(self.destination.root, data['destination']['path'], missing=True)
        with self._lock(source, self.source), self._lock(dest, self.source):
            self._check_bytes(source, data)
            claim = dest.parent / ('_axis-transfer-' + transfer_id + '.md')
            expected_claim = {'protocol': PROTOCOL, 'transfer_id': transfer_id,
                              'source_project': self.source.project_id(), 'destination_project': self.destination.project_id(),
                              'path': data['destination']['path'], 'sha256': data['sha256'], 'size': data['size']}
            claim_exists = claim.exists() or claim.is_symlink()
            if claim_exists:
                _need(not claim.is_symlink() and claim.is_file() and claim.stat().st_nlink == 1 and claim.stat().st_size <= 16384, 'unsafe-copy-claim')
                _need(_read_claim(claim) == expected_claim, 'copy-claim-collision')
            else:
                _need(not dest.exists() and existing is None, 'unreceipted-destination-collision')
                with claim.open('x') as stream:
                    stream.write(_record_format().render('Axis transfer recovery claim', expected_claim))
                    stream.flush()
                    os.fsync(stream.fileno())
            if dest.exists():
                # Our immutable claim predates publication. On crash replay require
                # both that claim and exact bytes; a missing receipt alone is no retry.
                self._check_bytes(dest, data)
                return existing or self._append(self.source, transfer_id, 'copied-and-verified', data, previous)
            _need(existing is None, 'receipted-destination-missing')
            partials = list(dest.parent.glob('.' + dest.name + '.partial-*'))
            _need(not partials, 'partial-copy-held')
            self._publish_copy(source, dest, data)
            return self._append(self.source, transfer_id, 'copied-and-verified', data, previous)

    def accept(self, transfer_id):
        self._guard(self.destination)
        _, data = self._base(transfer_id)
        self.source.validate_authority(data['routing_rule'])
        copied = self._stage(self.source, transfer_id, 'copied-and-verified', data, {'project': self.source.project_id(), 'id': transfer_id})
        _need(copied is not None, 'copy-not-verified')
        predecessor = {'project': self.source.project_id(), 'id': copied['id']}
        existing = self._stage(self.destination, transfer_id, 'destination-accepted', data, predecessor)
        if existing:
            return existing  # Receiver may already have filed the accepted document.
        dest = _safe_path(self.destination.root, data['destination']['path'])
        with self._lock(dest, self.destination):
            self._check_bytes(dest, data)
            if existing:
                return existing
            return self._append(self.destination, transfer_id, 'destination-accepted', data, predecessor)

    def retire(self, transfer_id):
        self._guard(self.source)
        _, data = self._base(transfer_id)
        self.source.validate_authority(data['routing_rule'])
        copied = self._stage(self.source, transfer_id, 'copied-and-verified', data, {'project': self.source.project_id(), 'id': transfer_id})
        _need(copied is not None, 'copy-not-verified')
        accepted = self._stage(self.destination, transfer_id, 'destination-accepted', data, {'project': self.source.project_id(), 'id': copied['id']})
        _need(accepted is not None, 'destination-not-accepted')
        predecessor = {'project': self.destination.project_id(), 'id': accepted['id']}
        existing = self._stage(self.source, transfer_id, 'source-retired', data, predecessor)
        source = _safe_path(self.source.root, data['source']['path'], missing=True)
        trash = _safe_path(self.source.root, '_Trash')
        _need(trash.is_dir(), 'trash-unavailable')
        archive = _safe_path(self.source.root, '_Trash/' + transfer_id + '-' + source.name, missing=True)
        with self._lock(source, self.source):
            if existing:
                _need(not source.exists(), 'source-reappeared-after-retirement')
                self._check_bytes(archive, data)
                return existing
            claim = archive.parent / ('_axis-transfer-retire-' + transfer_id + '.md')
            expected_claim = {'transfer_id': transfer_id, 'acceptance': predecessor,
                              'sha256': data['sha256'], 'size': data['size'], 'archive': archive.name}
            if claim.exists() or claim.is_symlink():
                _need(not claim.is_symlink() and claim.is_file() and claim.stat().st_nlink == 1 and claim.stat().st_size <= 16384, 'unsafe-retirement-claim')
                _need(_read_claim(claim) == expected_claim, 'retirement-claim-collision')
            else:
                _need(not archive.exists(), 'archive-collision')
                with claim.open('x') as stream:
                    stream.write(_record_format().render('Axis transfer recovery claim', expected_claim))
                    stream.flush()
                    os.fsync(stream.fileno())
            if archive.exists():
                self._check_bytes(archive, data)
            else:
                _need(source.exists(), 'source-missing-without-retirement-evidence')
                _need(not list(archive.parent.glob('.' + archive.name + '.partial-*')), 'partial-retirement-held')
                self._check_bytes(source, data)
                self._publish_copy(source, archive, data)
            if source.exists():
                before = self._check_bytes(source, data)
                self._guard(self.source)
                now = source.lstat()
                _need((before.st_dev, before.st_ino, before.st_mtime_ns, before.st_ctime_ns) == (now.st_dev, now.st_ino, now.st_mtime_ns, now.st_ctime_ns), 'source-changed')
                source.unlink()
            # The exact accepted receipt plus retained archive proves recovery. Missing
            # source alone never does. Retirement is reversible by the source Main.
            return self._append(self.source, transfer_id, 'source-retired', data, predecessor, {'archive': str(archive.relative_to(self.source.root))})

    def status(self, transfer_id):
        _, data = self._base(transfer_id)
        states = ['prepared']
        copied = self._stage(self.source, transfer_id, 'copied-and-verified', data, {'project': self.source.project_id(), 'id': transfer_id})
        if copied:
            states.append('copied-and-verified')
        accepted = self._stage(self.destination, transfer_id, 'destination-accepted', data, {'project': self.source.project_id(), 'id': copied['id'] if copied else None})
        _need(not accepted or copied is not None, 'acceptance-without-copy')
        if accepted:
            states.append('destination-accepted')
        retired = self._stage(self.source, transfer_id, 'source-retired', data, {'project': self.destination.project_id(), 'id': accepted['id'] if accepted else None})
        _need(not retired or accepted is not None, 'retirement-without-acceptance')
        if retired:
            states.append('source-retired')
        return {'transfer_id': transfer_id, 'stages': states, 'source': data['source'], 'destination': data['destination'], 'sha256': data['sha256'], 'size': data['size']}
