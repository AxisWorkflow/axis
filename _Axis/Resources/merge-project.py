#!/usr/bin/env python3
"""Reviewed project absorption with complete content accounting and recoverable writes.

New transactions use schema 2. Old journals retain their original pinned engine.
No network, imported-code execution, Git-history merge, or credential migration.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import posixpath
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

LIMIT_FILES = 50000
LIMIT_BYTES = 512 * 1024 * 1024
FILE_LIMIT = 32 * 1024 * 1024
PLAN_LIMIT = 16 * 1024 * 1024
ID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z')
SHA = re.compile(r'[0-9a-f]{64}')
RECORDS = {'Audit', 'CX', 'Followups', 'Ideas', 'Logs', 'Notes', 'Reminders',
           'Reviews', 'Snapshots', 'Status', 'Supervision', 'Tasks',
           'Teams', 'Messages', 'Jobs', 'Schedules'}
HISTORY_ONLY = {'Snapshots', 'Teams', 'Messages', 'Jobs', 'Schedules'}
MUTABLE = {'PROJECT.md', 'PLAN.md', 'TASKS.md', 'NOTES.md', 'IDEAS.md',
           'FOLLOWUPS.md', 'REMINDERS.md', 'SUPERVISION.md', 'ENVIRONMENT.md',
           'INITIATIVES.md', 'SNAPSHOTS.md'}
INDEXES = {'TASKS.md', 'NOTES.md', 'IDEAS.md', 'FOLLOWUPS.md', 'REMINDERS.md'}
WIKI_ADMIN = {'Library-Schema.md', 'Library-Index.md', 'Input-Index.md',
              'Library-Activity.md', 'Library-Status.md'}
ENTRY = {'agents.md', 'claude.md', 'gemini.md'}
HOST_DIRS = {'.claude', '.codex', '.gemini', '.cursor', '.vscode'}
ATTESTATIONS = {'continuation_confirmed', 'source_authority', 'destination_authority',
                'external_archive_verified', 'external_jobs_stopped',
                'references_verified', 'wiki_reconciled', 'content_preserved'}
TEXT_SUFFIXES = {'.md', '.txt', '.html', '.htm', '.json', '.yaml', '.yml', '.csv',
                 '.js', '.ts', '.jsx', '.tsx', '.css', '.py', '.sh', '.rst'}


class Held(Exception):
    pass


def need(value, why):
    if not value:
        raise Held(why)


def encode(value):
    return (json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def identity(path):
    info = Path(path).lstat()
    return [info.st_dev, info.st_ino]


def plain(path, kind='file', missing=False, spelling=False):
    path = Path(os.path.abspath(path))
    current = Path(path.anchor)
    for part in path.parts[1:]:
        parent = current
        current /= part
        if spelling and parent.is_dir():
            need(not any(p.name.casefold() == part.casefold() and p.name != part
                         for p in parent.iterdir()), 'case alias path')
        try:
            info = current.lstat()
        except FileNotFoundError:
            need(missing, 'missing path')
            return path
        need(not stat.S_ISLNK(info.st_mode), 'linked path')
        if current != path:
            need(stat.S_ISDIR(info.st_mode), 'non-directory ancestor')
        else:
            valid = stat.S_ISDIR(info.st_mode) if kind == 'dir' else (
                stat.S_ISREG(info.st_mode) and info.st_nlink == 1)
            need(valid, 'unsafe path type')
    return path


def read(path, limit=FILE_LIMIT):
    plain(path)
    with Path(path).open('rb') as stream:
        data = stream.read(limit + 1)
    need(len(data) <= limit, 'file size limit')
    return data


def relative(name):
    need(isinstance(name, str) and name and '\\' not in name and not name.startswith('/'),
         'invalid relative path')
    parts = name.split('/')
    need(all(p not in ('', '.', '..') and p == unicodedata.normalize('NFC', p)
             and not p.endswith((' ', '.'))
             and not any(ord(c) < 32 or c in '<>:"|?*' for c in p) for p in parts),
         'unsafe path spelling')
    need(all(not re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?', p, re.I)
             for p in parts), 'reserved path')
    return name


def protected(name, suffixes=('_U', '_X')):
    return name.endswith(suffixes) or Path(name).stem.endswith(suffixes)


def project(root):
    need(not any(protected(p) for p in Path(os.path.abspath(root)).parts), 'protected project root')
    root = plain(root, 'dir', spelling=True)
    ids = re.findall(r'^project-id: (\S+)\s*$', read(root / '_Axis/PROJECT.md').decode(), re.M)
    versions = re.findall(r'^current-version: (\d+)\.(\d+)\s*$',
                          read(root / '_Axis/CHANGELOG.md').decode(), re.M)
    need(len(ids) == 1, 'missing or ambiguous project identity')
    need(len(versions) == 1, 'missing release identity')
    return root, ids[0], tuple(map(int, versions[0]))


def load_state(root, session):
    spec = importlib.util.spec_from_file_location('merge_axis_state', root / '_Axis/Resources/startup-state.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    engine = module.Session(root, session)
    engine.guard()
    need(engine.lease[2], 'Main only')
    return module, engine


def archive_root(root):
    """Resolve only this project's configured Archive; never create a missing mount."""
    text = read(root / '_Axis/SETTINGS.md').decode()
    match = re.search(r'^### Archive Location\s*\n(?:(?!^### ).)*?^\*\*Value:\*\* ([^\n]+)$',
                      text, re.M | re.S)
    value = match[1].strip() if match else '_Axis/Archive/'
    need('\\' not in value and '..' not in value.split('/'), 'invalid Archive location')
    if value.rstrip('/') == '_Axis/Archive':
        return plain(root / '_Axis/Archive', 'dir', missing=True)
    path = Path(os.path.expanduser(value))
    path = path if path.is_absolute() else root / path
    return plain(path, 'dir', spelling=True)


def destination_path(root, name):
    relative(name)
    if name == '_Axis/Archive' or name.startswith('_Axis/Archive/'):
        return archive_root(root) / Path(name).relative_to('_Axis/Archive')
    return root / name


def markers(root, own=None):
    folder = root / '_Axis/Agents'
    if not folder.exists():
        return []
    plain(folder, 'dir')
    return [p.name for p in folder.iterdir() if p.suffix == '.md' and p.name != str(own) + '.md']


def credential_name(name):
    return (name == '.env' or name.startswith('.env.') or name in (
                '.netrc', '.npmrc', '.pypirc', '.aws', '.azure', '.ssh', '.gnupg', 'auth.json', 'credentials')
            or (name.startswith('credentials') and name.endswith('.json')))


def inventory(root, exclude_child=None, source=False):
    """Content manifest; credential/protected material is never opened or named in output."""
    files, directories, nested, folded = {}, [], [], set()
    omissions = {'protected': False, 'credentials': False, 'developer': False}
    count = 0
    total = 0
    archive = archive_root(root)
    default_archive = root / '_Axis/Archive'

    def walk(folder, prefix):
        nonlocal count, total
        for path in sorted(folder.iterdir(), key=lambda p: p.name):
            name = prefix + path.name
            if exclude_child is not None and (path == exclude_child or exclude_child in path.parents):
                continue
            if protected(path.name):
                omissions['protected'] = True
                continue
            if credential_name(path.name):
                omissions['credentials'] = True
                continue
            if path == root / '_Dev':
                omissions['developer'] = True
                continue
            if path == root / '.git':
                continue
            if not source and path in (root / '_Temp', root / '_Trash'):
                continue
            if name == '_Axis/Secrets':
                plain(path, 'dir')
                # Metadata-only existence predicate; no names or values enter the manifest.
                if any(p.name != '.gitkeep' for p in path.iterdir()):
                    omissions['credentials'] = True
                continue
            if name in ('_Axis/Flags', '_Axis/Agents'):
                continue
            if archive != default_archive and path == archive:
                continue
            if name == '_Axis/Archive' and archive != default_archive:
                # The local placeholder is not a second Archive.
                continue
            need(not path.name.endswith('.lock'), 'lock residue requires quiescent recovery before merging')
            count += 1
            need(count <= LIMIT_FILES, 'inventory file limit')
            relative(name)
            key = unicodedata.normalize('NFC', name).casefold()
            need(key not in folded, 'case/NFC collision')
            folded.add(key)
            info = path.lstat()
            need(not stat.S_ISLNK(info.st_mode), 'linked inventory path')
            if stat.S_ISDIR(info.st_mode):
                if path != root and (path / '_Axis/PROJECT.md').is_file():
                    nested.append(name)
                    continue
                directories.append(name)
                walk(path, name + '/')
            else:
                data = read(path)
                total += len(data)
                need(total <= LIMIT_BYTES, 'inventory byte limit')
                files[name] = {'sha256': digest(data), 'bytes': len(data), 'mode': stat.S_IMODE(info.st_mode)}
    walk(root, '')
    if archive != default_archive:
        walk(archive, '_Axis/Archive/')
    return {'files': files, 'directories': directories, 'nested_projects': nested,
            'omissions': omissions, 'bytes': total, 'digest': digest(encode(files)),
            'archive': os.path.relpath(archive, root)}


