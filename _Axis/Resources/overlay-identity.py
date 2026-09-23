#!/usr/bin/env python3
"""Optional read-only overlay identity check. Python 3 standard library only.

The caller supplies any independently approved content pin; this tool never
loads guidance, executes an overlay, writes a Flag or grants Main authority.
Without Python, Load-Project-Overlay.md defines the same file-only procedure.
"""
from pathlib import Path
import argparse,hashlib,json,re,stat,sys,time

def require(value,message):
    if not value:raise ValueError(message)

def safe(root,name):
    require(isinstance(name,str) and name and not name.startswith('/') and '\\' not in name and all(v not in ('','.','..') for v in name.split('/')),'unsafe path')
    current=root
    for part in name.split('/'):
        if current.exists():
            require(current.is_dir(),'invalid path parent')
            entries=[p.name for p in current.iterdir()]
            require(not (current/part).exists() or part in entries,'noncanonical path spelling')
            require(not any(p.casefold()==part.casefold() and p!=part for p in entries),'ambiguous path spelling')
        current/=part
        require(not current.is_symlink(),'symbolic path')
        if current.exists():
            mode=current.stat();require(stat.S_ISDIR(mode.st_mode) or stat.S_ISREG(mode.st_mode) and mode.st_nlink==1,'unsafe filesystem object')
    return current

def read(root,name):
    p=safe(root,name);require(p.is_file(),'missing file');return p.read_bytes()

def lease(root,sid,phase):
    require(re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',sid),'invalid session identity')
    name=f'_Axis/Agents/{sid}.md';p=safe(root,name);lines=read(root,name).decode().splitlines()
    require(len(lines)==4 and lines[:3]==['Main: session','','session: '+sid] and lines[3].startswith('host: ') and bool(lines[3][6:]),'invalid Main identity')
    require(not safe(root,f'_Axis/Agents/{sid}.kill').exists() and 0<=time.time()-p.stat().st_mtime<3600,'inactive Main lease')
    for q in safe(root,'_Axis/Agents').glob('*.md'):
        if q!=p and not safe(root,str(q.relative_to(root).with_suffix('.kill'))).exists():
            require(time.time()-q.stat().st_mtime>=3600 or not read(root,q.relative_to(root).as_posix()).startswith(b'Main: session\n'),'foreign Main')
    s=safe(root,'_Axis/Flags/starting');starting=s.read_text().splitlines() if s.exists() else []
    if phase=='prepare':require(starting and starting[0]==sid,'startup identity mismatch')
    else:
        require(not starting or not starting[0].strip() or starting[0]=='cleared','startup incomplete')
        require(read(root,'_Axis/Flags/session-id').decode().splitlines()[0]==sid,'session identity mismatch')

def validate(root,sid,phase,expected):
    lease(root,sid,phase)
    if expected is not None:require(re.fullmatch('[0-9a-f]{64}',expected),'invalid independent content pin')
    project=read(root,'_Axis/PROJECT.md');lines=project.decode().splitlines();begin='<!-- axis:project-overlay:begin -->';end='<!-- axis:project-overlay:end -->'
    if begin not in lines and end not in lines:
        require(b'axis:project-overlay:' not in project,'malformed declaration marker');return {'state':'absent','presentation':'standard'}
    require(lines.count(begin)==lines.count(end)==1 and lines.index(begin)<lines.index(end),'malformed declaration')
    fields=[line for line in lines[lines.index(begin)+1:lines.index(end)] if line.strip()]
    require(fields and fields[0] in ('project-overlay-schema: 1','project-overlay-schema: 2'),'unsupported schema')
    schema=int(fields[0][-1]);require(len(fields)==(3 if schema==1 else 4),'invalid field count')
    keys=['project-overlay-schema','project-overlay-id','project-overlay-path']+(['project-overlay-sha256'] if schema==2 else [])
    values=[]
    for field,key in zip(fields,keys):
        require(field.startswith(key+': ') and field.count(key+': ')==1,'invalid field order');values.append(field[len(key)+2:])
    oid,name=values[1:3];require(re.fullmatch('[a-z0-9][a-z0-9._-]{7,127}',oid),'invalid overlay ID');require(name.endswith('.md'),'overlay must be Markdown')
    forbidden=('_Axis/Secrets/','_Axis/Agents/','_Axis/Flags/','_Axis/Tracking/','_Temp/','_Trash/','Wiki/')
    require(not name.casefold().startswith(tuple(v.casefold() for v in forbidden)) and not any(p.casefold()=='.git' for p in name.split('/')),'forbidden overlay path')
    source=read(root,name);require(len(source)<=20000,'overlay exceeds size limit');text=source.decode();sl=text.splitlines()
    require(len(sl)>=2 and sl[0].startswith('# Project Overlay: ') and sl[1].startswith('> **Purpose:**'),'invalid overlay header')
    require([v for v in sl if v.startswith('project-overlay-schema:')]==['project-overlay-schema: 1'] and [v for v in sl if v.startswith('project-overlay-id:')]==['project-overlay-id: '+oid],'source identity mismatch')
    terminal='<!-- axis:project-overlay-file:end -->';require(sl.count(terminal)==1 and text.rstrip().endswith(terminal),'incomplete overlay')
    digest=hashlib.sha256(source).hexdigest();rsi=oid.startswith('axis-rsi-controller-')
    if schema==2:require(values[3]==digest,'declaration content mismatch')
    if schema==1 or rsi:require(expected is not None,'independent content pin required')
    if expected is not None:require(expected==digest,'independent content mismatch')
    lease(root,sid,phase);require(read(root,'_Axis/PROJECT.md')==project and read(root,name)==source,'identity changed during validation')
    return {'state':'valid','schema':schema,'id':oid,'path':name,'project_sha256':hashlib.sha256(project).hexdigest(),'sha256':digest,'presentation':'rsi' if rsi else 'standard'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--session',required=True);p.add_argument('--phase',choices=('prepare','activate'),required=True);p.add_argument('--expected-sha256');a=p.parse_args()
    try:
        root=Path(a.root).absolute();require(root==root.resolve() and root.is_dir(),'canonical project root required')
        print(json.dumps(validate(root,a.session,a.phase,a.expected_sha256),sort_keys=True));return 0
    except (ValueError,OSError,IndexError,UnicodeError) as e:
        print('Overlay inactive: '+str(e),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
