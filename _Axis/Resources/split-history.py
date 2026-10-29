#!/usr/bin/env python3
"""Review and stage relevant history for a new, never-booted subproject.

No network, installation, parent-record edits, child boot or automatic semantic
selection. Main supplies a complete reviewed disposition for the catalog.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import stat
import sys
from pathlib import Path

ID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z')
FAMILIES = ('ColdStorage', 'Audit', 'CX', 'Followups', 'Ideas', 'Logs', 'Notes', 'Reminders',
            'Reviews', 'Snapshots', 'Supervision', 'Tasks', 'Teams', 'Messages', 'Jobs', 'Schedules')
INERT = {'Teams', 'Messages', 'Jobs', 'Schedules', 'Snapshots'}
LIMIT = 50000
BYTES = 32 * 1024 * 1024


class Held(Exception):
    pass


def need(value, reason):
    if not value:
        raise Held(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def safe(path, directory=False, missing=False):
    path = Path(os.path.abspath(path))
    cur = Path(path.anchor)
    for part in path.parts[1:]:
        need(not part.endswith(('_U', '_X')), 'protected path')
        parent = cur
        cur /= part
        if parent.is_dir():
            need(not any(p.name.casefold() == part.casefold() and p.name != part for p in parent.iterdir()), 'case alias')
        if not os.path.lexists(cur):
            need(missing, 'missing path')
            continue
        info = cur.lstat()
        need(not stat.S_ISLNK(info.st_mode), 'linked path')
        if cur != path or directory:
            need(stat.S_ISDIR(info.st_mode), 'not a directory')
        else:
            need(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, 'unsafe file')
    return path


def read(path):
    path = safe(path)
    need(path.stat().st_size <= BYTES, 'record too large')
    return path.read_bytes()


def parent(root, session=None):
    root = safe(root, directory=True)
    if session:
        path = root / '_Axis/Resources/startup-state.py'
        spec = importlib.util.spec_from_file_location('split_parent_state', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        owner = module.Session(root, session)
        owner.guard()
        need(owner.lease[2], 'Main required')
        return owner
    return root


def archive(root):
    settings = read(root / '_Axis/SETTINGS.md').decode()
    match = re.search(r'^### Archive Location\s*\n(.*?)(?=^### |^## |\Z)', settings, re.M | re.S)
    value = re.search(r'^\*\*Value:\*\*\s*(.+)$', match[1], re.M) if match else None
    location = value[1].strip().strip('`') if value else '_Axis/Archive/'
    path = Path(os.path.expanduser(location))
    return safe(path if path.is_absolute() else root / path, directory=True)


def folder(root, name):
    parts = Path(name).parts
    need(name and not Path(name).is_absolute() and '\\' not in name
         and all(p not in ('.', '..') and not p.startswith(('.', '_')) for p in parts), 'ordinary relative subfolder required')
    target = safe(root / name, directory=True)
    need(target != root and target.is_relative_to(root), 'folder outside parent')
    for item in [target, *target.parents]:
        if item == root:
            break
        need(not (item / '_Axis').exists(), 'existing or incomplete child project')
    return target


def support_files(record):
    support = record.with_suffix('')
    if not os.path.lexists(support):
        return {}
    safe(support, directory=True)
    result = {}
    for base, dirs, files in os.walk(support, followlinks=False):
        for name in dirs:
            safe(Path(base) / name, directory=True)
        for name in sorted(files):
            p = Path(base) / name
            data = read(p)
            result[p.relative_to(support).as_posix()] = {'sha256': sha(data), 'bytes': len(data)}
            need(len(result) <= LIMIT, 'support inventory bound')
    return result


def catalog(root, target):
    root = parent(root)
    folder(root, target)
    project = read(root / '_Axis/PROJECT.md').decode()
    ids = re.findall(r'^project-id: (\S+)\s*$', project, re.M)
    need(len(ids) == 1, 'parent identity required')
    records = {}
    seen = set()
    def add(path, logical, family):
        data = read(path)
        ident = path.stem if ID.fullmatch(path.stem) else None
        if ident:
            need(ident not in seen, 'duplicate parent record identity')
            seen.add(ident)
        records[logical] = {'sha256': sha(data), 'bytes': len(data),
                            'subject': data.decode('utf-8').splitlines()[0] if data else '', 'family': family, 'support': support_files(path)}
        need(len(records) <= LIMIT, 'history inventory bound')
    for base, prefix in [(root / '_Axis', '_Axis/'), (archive(root), '_Axis/Archive/')]:
        for family in FAMILIES:
            directory = base / family
            if not directory.exists():
                continue
            safe(directory, directory=True)
            if family == 'Messages' and base == root/'_Axis':
                spec=importlib.util.spec_from_file_location('axis_split_messages',Path(__file__).with_name('message-paths.py'))
                module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                for path in module.paths(root):add(path,path.relative_to(root).as_posix(),family)
                continue
            for path in sorted(directory.iterdir()):
                if path.name == 'Archive' and path.is_dir():
                    safe(path,directory=True)
                    for entry in sorted(path.iterdir()):
                        if entry.name in ('.gitkeep','COLD.md'):continue
                        if entry.is_dir() and ID.fullmatch(entry.name):continue
                        need(entry.suffix=='.md' and ID.fullmatch(entry.stem),'unexpected family archive member')
                        add(entry,'_Axis/'+family+'/Archive/'+entry.name,family)
                    continue
                if path.name == '.gitkeep':
                    continue
                if path.is_dir() and ID.fullmatch(path.name):
                    safe(path, directory=True)
                    continue
                need(path.name.endswith('.md') and ID.fullmatch(path.stem), 'unexpected history member')
                add(path, prefix + family + '/' + path.name, family)
    # Typed imported history remains inert, with its full original logical path.
    imports = archive(root) / 'Imports'
    if imports.exists():
        safe(imports, directory=True)
        for base, dirs, files in os.walk(imports, followlinks=False):
            for name in dirs:
                safe(Path(base) / name, directory=True)
            for name in sorted(files):
                path = Path(base) / name
                if path.suffix == '.md' and ID.fullmatch(path.stem) and path.parent.name in FAMILIES:
                    add(path, '_Axis/Archive/' + path.relative_to(archive(root)).as_posix(), path.parent.name)
    # Memos are not index/detail records; filenames and exact bytes still survive.
    memos = root / '_Memos'
    if memos.exists():
        safe(memos, directory=True)
        for base, dirs, files in os.walk(memos, followlinks=False):
            for name in dirs:
                safe(Path(base) / name, directory=True)
            for name in sorted(files):
                path = Path(base) / name
                if path.suffix.lower() == '.md':
                    add(path, path.relative_to(root).as_posix(), 'Memos')
    index_hash = sha(read(root / '_Axis/TASKS.md'))
    return {'schema': 1, 'parent_project': ids[0], 'folder': target, 'records': records,
            'task_index_sha256': index_hash,
            'catalog_sha256': sha(encode({'records': records, 'task_index_sha256': index_hash}))}


def origin(root, logical):
    if logical.startswith('_Axis/Archive/'):
        return archive(root) / logical[len('_Axis/Archive/'):]
    return root / logical


def selection(root, value):
    need(set(value) == {'schema', 'parent_project', 'folder', 'catalog_sha256', 'records'}, 'selection fields')
    need(value['schema'] == 1, 'selection version')
    current = catalog(root, value['folder'])
    need(value['parent_project'] == current['parent_project'] and value['catalog_sha256'] == current['catalog_sha256'], 'history changed; review successor catalog')
    need(isinstance(value['records'], dict) and set(value['records']) == set(current['records']), 'every history record needs a reviewed disposition')
    chosen = {}
    for name, disposition in value['records'].items():
        need(isinstance(disposition, dict) and set(disposition) == {'decision', 'reason'}, 'disposition fields')
        need(disposition['decision'] in ('copy', 'support', 'skip') and isinstance(disposition['reason'], str) and disposition['reason'].strip(), 'reasoned disposition required')
        if disposition['decision'] != 'skip':
            chosen[name] = current['records'][name]
    # Resolve references to other actual records; session/event timestamps alone are not records.
    known = {Path(name).stem: name for name in current['records']}
    if (root/'_Axis/ColdStorage').exists():
        spec=importlib.util.spec_from_file_location('split_cold_ids',Path(__file__).with_name('archive-storage.py'));archive_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(archive_module)
        for path,record in archive_module.locators(root):
            need((path.with_suffix('')/'copied.json').is_file(),'finish pending cold copy before splitting history')
            for item in record['files']:
                if item['record_id']:known[item['record_id']]=path.relative_to(root).as_posix()
    missing = set()
    for name in chosen:
        data = read(origin(root, name)).decode('utf-8')
        for ident in ID.findall(data):
            if ident in known and known[ident] not in chosen:
                missing.add(known[ident])
    need(not missing, 'selected history needs contextual dependencies: ' + ', '.join(sorted(missing)))
    return current, chosen


def stage(root, session, selection_file, child, transaction):
    root = parent(root)
    owner = parent(root, session)
    need(ID.fullmatch(transaction), 'transaction identity')
    value = json.loads(read(selection_file))
    current, chosen = selection(root, value)
    child = safe(child, directory=True)
    need(child.is_relative_to(root / '_Temp') and child != root / '_Temp', 'stage must be inside parent scratch')
    need(not child.is_relative_to(folder(root, value['folder'])), 'stage overlaps target')
    need((child / '_Axis/PROJECT.md').is_file(), 'install verified Axis template into stage first')
    for name in ('Agents', 'Flags', 'Logs', 'Notes', 'Tasks', 'Ideas'):
        p = safe(child / '_Axis' / name, directory=True)
        need(not any(x.name != '.gitkeep' for x in p.iterdir()), 'stage already has live state')
    provenance = child / '_Axis/Splits' / transaction
    need(not provenance.exists(), 'history stage already exists')
    operations = []
    for name, row in chosen.items():
        family = row['family']
        target = ('_Axis/Archive/Imports/' + transaction + '/' + family + '/' + Path(name).name
                  if family in INERT and not name.startswith('_Axis/Archive/Imports/') else name)
        data = read(origin(root, name))
        need(sha(data) == row['sha256'], 'source changed')
        operations.append((target, data, name))
        support = origin(root, name).with_suffix('')
        need(support_files(origin(root, name)) == row['support'], 'support changed')
        for rel, expected in row['support'].items():
            data = read(support / rel)
            need(sha(data) == expected['sha256'], 'support changed')
            operations.append((target[:-3] + '/' + rel, data, name[:-3] + '/' + rel))
            need(len(operations) <= LIMIT, 'support inventory bound')
    total = sum(len(data) for _, data, _ in operations)
    need(total <= 512 * 1024 * 1024, 'history byte bound')
    destinations = set()
    for target, _, _ in operations:
        need(target.casefold() not in destinations, 'import collision')
        destinations.add(target.casefold())
        path = safe(child / target, missing=True)
        need(not path.exists(), 'never overwrite staged content')
    # Write start first. On interruption discard only this disposable stage and rebuild;
    # parent originals and the actual target folder remain untouched.
    owner.guard()
    provenance.mkdir(parents=True)
    (provenance / 'start.json').write_bytes(encode({'schema': 1, 'selection': value, 'catalog': current, 'files': {target: sha(data) for target, data, _ in operations}}))
    imports = {}
    for target, data, original in operations:
        owner.guard()
        path = safe(child / target, missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('xb') as stream:
            stream.write(data)
        need(read(path) == data, 'import readback')
        imports[target] = {'parent_path': original, 'sha256': sha(data), 'bytes': len(data)}
    # Copy Task index entries as historical status, without inventing new dates.
    task_ids = {Path(name).stem for name in chosen if chosen[name]['family'] == 'Tasks' and '/Archive/' not in name}
    index_bytes = read(root / '_Axis/TASKS.md')
    need(sha(index_bytes) == current['task_index_sha256'], 'Task index changed')
    task_index = index_bytes.decode()
    entries = []
    indexed = set()
    for part in re.split(r'(?m)(?=^## )', task_index):
        if not part.startswith('## '):
            continue
        links = re.findall(r'\[Details\.\.\.\]\(((?:Tasks|Tasks/Archive|Archive/Tasks)/(' + ID.pattern + r')\.md)\)', part)
        if len(links) != 1:
            need(not task_ids.intersection(ID.findall(part)), 'ambiguous selected Task index identity')
            continue
        link, ident = links[0]
        if ident not in task_ids:
            continue
        need(ident not in indexed, 'duplicate selected Task index entry')
        need('_Axis/' + link in chosen, 'selected Task index path differs from record')
        indexed.add(ident)
        entries.append(part)
    need(task_ids == indexed, 'selected Task has no canonical index entry')
    if entries:
        owner.guard()
        index = child / '_Axis/TASKS.md'
        index.write_text('# Tasks\n> **Purpose:** Track transferred project work.\n\n' + '\n'.join(entries))
    receipt = {'schema': 1, 'parent_project': current['parent_project'], 'folder': current['folder'],
               'transaction': transaction, 'catalog_sha256': current['catalog_sha256'], 'imports': imports,
               'authority': 'Copied history is context, not authorization to execute parent jobs or schedules.',
               'complete': True}
    owner.guard()
    need(catalog(root, value['folder']) == current, 'parent history changed during staging')
    with (provenance / 'complete.json').open('xb') as f:
        f.write(encode(receipt))
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', default='.')
    sub = p.add_subparsers(dest='command', required=True)
    c = sub.add_parser('catalog'); c.add_argument('--folder', required=True)
    c = sub.add_parser('check'); c.add_argument('--selection', required=True)
    c = sub.add_parser('stage')
    for flag in ('session', 'selection', 'child', 'transaction'):
        c.add_argument('--' + flag, required=True)
    a = p.parse_args(); root = Path(a.root).absolute()
    try:
        if a.command == 'catalog': result = catalog(root, a.folder)
        elif a.command == 'check':
            current, selected = selection(root, json.loads(read(Path(a.selection))))
            result = {'status': 'reviewed', 'total': len(current['records']), 'selected': len(selected)}
        else: result = stage(root, a.session, Path(a.selection), Path(a.child), a.transaction)
        print(json.dumps(result, sort_keys=True)); return 0
    except (Held, OSError, ValueError, UnicodeError) as e:
        print(json.dumps({'status': 'held', 'reason': str(e)})); return 2


if __name__ == '__main__':
    raise SystemExit(main())