def source_path(root, inv, name, quarantine=None):
    if name.startswith('_Axis/Archive/'):
        archive = Path(os.path.abspath(root / inv['archive']))
        if quarantine is not None and archive.is_relative_to(root):
            rel = archive.relative_to(root)
            if rel.parts and os.path.lexists(quarantine / rel.parts[0]):
                archive = quarantine / rel
        return plain(archive, 'dir', missing=True) / Path(name).relative_to('_Axis/Archive')
    top = name.split('/')[0]
    if quarantine is not None and os.path.lexists(quarantine / top):
        return quarantine / name
    return root / name


def git_kind(root):
    path = root / '.git'
    if not os.path.lexists(path):
        return 'none'
    info = path.lstat()
    need(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode),
         'linked Git worktree or non-directory .git is outside absorption scope')
    return 'independent'


def preview(dest, source, own=None, folder=None):
    dest, did, dver = project(dest)
    source, sid, sver = project(dest / source)
    need(dest != source and source not in dest.parents, 'destination cannot equal source or be inside it')
    need(did != sid, 'same project identity: replica reconciliation is not a merge')
    child = dest in source.parents
    need(folder is None or not child or folder == source.relative_to(dest).as_posix(),
         'nested source must remain at its current path')
    content = source.relative_to(dest).as_posix() if child else (folder or source.name)
    relative(content)
    need(child or '/' not in content, 'imported folder must be directly under continuation root')
    need(not any(p.startswith('.') or p in ('_Axis', '_Memos', '_Wiki', '_Temp', '_Trash', '_Dev')
                 or protected(p) for p in content.split('/')),
         'ordinary imported folder required')
    target = plain(dest / content, 'dir', missing=True, spelling=True)
    blockers = []
    if not child and os.path.lexists(target):
        blockers.append('imported folder name already exists; select a distinct folder in the plan')
    src = inventory(source, source=True)
    dst = inventory(dest, exclude_child=source if child else None)
    if archive_root(source) == archive_root(dest):
        blockers.append('source and destination share an Archive; resolve ownership before absorption')
    if dver != sver or dver < (3, 4):
        blockers.append('align both projects on the same merge-capable release first')
    if markers(source):
        blockers.append('source has session markers; quiesce through its owner, never infer death from age')
    if own and markers(dest, own):
        blockers.append('destination has other session markers')
    if src['nested_projects']:
        blockers.append('source has nested projects; explicitly resolve them before absorption')
    if src['omissions']['developer']:
        blockers.append('_Dev projects/folders are outside absorption scope')
    if src['omissions']['protected']:
        blockers.append('protected source content requires its owning procedure; no partial absorption')
    if src['omissions']['credentials']:
        blockers.append('credential material requires its owning procedure before source infrastructure removal')
    for root, label in ((source, 'source'), (dest, 'destination')):
        updates = root / '_Axis/Updates'
        if updates.exists():
            plain(updates, 'dir')
            if any(p.is_dir() and (p / 'start.json').exists() and not (p / 'consumed.json').exists()
                   for p in updates.iterdir()):
                blockers.append(label + ' has unconsumed update history')
        if status(root)['status'] != 'clear':
            blockers.append(label + ' has pending or retired merge state')
    return {'schema': 2, 'source': os.path.relpath(source, dest), 'destination': '.',
            'source_id': sid, 'destination_id': did, 'source_version': '.'.join(map(str, sver)),
            'destination_version': '.'.join(map(str, dver)), 'mode': 'absorb-child' if child else 'combine',
            'content_root': content, 'source_inventory': src, 'destination_inventory': dst,
            'source_git': git_kind(source), 'blockers': blockers,
            'limitations': ['Old Git history is abandoned after verified acceptance, never merged into the destination.',
                            'Wiki types, citations, indexes and overall synthesis require Main reconciliation.',
                            'Credentials, protected content, nested projects and _Dev require resolution before absorption.']}


def occupied_ids(root, exclude_child=None):
    result = set()
    bases = [root / '_Axis', root / '_Memos', archive_root(root)]
    seen = set()
    for base in bases:
        if base in seen or not base.exists():
            continue
        seen.add(base)
        for parent, dirs, names in os.walk(base, followlinks=False):
            dirs[:] = [d for d in dirs if d not in ('Secrets', '.git')
                       and (exclude_child is None or Path(parent) / d != exclude_child)]
            for name in dirs + names:
                result.update(ID.findall(name))
    claims = root / '_Temp'
    if claims.exists():
        result.update(p.name[:-8] for p in claims.iterdir() if p.name.endswith('.tsclaim') and ID.fullmatch(p.name[:-8]))
    return result


def allocate_ids(root, view, txid):
    originals = {value for path in view['source_inventory']['files'] for value in ID.findall(path)}
    occupied = occupied_ids(root)
    occupied.add(txid)
    # Preserve every free original before allocating offsets for collisions.
    used = occupied | originals
    answer = {}
    for old in sorted(originals):
        value = old
        if old in occupied:
            when = dt.datetime.strptime(old, '%Y.%m.%d.%H.%M.%S.%fZ')
            for _ in range(1000000):
                when += dt.timedelta(milliseconds=1)
                value = when.strftime('%Y.%m.%d.%H.%M.%S.') + f'{when.microsecond // 1000:03d}Z'
                if value not in used:
                    break
            else:
                raise Held('timestamp collision bound')
        answer[old] = value
        used.add(value)
    return answer


def remap_ids(value, mapping):
    return ID.sub(lambda m: mapping.get(m[0], m[0]), value)


def kind(name):
    parts = name.split('/')
    if Path(name).name == '.gitkeep' and parts[0] in ('_Axis', '_Memos', '_Wiki'):
        return 'evidence'
    if parts[0] == '_Axis':
        tail = parts[2:] if len(parts) > 1 and parts[1] == 'Archive' else parts[1:]
        if len(tail) == 4 and tail[0] == 'Imports' and ID.fullmatch(tail[1]) and tail[2] in HISTORY_ONLY:
            tail = tail[2:]
        if len(tail) == 2 and tail[0] in RECORDS and ID.fullmatch(Path(tail[1]).stem) and tail[1].endswith('.md'):
            return 'record'
        if len(parts) == 2 and parts[1] in INDEXES:
            return 'index'
        return 'evidence'
    if parts[0] == '_Memos':
        return 'memo'
    if parts[:2] == ['_Wiki', '_Inbox']:
        return 'raw-wiki'
    if parts[0] == '_Wiki':
        return 'wiki'
    if any(p.casefold() in ENTRY for p in parts) or parts[0] in HOST_DIRS:
        return 'inert'
    return 'content'


def unique_path(root, proposed, used):
    candidate = proposed
    n = 1
    while candidate.casefold() in used or os.path.lexists(destination_path(root, candidate)):
        p = Path(proposed)
        n += 1
        candidate = (p.parent / (p.stem + '-imported-' + str(n) + p.suffix)).as_posix()
    used.add(candidate.casefold())
    return candidate


