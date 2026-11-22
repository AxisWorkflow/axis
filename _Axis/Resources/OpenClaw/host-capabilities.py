#!/usr/bin/env python3
"""OpenClaw host capability record for the strict chat gate: validate it, answer strict admission, and check it
against an installed OpenClaw package.

The record (axis-guardrails/host-capabilities.json) is closed, source-pinned data from static review. Strict
admission is unavailable for every build and carrier: a named build gives the reasons, and anything the record does
not name, or a record that fails validation, is unavailable too. Nothing here starts a host, reads host or account
configuration, or grants authority. `check` reads only the pinned files below an explicitly given package root,
read-only; it never opens an excluded file, follows a symlink or reads a file over 1 MB.

  host-capabilities.py [--record PATH] validate
  host-capabilities.py [--record PATH] admission --version V --carrier C
  host-capabilities.py [--record PATH] check --package-root DIR

Exit status: validate 0 valid, 1 invalid. admission 0, or 1 when the record is invalid. check 0 when the package is
the recorded build byte for byte and every static check holds, 2 when it is not, 1 on an invalid record or root.
Every admission answer is unavailable, whatever the exit status.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

SCHEMA = 'axis.openclaw-host-capabilities/v1'
PREDICATES = ('H1', 'H2', 'H3', 'H4', 'H5', 'tool-requester')
STATUSES = ('denied', 'partial', 'unavailable', 'met')
CARRIERS = ('embedded-external-user', 'cli-mcp', 'http-rpc', 'native-relay', 'worker')
REVOCATION = ('revoke-host-invocation', 'revoke-policy', 'revoke-axis-lease')
TOP_KEYS = {'schema', 'about', 'predicates', 'statuses', 'evidence', 'builds'}
BUILD_KEYS = {'package', 'version', 'pins', 'excluded', 'checks', 'carriers', 'final_effect_revocation'}
MAX_READ = 1000000
MAX_RECORD = 262144
DEFAULT_RECORD = Path(__file__).resolve().parent / 'axis-guardrails' / 'host-capabilities.json'
HEX64 = re.compile(r'[0-9a-f]{64}')
SEGMENT = re.compile(r'[A-Za-z0-9_][A-Za-z0-9._-]*')
CHECK_ID = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
VERSION = re.compile(r'[0-9A-Za-z][0-9A-Za-z.+-]*')
TAIL = ['final-effect-revocation:not-runnable', 'live-qualification-absent']


class Refused(Exception):
    pass


def unavailable(reasons):
    return {'strict_admission': 'unavailable', 'host_pass': False, 'execution_authority': False,
            'reasons': list(reasons)}


def _unique(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise ValueError('duplicate key: ' + key)
        out[key] = value
    return out


def load_record(path=DEFAULT_RECORD):
    """Return (record, errors). A symlinked, oversized, non-UTF-8, malformed or invalid record yields errors."""
    path = Path(path)
    try:
        info = os.lstat(path)
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            return None, ['record is not a regular file']
        if info.st_size > MAX_RECORD:
            return None, ['record exceeds %d bytes' % MAX_RECORD]
        with open(path, 'rb') as handle:
            raw = handle.read(MAX_RECORD + 1)
        record = json.loads(raw.decode('utf-8'), object_pairs_hook=_unique)
    except (OSError, UnicodeDecodeError, ValueError) as error:
        return None, ['record unreadable: %s' % error]
    return record, validate(record)


def _keys(value, keys):
    return isinstance(value, dict) and set(value) == set(keys)


def _text(value):
    return isinstance(value, str) and value.strip() != ''


def _count(value, low, high):
    return type(value) is int and low <= value <= high


def _path(value):
    if not isinstance(value, str):
        return False
    parts = value.split('/')
    return all(SEGMENT.fullmatch(p) and p not in ('.', '..') and p != 'node_modules' for p in parts)


def validate(record):
    """Closed-schema errors for a parsed record; an empty list means valid. Any unexpected shape is an error."""
    try:
        return _validate(record)
    except Exception as error:  # fail closed: a record the validator cannot walk is invalid
        return ['record shape not understood: %s' % type(error).__name__]


def _validate(record):
    errors = []
    need = lambda ok, message: ok or errors.append(message)
    if not _keys(record, TOP_KEYS):
        return ['top-level keys must be exactly %s' % sorted(TOP_KEYS)]
    need(record['schema'] == SCHEMA, 'unsupported schema')
    need(_text(record['about']), 'about must be text')
    need(_keys(record['predicates'], PREDICATES) and all(_text(v) for v in record['predicates'].values()),
         'predicates must name exactly %s' % list(PREDICATES))
    need(_keys(record['statuses'], STATUSES) and all(_text(v) for v in record['statuses'].values()),
         'statuses must name exactly %s' % list(STATUSES))
    evidence = record['evidence']
    need(isinstance(evidence, list) and evidence and all(
        _keys(e, ('name', 'sha256')) and _text(e['name']) and isinstance(e['sha256'], str) and HEX64.fullmatch(e['sha256'])
        for e in evidence), 'evidence must list name and sha256')
    builds = record['builds']
    if not (isinstance(builds, list) and builds):
        return errors + ['builds must be a non-empty list']
    versions = []
    for index, build in enumerate(builds):
        where = 'build %d' % index
        if not _keys(build, BUILD_KEYS):
            errors.append(where + ': keys must be exactly %s' % sorted(BUILD_KEYS))
            continue
        need(build['package'] == 'openclaw', where + ': package must be openclaw')
        need(isinstance(build['version'], str) and VERSION.fullmatch(build['version']), where + ': invalid version')
        versions.append(build['version'])
        errors.extend(where + ': ' + e for e in _validate_build(build))
    need(len(versions) == len(set(versions)), 'build versions must be unique')
    return errors


def _validate_build(build):
    errors = []
    need = lambda ok, message: ok or errors.append(message)
    pins, excluded, checks = build['pins'], build['excluded'], build['checks']
    pinned, outside = set(), set()
    if isinstance(pins, list) and pins:
        for pin in pins:
            ok = (_keys(pin, ('path', 'bytes', 'sha256')) and _path(pin['path']) and _count(pin['bytes'], 0, MAX_READ)
                  and isinstance(pin['sha256'], str) and HEX64.fullmatch(pin['sha256']))
            need(ok and pin['path'] not in pinned, 'invalid or duplicate pin: %r' % (pin,))
            if ok:
                pinned.add(pin['path'])
    else:
        errors.append('pins must be a non-empty list')
    if isinstance(excluded, list):
        for item in excluded:
            ok = (_keys(item, ('path', 'bytes', 'sha256', 'reason')) and _path(item['path'])
                  and _count(item['bytes'], MAX_READ + 1, 2 ** 40) and isinstance(item['sha256'], str)
                  and HEX64.fullmatch(item['sha256']) and _text(item['reason']))
            need(ok and item['path'] not in pinned and item['path'] not in outside, 'invalid excluded file: %r' % (item,))
            if ok:
                outside.add(item['path'])
    else:
        errors.append('excluded must be a list')
    used = set()
    if isinstance(checks, dict) and checks:
        for name, check in checks.items():
            ok = (CHECK_ID.fullmatch(name) and _keys(check, ('path', 'lines', 'present', 'absent'))
                  and check['path'] in pinned and isinstance(check['lines'], list) and len(check['lines']) == 2
                  and _count(check['lines'][0], 1, 10 ** 7) and _count(check['lines'][1], 1, 10 ** 7)
                  and 0 <= check['lines'][1] - check['lines'][0] <= 200
                  and isinstance(check['present'], list) and isinstance(check['absent'], list)
                  and check['present'] + check['absent'])
            if ok:
                for pattern in check['present'] + check['absent']:
                    try:
                        ok = ok and isinstance(pattern, str) and 0 < len(pattern) <= 300 and re.compile(pattern) is not None
                    except re.error:
                        ok = False
            need(ok, 'invalid check: %s' % name)
    else:
        errors.append('checks must be a non-empty object')
        checks = {}
    carriers = build['carriers']
    if _keys(carriers, CARRIERS):
        for name, carrier in carriers.items():
            if not (_keys(carrier, ('label', 'strict_admission', 'predicates')) and _text(carrier['label'])):
                errors.append('carrier %s: keys must be label, strict_admission and predicates' % name)
                continue
            need(carrier['strict_admission'] == 'unavailable', 'carrier %s: strict_admission must be unavailable' % name)
            predicates = carrier['predicates']
            if not _keys(predicates, PREDICATES):
                errors.append('carrier %s: predicates must be exactly %s' % (name, list(PREDICATES)))
                continue
            for key, value in predicates.items():
                status = value.get('status') if isinstance(value, dict) else None
                fields = ('status', 'evidence') if status == 'met' else ('status', 'missing', 'evidence')
                ok = status in STATUSES and _keys(value, fields) and isinstance(value['evidence'], list)
                ok = ok and all(isinstance(e, str) and e in checks for e in value['evidence'])
                ok = ok and len(set(value['evidence'])) == len(value['evidence'])
                ok = ok and (status == 'met' or _text(value['missing']))
                ok = ok and (status not in ('denied', 'partial', 'met') or value['evidence'])
                need(ok, 'carrier %s: invalid predicate %s' % (name, key))
                if ok:
                    used.update(value['evidence'])
    else:
        errors.append('carriers must be exactly %s' % list(CARRIERS))
    need(not set(checks) - used, 'checks no carrier cites: %s' % sorted(set(checks) - used))
    revocation = build['final_effect_revocation']
    need(_keys(revocation, REVOCATION) and all(
        _keys(v, ('result', 'reason')) and v['result'] == 'not-runnable' and _text(v['reason'])
        for v in revocation.values()), 'final_effect_revocation must record %s as not-runnable' % list(REVOCATION))
    return errors


def admission(record, version, carrier):
    """Strict admission for one carrier of one build. Always unavailable; the reasons say why."""
    if not isinstance(record, dict) or validate(record):
        return unavailable(['record-invalid'])
    build = next((b for b in record['builds'] if isinstance(version, str) and b['version'] == version), None)
    if build is None:
        return unavailable(['unknown-build'])
    entry = build['carriers'].get(carrier) if isinstance(carrier, str) else None
    if entry is None:
        return unavailable(['unknown-carrier'])
    statuses = [(key, entry['predicates'][key]['status']) for key in PREDICATES]
    return unavailable(['%s:%s' % pair for pair in statuses if pair[1] != 'met'] + TAIL)


def _read_pinned(root, relative):
    """Read one regular file below root without following any symlink; refuse files over MAX_READ."""
    current = root
    info = None
    for part in relative.split('/'):
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            raise Refused('missing')
        if stat.S_ISLNK(info.st_mode):
            raise Refused('symlink')
    if not stat.S_ISREG(info.st_mode):
        raise Refused('not a regular file')
    if info.st_size > MAX_READ:
        raise Refused('over the read limit')
    descriptor = os.open(current, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0))
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise Refused('not a regular file')
        chunks, size = [], 0
        while size <= MAX_READ:
            chunk = os.read(descriptor, 65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
    finally:
        os.close(descriptor)
    data = b''.join(chunks)
    if len(data) > MAX_READ:
        raise Refused('over the read limit')
    return data


def _excluded_size(root, relative):
    """Compare an excluded file by lstat only; its content is never opened."""
    current = root
    info = None
    for part in relative.split('/'):
        current = os.path.join(current, part)
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(info.st_mode):
            return None
    return info.st_size if stat.S_ISREG(info.st_mode) else None


def check(record, package_root):
    """Compare an installed package with the record, read-only. Returns (report, exit status)."""
    if not isinstance(record, dict) or validate(record):
        return {'record_valid': False, 'carriers': {c: unavailable(['record-invalid']) for c in CARRIERS}}, 1
    root = os.path.abspath(package_root)
    try:
        root_info = os.lstat(root)
    except OSError:
        root_info = None
    if root_info is None or stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        return {'record_valid': True, 'package_root': root, 'error': 'package root must be a real directory',
                'carriers': {c: unavailable(['unknown-build']) for c in CARRIERS}}, 1
    try:
        version = json.loads(_read_pinned(root, 'package.json').decode('utf-8')).get('version')
    except (Refused, OSError, UnicodeDecodeError, ValueError, AttributeError):
        version = None
    build = next((b for b in record['builds'] if isinstance(version, str) and b['version'] == version), None)
    report = {'record_valid': True, 'package_root': root, 'version_observed': version if isinstance(version, str) else None,
              'build_known': build is not None, 'host_pass': False, 'execution_authority': False}
    if build is None:
        report['installed_build_matches_record'] = False
        report['carriers'] = {c: unavailable(['unknown-build']) for c in CARRIERS}
        return report, 2
    contents, mismatched = {}, []
    for pin in build['pins']:
        try:
            data = _read_pinned(root, pin['path'])
        except (Refused, OSError) as error:
            mismatched.append({'path': pin['path'], 'reason': str(error) or type(error).__name__})
            continue
        contents[pin['path']] = data
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            mismatched.append({'path': pin['path'], 'reason': 'bytes or sha256 differ'})
    excluded = [{'path': e['path'], 'content_read': False, 'size_matches': _excluded_size(root, e['path']) == e['bytes']}
                for e in build['excluded']]
    failed = []
    for name, spec in sorted(build['checks'].items()):
        data = contents.get(spec['path'])
        try:
            lines = data.decode('utf-8').split('\n') if data is not None else []
        except UnicodeDecodeError:
            lines = []
        first, last = spec['lines']
        text = '\n'.join(lines[first - 1:last]) if last <= len(lines) else None
        held = (text is not None and all(re.search(p, text) for p in spec['present'])
                and not any(re.search(p, text) for p in spec['absent']))
        if not held:
            failed.append(name)
    matches = not mismatched and not failed and all(e['size_matches'] for e in excluded)
    report.update({
        'pins': {'total': len(build['pins']), 'matched': len(build['pins']) - len(mismatched), 'mismatched': mismatched},
        'excluded': excluded,
        'checks': {'total': len(build['checks']), 'observed': len(build['checks']) - len(failed), 'failed': failed},
        'installed_build_matches_record': matches,
        'carriers': {c: admission(record, version, c) if matches else unavailable(['installed-build-unverified'])
                     for c in CARRIERS},
    })
    return report, 0 if matches else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description='OpenClaw host capability record (strict admission stays unavailable).')
    parser.add_argument('--record', default=str(DEFAULT_RECORD))
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('validate')
    asked = commands.add_parser('admission')
    asked.add_argument('--version', required=True)
    asked.add_argument('--carrier', required=True)
    checked = commands.add_parser('check')
    checked.add_argument('--package-root', required=True)
    args = parser.parse_args(argv)
    record, errors = load_record(args.record)
    if args.command == 'validate':
        result, code = {'valid': not errors, 'errors': errors}, 1 if errors else 0
    elif args.command == 'admission':
        result = admission(record, args.version, args.carrier) if not errors else unavailable(['record-invalid'])
        code = 1 if errors else 0
    else:
        result, code = check(record if not errors else None, args.package_root)
    print(json.dumps(result, indent=1, sort_keys=True))
    return code


if __name__ == '__main__':
    sys.exit(main())
