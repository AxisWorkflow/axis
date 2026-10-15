#!/usr/bin/env python3
"""Optional pre-commit record checks for ^save. Python3 standard library and Git; no network or model calls.
Reads names, Git metadata and the status lines of Tasks, Follow-Ups and Reminders; never prints record contents.

Run from the project root:
  python3 _Axis/Resources/record-check.py names [--since {Session ID}]
      Record filenames in the twelve record folders and the in-project Archive. A name that is not exactly
      yyyy.mm.dd.hh.mm.ss.xxxZ.md refuses the commit (^refresh repairs it); a .000Z name new since the last
      commit (or, without Git, at or after --since) is reported.
  python3 _Axis/Resources/record-check.py write-once
      Staged changes against HEAD. A modified write-once file refuses the commit; renames (archive moves) and
      deletions pass. Paths named by an update transaction whose evidence is added in the same commit pass.
Exit 0 prints OK (after any warning lines); 1 prints REFUSED; 2 means this check cannot run: use the manual steps."""
import argparse,datetime as dt,json,os,re,subprocess,sys
from pathlib import Path

NAME=re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md')
FAMILIES=('Audit','CX','Followups','Ideas','Logs','Notes','Reminders','Reviews','Snapshots','Status','Supervision','Tasks')
IGNORED=('.gitkeep','.DS_Store')
WORM={'Logs':'Logs','Snapshots':'Snapshots','CX':'CX reports','Audit':'Audit reports','Reviews':'Review reports',
      'Status':'Status reports','Supervision':'Supervision records'}
LIMIT=50

def valid(name):
    if not NAME.fullmatch(name):return False
    try:dt.datetime.strptime(name[:-3],'%Y.%m.%d.%H.%M.%S.%fZ');return True
    except ValueError:return False

def git(root,*args):
    try:r=subprocess.run(['git','-C',str(root),*args],capture_output=True,timeout=30)
    except (OSError,subprocess.TimeoutExpired):return None
    return r.stdout if r.returncode==0 else None

def exact_repo(root):
    top=git(root,'rev-parse','--show-toplevel')
    return top is not None and os.path.realpath(top.decode().strip())==os.path.realpath(root)

def has_head(root):return git(root,'rev-parse','--verify','-q','HEAD^{commit}') is not None

def names(root,since):
    malformed=[];zero=[];folders=['_Axis/'+f for f in FAMILIES]
    archive=root/'_Axis/Archive'
    if archive.is_dir() and not archive.is_symlink():
        for entry in sorted(archive.iterdir()):
            if entry.name in IGNORED:continue
            if entry.is_dir() and not entry.is_symlink():folders.append('_Axis/Archive/'+entry.name)
            else:malformed.append('_Axis/Archive/'+entry.name)
    found=[]
    for folder in folders:
        base=root/folder
        if not base.is_dir() or base.is_symlink():continue
        for entry in sorted(base.iterdir()):
            relative=folder+'/'+entry.name
            if entry.name in IGNORED and not entry.is_symlink():continue
            if entry.is_symlink() or not entry.is_file() or not valid(entry.name):malformed.append(relative)
            else:found.append(relative)
    known=None
    if exact_repo(root):
        if has_head(root):
            listing=git(root,'ls-tree','-r','-z','--name-only','HEAD','--','_Axis')
            if listing is None:return 2,['UNAVAILABLE: git ls-tree failed']
            known={p.rsplit('/',1)[-1] for p in listing.decode('utf-8','surrogateescape').split('\0') if p}
        else:known=set()
    lines=[]
    for relative in found:
        name=relative.rsplit('/',1)[-1]
        if not name.endswith('.000Z.md'):continue
        if known is not None and name not in known:zero.append(relative)
        elif known is None and since and name[:-3]>=since:zero.append(relative)
    if known is None and not since:lines.append('NOTE: no Git repository at this root and no --since; zero-millisecond check skipped')
    lines+=['MALFORMED '+p for p in malformed[:LIMIT]]+(['MALFORMED ... '+str(len(malformed)-LIMIT)+' more'] if len(malformed)>LIMIT else [])
    lines+=['ZERO-MS '+p for p in zero[:LIMIT]]+(['ZERO-MS ... '+str(len(zero)-LIMIT)+' more'] if len(zero)>LIMIT else [])
    if malformed:return 1,lines+[f'REFUSED: {len(malformed)} malformed record name(s); do not commit; ^refresh repairs record names']
    if zero:lines.append(f'WARNING: {len(zero)} new record name(s) end in .000Z (zeroed milliseconds); ^audit and ^refresh review them')
    return 0,lines+['OK']