def layout(root, view, txid, ids):
    """Complete source-to-destination map; opaque runtime machinery stays inert evidence."""
    mappings = {}
    folder = view['content_root']
    used = set()
    top_map = {}
    source_tops = {p.split('/')[0] for p in view['source_inventory']['files']}
    source_tops.update(p.split('/')[0] for p in view['source_inventory']['directories'])
    top_dirs = {p for p in view['source_inventory']['directories'] if '/' not in p}
    inert_folder = 'Imported-instructions'
    number = 1
    while inert_folder.casefold() in {p.casefold() for p in source_tops}:
        number += 1
        inert_folder = 'Imported-instructions-' + str(number)
    ordinary = {p.casefold() for p in source_tops if not p.startswith(('_', '.'))}
    for top in sorted(source_tops):
        if top in top_dirs and top.startswith('_') and top not in ('_Axis', '_Memos', '_Wiki'):
            base = top.lstrip('_') or 'Imported-content'
            value = base
            n = 1
            while value.casefold() in ordinary:
                n += 1
                value = base + '-imported-' + str(n)
            ordinary.add(value.casefold())
            top_map[top] = value
    for name, info in view['source_inventory']['files'].items():
        category = kind(name)
        parts = name.split('/')
        renamed = remap_ids(name, ids)
        if category == 'record':
            archived = parts[1] == 'Archive'
            family = parts[-2]
            filename = remap_ids(parts[-1], ids)
            if family in HISTORY_ONLY:
                target = '_Axis/Archive/Imports/' + txid + '/' + family + '/' + filename
            else:
                target = '_Axis/' + ('Archive/' if archived else '') + family + '/' + filename
        elif category == 'memo':
            target = renamed
            # Current timestamp names have already been globally allocated; legacy names remain meaningful.
            if not ID.search(parts[-1]):
                target = unique_path(root, target, used)
        elif category in ('wiki', 'raw-wiki'):
            target = unique_path(root, renamed, used)
        elif category == 'index':
            target = name
        elif category == 'evidence':
            existing = destination_path(root, name)
            project_specific = name.startswith('_Axis/Wiki/') or name in {
                '_Axis/' + p for p in MUTABLE | {'SETTINGS.md', 'INSTRUCTIONS.md', 'ENVIRONMENT.md'}}
            if not project_specific and existing.is_file() and digest(read(existing)) == info['sha256']:
                target = name
            else:
                target = '_Axis/Merges/' + txid + '/source/' + renamed + '.source'
        elif category == 'inert':
            safe = name.lstrip('.')
            target = folder + '/' + inert_folder + '/' + safe
            if any(p.casefold() in ENTRY for p in parts):
                target += '.txt'
        else:
            target = folder + '/' + '/'.join([top_map.get(parts[0], parts[0]), *parts[1:]])
        mappings[name] = target
        if category not in ('evidence', 'index', 'wiki', 'raw-wiki') and not (
                category == 'memo' and not ID.search(parts[-1])):
            need(target.casefold() not in used, 'import destination collision')
            used.add(target.casefold())
    directories = {folder}
    for name in view['source_inventory']['directories']:
        parts = name.split('/')
        if parts[0] not in ('_Axis', '_Memos', '_Wiki') and parts[0] not in HOST_DIRS:
            directories.add(folder + '/' + '/'.join([top_map.get(parts[0], parts[0]), *parts[1:]]))
    for target in mappings.values():
        if '/objects/' not in target:
            parent = Path(target).parent
            while parent.as_posix() != '.':
                directories.add(parent.as_posix())
                parent = parent.parent
    return mappings, sorted(directories, key=lambda x: (x.count('/'), x))


def rewrite(data, source_name, target_name, source, root, view, mappings, ids):
    """Repair known file/record references without changing historical date/status fields."""
    if Path(source_name).suffix.lower() not in TEXT_SUFFIXES:
        return data
    try:
        text = data.decode('utf-8')
    except UnicodeError:
        return data
    lookups = {}
    for old, new in mappings.items():
        lookups[os.path.abspath(source_path(source, view['source_inventory'], old))] = new
        lookups[os.path.abspath(source / old)] = new
    old_file = source_path(source, view['source_inventory'], source_name)
    new_file = destination_path(root, target_name)

    def link(value):
        angle = value.startswith('<') and value.endswith('>')
        raw = value[1:-1] if angle else value
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc or not parsed.path:
            return value
        path = unquote(parsed.path)
        absolute = os.path.abspath(old_file.parent / path)
        mapped = mappings.get(path.lstrip('/')) if path.startswith('/') else None
        mapped = mapped or lookups.get(absolute)
        if mapped is None:
            # Axis Archive links use a logical path even with an external Archive.
            logical = os.path.abspath((source / source_name).parent / path)
            mapped = lookups.get(logical)
        target = destination_path(root, mapped) if mapped else Path(absolute)
        if not mapped and not target.exists():
            return value
        result = os.path.relpath(target, new_file.parent).replace(os.sep, '/')
        result = quote(result, safe='/@:+~.-_')
        if parsed.query:
            result += '?' + parsed.query
        if parsed.fragment:
            result += '#' + parsed.fragment
        return '<' + result + '>' if angle else result

    text = re.sub(r'(!?\[[^\]\n]*\]\()(<[^>\n]+>|[^\s)]+)([^\n)]*\))',
                  lambda m: m[1] + link(m[2]) + m[3], text)
    text = re.sub(r'(^\s*\[[^]\n]+\]:\s*)(<[^>\n]+>|\S+)',
                  lambda m: m[1] + link(m[2]), text, flags=re.M)

    def wikilink(match):
        value = match[1]
        path, sep, label = value.partition('|')
        stem, mark, fragment = path.partition('#')
        candidates = [name for name in mappings if name.startswith('_Wiki/')
                      and (name[6:] == stem or name[6:] == stem + '.md'
                           or Path(name).stem == stem)]
        if len(candidates) != 1:
            return match[0]
        target = mappings[candidates[0]]
        if not target.startswith('_Wiki/'):
            return match[0]
        new = target[6:]
        if new.endswith('.md') and not stem.endswith('.md'):
            new = new[:-3]
        return '[[' + new + (mark + fragment if mark else '') + (sep + label if sep else '') + ']]'
    text = re.sub(r'\[\[([^]\n]+)\]\]', wikilink, text)
    # Exact path tokens and quoted file paths, including ordinary source references.
    for old in sorted(mappings, key=len, reverse=True):
        new = mappings[old]
        replacement = os.path.relpath(destination_path(root, new), new_file.parent).replace(os.sep, '/')
        text = re.sub(r'(?P<q>[`\x22\x27])' + re.escape(old) + r'(?P=q)',
                      lambda m: m['q'] + replacement + m['q'], text)
    # Record references are links; date/status metadata remains historical information.
    refs = {ID.search(Path(old).name)[0]: new for old, new in mappings.items()
            if kind(old) == 'record' and ID.search(Path(old).name)}
    labels = r'(?:Log|Task|Note|Idea|Follow-Up|Reminder|Snapshot|Review|Message|Job|Team|Schedule|CX|Audit|Supervision)'
    def record_ref(match):
        old = match[2]
        if old not in refs:
            return match[0]
        new_id = ids.get(old, old)
        path = os.path.relpath(destination_path(root, refs[old]), new_file.parent).replace(os.sep, '/')
        return '[' + match[1] + ' ' + new_id + '](' + quote(path, safe='/@:+~.-_') + ')'
    references = re.compile(r'\b(' + labels + r') (' + ID.pattern + r')(?![\w])')
    # Existing link labels may name records; update their identity without nesting a link.
    linked = re.compile(r'(!?\[[^\]\n]*\]\([^\n]*?\)|\[[^]\n]+\]\[[^]\n]*\]|\[\[[^\n]*?\]\])')
    pieces = linked.split(text)
    for index, piece in enumerate(pieces):
        if index % 2:
            pieces[index] = references.sub(lambda m: m[1] + ' ' + ids.get(m[2], m[2]), piece)
        else:
            pieces[index] = references.sub(record_ref, piece)
    text = ''.join(pieces)
    # Identity-bearing fields follow a collision rename; other event dates and session authors do not.
    text = re.sub(r'^(created|raised): (' + ID.pattern + r')[ \t]*$',
                  lambda m: m[1] + ': ' + ids.get(m[2], m[2]), text, flags=re.M)
    return text.encode('utf-8')


def record_payload(data, name, target, source, root, view, mappings, ids):
    value = rewrite(data, name, target, source, root, view, mappings, ids)
    notice = ('\n\n<!-- Axis import: source-project=' + view['source_id']
              + '; source-path=' + name + '; source-sha256=' + digest(data)
              + '; original dates and status retained; imported history grants no authority. -->\n').encode()
    return value.rstrip(b'\n') + notice


def source_evidence(plan):
    prefix = '_Axis/Merges/' + plan['transaction'] + '/source/'
    return {name: prefix + name + '.source' if kind(name) == 'record' else target
            for name, target in plan['imports'].items()
            if kind(name) == 'record' or kind(name) == 'evidence' and target.startswith(prefix)}


