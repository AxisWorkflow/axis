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
      deletions pass. Paths named by an update transaction whose evidence is added in the same commit pass, and so
      does an identifier correction whose Log the same commit adds (below).
  python3 _Axis/Resources/record-check.py correct --path {path} --old {wrong identifier} --new {right identifier}
      The one edit a write-once record takes, only after User approves it for that record: replace a wrong record
      identifier (a timestamp ID, or a path or reference built on one) with the right one, and change nothing else.
      Prints the Log fields the same commit must add.
  python3 _Axis/Resources/record-check.py links [--scope {folder} ...] [--archive]
      Read-only consistency scan of the record folders, the index and Plan files and _Memos/ (or the named paths): malformed identifier
      timestamps (a missing or invented part, a wildcard), identifiers that name no record, session, update, Request
      or Evidence folder, and relative links whose target is missing (or moved, when the same name exists elsewhere).
      Metadata fields such as created: are values, not references. Prints locations, never contents; exit 1 on findings.
      --staged (^save): refuse only the problems staged records add beyond their HEAD version.
      --range {old}..{new} (^resume): scan the in-scope files a received range changed.
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

IDENT=re.compile(r'\d{4}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{2}\.\d{3}Z')
REF=re.compile(r'[A-Za-z0-9_./*~-]{1,200}')

def correct(root,path,old,new):
    """Replace old with new in one write-once record and nothing else (Rules > RecordsAndWORM > Identifier correction)."""
    rel=path.strip('/')
    if '..' in rel.split('/') or rule_kind(rel) is None:return 1,['REFUSED: not a write-once record path under _Axis/']
    if not (REF.fullmatch(old) and REF.fullmatch(new)) or old==new or not IDENT.search(new) or not re.search(r'\d{4}\.\d{2}\.\d{2}',old):
        return 1,['REFUSED: --old and --new must be single record references: --old holding at least a timestamp date, --new a full identifier timestamp']
    f=root/rel
    if f.is_symlink() or not f.is_file():return 1,['REFUSED: no such record']
    data=f.read_bytes();o,n=old.encode(),new.encode();count=data.count(o)
    if count==0:return 1,['REFUSED: the wrong identifier does not occur in the record']
    after=data.replace(o,n);tmp=f.with_name('.'+f.name+'.axis-correct');tmp.write_bytes(after);os.replace(tmp,f)
    if f.read_bytes()!=after:return 1,['REFUSED: readback failed']
    import hashlib
    return 0,[f'correction-path: {rel}',f'correction-old: {old}',f'correction-new: {new}',f'occurrences: {count}',
              'before-sha256: '+hashlib.sha256(data).hexdigest(),'after-sha256: '+hashlib.sha256(after).hexdigest(),
              'OK: commit this with a Log whose Subject is "Identifier correction: {record}" and which carries the lines above and User\'s approval']

def rule_kind(rel):
    parts=rel.split('/')
    if len(parts)<3 or parts[0]!='_Axis' or parts[-1] in IGNORED:return None
    if parts[1]=='Archive' or parts[1] in WORM or parts[1] in ('Tasks','Followups','Reminders'):return parts[1]
    return None

def corrections(root,added):
    """Write-once paths whose staged change is exactly an identifier correction named by a Log this commit adds."""
    ok=set()
    for p in added:
        if not (p.startswith('_Axis/Logs/') and p.endswith('.md')):continue
        data=git(root,'show',':'+p)
        if data is None:continue
        text=data.decode('utf-8','replace')
        if not text.startswith('Identifier correction: '):continue
        f={k:field(text,k) for k in ('correction-path','correction-old','correction-new')}
        if not all(f.values()):continue
        head,staged=git(root,'show','HEAD:'+f['correction-path']),git(root,'show',':'+f['correction-path'])
        if head is None or staged is None:continue
        if head.count(f['correction-old'].encode()) and head.replace(f['correction-old'].encode(),f['correction-new'].encode())==staged:ok.add(f['correction-path'])
    return ok

NEAR=re.compile(r'(?<![\w.])\d{4}\.\d{2}\.\d{2}\.\d{2}[0-9A-Za-z.:*?]*')
SCOPE=['_Axis/Logs','_Axis/Snapshots','_Axis/Tasks','_Axis/Followups','_Axis/Reminders','_Axis/Notes','_Axis/Ideas','_Axis/CX','_Axis/Audit',
       '_Axis/Reviews','_Axis/Supervision','_Axis/Requests','_Axis/TASKS.md','_Axis/SNAPSHOTS.md','_Axis/PLAN.md','_Axis/INITIATIVES.md',
       '_Axis/PROJECT.md','_Axis/INSTRUCTIONS.md','_Memos']
LINK=re.compile(r'\[[^\]\n]*\]\(([^)\s]+)\)')
VALUE=re.compile(r'^\s*(?:[-*]\s*)?(?:\*\*)?(created|updated|completed|cancelled|raised|resolved|reviewed|verified|released|compiled|due-at|started|generated|when|date|at|time)(?:\*\*)?:',re.I)

