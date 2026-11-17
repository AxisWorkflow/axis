#!/usr/bin/env python3
"""Read-only nested Axis discovery. Reports ancestry; grants no action authority."""
import argparse,json,os,re,stat
from pathlib import Path
# BEGIN GENERATED: project-files
PROJECT_FILES=('PROJECT.md','PLAN.md','INITIATIVES.md','TASKS.md','INSTRUCTIONS.md','SETTINGS.md','MINDSET.md','DIRECTIVES.md')
def project_file(root,name):
    """Path of project file NAME: in _Config/ once moved, in _Axis/ before. Two differing copies are an error, never a choice."""
    import pathlib
    if name not in PROJECT_FILES:raise ValueError('not a project file: '+str(name))
    new=pathlib.Path(root)/'_Config'/name;old=pathlib.Path(root)/'_Axis'/name
    if new.is_file() and old.is_file() and new.read_bytes()!=old.read_bytes():raise ValueError('project file differs between _Config and _Axis: '+name)
    return new if new.is_file() or not old.is_file() else old
def project_name(root,name):
    """Project-relative name of project file NAME, by the same rule: `_Config/NAME` or `_Axis/NAME`."""
    import pathlib
    return project_file(root,name).relative_to(pathlib.Path(root)).as_posix()
# END GENERATED: project-files
ANCHORS=('AGENTS.md','CLAUDE.md','GEMINI.md','_Axis/MANIFEST.md','_Axis/PRACTICES.md','_Axis/RULES.md','_Temp')
# The brief identifies a project in either place; a child may still hold it in _Axis/.
BRIEFS=('_Config/PROJECT.md','_Axis/PROJECT.md')
OPAQUE={'_Axis','_Config','_Temp','_Trash','_Wiki','Wiki','_Inbox','_Memos','_Dev'}

def anchored(path,anchor):
    q=path
    for part in Path(anchor).parts:
        q/=part
        try:s=q.lstat()
        except FileNotFoundError:return False
        if stat.S_ISLNK(s.st_mode):return False
    if anchor=='_Temp':return stat.S_ISDIR(s.st_mode)
    return stat.S_ISREG(s.st_mode) and s.st_nlink==1

def brief(path):
    for name in BRIEFS:
        try:
            if anchored(path,name):return True
        except NotADirectoryError:pass  # a file named _Config holds no brief; the other place still counts
    return False

def recognized(path):
    return all(anchored(path,anchor) for anchor in ANCHORS) and brief(path)

def retirement(path):
    q=path/'_Axis/Merges'
    if not os.path.lexists(q):return None
    info=q.lstat()
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):raise ValueError('unsafe merge state')
    q=q/'retired.json'
    if not os.path.lexists(q):return None
    info=q.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>4096:raise ValueError('invalid retirement record')
    value=json.loads(q.read_text());ids=re.findall(r'^project-id: (\S+)\s*$',project_file(path,'PROJECT.md').read_text(),re.M)
    if len(ids)!=1 or value.get('schema')!=1 or value.get('source_id')!=ids[0] or value.get('source_preserved') is not True or not re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',value.get('transaction','')):raise ValueError('retirement identity mismatch')
    return value['destination_id']

def discover(root,limit=50000):
    root=Path(root).absolute()
    if root!=root.resolve() or not root.is_dir():raise ValueError('canonical non-linked root required')
    found=[];held=[];retired=[];visited=0
    def walk(parent,ancestor,depth,readonly):
        nonlocal visited
        try:entries=sorted(parent.iterdir(),key=lambda p:p.name)
        except OSError as error:held.append({'path':str(parent.relative_to(root)),'reason':type(error).__name__});return
        for p in entries:
            if p.name.startswith('.') or p.name in OPAQUE or p.name.endswith('_X'):continue
            try:s=p.lstat()
            except OSError as error:held.append({'path':str(p.relative_to(root)),'reason':type(error).__name__});continue
            if not stat.S_ISDIR(s.st_mode):continue
            visited+=1
            if visited>limit:raise ValueError('discovery bound exceeded; no complete coverage claim')
            rel=p.relative_to(root).as_posix();ro=readonly or p.name.endswith('_U')
            try:is_project=recognized(p)
            except OSError as error:held.append({'path':rel,'reason':type(error).__name__});continue
            if is_project:
                try:destination=retirement(p)
                except (OSError,ValueError,KeyError,TypeError) as error:held.append({'path':rel,'reason':'invalid retirement state'});continue
                if destination is not None:retired.append({'path':rel,'destination_id':destination});continue
                found.append({'path':rel,'parent':ancestor,'depth':depth+1,'read_only':ro});walk(p,rel,depth+1,ro)
            else:walk(p,ancestor,depth,ro)
    walk(root,'.',0,False)
    return {'status':'partial' if held else 'complete','projects':found,'retired':retired,'held':held,'visited_directories':visited}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',default='.');a=p.parse_args()
    try:print(json.dumps(discover(a.root),sort_keys=True));return 0
    except (OSError,ValueError) as error:print(json.dumps({'status':'held','reason':str(error)}));return 2
if __name__=='__main__':raise SystemExit(main())