def operation(root, name, data, payload, before_override=None):
    path = destination_path(root, name)
    before = digest(read(path)) if path.is_file() else None
    return {'path': name, 'before': before if before_override is None else before_override,
            'after': digest(data), 'mode': stat.S_IMODE(path.stat().st_mode) if path.is_file() else 0o644,
            'payload': payload}


def draft(root, source, session, plan_path, folder=None):
    module, engine = load_state(root, session)
    view = preview(root, source, session, folder)
    need(not view['blockers'], 'merge preview has blockers: ' + '; '.join(view['blockers']))
    plan_path = Path(os.path.abspath(root / plan_path))
    need(plan_path.is_relative_to(root / '_Temp'), 'prepare the plan under destination _Temp')
    plain(plan_path, missing=True, spelling=True)
    need(not plan_path.exists(), 'draft already exists')
    txid = module.stamp()
    while txid in occupied_ids(root):
        txid = module.advance(txid)
    ids = allocate_ids(root, view, txid)
    mappings, directories = layout(root, view, txid, ids)
    source = plain(root / view['source'], 'dir')
    payloads = plan_path.parent / 'payloads'
    need(not payloads.exists(), 'payload directory already exists')
    payloads.mkdir(parents=True)
    ops = []
    for name, target in mappings.items():
        category = kind(name)
        if category == 'evidence':
            continue
        original = read(source_path(source, view['source_inventory'], name))
        if category == 'raw-wiki':
            data = original
        elif category == 'record':
            data = record_payload(original, name, target, source, root, view, mappings, ids)
        else:
            data = rewrite(original, name, target, source, root, view, mappings, ids)
        if category == 'index':
            old = read(destination_path(root, target))
            text = data.decode()
            family = name.split('/')[-1][:-3].capitalize()
            ids_for_index = {plan_id for old_name in mappings if kind(old_name) == 'record'
                             and old_name.split('/')[-2] == family
                             for plan_id in (ids.get(Path(old_name).stem, Path(old_name).stem),)}
            # Empty template examples are scaffolding, not imported work records.
            sections = [part for part in re.split(r'(?m)(?=^## )', text)
                        if part.startswith('## ') and set(ID.findall(part)) & ids_for_index]
            if not sections:
                continue
            data = old.rstrip(b'\n') + b'\n\n' + '\n'.join(sections).encode()
        p = destination_path(root, target)
        if p.is_file() and read(p) == data:
            continue
        filename = 'payloads/' + str(len(ops))
        (plan_path.parent / filename).write_bytes(data)
        op = operation(root, target, data, filename)
        if category in ('content', 'inert', 'raw-wiki', 'wiki', 'memo', 'record') and op['before'] is None:
            op['mode'] = view['source_inventory']['files'][name]['mode']
        ops.append(op)
    plan = {'schema': 2, 'transaction': txid, 'preview': view, 'engine_sha256': digest(Path(__file__).read_bytes()),
            'id_map': ids, 'imports': mappings, 'directories': directories, 'operations': ops,
            **{name: False for name in ATTESTATIONS}}
    engine.guard()
    plan_path.write_bytes(encode(plan))
    return {'status': 'draft-awaiting-main-review', 'transaction': txid, 'plan': str(plan_path.relative_to(root)),
            'records': sum(kind(p) == 'record' for p in mappings), 'operations': len(ops),
            'next': 'Reconcile Project/Plan, Memo/Wiki/index references and exact payloads; set attestations only after review, then obtain one concrete User approval.'}


def once(path, data):
    plain(path, missing=True)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    try:
        with os.fdopen(fd, 'wb', closefd=False) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    finally:
        os.close(fd)
    need(read(path, max(FILE_LIMIT, len(data))) == data, 'write readback failed')


def mkdirs(path):
    path = Path(os.path.abspath(path))
    plain(path, 'dir', missing=True, spelling=True)
    path.mkdir(parents=True, exist_ok=True)
    plain(path, 'dir', spelling=True)


def allowed(name, txid=None):
    relative(name)
    parts = name.split('/')
    need(not any(protected(p) for p in parts), 'protected destination')
    need('.git' not in parts and not any(p.casefold() in ENTRY for p in parts), 'entry files or Git metadata are protected')
    if parts[0] == '_Axis':
        if len(parts) == 2:
            need(parts[1] in MUTABLE, 'protected Axis path')
        elif parts[1] == 'Wiki':
            need(len(parts) == 3 and parts[2] in WIKI_ADMIN, 'unsupported Wiki administration path')
        elif parts[1] == 'Archive':
            need(len(parts) >= 4 and parts[-1].endswith('.md') and ID.fullmatch(Path(parts[-1]).stem),
                 'new archived record required')
        else:
            need(len(parts) == 3 and parts[1] in RECORDS - HISTORY_ONLY
                 and parts[-1].endswith('.md') and ID.fullmatch(Path(parts[-1]).stem), 'protected Axis path')
    elif parts[0].startswith('_'):
        need(parts[0] in ('_Memos', '_Wiki'), 'unsupported project root')
    need('_Axis' not in parts[1:] and not any(p in HOST_DIRS for p in parts), 'nested control tree excluded')
    need(not any(credential_name(p) for p in parts), 'credential destination excluded')


def target_hash(root, name, source=None):
    allowed(name)
    path = destination_path(root, name)
    need(not path.is_relative_to(archive_root(root)) or name.startswith('_Axis/Archive/'),
         'configured Archive requires its logical immutable-record path')
    plain(path, missing=True, spelling=True)
    for parent in path.parents:
        if parent in (root, archive_root(root)):
            break
        if parent == source:
            continue
        need(not (parent / '_Axis/PROJECT.md').exists(), 'destination crosses a nested project')
    return digest(read(path)) if path.exists() else None


def flag_bytes(start):
    return encode({'schema': 1, 'transaction': start['transaction'], 'plan_sha256': start['plan_sha256'],
                   'destination_id': start['preview']['destination_id'], 'source_id': start['preview']['source_id']})


def _without_approval(inv, name):
    inv = json.loads(json.dumps(inv))
    inv['files'].pop(name, None)
    inv['bytes'] = sum(v['bytes'] for v in inv['files'].values())
    inv['digest'] = digest(encode(inv['files']))
    return inv


def physical_manifest(root):
    """Exact removable tree; Git is opaque because its history is deliberately abandoned."""
    root = plain(root, 'dir')
    result = {}
    count = 0

    def walk(folder):
        nonlocal count
        for path in sorted(folder.iterdir(), key=lambda p: p.name):
            count += 1
            need(count <= LIMIT_FILES + 1000, 'physical inventory bound')
            name = path.relative_to(root).as_posix()
            info = path.lstat()
            need(not stat.S_ISLNK(info.st_mode), 'linked physical inventory path')
            if path.name == '.git':
                plain(path, 'dir')
                result[name] = {'kind': 'git', 'identity': identity(path)}
            elif path.is_dir():
                result[name] = {'kind': 'dir'}
                walk(path)
            else:
                result[name] = {'kind': 'file', 'sha256': digest(read(path)),
                                'mode': stat.S_IMODE(info.st_mode)}
    walk(root)
    return result