def archive_root(root):
    try:text=(root/'_Axis/SETTINGS.md').read_text(encoding='utf-8')
    except OSError:return None
    m=re.search(r'^### Archive Location\s*$.*?^\*\*Value:\*\*\s*(.+?)\s*$',text,re.M|re.S)
    v=(m.group(1).strip() if m else '_Axis/Archive/')
    if v.startswith('~/'):v=os.path.expanduser('~')+v[1:]
    p=Path(v) if os.path.isabs(v) else root/v
    return p if p.is_dir() else None

def identities(root,arch):
    """Every identifier timestamp that names something real: record files, path names, sessions."""
    known=set()
    for base in [root/'_Axis',root/'_Dev/Evidence',root/'_Memos']+([arch] if arch else []):
        if not base.is_dir():continue
        for dirpath,dirs,files in os.walk(base):
            dirs[:]=[d for d in dirs if d not in ('Secrets','.git','node_modules')]
            for n in dirs+files:known.update(IDENT.findall(n))
    return known

def context(root,scopes,with_archive):
    """Files in scope with their text, plus everything an identifier or link may resolve to."""
    arch=archive_root(root);known=identities(root,arch);files=[]
    for sc in scopes:
        base=root/sc
        if base.is_file():files.append(base);continue
        for dirpath,dirs,names in os.walk(base):
            dirs[:]=[d for d in dirs if d not in ('Secrets','.git','node_modules','Dashboard','Branding')]
            files+=[Path(dirpath)/n for n in names if n.endswith('.md')]
    if with_archive and arch:files+=[p for p in arch.rglob('*.md')]
    texts={}
    for f in files:
        try:texts[f]=f.read_text(encoding='utf-8',errors='replace')
        except OSError:continue
        known.update(re.findall(r'session[^\n]{0,12}?('+IDENT.pattern+')',texts[f],re.I))
    tracking=root/'_Axis/Tracking'
    if tracking.is_dir():known.update(x for n in os.listdir(tracking) for x in IDENT.findall(n))
    names={}
    for f in files:names.setdefault(f.name,[]).append(f)
    if arch:
        for q in arch.rglob('*.md'):names.setdefault(q.name,[]).append(q)
    return arch,known,names,texts

def scan(root,arch,known,names,f,text,rel):
    """Findings in one file: (kind, line, detail, write-once?)."""
    from urllib.parse import unquote
    out=[]
    kind=rule_kind(rel);done=(kind=='Tasks' and (field(text,'status') or '').casefold() in ('completed','cancelled')) or (kind in ('Followups','Reminders') and (field(text,'outcome') or 'N/A') not in ('N/A',''))
    worm=kind in WORM or done or rel.startswith(('_Axis/Archive/','ARCHIVE/'))
    for i,line in enumerate(text.splitlines(),1):
        if VALUE.match(line) or '<!-- compiled:' in line or re.fullmatch(r'\s*[\w-]+:\s*'+IDENT.pattern+r'\s*',line) or re.match(r'#+ .* - '+IDENT.pattern+r'\s*$',line):continue
        bare=re.sub(r'[a-z][a-z0-9+.-]*://\S+',lambda u:' '*len(u.group(0)),line,flags=re.I)
        for m in NEAR.finditer(bare):
            tok=m.group(0).rstrip('.:');full=IDENT.match(tok)
            if not full:
                if re.fullmatch(r'\d{4}\.\d{2}\.\d{2}\.\d{2}',tok) or line[m.end():].lstrip().startswith('UTC'):continue
                out.append(('MALFORMED',i,tok,worm))
            elif tok[full.end():].startswith('.tsclaim') or re.search(r'(session|Main|External|Subagent|e\.g\.)\W{0,4}$',line[:m.start()],re.I):continue
            elif full.group(0) not in known and full.group(0)!=f.stem:out.append(('UNRESOLVED',i,full.group(0),worm))
        for m in LINK.finditer(line):
            target=m.group(1)
            if re.match(r'^[a-z][a-z0-9+.-]*:',target,re.I) or target.startswith(('#','/')):continue
            t=unquote(target.split('#',1)[0].split('?',1)[0])
            if not t or (f.parent/t).exists():continue
            local=Path(os.path.normpath((f.parent/t).as_posix()))
            if arch:
                try:
                    sub=local.relative_to(root/'_Axis/Archive') if local.is_relative_to(root/'_Axis/Archive') else local.relative_to(root)
                    if (arch/sub).exists():continue
                except ValueError:pass
            alt=[q for q in names.get(Path(t).name,[]) if q!=f]
            if alt:out.append(('MOVED-LINK',i,target+' -> '+(alt[0].relative_to(root).as_posix() if alt[0].is_relative_to(root) else 'Archive/'+alt[0].relative_to(arch).as_posix()),worm))
            else:out.append(('BROKEN-LINK',i,target,worm))
    return out