def field(text,key):
    for line in text.splitlines():
        m=re.fullmatch(key+r':[ \t]*(.*)',line.strip())
        if m:return m[1].strip().strip('*').strip()
    return None

def rule(root,path):
    """The write-once rule that covers path as committed at HEAD, or None."""
    parts=path.split('/')
    if len(parts)<3 or parts[0]!='_Axis' or parts[-1] in IGNORED:return None
    family=parts[1]
    if family=='Archive':return 'archived history is write-once'
    if family=='Updates':return None if parts[-1]=='operation.lck' else 'update evidence is write-once'
    if family in WORM:return WORM[family]+' are write-once'
    if family in ('Tasks','Followups','Reminders') and len(parts)==3:
        data=git(root,'show','HEAD:'+path)
        if data is None:return None
        text=data.decode('utf-8','replace')
        if family=='Tasks':
            if (field(text,'status') or '').casefold() in ('completed','cancelled'):return 'a Completed or Cancelled Task is write-once'
        elif (field(text,'outcome') or 'N/A') not in ('N/A',''):
            return ('a resolved Follow-Up' if family=='Followups' else 'a terminal Reminder')+' is write-once'
    return None

def update_exempt(root,added):
    """Paths named by an update transaction whose evidence this commit adds (apply, adoption or rollback)."""
    exempt=set()
    for tx in sorted({p.split('/')[2] for p in added if p.startswith('_Axis/Updates/') and p.count('/')>=3}):
        data=git(root,'show',':_Axis/Updates/'+tx+'/start.json')
        try:
            plan=json.loads(data.decode())['plan']
            exempt|={c['path'] for c in plan['changes']}|set(plan.get('reconciliation',{}))|set(plan.get('migration_paths',[]))
            exempt|={r['archive_to'] for r in plan.get('reconciliation',{}).values() if 'archive_to' in r}
        except (AttributeError,ValueError,KeyError,TypeError):continue
    return exempt

def write_once(root):
    if not exact_repo(root):return 2,['UNAVAILABLE: no Git repository at this root']
    if not has_head(root):return 0,['OK']
    raw=git(root,'-c','core.quotePath=false','diff','--cached','--no-ext-diff','--name-status','-z','-M','HEAD')
    if raw is None:return 2,['UNAVAILABLE: git diff --cached failed']
    tokens=raw.decode('utf-8','surrogateescape').split('\0');entries=[];i=0
    while i<len(tokens) and tokens[i]:
        status=tokens[i]
        if status[:1] in 'RC':entries.append((status,tokens[i+1],tokens[i+2]));i+=3
        else:entries.append((status,tokens[i+1],None));i+=2
    exempt=update_exempt(root,[p for s,p,_ in entries if s=='A'])
    # A move Git did not pair (heavy edit, rename limit) keeps its identity: pair a deletion and an addition by name.
    deleted={p.rsplit('/',1)[-1]:p for s,p,_ in entries if s=='D'}
    for status,path,_ in list(entries):
        old=deleted.get(path.rsplit('/',1)[-1]) if status=='A' else None
        if old and git(root,'rev-parse','HEAD:'+old)!=git(root,'rev-parse',':'+path):entries.append(('R000',old,path))
    refused=[]
    for status,path,new in entries:
        if status[:1] in 'MT':why=rule(root,path);label=path
        elif status[:1]=='R' and status!='R100':why=rule(root,path);label=path+' -> '+new;why=why and why+' (renamed with changes)'
        else:continue
        if why and path not in exempt:refused.append('WRITE-ONCE '+label+': '+why)
    if refused:return 1,refused[:LIMIT]+[f'REFUSED: {len(refused)} write-once file(s) changed; do not commit; show User these paths and ask how to proceed']
    return 0,['OK']

def main():
    p=argparse.ArgumentParser(description='Axis pre-commit record checks');p.add_argument('--root',default='.')
    sub=p.add_subparsers(dest='check',required=True);n=sub.add_parser('names');n.add_argument('--since');sub.add_parser('write-once')
    a=p.parse_args();root=Path(os.path.abspath(a.root))
    if a.check=='names' and a.since is not None and not re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',a.since):
        print('UNAVAILABLE: --since is not a Session ID');return 2
    if not (root/'_Axis').is_dir():print('UNAVAILABLE: run from the project root');return 2
    code,lines=names(root,a.since) if a.check=='names' else write_once(root)
    for line in lines:print(line)
    return code

if __name__=='__main__':sys.exit(main())