def check_plan(root, source, plan, base):
    view = plan['preview']
    txid = plan['transaction']
    need(set(plan) == {'schema', 'transaction', 'preview', 'engine_sha256', 'id_map', 'imports',
                       'directories', 'operations'} | ATTESTATIONS, 'plan schema')
    need(plan['schema'] == 2 and ID.fullmatch(txid), 'plan version or transaction')
    for name in ATTESTATIONS:
        need(plan[name] is True, 'Main must establish ' + name)
    need(plan['id_map'] == allocate_ids(root, view, txid), 'timestamp allocation differs from original/minimal collision map')
    mappings = plan['imports']
    files = view['source_inventory']['files']
    need(set(mappings) == set(files), 'every source file needs a disposition')
    expected, _ = layout(root, view, txid, plan['id_map'])
    for name, target in mappings.items():
        relative(target)
        category = kind(name)
        if category not in ('wiki', 'raw-wiki'):
            need(target == expected[name], 'source disposition changed: ' + name)
        else:
            need(target.startswith('_Wiki/'), 'Wiki content must join the destination Wiki')
            need((category == 'raw-wiki') == target.startswith('_Wiki/_Inbox/'), 'raw Wiki boundary')
    ops = plan['operations']
    need(isinstance(ops, list) and 0 < len(ops) <= LIMIT_FILES, 'operation count')
    by_path = {}
    objects = {}
    for op in ops:
        need(set(op) == {'path', 'before', 'after', 'mode', 'payload'}, 'operation schema')
        name = op['path']
        allowed(name)
        need(name.casefold() not in {p.casefold() for p in by_path}, 'duplicate destination')
        need(type(op['mode']) is int and op['mode'] in (0o600, 0o644, 0o755), 'unsupported output mode')
        need(op['before'] is None or isinstance(op['before'], str) and SHA.fullmatch(op['before']), 'invalid preimage hash')
        relative(op['payload'])
        need(op['payload'].startswith('payloads/'), 'payload must be in prepared payloads')
        data = read(base / op['payload'])
        need(digest(data) == op['after'], 'approved payload changed')
        before = target_hash(root, name, source)
        need(before == op['before'], 'destination changed')
        need(before != op['after'], 'no-op operation')
        if name.startswith(('_Memos/', '_Axis/Archive/')) or re.fullmatch(r'_Axis/[^/]+/' + ID.pattern + r'\.md', name):
            need(before is None, 'never overwrite destination records or Memos')
        if name.startswith('_Wiki/_Inbox/'):
            need(before is None, 'existing raw Wiki input is immutable')
        if name == '_Axis/PROJECT.md':
            need(re.findall(r'^project-id: (\S+)\s*$', data.decode(), re.M) == [view['destination_id']],
                 'destination project identity must survive')
        if name in ('_Axis/Wiki/Library-Activity.md', '_Axis/Wiki/Library-Status.md') and before:
            need(data.startswith(read(destination_path(root, name))), 'Wiki history is append-only')
        # No operation crosses another active project, or writes source infrastructure.
        for parent in destination_path(root, name).parents:
            if parent == root or parent == archive_root(root):
                break
            if parent == source and view['mode'] == 'absorb-child':
                continue
            need(not (parent / '_Axis/PROJECT.md').exists(), 'destination crosses a nested project')
        if view['mode'] == 'absorb-child' and name.startswith(view['content_root'] + '/'):
            top = name[len(view['content_root']) + 1:].split('/')[0]
            need(not top.startswith('_') and top != '.git' and top.casefold() not in ENTRY,
                 'source infrastructure is not a destination')
        if before:
            objects[before] = read(destination_path(root, name))
        objects[op['after']] = data
        by_path[name] = {**op, 'before_mode': stat.S_IMODE(destination_path(root, name).stat().st_mode) if before else None}
    for name, target in mappings.items():
        category = kind(name)
        original = read(source_path(source, view['source_inventory'], name))
        need(digest(original) == files[name]['sha256'], 'source changed during preservation')
        objects[files[name]['sha256']] = original
        if category == 'evidence':
            continue
        expected_data = (record_payload(original, name, target, source, root, view, mappings, plan['id_map'])
                         if category == 'record' else original if category == 'raw-wiki'
                         else rewrite(original, name, target, source, root, view, mappings, plan['id_map']))
        after = objects[by_path[target]['after']] if target in by_path else read(destination_path(root, target))
        if category not in ('wiki', 'index'):
            need(after == expected_data, 'source content or full record text was lost: ' + name)
        if category == 'index':
            # Main may reconcile index structure; every copied detail must remain reachable.
            for old, new in mappings.items():
                if kind(old) == 'record' and old.split('/')[-2] == name.split('/')[-1][:-3].capitalize():
                    need(Path(new).stem.encode() in after, 'imported record missing from index')
    need(sum(map(len, objects.values())) <= LIMIT_BYTES * 2, 'preservation byte limit')
    need(isinstance(plan['directories'], list) and len(plan['directories']) <= LIMIT_FILES, 'directory bound')
    for name in plan['directories']:
        relative(name)
        need(not any(protected(p) or p in ('.git',) for p in name.split('/')), 'unsafe directory')
        need(name == view['content_root'] or name.startswith(view['content_root'] + '/')
             or name in ('_Axis', '_Axis/Archive', '_Memos', '_Wiki')
             or any(p.startswith(name + '/') for p in mappings.values() if '/objects/' not in p),
             'unrelated directory')
    return list(by_path.values()), objects


def prepare(root, session, plan_path, approval):
    _, engine = load_state(root, session)
    plan_path = plain(root / plan_path)
    need(plan_path.is_relative_to(root / '_Temp'), 'prepare the plan under destination _Temp')
    plan = json.loads(read(plan_path, PLAN_LIMIT))
    need(plan.get('schema') == 2, 'new plans require absorption schema 2')
    need(approval == plan['transaction'], 'approval Log must use the proposed transaction identity')
    need(plan['engine_sha256'] == digest(Path(__file__).read_bytes()), 'plan engine identity')
    view = plan['preview']
    fresh = preview(root, view['source'], session, view['content_root'])
    need(not fresh['blockers'], 'merge preview has blockers')
    approval_path = '_Axis/Logs/' + approval + '.md'
    need(approval_path not in view['destination_inventory']['files'], 'approval must be a new scoped Log')
    fresh['destination_inventory'] = _without_approval(fresh['destination_inventory'], approval_path)
    need(fresh == view, 'source or destination changed since preview')
    auth = read(root / approval_path).decode()
    ph = digest(encode(plan))
    need('\nmerge-plan-sha256: ' + ph + '\n' in auth, 'approval Log must bind the exact canonical plan digest')
    need('\nmerge-source-id: ' + view['source_id'] + '\n' in auth
         and '\nmerge-destination-id: ' + view['destination_id'] + '\n' in auth, 'approval project identity binding')
    source = plain(root / view['source'], 'dir')
    operations, objects = check_plan(root, source, plan, plan_path.parent)
    tx = root / '_Axis/Merges' / approval
    need(not os.path.lexists(tx), 'transaction exists')
    engine.guard()
    mkdirs(tx / 'objects')
    for sha, data in objects.items():
        engine.guard()
        once(tx / 'objects' / sha, data)
    for name, target in source_evidence(plan).items():
        engine.guard()
        path = root / target
        mkdirs(path.parent)
        once(path, objects[view['source_inventory']['files'][name]['sha256']])
    removals = [p.name for p in source.iterdir() if (p.is_dir() and p.name.startswith('_')) or p.name == '.git'
                or p.name.casefold() in ENTRY or p.name in HOST_DIRS]
    quarantine = '_Temp/MergeRecovery-' + approval
    need(not os.path.lexists(root / quarantine), 'recovery path already exists')
    start = {'schema': 2, 'transaction': approval, 'plan_sha256': ph, 'approval_log': approval,
             'preview': view, 'operations': operations, 'engine_sha256': plan['engine_sha256'],
             'session': session, 'recovery': quarantine,
             'source_identity': identity(source),
             'source_tree': physical_manifest(source),
             'retirement': os.path.relpath(source.with_name('.' + source.name + '.axis-absorb-' + approval), root),
             'removals': {name: identity(source / name) for name in sorted(removals)},
             'created_directories': [name for name in plan['directories'] if not destination_path(root, name).exists()]}
    start['source_tree']['_Axis/Flags/merge-pending'] = {'kind': 'file', 'sha256': digest(flag_bytes(start)), 'mode': 0o600}
    once(tx / 'start.json', encode(start))
    once(tx / 'engine.py', Path(__file__).read_bytes())
    once(tx / 'plan.json', encode(plan))
    need(inventory(source, source=True) == view['source_inventory'], 'source changed after preservation')
    engine.guard()
    once(root / '_Axis/Flags/merge-pending', flag_bytes(start))
    once(source / '_Axis/Flags/merge-pending', flag_bytes(start))
    need(not markers(source) and inventory(source, source=True) == view['source_inventory'],
         'source changed while installing barriers; preserve and reconcile')
    return {'status': 'prepared', 'transaction': approval, 'plan_sha256': ph}


