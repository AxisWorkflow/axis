#!/usr/bin/env python3
"""Physical Message locations. Placement is never evidence of record authority."""
import os
from pathlib import Path
import re
import stat
ID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\Z')


def directory(path):
    info = path.lstat()
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode): raise ValueError('unsafe Message directory')
    return path


def folders(root, team=None, archived=True):
    base = Path(root) / '_Axis/Messages'
    if not base.exists(): return
    directory(base)
    yield base  # legacy fallback, including unresolved records left by adoption
    for prefix in [base] + ([base / 'Archive'] if archived else []):
        if not prefix.exists(): continue
        directory(prefix)
        individual = prefix / 'Individual'
        if individual.exists(): yield directory(individual)
        teams = prefix / 'Teams'
        if teams.exists():
            directory(teams)
            for path in ([teams / team] if team else sorted(teams.iterdir())):
                if not path.exists(): continue
                if not ID.fullmatch(path.name):
                    if path.name == '.gitkeep': continue
                    raise ValueError('invalid Message Team directory')
                yield directory(path)
        if prefix != base: yield prefix  # previous flat family archive


def paths(root, team=None, archived=True):
    seen = set()
    for folder in folders(root, team, archived):
        for path in sorted(folder.iterdir()):
            if path.name=='.gitkeep':
                info=path.lstat()
                if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size!=0:raise ValueError('unexpected-record-file')
                continue
            if not path.name.endswith('.md'):continue
            if not ID.fullmatch(path.stem):raise ValueError('unexpected-record-file')
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1: raise ValueError('unsafe Message record')
            if path not in seen: seen.add(path); yield path


def resolve(root, ident):
    if not ID.fullmatch(ident): raise ValueError('invalid Message identity')
    matches = [folder / (ident + '.md') for folder in folders(root) if os.path.lexists(folder / (ident + '.md'))]
    if len(matches) != 1: raise ValueError('Message missing or duplicate')
    path = matches[0]; info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1: raise ValueError('unsafe Message record')
    return path


def destination(root, team=None):
    base = Path(root) / '_Axis/Messages'
    directory(base)
    if team is not None and not ID.fullmatch(team): raise ValueError('invalid Message Team identity')
    # Late retained results go to Main's Individual queue without reopening the Team.
    if team and (base/'Archive/Teams'/team).exists(): team = None
    parts = ['Teams', team] if team else ['Individual']
    path = base
    for part in parts:
        path = path / part
        try: path.mkdir()
        except FileExistsError: pass
        directory(path)
    return path.relative_to(root).as_posix()


def alias(root,name):
    """Resolve former record/support addresses by the unchanged globally unique ID."""
    parts=name.split('/')
    if parts[:2]!=['_Axis','Messages']:return None
    for index,part in enumerate(parts[2:],2):
        ident=part[:-3] if part.endswith('.md') else part
        if not ID.fullmatch(ident):continue
        # Teams/{id} is the routing container, not the record's support identity.
        if index>0 and parts[index-1]=='Teams':continue
        try: record=resolve(root,ident)
        except ValueError: return None
        target=record if part.endswith('.md') else record.with_suffix('')
        if index+1<len(parts):target=target.joinpath(*parts[index+1:])
        return target.relative_to(root).as_posix()
    return None
