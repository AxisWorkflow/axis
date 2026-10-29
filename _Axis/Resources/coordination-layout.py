#!/usr/bin/env python3
"""Missing-only coordination layout during owned Main startup; never imports or dispatches work."""
import argparse,importlib.util,json,os,stat,sys
from pathlib import Path
FAMILIES=('Submissions','Messages','Teams','Jobs','Schedules')

def empty_messages(folder):
    # Only the shipped structural skeleton is an empty family. Never ignore
    # unknown folders or records while constructing a zero-count index.
    allowed={'Individual','Teams','Archive','Archive/Individual','Archive/Teams'}
    for p in folder.rglob('*'):
        rel=p.relative_to(folder).as_posix()
        if p.is_symlink():return False
        if p.is_dir():
            if rel not in allowed:return False
        elif p.name not in ('.gitkeep','.DS_Store') or not p.is_file() or p.name=='.gitkeep' and p.stat().st_size:return False
    return True


def harmonize(startup):
    startup.guard()
    axis=startup.path('_Axis',kind='directory')
    names=[p.name for p in axis.iterdir()]
    wanted=['Merges']+list(FAMILIES)+[f.upper()+'.md' for f in FAMILIES if f!='Submissions']
    for name in wanted:
        if any(n.casefold()==name.casefold() and n!=name for n in names):raise ValueError('coordination layout spelling collision: '+name)
    missing=[];indexes=[];keepers=[]
    merges=startup.path('_Axis/Merges',missing=True,kind='directory')
    if not merges.exists():missing.append('Merges')
    for family in FAMILIES:
        folder=startup.path('_Axis/'+family,missing=True,kind='directory')
        if not folder.exists():missing.append(family)
        if family=='Submissions':continue
        name='_Axis/'+family.upper()+'.md';index=startup.path(name,missing=True)
        if index.exists():continue
        # An absent populated index needs canonical projection, never an invented zero count.
        if folder.exists() and (not empty_messages(folder) if family=='Messages' else any(p.name not in ('.gitkeep','.DS_Store') for p in folder.iterdir())):raise ValueError('missing index for populated family; rebuild canonically before startup: '+name)
        indexes.append((name,('# '+family+'\n> **Purpose:** Show cached coordination state; records and accepted events are authoritative.\n\npending-count: 0\nverified: never\n\n| ID | Subject | State | Head |\n| --- | --- | --- | --- |\n').encode()))
    for family in ('Merges',*FAMILIES):
        if family in missing:continue
        marker=startup.path('_Axis/'+family+'/.gitkeep',missing=True)
        if family not in missing and not marker.exists():keepers.append('_Axis/'+family+'/.gitkeep')
    created=[]
    for family in missing:
        startup.guard();name='_Axis/'+family;p=startup.path(name,missing=True,kind='directory');p.mkdir();created.append(name+'/')
        startup.guard();fd=os.open(p/'.gitkeep',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        try:os.fsync(fd)
        finally:os.close(fd)
    for name in keepers:
        startup.guard();p=startup.path(name,missing=True);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        try:os.fsync(fd)
        finally:os.close(fd)
        created.append(name)
    for name,data in indexes:
        startup.guard();p=startup.path(name,missing=True);fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o644)
        try:
            with os.fdopen(fd,'wb',closefd=False) as stream:stream.write(data);stream.flush();os.fsync(fd)
        finally:os.close(fd)
        if p.read_bytes()!=data:raise ValueError('coordination layout readback mismatch: '+name)
        created.append(name)
    startup.guard()
    return {'status':'harmonized','created':created,'dispatch':False,'project_identity_changed':False}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--session',required=True);p.add_argument('--owner',required=True);a=p.parse_args()
    spec=importlib.util.spec_from_file_location('axis_startup',Path(__file__).with_name('startup-state.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);s=None
    try:
        s=m.Startup(a.root);s.load(a.session,a.owner);s.guard();print(json.dumps(harmonize(s)));return 0
    except (OSError,ValueError,m.Fault) as error:print(json.dumps({'status':'held','reason':str(error)}));return 2
    finally:
        if s is not None:s.close()
if __name__=='__main__':raise SystemExit(main())