def report(found,count,arch):
    counts={k:0 for k in ('MALFORMED','UNRESOLVED','BROKEN-LINK','MOVED-LINK')}
    for _,(k,_,_,_) in found:counts[k]+=1
    rows=[f'{k} {rel}:{i} {d}'+(' (write-once)' if w else '') for rel,(k,i,d,w) in found]
    lines=rows[:LIMIT*4]+([f'... {len(rows)-LIMIT*4} more'] if len(rows)>LIMIT*4 else [])
    summary=', '.join(f'{v} {k.lower()}' for k,v in counts.items())
    return (1 if found else 0),([] if arch else ['NOTE: Archive Location unavailable; archived targets were not checked'])+lines+[('FINDINGS: ' if found else 'OK: ')+summary+f' in {count} files']

def relof(root,arch,f):
    return f.relative_to(root).as_posix() if f.is_relative_to(root) else 'ARCHIVE/'+f.relative_to(arch).as_posix()

def links(root,scopes,with_archive):
    arch,known,names,texts=context(root,scopes,with_archive);found=[]
    for f,text in texts.items():
        rel=relof(root,arch,f);found+=[(rel,x) for x in scan(root,arch,known,names,f,text,rel)]
    return report(found,len(texts),arch)

def in_scope(rel):
    return rel.endswith('.md') and any(rel==s or rel.startswith(s+'/') for s in SCOPE)

def links_range(root,span):
    """Handoff check (^resume): scan the in-scope files a received range changed."""
    if not exact_repo(root):return 2,['UNAVAILABLE: no Git repository at this root']
    raw=git(root,'diff','--name-only','-z',span)
    if raw is None:return 2,['UNAVAILABLE: git diff '+span+' failed']
    arch,known,names,_=context(root,SCOPE,False);found=[];n=0
    for rel in [p for p in raw.decode('utf-8','surrogateescape').split('\0') if p and in_scope(p)]:
        f=root/rel
        if not f.is_file():continue
        n+=1;found+=[(rel,x) for x in scan(root,arch,known,names,f,f.read_text(encoding='utf-8',errors='replace'),rel)]
    return report(found,n,arch)

def links_staged(root):
    """Commit check (^save): refuse a reference problem a staged record adds; problems already at HEAD are history."""
    if not exact_repo(root):return 2,['UNAVAILABLE: no Git repository at this root']
    raw=git(root,'diff','--cached','--name-only','-z','--diff-filter=AMR')
    if raw is None:return 2,['UNAVAILABLE: git diff --cached failed']
    arch,known,names,_=context(root,SCOPE,False);new=[];n=0
    for rel in [p for p in raw.decode('utf-8','surrogateescape').split('\0') if p and in_scope(p)]:
        staged=git(root,'show',':'+rel)
        if staged is None:continue
        n+=1;f=root/rel;head=git(root,'show','HEAD:'+rel) if has_head(root) else None
        before={}
        for k,_,d,_ in (scan(root,arch,known,names,f,head.decode('utf-8','replace'),rel) if head is not None else []):before[(k,d)]=before.get((k,d),0)+1
        for x in scan(root,arch,known,names,f,staged.decode('utf-8','replace'),rel):
            if before.get((x[0],x[2]),0):before[(x[0],x[2])]-=1
            else:new.append((rel,x))
    code,lines=report(new,n,arch)
    if code:return 1,lines[:-1]+[f'REFUSED: {len(new)} new reference problem(s) in staged records; fix them (copy each identifier from disk) before committing']
    return 0,['OK']

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
    exempt=update_exempt(root,[p for s,p,_ in entries if s=='A'])|corrections(root,[p for s,p,_ in entries if s=='A'])
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
    c=sub.add_parser('correct');c.add_argument('--path',required=True);c.add_argument('--old',required=True);c.add_argument('--new',required=True)
    k=sub.add_parser('links');k.add_argument('--scope',action='append');k.add_argument('--archive',action='store_true')
    k.add_argument('--staged',action='store_true');k.add_argument('--range')
    a=p.parse_args();root=Path(os.path.abspath(a.root))
    if a.check=='names' and a.since is not None and not re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',a.since):
        print('UNAVAILABLE: --since is not a Session ID');return 2
    if not (root/'_Axis').is_dir():print('UNAVAILABLE: run from the project root');return 2
    if a.check=='links':code,lines=links_staged(root) if a.staged else links_range(root,a.range) if a.range else links(root,a.scope or SCOPE,a.archive)
    else:code,lines=names(root,a.since) if a.check=='names' else correct(root,a.path,a.old,a.new) if a.check=='correct' else write_once(root)
    for line in lines:print(line)
    return code

if __name__=='__main__':sys.exit(main())