def transaction(root, session, txid):
    module, engine = load_state(root, session)
    need(ID.fullmatch(txid), 'transaction identity')
    tx = plain(root / '_Axis/Merges' / txid, 'dir')
    start = json.loads(read(tx / 'start.json', PLAN_LIMIT))
    need(start.get('schema') == 2, 'historical merge: use its original pinned engine and original state rules')
    need(start['transaction'] == txid, 'transaction binding')
    plan_bytes = read(tx / 'plan.json', PLAN_LIMIT)
    need(digest(plan_bytes) == start['plan_sha256'], 'plan changed')
    plan = json.loads(plan_bytes)
    need(start['preview'] == plan['preview'] and start['engine_sha256'] == plan['engine_sha256'], 'transaction differs from approved plan')
    need([{k: op[k] for k in ('path', 'before', 'after', 'mode', 'payload')} for op in start['operations']]
         == plan['operations'], 'transaction operations changed')
    need(digest(read(tx / 'engine.py')) == start['engine_sha256']
         and digest(Path(__file__).read_bytes()) == start['engine_sha256'], 'run the pinned merge engine')
    auth = read(root / '_Axis/Logs' / (txid + '.md')).decode()
    need('\nmerge-plan-sha256: ' + start['plan_sha256'] + '\n' in auth, 'approval binding changed')
    need(project(root)[1] == start['preview']['destination_id'], 'destination identity changed')
    for op in start['operations']:
        allowed(op['path'])
        need(digest(read(tx / 'objects' / op['after'])) == op['after'], 'payload changed')
        if op['before']:
            need(digest(read(tx / 'objects' / op['before'])) == op['before'], 'preimage changed')
    for item in start['preview']['source_inventory']['files'].values():
        need(digest(read(tx / 'objects' / item['sha256'])) == item['sha256'], 'preserved source object changed')
    for name, target in source_evidence(plan).items():
        need(digest(read(root / target)) == start['preview']['source_inventory']['files'][name]['sha256'],
             'named source evidence changed')
    return module, engine, tx, start, Path(os.path.abspath(root / start['preview']['source']))


def source_guard(root, start, source, ephemeral=None):
    source = Path(os.path.abspath(source))
    view = start['preview']
    need(plain(source, 'dir') == source and identity(source) == start['source_identity'], 'source root identity changed')
    recovery = root / start['recovery']
    q = recovery / 'quarantine'
    if view['mode'] == 'combine':
        need(project(source)[1] == view['source_id'] and not markers(source), 'source identity or quiescence lost')
        need(inventory(source, source=True) == view['source_inventory'], 'source changed')
        need(read(source / '_Axis/Flags/merge-pending') == flag_bytes(start), 'source maintenance barrier changed')
        need(physical_manifest(source) == start['source_tree'], 'source physical state changed')
        return
    axis = q / '_Axis' if (q / '_Axis').exists() else source / '_Axis'
    if axis == q / '_Axis':
        need(not os.path.lexists(source / '_Axis'), 'source infrastructure reappeared')
    need(not any(p.suffix == '.md' for p in (axis / 'Agents').iterdir()), 'source quiescence lost')
    need(read(axis / 'Flags/merge-pending') == flag_bytes(start), 'source maintenance barrier changed')
    current = physical_manifest(source)
    if q.exists():
        for name, item in physical_manifest(q).items():
            need(name not in current, 'source and quarantine overlap')
            current[name] = item
    baseline = start['source_tree']
    allowed = {name: [item] for name, item in baseline.items()}
    for op in start['operations']:
        if op['path'].startswith(view['content_root'] + '/'):
            name = op['path'][len(view['content_root']) + 1:]
            allowed.setdefault(name, []).append({'kind': 'file', 'sha256': op['after'], 'mode': op['mode']})
    plan = json.loads(read(root / '_Axis/Merges' / start['transaction'] / 'plan.json', PLAN_LIMIT))
    for name in plan['directories']:
        if name.startswith(view['content_root'] + '/'):
            allowed.setdefault(name[len(view['content_root']) + 1:], []).append({'kind': 'dir'})
    for path, item in (ephemeral or {}).items():
        path = Path(path)
        if path.is_relative_to(source):
            allowed.setdefault(path.relative_to(source).as_posix(), []).append(item)
    need(set(baseline) <= set(current) <= set(allowed), 'source contains missing or unplanned paths')
    need(all(item in allowed[name] for name, item in current.items()),
         'source changed outside exact before/after state')
    # A configured external Archive is not moved or deleted with the source folder.
    for name, item in view['source_inventory']['files'].items():
        p = source_path(source, view['source_inventory'], name, q)
        if not p.is_relative_to(source) and not p.is_relative_to(q):
            need(digest(read(p)) == item['sha256'], 'source Archive changed')
    for name, before in start['removals'].items():
        a, b = source / name, q / name
        need(os.path.lexists(a) != os.path.lexists(b), 'ambiguous source infrastructure location')
        need(identity(b if b.exists() else a) == before, 'source infrastructure identity changed')


def merge_guard(root, engine, tx, ephemeral=None):
    engine.guard()
    start = json.loads(read(tx / 'start.json', PLAN_LIMIT))
    need(not markers(root, engine.sid), 'destination quiescence lost')
    need(read(root / '_Axis/Flags/merge-pending') == flag_bytes(start), 'destination maintenance barrier changed')
    source_guard(root, start, root / start['preview']['source'], ephemeral)


def quarantine_source(root, engine, tx, start, source, reverse=False):
    if start['preview']['mode'] != 'absorb-child':
        return
    q = root / start['recovery'] / 'quarantine'
    mkdirs(q)
    names = list(start['removals'])
    if reverse:
        names.reverse()
    for name in names:
        merge_guard(root, engine, tx)
        a, b = source / name, q / name
        origin, target = (b, a) if reverse else (a, b)
        if not os.path.lexists(origin):
            need(identity(target) == start['removals'][name], 'quarantine move has unknown state')
            continue
        need(not os.path.lexists(target), 'quarantine destination occupied')
        need(identity(origin) == start['removals'][name], 'quarantine ownership changed')
        os.rename(origin, target)
        need(identity(target) == start['removals'][name], 'quarantine readback')
    merge_guard(root, engine, tx)


def replace(root, engine, tx, op, reverse=False):
    ephemeral = {}
    guard = lambda: merge_guard(root, engine, tx, ephemeral)
    name = op['path']
    start = json.loads(read(tx / 'start.json', PLAN_LIMIT))
    source = Path(os.path.abspath(root / start['preview']['source'])) if start['preview']['mode'] == 'absorb-child' else None
    current_hash = lambda: target_hash(root, name, source)
    expected = op['after'] if reverse else op['before']
    wanted = op['before'] if reverse else op['after']
    actual = current_hash()
    mode = op['before_mode'] if reverse else op['mode']
    if actual == wanted:
        if actual is not None:
            need(stat.S_IMODE(destination_path(root, name).stat().st_mode) == mode, 'destination mode diverged')
        return
    need(actual == expected, 'destination diverged: ' + name)
    if actual is not None:
        need(stat.S_IMODE(destination_path(root, name).stat().st_mode)
             == (op['mode'] if reverse else op['before_mode']), 'destination mode changed')
    guard()
    p = destination_path(root, name)
    mkdirs(p.parent)
    lock = p.with_name(p.name + '.lock')
    lock.mkdir()
    token = secrets.token_hex(16)
    once(lock / 'OWNER', token.encode())
    ephemeral[str(lock)] = {'kind': 'dir'}
    ephemeral[str(lock / 'OWNER')] = {'kind': 'file', 'sha256': digest(token.encode()), 'mode': 0o600}
    started = time.monotonic()
    claim = None
    try:
        guard()
        need(read(lock / 'OWNER') == token.encode() and current_hash() == expected, 'write ownership or bytes changed')
        if not reverse and expected is None:
            match = ID.match(Path(name).name) if name.startswith(('_Axis/', '_Memos/')) else None
            if match:
                value = match[0]
                claim_name = '_Temp/' + value + '.tsclaim'
                cp = engine.path(claim_name, missing=True, kind='directory')
                cp.mkdir()
                claim = (claim_name, token, (cp.stat().st_dev, cp.stat().st_ino), time.monotonic())
                once(cp / 'OWNER', token.encode())
                need(not engine.collision(value), 'import identity is occupied; replan without overwriting')
        if wanted is None:
            p.unlink()
        else:
            data = read(tx / 'objects' / wanted)
            temporary = p.with_name('.' + p.name + '.merge-' + token)
            once(temporary, data)
            os.chmod(temporary, mode)
            ephemeral[str(temporary)] = {'kind': 'file', 'sha256': wanted, 'mode': mode}
            need(time.monotonic() - started < 10, 'write lock expired')
            guard()
            need(current_hash() == expected, 'destination changed before replace')
            if expected is None:
                os.link(temporary, p, follow_symlinks=False)
                temporary.unlink()
            else:
                os.replace(temporary, p)
        need(current_hash() == wanted, 'destination readback failed')
    finally:
        if 'temporary' in locals() and os.path.lexists(temporary):
            if digest(read(temporary)) == wanted:
                temporary.unlink()
        if claim is not None:
            engine.release_timestamp(*claim)
        if time.monotonic() - started < 10 and read(lock / 'OWNER') == token.encode():
            (lock / 'OWNER').unlink()
            lock.rmdir()


def remove_created_directories(root, start):
    for name in sorted(start['created_directories'], key=lambda x: (-x.count('/'), x)):
        p = destination_path(root, name)
        if p.exists():
            plain(p, 'dir')
            need(not any(p.iterdir()), 'new directory contains unplanned content; preserve for reconciliation')
            p.rmdir()


def apply(root, session, txid, reverse=False):
    _, engine, tx, start, source = transaction(root, session, txid)
    need(not (tx / 'accepted.json').exists(), 'accepted merge cannot be blindly rolled back')
    if (tx / 'aborted.json').exists():
        need(reverse, 'aborted transaction')
        for directory in (source, root):
            flag = directory / '_Axis/Flags/merge-pending'
            if os.path.lexists(flag):
                need(read(flag) == flag_bytes(start), 'foreign maintenance barrier')
                flag.unlink()
        return {'status': 'aborted', 'transaction': txid}
    merge_guard(root, engine, tx)
    if not reverse:
        quarantine_source(root, engine, tx, start, source)
        for name in start['created_directories']:
            merge_guard(root, engine, tx)
            mkdirs(destination_path(root, name))
    for op in reversed(start['operations']) if reverse else start['operations']:
        replace(root, engine, tx, op, reverse)
    if reverse:
        remove_created_directories(root, start)
        quarantine_source(root, engine, tx, start, source, True)
        merge_guard(root, engine, tx)
        once(tx / 'aborted.json', encode({'schema': 1, 'transaction': txid, 'restored': True, 'mode': 'absorption-v2'}))
        for directory in (source, root):
            p = directory / '_Axis/Flags/merge-pending'
            need(read(p) == flag_bytes(start), 'foreign maintenance barrier')
            p.unlink()
        recovery = root / start['recovery']
        if recovery.exists():
            need(not any(p.is_file() for p in recovery.rglob('*')), 'recovery contains unexpected content')
            shutil.rmtree(recovery)
    elif not (tx / 'applied.json').exists():
        merge_guard(root, engine, tx)
        once(tx / 'applied.json', encode({'schema': 2, 'transaction': txid, 'applied': len(start['operations'])}))
    return {'status': 'aborted' if reverse else 'applied-awaiting-validation', 'transaction': txid}


def checkpoint_file(root, checkpoint, name, expected, mode):
    need(checkpoint is not None and re.fullmatch('[0-9a-f]{40}', checkpoint), 'exact local checkpoint required')
    base = ['git', '-C', str(root)]
    result = subprocess.run(base + ['cat-file', '-t', checkpoint], capture_output=True)
    need(result.returncode == 0 and result.stdout == b'commit\n', 'checkpoint must name a commit')
    need(subprocess.run(base + ['merge-base', '--is-ancestor', checkpoint, 'HEAD'], capture_output=True).returncode == 0,
         'checkpoint must be retained in current history')
    result = subprocess.run(base + ['ls-tree', '-z', checkpoint, '--', name], capture_output=True)
    prefix = ('100755' if mode & 0o111 else '100644') + ' blob '
    need(result.returncode == 0 and result.stdout.count(b'\0') == 1 and result.stdout.startswith(prefix.encode())
         and result.stdout.split(b'\t', 1)[-1] == name.encode() + b'\0', 'checkpoint file mode/type differs')
    result = subprocess.run(base + ['show', checkpoint + ':' + name], capture_output=True)
    need(result.returncode == 0 and digest(result.stdout) == expected, 'checkpoint does not contain merged bytes')


def final_content(root, tx, start):
    plan = json.loads(read(tx / 'plan.json', PLAN_LIMIT))
    folder = root / start['preview']['content_root']
    plain(folder, 'dir')
    expected = {p[len(start['preview']['content_root']) + 1:] for p in plan['imports'].values()
                if p.startswith(start['preview']['content_root'] + '/')}
    actual = set()
    for parent, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs:
            plain(Path(parent) / name, 'dir')
        for name in files:
            p = Path(parent) / name
            plain(p)
            actual.add(p.relative_to(folder).as_posix())
    need(actual == expected, 'imported folder contains missing or unplanned content')
    need(not any((p.is_dir() and p.name.startswith('_')) or p.name == '.git' or p.name.casefold() in ENTRY
                 for p in folder.iterdir()),
         'source infrastructure remains')
    by_path = {op['path']: op for op in start['operations']}
    for original, target in plan['imports'].items():
        if target.startswith(start['preview']['content_root'] + '/') and target not in by_path:
            need(digest(read(root / target)) == start['preview']['source_inventory']['files'][original]['sha256'],
                 'unchanged imported content drifted')
    for op in start['operations']:
        need(target_hash(root, op['path']) == op['after'], 'applied content changed')
        need(stat.S_IMODE(destination_path(root, op['path']).stat().st_mode) == op['mode'], 'applied file mode changed')


def finish(root, session, txid, checkpoint=None):
    _, engine, tx, start, source = transaction(root, session, txid)
    if (tx / 'accepted.json').exists():
        return retire(root, session, txid)
    merge_guard(root, engine, tx)
    need((tx / 'applied.json').exists() and not (tx / 'aborted.json').exists(), 'transaction not applied')
    final_content(root, tx, start)
    checker = root / '_Axis/Resources/record-check.py'
    scopes = [str(destination_path(root, op['path'])) for op in start['operations'] if op['path'].endswith('.md')]
    for args in (['names'], ['links', *sum((['--scope', p] for p in scopes), [])]):
        result = subprocess.run([sys.executable, '-B', str(checker), '--root', str(root), *args],
                                capture_output=True, text=True, timeout=120)
        need(result.returncode == 0, 'record validation held; inspect record-check diagnostics')
    local_only = []
    if (root / '.git').exists():
        outputs = {op['path']: (op['after'], op['mode']) for op in start['operations']}
        plan = json.loads(read(tx / 'plan.json', PLAN_LIMIT))
        for original, name in plan['imports'].items():
            if name.startswith(start['preview']['content_root'] + '/') and name not in outputs:
                info = start['preview']['source_inventory']['files'][original]
                outputs[name] = (info['sha256'], info['mode'])
        for name, (expected, mode) in outputs.items():
            path = destination_path(root, name)
            if not path.is_relative_to(root):
                local_only.append(name)
                continue
            ignored = subprocess.run(['git', '-C', str(root), 'check-ignore', '-q', '--', name], capture_output=True)
            if ignored.returncode == 0:
                local_only.append(name)
            else:
                need(ignored.returncode == 1, 'checkpoint eligibility held; reconcile Git errors and stage any approved gitlink conversion')
                checkpoint_file(root, checkpoint, name, expected, mode)
    merge_guard(root, engine, tx)
    cleanup_target = source if start['preview']['mode'] == 'combine' else root / start['recovery']
    cleanup = {'schema': 2, 'transaction': txid, 'identity': identity(cleanup_target),
               'tree': physical_manifest(cleanup_target)}
    cleanup_path = tx / 'cleanup-inventory.json'
    if cleanup_path.exists():
        need(read(cleanup_path, PLAN_LIMIT) == encode(cleanup), 'cleanup inventory changed before acceptance')
    else:
        once(cleanup_path, encode(cleanup))
    once(tx / 'accepted.json', encode({'schema': 2, 'transaction': txid, 'checkpoint': checkpoint,
         'source_id': start['preview']['source_id'], 'destination_id': start['preview']['destination_id'],
         'local_only_outputs': local_only, 'source_git_history': 'abandoned; no history merge'}))
    return retire(root, session, txid)


def remove_known_tree(path, manifest, engine):
    """Resume accepted cleanup without deleting a new path or a changed ordinary file."""
    if not os.path.lexists(path):
        return
    plain(path, 'dir')
    need(identity(path) == manifest['identity'], 'cleanup root identity changed')
    remaining = physical_manifest(path)
    need(set(remaining) <= set(manifest['tree']), 'cleanup contains unplanned content')
    need(all(item == manifest['tree'][name] for name, item in remaining.items()), 'cleanup content changed')
    for name in sorted(remaining, key=lambda p: (-p.count('/'), p)):
        engine.guard()
        item = remaining[name]
        p = path / name
        if item['kind'] == 'dir':
            plain(p, 'dir')
            p.rmdir()
        elif item['kind'] == 'git':
            need(identity(plain(p, 'dir')) == item['identity'], 'old Git repository identity changed')
            shutil.rmtree(p)
        else:
            need(digest(read(p)) == item['sha256'] and stat.S_IMODE(p.stat().st_mode) == item['mode'],
                 'cleanup file changed')
            p.unlink()
    path.rmdir()


def retire(root, session, txid, source_checkpoint=None):
    _, engine, tx, start, source = transaction(root, session, txid)
    need((tx / 'accepted.json').exists(), 'acceptance required')
    need(source_checkpoint is None, 'source Git history is not checkpointed or imported by absorption')
    if (tx / 'retired.json').exists():
        flag = root / '_Axis/Flags/merge-pending'
        if os.path.lexists(flag):
            need(read(flag) == flag_bytes(start), 'foreign pending merge')
            flag.unlink()
        return {'status': 'complete', 'transaction': txid, 'content_root': start['preview']['content_root']}
    engine.guard()
    need(not markers(root, session), 'destination quiescence lost')
    final_content(root, tx, start)
    receipt = tx / 'cleanup-start.json'
    if not receipt.exists():
        merge_guard(root, engine, tx)
        once(receipt, encode({'schema': 2, 'transaction': txid, 'source_identity': start['source_identity'],
                             'mode': start['preview']['mode'], 'accepted': True}))
    cleanup = json.loads(read(tx / 'cleanup-inventory.json', PLAN_LIMIT))
    # The old external root moves atomically within its own volume before deletion.
    # A new file or replacement path holds cleanup; the continuing content stays intact.
    if start['preview']['mode'] == 'combine':
        retired = root / start['retirement']
        if not (tx / 'source-move-start.json').exists():
            source_guard(root, start, source)
            need(not os.path.lexists(retired), 'retirement staging path occupied')
            once(tx / 'source-move-start.json', encode({'schema': 2, 'transaction': txid,
                                                       'identity': start['source_identity']}))
        if source.exists():
            need(not os.path.lexists(retired) and identity(source) == start['source_identity'],
                 'source replacement during cleanup')
            need(physical_manifest(source) == cleanup['tree'], 'source changed before retirement move')
            os.rename(source, retired)
        remove_known_tree(retired, cleanup, engine)
        need(not os.path.lexists(source), 'old source removal incomplete')
    else:
        remove_known_tree(root / start['recovery'], cleanup, engine)
    engine.guard()
    final_content(root, tx, start)
    # Compatible terminal shape lets existing startup/update guards recognize completion.
    once(tx / 'retired.json', encode({'schema': 1, 'transaction': txid, 'source_preserved': True,
         'mode': 'absorption-v2', 'content_root': start['preview']['content_root'],
         'source_id': start['preview']['source_id'], 'destination_id': start['preview']['destination_id'],
         'source_infrastructure_removed': True, 'source_git_history': 'abandoned'}))
    flag = root / '_Axis/Flags/merge-pending'
    need(read(flag) == flag_bytes(start), 'foreign pending merge')
    flag.unlink()
    return {'status': 'complete', 'transaction': txid, 'content_root': start['preview']['content_root'],
            'source': 'ordinary content folder; Axis infrastructure removed; old Git repository abandoned'}


def repair_barriers(root, session, txid):
    _, engine, tx, start, source = transaction(root, session, txid)
    need(not any((tx / n).exists() for n in ('applied.json', 'accepted.json', 'aborted.json')),
         'barrier repair only before application')
    need(not (root / start['recovery']).exists(), 'cannot repair barriers after source movement')
    need(inventory(source, source=True) == start['preview']['source_inventory'], 'source changed')
    need(not markers(source) and not markers(root, session), 'quiescence lost')
    for op in start['operations']:
        need(target_hash(root, op['path'], source) == op['before'], 'cannot repair barriers after material changes')
    for directory in (root, source):
        flag = directory / '_Axis/Flags/merge-pending'
        if os.path.lexists(flag):
            need(read(flag) == flag_bytes(start), 'foreign maintenance barrier')
        else:
            engine.guard()
            once(flag, flag_bytes(start))
    return {'status': 'prepared', 'transaction': txid, 'barriers': 'verified'}


def status(root):
    """Data-only admission for both historical v1 and current v2 journals."""
    root = plain(root, 'dir')
    pending = root / '_Axis/Flags/merge-pending'
    retired = root / '_Axis/Merges/retired.json'
    folder = root / '_Axis/Merges'
    rows = []
    if not os.path.lexists(retired) and not os.path.lexists(pending) and (
            not os.path.lexists(folder) or (plain(folder, 'dir') and not any(p.name != '.gitkeep' for p in folder.iterdir()))):
        return {'status': 'clear', 'transactions': []}
    root, pid, _ = project(root)
    if os.path.lexists(retired):
        value = json.loads(read(retired))
        need(value.get('schema') == 1 and value.get('source_id') == pid and value.get('source_preserved') is True
             and ID.fullmatch(value.get('transaction', '')), 'invalid retirement marker')
        return {'status': 'retired', 'destination_id': value['destination_id']}
    if os.path.lexists(pending):
        value = json.loads(read(pending))
        need(value.get('schema') == 1 and pid in (value.get('source_id'), value.get('destination_id'))
             and ID.fullmatch(value.get('transaction', '')), 'invalid pending merge')
        rows.append(value['transaction'])
        if pid == value['source_id']:
            return {'status': 'source-held', 'destination_id': value['destination_id'], 'transaction': value['transaction']}
    if os.path.lexists(folder):
        plain(folder, 'dir')
        entries = list(folder.iterdir())
        need(len(entries) <= 1000, 'merge journal inventory limit')
        for path in entries:
            if path.name in ('.gitkeep', 'retired.json'):
                continue
            need(ID.fullmatch(path.name), 'unexpected merge journal entry')
            plain(path, 'dir')
            terminal = []
            for receipt, field in (('retired.json', 'source_preserved'), ('aborted.json', 'restored')):
                q = path / receipt
                if os.path.lexists(q):
                    value = json.loads(read(q, 4096))
                    need(value.get('schema') == 1 and value.get('transaction') == path.name
                         and value.get(field) is True, 'invalid terminal merge receipt')
                    terminal.append(receipt)
            need(len(terminal) <= 1, 'conflicting terminal merge receipts')
            if not terminal:
                rows.append(path.name)
    return {'status': 'recovery' if rows else 'clear', 'transactions': sorted(set(rows))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('preview')
    p.add_argument('--source', required=True)
    p.add_argument('--session')
    p.add_argument('--folder')
    p = sub.add_parser('draft')
    p.add_argument('--source', required=True)
    p.add_argument('--session', required=True)
    p.add_argument('--plan', required=True)
    p.add_argument('--folder')
    p = sub.add_parser('prepare')
    p.add_argument('--session', required=True)
    p.add_argument('--plan', required=True)
    p.add_argument('--approval-log', required=True)
    for name in ('apply', 'abort', 'finish', 'retire', 'repair-barriers'):
        p = sub.add_parser(name)
        p.add_argument('--session', required=True)
        p.add_argument('--transaction', required=True)
        if name == 'finish':
            p.add_argument('--checkpoint')
    sub.add_parser('status')
    args = parser.parse_args()
    try:
        root = plain(args.root, 'dir')
        if args.command == 'status':
            value = status(root)
        elif args.command == 'preview':
            value = preview(root, Path(args.source), args.session, args.folder)
        elif args.command == 'draft':
            value = draft(root, Path(args.source), args.session, Path(args.plan), args.folder)
        elif args.command == 'prepare':
            value = prepare(root, args.session, Path(args.plan), args.approval_log)
        elif args.command in ('apply', 'abort'):
            value = apply(root, args.session, args.transaction, args.command == 'abort')
        elif args.command == 'finish':
            value = finish(root, args.session, args.transaction, args.checkpoint)
        elif args.command == 'repair-barriers':
            value = repair_barriers(root, args.session, args.transaction)
        else:
            value = retire(root, args.session, args.transaction)
        print(json.dumps(value, sort_keys=True))
        return 0
    except (Held, OSError, ValueError, KeyError, TypeError, UnicodeError) as error:
        print(json.dumps({'status': 'held', 'reason': str(error)[:240]}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
