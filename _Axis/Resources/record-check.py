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
      The one edit a write-once record takes, under LinkMaintenance Permissions: replace a wrong record
      identifier (a timestamp ID, or a path or reference built on one) with the right one, and change nothing else.
      --link replaces exact simple Markdown destinations only. Prints the Log fields the same commit must add.
  python3 _Axis/Resources/record-check.py links [--scope {folder} ...] [--archive]
      Read-only consistency scan of the record folders, the index and Plan files and _Memos/ (or the named paths): malformed identifier
      timestamps (a missing or invented part, a wildcard), identifiers that name no record, session, update, Submission
      or Evidence folder, and relative links whose target is missing (or moved, when the same name exists elsewhere).
      Metadata fields such as created: are values, not references. An identifier followed by `(missing)` reports a
      record known to be missing and counts as acknowledged, not a finding; identifiers listed in
      _Dev/Evidence/DELETED.md (removed development Evidence) resolve. Prints locations, never contents; exit 1 on findings.
      Optional _Axis/EXCEPTIONS.md binds acknowledged historical quotations to exact source bytes and occurrences;
      acknowledged exceptions remain visible, stale entries never suppress findings, invalid registries refuse the check.
      --staged (^save): refuse only the problems staged records add beyond their HEAD version.
      --range {old}..{new} (^resume): scan the in-scope files a received range changed. Git checks use their index or
      destination-commit registry and source bytes, never uncommitted working-tree exceptions.
Exit 0 prints OK (after any warning lines); 1 prints REFUSED; 2 means this check cannot run: use the manual steps."""
import argparse,datetime as dt,hashlib,json,os,re,subprocess,sys
from pathlib import Path,PurePosixPath

NAME=re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md')
FAMILIES=('Audit','CX','Followups','Ideas','Logs','Notes','Reminders','Reviews','Snapshots','Status','Supervision','Tasks','Teams','Messages','Jobs','Schedules')
IGNORED=('.gitkeep','.DS_Store')
WORM={'Logs':'Logs','Snapshots':'Snapshots','CX':'CX reports','Audit':'Audit reports','Reviews':'Review reports',
      'Status':'Status reports','Supervision':'Supervision records','Teams':'Team charters',
      'Messages':'Messages','Jobs':'Job mandates'}
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
            if entry.name=='Imports' and entry.is_dir() and not entry.is_symlink():
                for transaction in sorted(entry.iterdir()):
                    if not transaction.is_dir() or transaction.is_symlink() or not valid(transaction.name+'.md'):
                        malformed.append(transaction.relative_to(root).as_posix());continue
                    for family in sorted(transaction.iterdir()):
                        relative=family.relative_to(root).as_posix()
                        if family.name not in ('Snapshots','Teams','Messages','Jobs','Schedules') or not family.is_dir() or family.is_symlink():
                            malformed.append(relative)
                        else:folders.append(relative)
            elif entry.is_dir() and not entry.is_symlink():folders.append('_Axis/Archive/'+entry.name)
            else:malformed.append('_Axis/Archive/'+entry.name)
    found=[]
    for folder in folders:
        base=root/folder
        if not base.is_dir() or base.is_symlink():continue
        for entry in sorted(base.iterdir()):
            relative=folder+'/'+entry.name
            if entry.name in IGNORED and not entry.is_symlink():continue
            if folder.endswith(('/Teams','/Messages')) and entry.is_dir() and not entry.is_symlink() and valid(entry.name+'.md') and (base/(entry.name+'.md')).is_file() and not (base/(entry.name+'.md')).is_symlink() and (base/(entry.name+'.md')).stat().st_nlink==1:continue
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
    if family=='Merges':return 'merge history is write-once and retained'
    if family in WORM and (family not in ('Teams','Messages','Jobs') or len(parts)==3):return WORM[family]+' are write-once'
    if family in ('Tasks','Followups','Reminders') and len(parts)==3:
        data=git(root,'show','HEAD:'+path)
        if data is None:return None
        text=data.decode('utf-8','replace')
        if family=='Tasks':
            if (field(text,'status') or '').casefold() in ('completed','cancelled'):return 'a Completed or Cancelled Task is write-once'
        elif (field(text,'outcome') or 'N/A') not in ('N/A',''):
            return ('a resolved Follow-Up' if family=='Followups' else 'a terminal Reminder')+' is write-once'
    return None

def compaction_exempt(root,added):
    """A receipt accounts for exact deletions only; it never waives a retained-file modification."""
    removed=set()
    for path in added:
        if not re.fullmatch(r'_Axis/Updates/'+IDENT.pattern+r'/compacted\.json',path):continue
        prefix=path.rsplit('/',1)[0]+'/'
        try:
            value=json.loads(git(root,'show',':'+path).decode(),object_pairs_hook=_json_unique)
            items=value['removed'];canonical=(json.dumps(items,sort_keys=True,indent=2)+'\n').encode()
            if value['schema']!=1 or value['transaction']!=path.split('/')[2] or hashlib.sha256(canonical).hexdigest()!=value['removed_sha256']:continue
            kept=value['kept']
            if not isinstance(kept,list) or not isinstance(items,list):continue
            accounted=set()
            for item in items:
                if set(item)!={'name','sha256','bytes'} or not _safe_relative(item['name']) or '/' in item['name'] or item['name'] in kept:break
                old=git(root,'show','HEAD:'+prefix+item['name']);new=git(root,'show',':'+prefix+item['name'])
                if old is not None and new is None and len(old)==item['bytes'] and hashlib.sha256(old).hexdigest()==item['sha256']:accounted.add(prefix+item['name'])
            else:removed.update(accounted)
        except (ValueError,KeyError,TypeError,AttributeError):continue
    return removed

def update_exempt(root,added):
    """Paths named by an update transaction whose evidence this commit adds (apply, adoption or rollback)."""
    exempt=compaction_exempt(root,added)
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

def replace_link(data,old,new):
    """Exact one-line Markdown destinations only, excluding code and block quotations."""
    if old==new or not all(isinstance(s,str) and 0<len(s)<=4096 and not re.search(r'[\s<>`\\()]',s) for s in (old,new)):
        raise ValueError('link destinations must be distinct nonempty single-line tokens')
    if re.match(r'(?i)^(javascript|data|vbscript):',new):raise ValueError('active link schemes are not repair destinations')
    text=data.decode('utf-8');out=[];count=0;fence=None
    for line in text.splitlines(keepends=True):
        mark=re.match(r'^ {0,3}(`{3,}|~{3,})',line)
        if mark:
            token=mark[1]
            if fence is None:fence=token
            elif token[0]==fence[0] and len(token)>=len(fence):fence=None
            out.append(line);continue
        if fence or line.startswith(('    ','\t')) or line.lstrip().startswith('>'):
            out.append(line);continue
        code=[m.span() for m in re.finditer(r'(`+).*?\1',line)]
        spans=[m.span(1) for m in LINK.finditer(line) if m[1]==old and not any(a<=m.start()<b for a,b in code)]
        for a,b in reversed(spans):line=line[:a]+new+line[b:]
        count+=len(spans);out.append(line)
    if not count:raise ValueError('no unquoted Markdown destination matches --old')
    return ''.join(out).encode('utf-8'),count

def protected_coordination_detail(rel,data):
    return bool(re.match(r'^_Axis/(?:Archive/)?(?:Teams|Messages|Jobs|Schedules)/',rel) or re.search(rb'^checksum-sha256: [^\r\n]+\r?$',data,re.M))

def correct(root,path,old,new,link=False):
    """Replace old with new in one write-once record and nothing else (Rules > RecordsAndWORM > Identifier correction)."""
    rel=path
    if not _safe_relative(rel) or rule_kind(rel) is None or (link and not rel.endswith('.md')):return 1,['REFUSED: not a write-once record path under _Axis/']
    if not link and (not (REF.fullmatch(old) and REF.fullmatch(new)) or old==new or not IDENT.search(new) or not re.search(r'\d{4}\.\d{2}\.\d{2}',old)):
        return 1,['REFUSED: --old and --new must be single record references: --old holding at least a timestamp date, --new a full identifier timestamp']
    f=root/rel
    if any(p.is_symlink() for p in (f,*f.parents)) or not f.is_file() or f.stat().st_nlink!=1:return 1,['REFUSED: no such ordinary record']
    data=f.read_bytes()
    if protected_coordination_detail(rel,data):return 1,['REFUSED: checked Coordination history cannot be rewritten; append a correction record or exact exception']
    o,n=old.encode(),new.encode();count=data.count(o)
    if count==0:return 1,['REFUSED: the wrong identifier does not occur in the record']
    try:after,count=replace_link(data,old,new) if link else (data.replace(o,n),count)
    except (ValueError,UnicodeError) as error:return 1,['REFUSED: '+str(error)]
    import tempfile,stat
    fd,name=tempfile.mkstemp(prefix='.'+f.name+'.axis-correct-',dir=f.parent);tmp=Path(name)
    try:
        with os.fdopen(fd,'wb') as stream:
            os.fchmod(stream.fileno(),stat.S_IMODE(f.stat().st_mode));stream.write(after);stream.flush();os.fsync(stream.fileno())
        if f.read_bytes()!=data:return 1,['REFUSED: source changed before replacement']
        os.replace(tmp,f)
    finally:
        if tmp.exists():tmp.unlink()
    if f.read_bytes()!=after:return 1,['REFUSED: readback failed']
    import hashlib
    return 0,[f'correction-path: {rel}',f'correction-old: {old}',f'correction-new: {new}',f'correction-mode: {"link" if link else "identifier"}',f'occurrences: {count}',
              'before-sha256: '+hashlib.sha256(data).hexdigest(),'after-sha256: '+hashlib.sha256(after).hexdigest(),
              'OK: commit this with a Log whose Subject is "Identifier correction: {record}" and which carries these fields, target evidence, Permissions authorization and rollback']

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
        if not all(f.values()) or not _safe_relative(f['correction-path']) or rule_kind(f['correction-path']) is None:continue
        head,staged=git(root,'show','HEAD:'+f['correction-path']),git(root,'show',':'+f['correction-path'])
        if head is None or staged is None:continue
        if protected_coordination_detail(f['correction-path'],head) or protected_coordination_detail(f['correction-path'],staged):continue
        mode=field(text,'correction-mode') or 'identifier'
        if mode=='link':
            if not f['correction-path'].endswith('.md'):continue
            try:expected,count=replace_link(head,f['correction-old'],f['correction-new'])
            except (ValueError,UnicodeError):continue
            if expected==staged and field(text,'before-sha256')==hashlib.sha256(head).hexdigest() and field(text,'after-sha256')==hashlib.sha256(staged).hexdigest() and field(text,'occurrences')==str(count):ok.add(f['correction-path'])
        elif mode=='identifier':
            old,new=f['correction-old'],f['correction-new']
            if REF.fullmatch(old) and REF.fullmatch(new) and old!=new and IDENT.search(new) and re.search(r'\d{4}\.\d{2}\.\d{2}',old) and head.count(old.encode()) and head.replace(old.encode(),new.encode())==staged:ok.add(f['correction-path'])
    return ok

NEAR=re.compile(r'(?<![\w.])\d{4}\.\d{2}\.\d{2}\.\d{2}[0-9A-Za-z.:*?]*')
SCOPE=['_Axis/Logs','_Axis/Snapshots','_Axis/Tasks','_Axis/Followups','_Axis/Reminders','_Axis/Notes','_Axis/Ideas','_Axis/CX','_Axis/Audit',
       '_Axis/Reviews','_Axis/Supervision','_Axis/Teams','_Axis/Messages','_Axis/Jobs','_Axis/Schedules','_Axis/TEAMS.md','_Axis/MESSAGES.md','_Axis/JOBS.md','_Axis/SCHEDULES.md','_Axis/TASKS.md','_Axis/SNAPSHOTS.md','_Axis/PLAN.md','_Axis/INITIATIVES.md',
       '_Axis/PROJECT.md','_Axis/INSTRUCTIONS.md','_Memos']
LINK=re.compile(r'\[[^\]\n]*\]\(([^)\s]+)\)')
VALUE=re.compile(r'^\s*(?:[-*]\s*)?(?:\*\*)?(created|updated|completed|cancelled|raised|resolved|reviewed|verified|released|compiled|due-at|started|generated|when|date|at|time)(?:\*\*)?:',re.I)

EXCEPTIONS_PATH='_Axis/EXCEPTIONS.md'
EXCEPTIONS_LIMIT=262144
EXCEPTIONS_COUNT=1000
EXCEPTION_KINDS={'MALFORMED','UNRESOLVED','BROKEN-LINK','MOVED-LINK'}
ACK_EXCEPTION='ACKNOWLEDGED-EXCEPTION'

class ExceptionsError(ValueError):
    """An exception registry cannot be trusted; callers must not silently ignore this error."""

def _safe_relative(value):
    return (isinstance(value,str) and bool(value) and len(value)<=1024 and
            not any(c in value for c in '\\*?[]\x00\r\n') and not value.startswith('/') and
            str(PurePosixPath(value))==value and
            not any(p in ('..','.git','Secrets') or p.endswith('_X') or Path(p).stem.endswith('_X') for p in value.split('/')) and value!='.')

def _json_unique(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ExceptionsError('duplicate JSON key: '+key)
        result[key]=value
    return result

def _working_source(root,rel,arch=None):
    """Read exact bytes without following source or parent symlinks. None means absent."""
    if not _safe_relative(rel):raise ExceptionsError('unsafe source path')
    if rel.startswith('ARCHIVE/'):
        if arch is None:return None
        base=arch;parts=rel.split('/')[1:]
    else:base=root;parts=rel.split('/')
    if base.is_symlink():raise ExceptionsError('symlinked source root: '+rel)
    path=base
    for part in parts:
        path=path/part
        if path.is_symlink():raise ExceptionsError('symlinked source: '+rel)
    try:
        with path.open('rb') as stream:
            data=stream.read(EXCEPTIONS_LIMIT+1) if rel==EXCEPTIONS_PATH else stream.read()
    except FileNotFoundError:return None
    except OSError as e:raise ExceptionsError('unreadable source: '+rel+' ('+type(e).__name__+')') from e
    return data

def _git_entries(root,revision):
    raw=git(root,'ls-files','--stage','-z') if revision=='INDEX' else git(root,'ls-tree','-r','-z',revision)
    if raw is None:raise ExceptionsError('cannot read '+revision+' file inventory')
    entries={}
    for entry in raw.split(b'\0'):
        if not entry:continue
        meta,path=entry.split(b'\t',1);parts=meta.decode('ascii').split()
        rel=path.decode('utf-8','surrogateescape')
        if revision=='INDEX' and parts[2]!='0':raise ExceptionsError('unmerged index entry: '+rel)
        entries[rel]=(parts[0],parts[1] if revision=='INDEX' else parts[2])
    return entries

def _git_reader(root,revision,entries=None):
    entries=_git_entries(root,revision) if entries is None else entries;cache={}
    def read(rel):
        if rel in cache:return cache[rel]
        if rel not in entries:return None
        mode,oid=entries[rel]
        if mode not in ('100644','100755'):raise ExceptionsError('non-regular '+revision+' source: '+rel)
        if rel==EXCEPTIONS_PATH:
            size=git(root,'cat-file','-s',oid)
            if size is None:raise ExceptionsError('cannot read registry size from '+revision)
            if int(size)>EXCEPTIONS_LIMIT:raise ExceptionsError('registry exceeds '+str(EXCEPTIONS_LIMIT)+' bytes')
        data=git(root,'cat-file','blob',oid)
        if data is None:raise ExceptionsError('cannot read '+revision+' source: '+rel)
        cache[rel]=data;return data
    return read

def load_exceptions(root,revision=None,reader=None):
    """Read optional EXCEPTIONS.md. revision=None means disk, INDEX or a commit selects Git bytes.

    A single fenced axis-link-exceptions JSON object has schema=1 and exceptions=[...]. Each
    exact entry binds path, source_sha256, kind, line, detail, occurrence and reason. occurrence
    is 1-based among findings with the same kind/line/detail. Invalid registries raise
    ExceptionsError (including duplicates, unknown fields and symlinks); absence returns [].
    """
    if reader is None:reader=_git_reader(root,revision) if revision else lambda rel:_working_source(root,rel)
    data=reader(EXCEPTIONS_PATH)
    if data is None:return []
    if len(data)>EXCEPTIONS_LIMIT:raise ExceptionsError('registry exceeds '+str(EXCEPTIONS_LIMIT)+' bytes')
    try:text=data.decode('utf-8')
    except UnicodeError as e:raise ExceptionsError('registry is not UTF-8') from e
    fences=re.findall(r'^```axis-link-exceptions[ \t]*\r?\n(.*?)^```[ \t]*\r?$',text,re.M|re.S)
    openings=re.findall(r'^```axis-link-exceptions[^\n]*$',text,re.M)
    if len(fences)!=1 or len(openings)!=1:raise ExceptionsError('registry needs exactly one axis-link-exceptions fenced block')
    try:obj=json.loads(fences[0],object_pairs_hook=_json_unique)
    except (ValueError,RecursionError) as e:raise ExceptionsError('invalid registry JSON: '+str(e)[:160]) from e
    if not isinstance(obj,dict) or set(obj)!={'schema','exceptions'} or type(obj['schema']) is not int or obj['schema']!=1:
        raise ExceptionsError('registry must contain only schema: 1 and exceptions')
    entries=obj['exceptions']
    if not isinstance(entries,list) or len(entries)>EXCEPTIONS_COUNT:raise ExceptionsError('exceptions must be a list of at most '+str(EXCEPTIONS_COUNT)+' entries')
    keys={'path','source_sha256','kind','line','detail','occurrence','reason'};seen=set()
    for i,e in enumerate(entries,1):
        prefix='exception '+str(i)+': '
        if not isinstance(e,dict) or set(e)!=keys:raise ExceptionsError(prefix+'unknown or missing fields')
        if not _safe_relative(e['path']) or e['path']==EXCEPTIONS_PATH or e['path']=='ARCHIVE':raise ExceptionsError(prefix+'path must be an exact safe project-relative or ARCHIVE/ path')
        if not isinstance(e['source_sha256'],str) or not re.fullmatch('[0-9a-f]{64}',e['source_sha256']):raise ExceptionsError(prefix+'source_sha256 must be a lowercase SHA-256')
        if not isinstance(e['kind'],str) or e['kind'] not in EXCEPTION_KINDS:raise ExceptionsError(prefix+'unsupported finding kind')
        if any(type(e[k]) is not int or not 1<=e[k]<=10000000 for k in ('line','occurrence')):raise ExceptionsError(prefix+'line and occurrence must be positive integers')
        if not isinstance(e['detail'],str) or not 1<=len(e['detail'])<=4096 or any(c in e['detail'] for c in '\x00\r\n'):raise ExceptionsError(prefix+'detail must be a nonempty single-line exact scanner detail')
        if not isinstance(e['reason'],str) or not e['reason'].strip() or len(e['reason'])>4096:raise ExceptionsError(prefix+'reason must be nonempty and at most 4096 characters')
        key=tuple(e[k] for k in ('path','source_sha256','kind','line','detail','occurrence'))
        if key in seen:raise ExceptionsError(prefix+'duplicate exception identity')
        seen.add(key)
    return entries

def _finding_occurrences(findings):
    counts={}
    for item in findings:
        k,line,detail,_=item;key=(k,line,detail);counts[key]=counts.get(key,0)+1
        yield item,(*key,counts[key])

def apply_exceptions(entries,rel,source_bytes,findings):
    """Pure exact matching; raw scan() stays compatible and does not load working-tree authority."""
    digest=hashlib.sha256(source_bytes).hexdigest()
    allowed={(e['kind'],e['line'],e['detail'],e['occurrence']):i for i,e in enumerate(entries,1)
             if e['path']==rel and e['source_sha256']==digest}
    return [(ACK_EXCEPTION,x[1],x[0]+' '+x[2]+' [exception '+str(allowed[key])+']',x[3]) if key in allowed else x
            for x,key in _finding_occurrences(findings)]

def exception_diagnostics(entries,reader,raw_findings=None):
    """Stale entries are visible, never authority. Findings outside this scan are not guessed."""
    rows=[];sources={};raw_findings=raw_findings or {}
    for i,e in enumerate(entries,1):
        rel=e['path'];why=None
        if rel not in sources:
            try:sources[rel]=reader(rel)
            except ExceptionsError as error:sources[rel]=str(error)
        data=sources[rel]
        if isinstance(data,str):why=data
        elif data is None:why='source is absent from this view'
        elif hashlib.sha256(data).hexdigest()!=e['source_sha256']:why='source SHA-256 differs; review before rebinding'
        elif rel in raw_findings and (e['kind'],e['line'],e['detail'],e['occurrence']) not in {key for _,key in _finding_occurrences(raw_findings[rel])}:
            why='bound finding is not present in this scan'
        if why:rows.append(f'STALE-EXCEPTION {i} {rel}:{e["line"]}: {why}')
    return rows

RECEIPT_SUBJECTS={'move':'Reference move','override':'Checkpoint override','warnings':'Reference warnings'}

def receipt_data(data):
    if not data:return None
    try:
        text=data.decode('utf-8');subject=text.splitlines()[0]
        matches=list(re.finditer(r'^```axis-record-receipt\n(.*?)\n```\s*$',text,re.M|re.S))
        if len(matches)!=1:return None
        value=json.loads(matches[0][1],object_pairs_hook=_json_unique)
        if value.get('schema')!=1 or RECEIPT_SUBJECTS.get(value.get('kind'))!=subject:return None
        return value
    except (ValueError,TypeError,AttributeError,IndexError):return None

def session_writer(root,session):
    import importlib.util
    spec=importlib.util.spec_from_file_location('axis_receipt_session',Path(__file__).with_name('startup-state.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module)
    writer=module.Session(root,session);writer.guard()
    marker=root/'_Axis/Agents'/(session+'.md')
    if marker.read_text().splitlines()[0]!='Main: session':raise ValueError('only Main records checkpoint receipts')
    return writer

def save_receipt(root,session,value):
    writer=session_writer(root,session)
    subject=RECEIPT_SUBJECTS[value['kind']]
    body=subject+'\n\nby: Main Agent\nsession: '+session+'\n\n```axis-record-receipt\n'+json.dumps(value,sort_keys=True,indent=2)+'\n```\n'
    if len(body.encode())>8192:raise ValueError('receipt exceeds 8 KiB; split the approved paths into smaller receipts')
    _,path=writer.record('Logs',lambda identifier:body)
    return str(path)

def move_receipt(root,session,source,target,reason,recover=False):
    """Write intent before the caller moves exact bytes; never overwrite or move a project boundary."""
    if not all(_safe_relative(p) for p in (source,target)) or source==target:raise ValueError('move requires distinct project-local paths')
    if foreign_link(root,root/'anchor',source) or foreign_link(root,root/'anchor',target):raise ValueError('move crosses a project boundary')
    data=_working_source(root,source);proof=None
    if recover:
        destination=_working_source(root,target)
        if data is not None or destination is None or not exact_repo(root):raise ValueError('recovery requires an absent source, existing destination and exact-root Git history')
        revisions=git(root,'log','--all','--format=%H','-256','--',source) or b''
        for revision in revisions.decode().splitlines():
            old=git(root,'show',revision+':'+source)
            if old==destination:proof=revision;data=old;break
        if proof is None:raise ValueError('no exact historical source bytes match this destination; retain the unresolved finding')
    elif data is None or _working_source(root,target) is not None or (root/target).exists():raise ValueError('source must be a plain file and destination must be absent')
    if not reason.strip():raise ValueError('move reason required')
    value={'schema':1,'kind':'move','source':source,'target':target,'sha256':hashlib.sha256(data).hexdigest(),'reason':reason}
    if proof is None and exact_repo(root) and git(root,'show','HEAD:'+source)==data:
        proof=(git(root,'rev-parse','HEAD') or b'').decode().strip()
    if proof:value['source_commit']=proof
    return save_receipt(root,session,value)

def reference_history(root,known,names,reader,paths,revision=None):
    history={}
    for path in paths:
        if not re.fullmatch(r'_Axis/(?:Archive/)?Logs/'+IDENT.pattern+r'\.md',path):continue
        try:value=receipt_data(reader(path))
        except ExceptionsError:continue
        if not value or value.get('kind')!='move' or set(value)-{'source_commit'}!={'schema','kind','source','target','sha256','reason'}:continue
        src,dst,digest=value['source'],value['target'],value['sha256']
        if not all(_safe_relative(p) for p in (src,dst)) or src==dst or not isinstance(digest,str) or not re.fullmatch('[a-f0-9]{64}',digest):continue
        # Even committed receipts need byte evidence; merely committing a fabricated alias cannot bless it.
        candidates=[reader(dst)]
        if revision is None:candidates.append(reader(src))
        else:candidates.append(git(root,'show','HEAD:'+src) if revision=='INDEX' else None)
        proof=value.get('source_commit')
        if isinstance(proof,str) and re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',proof):candidates.append(git(root,'show',proof+':'+src))
        verified=any(data is not None and hashlib.sha256(data).hexdigest()==digest for data in candidates)
        if not verified and exact_repo(root):
            ref='HEAD' if revision in (None,'INDEX') else revision
            origin=git(root,'log','--follow','--diff-filter=A','--format=%H','-1',ref,'--',path)
            commit=origin.decode().strip() if origin else ''
            if re.fullmatch(r'[a-f0-9]{40}|[a-f0-9]{64}',commit):
                candidates=[git(root,'show',commit+':'+dst),git(root,'show',commit+'^:'+src)]
                verified=any(data is not None and hashlib.sha256(data).hexdigest()==digest for data in candidates)
        if not verified:continue
        history.setdefault(src,set()).add(dst)
    names['__history__']={src:next(iter(dst)) for src,dst in history.items() if len(dst)==1}
    for src in names['__history__']:known.update(IDENT.findall(Path(src).name))

def staged_receipts(root,kind):
    raw=git(root,'diff','--cached','--name-only','-z','--diff-filter=A') or b''
    for path in raw.decode('utf-8','surrogateescape').split('\0'):
        if not re.fullmatch(r'_Axis/Logs/'+IDENT.pattern+r'\.md',path):continue
        value=receipt_data(git(root,'show',':'+path))
        if value and value.get('kind')==kind:yield path,value

def blob_digest(root,revision,path):
    data=git(root,'show',revision+':'+path)
    return hashlib.sha256(data).hexdigest() if data is not None else None

def approved_paths(root,check):
    head=(git(root,'rev-parse','--verify','HEAD') or b'').decode().strip();approved=set()
    for log,value in staged_receipts(root,'override'):
        if set(value)!={'schema','kind','head','check','paths','reason','user_words'} or value['head']!=head or value['check']!=check:continue
        if not all(isinstance(value[k],str) and value[k].strip() for k in ('reason','user_words')) or not isinstance(value['paths'],list) or not value['paths']:continue
        good=set()
        for item in value['paths']:
            if not isinstance(item,dict) or set(item)!={'path','before_sha256','after_sha256'} or not _safe_relative(item['path']):break
            path=item['path']
            if path==log or item['before_sha256']!=blob_digest(root,'HEAD',path) or item['after_sha256']!=blob_digest(root,'',path):break
            # No blanket waiver for deletions, names, Secrets, leases, or files outside this exact commit.
            if item['before_sha256']==item['after_sha256']:break
            good.add(path)
        else:approved.update(good)
    return approved

def approval_receipt(root,session,check,paths,reason,user_words):
    if check not in ('write-once','links') or not exact_repo(root):raise ValueError('override requires a project repository and named record check')
    if not reason.strip() or not user_words.strip() or not paths:raise ValueError('record the reason and actual User approval words')
    bindings=[]
    for path in sorted(set(paths)):
        if not _safe_relative(path):raise ValueError('override path is not project-local')
        before,after=blob_digest(root,'HEAD',path),blob_digest(root,'',path)
        if before==after:raise ValueError('override requires an exact changed staged file: '+path)
        bindings.append({'path':path,'before_sha256':before,'after_sha256':after})
    return save_receipt(root,session,{'schema':1,'kind':'override','head':(git(root,'rev-parse','--verify','HEAD') or b'').decode().strip(),'check':check,'paths':bindings,'reason':reason,'user_words':user_words})

def warning_receipt(root,session,lines):
    warnings=[line for line in lines if line.split(' ',1)[0] in WARNING_KINDS]
    if not warnings:return None
    # The recorded diagnostics bind the staged view before this Log is staged. Re-run checks after staging it.
    return save_receipt(root,session,{'schema':1,'kind':'warnings','head':(git(root,'rev-parse','HEAD') or b'').decode().strip(),'index_tree':(git(root,'write-tree') or b'').decode().strip(),'warnings':[line[:500] for line in warnings[:5]],'diagnostics_sha256':hashlib.sha256('\n'.join(lines).encode()).hexdigest(),'summary':lines[-1] if lines else ''})

def archive_root(root,text=None,allow_missing=False):
    if text is None:
        try:text=(root/'_Axis/SETTINGS.md').read_text(encoding='utf-8')
        except OSError:return None
    m=re.search(r'^### Archive Location\s*$.*?^\*\*Value:\*\*\s*(.+?)\s*$',text,re.M|re.S)
    v=(m.group(1).strip() if m else '_Axis/Archive/')
    if v.startswith('~/'):v=os.path.expanduser('~')+v[1:]
    p=Path(v) if os.path.isabs(v) else root/v
    return p if allow_missing or p.is_dir() else None

def identities(root,arch):
    """Every identifier timestamp that names something real: record files, path names, sessions."""
    known=set()
    for base in [root/'_Axis',root/'_Dev/Evidence',root/'_Memos']+([arch] if arch else []):
        if not base.is_dir():continue
        for dirpath,dirs,files in os.walk(base):
            dirs[:]=[d for d in dirs if d not in ('Secrets','.git','node_modules')]
            for n in dirs+files:known.update(IDENT.findall(n))
    try:known.update(IDENT.findall((root/'_Dev/Evidence/DELETED.md').read_text(encoding='utf-8',errors='replace')))
    except OSError:pass
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
        if f==root/EXCEPTIONS_PATH:continue
        try:texts[f]=f.read_text(encoding='utf-8',errors='replace')
        except OSError:continue
        known.update(re.findall(r'session[^\n]{0,12}?('+IDENT.pattern+')',texts[f],re.I))
    tracking=root/'_Axis/Tracking'
    if tracking.is_dir():known.update(x for n in os.listdir(tracking) for x in IDENT.findall(n))
    names={}
    for f in files:names.setdefault(f.name,[]).append(f)
    if arch:
        for q in arch.rglob('*.md'):names.setdefault(q.name,[]).append(q)
    logs=[p.relative_to(root).as_posix() for p in (root/'_Axis/Logs').glob('*.md')]
    logs += [p.relative_to(root).as_posix() for p in (root/'_Axis/Archive/Logs').glob('*.md')]
    reference_history(root,known,names,lambda p:_working_source(root,p),logs)
    return arch,known,names,texts

def snapshot_context(root,revision):
    """Resolve Git checks against the chosen index/commit, not uncommitted source/registry bytes."""
    entries=_git_entries(root,revision);reader=_git_reader(root,revision,entries)
    settings=reader('_Axis/SETTINGS.md');arch=archive_root(root,settings.decode('utf-8','replace') if settings else '',True)
    archive_rel=arch.relative_to(root).as_posix() if arch.is_relative_to(root) else None
    known=set();names={};texts={};present=set()
    for rel,(mode,_) in entries.items():
        if any(p in ('Secrets','.git','node_modules') for p in rel.split('/')):continue
        present.add(rel)
        present.update(p.as_posix() for p in PurePosixPath(rel).parents if p.as_posix()!='.')
        if rel.startswith(('_Axis/','_Dev/Evidence/','_Memos/')):known.update(IDENT.findall(rel))
        if in_scope(rel) and mode in ('100644','100755'):
            data=reader(rel);f=root/rel;texts[f]=data.decode('utf-8','replace')
            known.update(re.findall(r'session[^\n]{0,12}?('+IDENT.pattern+')',texts[f],re.I))
            names.setdefault(f.name,[]).append(f)
        elif archive_rel is not None and rel.startswith(archive_rel+'/') and rel.endswith('.md'):
            names.setdefault(Path(rel).name,[]).append(root/rel)
    deleted=reader('_Dev/Evidence/DELETED.md')
    if deleted:known.update(IDENT.findall(deleted.decode('utf-8','replace')))
    if archive_rel is not None:
        if archive_rel not in present:arch=None
    elif arch.is_dir():
        for dirpath,dirs,files in os.walk(arch):
            dirs[:]=[d for d in dirs if d not in ('Secrets','.git','node_modules')]
            for n in dirs+files:known.update(IDENT.findall(n))
            for n in files:
                if n.endswith('.md'):names.setdefault(n,[]).append(Path(dirpath)/n)
    else:arch=None
    def exists(path):
        path=Path(os.path.normpath(path))
        try:rel=path.relative_to(root).as_posix()
        except ValueError:return path.exists()
        return rel in present
    reference_history(root,known,names,reader,entries,revision)
    return arch,known,names,texts,reader,exists

def coordination_metadata_lines(text,rel):
    if not re.match(r'^_Axis/(?:Archive/)?(?:Teams|Messages|Jobs|Schedules)/',rel):return set()
    try:
        import importlib.util
        spec=importlib.util.spec_from_file_location('axis_record_format',Path(__file__).with_name('coordination-record.py'))
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module.reference_metadata_lines(text)
    except (OSError,ValueError,TypeError,AttributeError,RecursionError):return set()

WARNING_KINDS={'EXTERNAL-LINK','HISTORICAL-LINK'}
ANCHORS=('AGENTS.md','CLAUDE.md','GEMINI.md','_Axis/MANIFEST.md','_Axis/PROJECT.md','_Axis/PRACTICES.md','_Axis/RULES.md','_Temp')

def foreign_link(root,f,target,exists=None):
    from urllib.parse import unquote
    if target.startswith('parent:'):return True
    if re.match(r'^[a-z][a-z0-9+.-]*:',target,re.I) or target.startswith('#'):return False
    value=unquote(target.split('#',1)[0].split('?',1)[0])
    if not value:return False
    local=Path(os.path.normpath(f.parent/value))
    if not local.is_relative_to(root):return True
    check=exists or (lambda p:p.exists())
    # Only inspect anchors along this target's path; never traverse or read child instructions.
    for ancestor in (local,*local.parents):
        if ancestor==root:break
        if all(check(ancestor/a) for a in ANCHORS) or all((ancestor/a).exists() for a in ANCHORS):return True
    return False

def scan(root,arch,known,names,f,text,rel,exists=None):
    """Findings in one file: (kind, line, detail, write-once?)."""
    from urllib.parse import unquote
    if rel==EXCEPTIONS_PATH:return []
    receipt=receipt_data(text.encode('utf-8'))
    if receipt and rule_kind(rel)=='Logs':
        text=re.sub(r'^```axis-record-receipt\n.*?\n```\s*$',lambda m:'\n'*m[0].count('\n'),text,flags=re.M|re.S)
    out=[]
    kind=rule_kind(rel);done=(kind=='Tasks' and (field(text,'status') or '').casefold() in ('completed','cancelled')) or (kind in ('Followups','Reminders') and (field(text,'outcome') or 'N/A') not in ('N/A',''))
    worm=kind in WORM or done or rel.startswith(('_Axis/Archive/','ARCHIVE/'))
    metadata=coordination_metadata_lines(text,rel)
    for i,line in enumerate(text.splitlines(),1):
        if i in metadata:continue
        if re.match(r'^\s*"(?:created|updated|expires|deadline|authority_expires|session|issuer_session)"\s*:',line):continue
        if VALUE.match(line) or '<!-- compiled:' in line or re.fullmatch(r'\s*[\w-]+:\s*'+IDENT.pattern+r'\s*',line) or re.match(r'#+ .* - '+IDENT.pattern+r'\s*$',line):continue
        bare=re.sub(r'[a-z][a-z0-9+.-]*://\S+',lambda u:' '*len(u.group(0)),line,flags=re.I)
        foreign=[]
        for match in LINK.finditer(line):
            if foreign_link(root,f,match[1],exists):foreign.append((match.start(),match.end(),match[1]))
        for match in re.finditer(r'parent:[^\s`<>\)]+',line):foreign.append((match.start(),match.end(),match[0]))
        legacy=re.search(r'delegated by parent supervision record\s+[`*]*(?:_Axis/Supervision/)?('+IDENT.pattern+r')',line,re.I)
        if legacy:foreign.append((legacy.start(),legacy.end(),'parent:_Axis/Supervision/'+legacy[1]+'.md'))
        emitted=set()
        for start,end,target in foreign:
            bare=bare[:start]+' '*(end-start)+bare[end:]
            if target not in emitted:out.append(('EXTERNAL-LINK',i,target,worm));emitted.add(target)
        # Scratch path components are file names, not record references. Mask only that span;
        # a bare identifier beside it and ordinary Markdown destination checks still apply.
        bare=re.sub(r"(?<![\w])_Temp/[^\s`<>\[\]()\"']+",lambda m:' '*len(m[0]),bare)
        for m in NEAR.finditer(bare):
            tok=m.group(0).rstrip('.:');full=IDENT.match(tok)
            if not full:
                if re.fullmatch(r'\d{4}\.\d{2}\.\d{2}\.\d{2}',tok) or line[m.end():].lstrip().startswith('UTC'):continue
                out.append(('MALFORMED',i,tok,worm))
            elif tok[full.end():].startswith('.tsclaim') or re.search(r'(session|Main|External|Subagent|e\.g\.)\W{0,4}$',line[:m.start()],re.I):continue
            elif full.group(0) not in known and full.group(0)!=f.stem:
                out.append(('ACKNOWLEDGED' if re.match(r'[`*_]*\s*\(missing\)',line[m.end():]) else 'UNRESOLVED',i,full.group(0),worm))
        for m in LINK.finditer(line):
            target=m.group(1)
            if foreign_link(root,f,target,exists) or re.match(r'^[a-z][a-z0-9+.-]*:',target,re.I) or target.startswith(('#','/')):continue
            t=unquote(target.split('#',1)[0].split('?',1)[0])
            if not t or (exists(f.parent/t) if exists else (f.parent/t).exists()):continue
            local=Path(os.path.normpath((f.parent/t).as_posix()))
            alias=names.get('__history__',{}).get(local.relative_to(root).as_posix()) if local.is_relative_to(root) else None
            if alias:
                out.append(('HISTORICAL-LINK',i,target+' -> '+alias,worm));continue
            if arch:
                try:
                    sub=local.relative_to(root/'_Axis/Archive') if local.is_relative_to(root/'_Axis/Archive') else local.relative_to(root)
                    if exists(arch/sub) if exists else (arch/sub).exists():continue
                except ValueError:pass
            alt=[q for q in names.get(Path(t).name,[]) if q!=f]
            if alt:out.append(('MOVED-LINK',i,target+' -> '+(alt[0].relative_to(root).as_posix() if alt[0].is_relative_to(root) else 'Archive/'+alt[0].relative_to(arch).as_posix()),worm))
            else:out.append(('BROKEN-LINK',i,target,worm))
    return out

def report(found,count,arch):
    counts={k:0 for k in ('MALFORMED','UNRESOLVED','BROKEN-LINK','MOVED-LINK')}
    seen=sum(1 for _,x in found if x[0]=='ACKNOWLEDGED');ack=sum(1 for _,x in found if x[0]==ACK_EXCEPTION)
    visible=[x for x in found if x[1][0]!='ACKNOWLEDGED'];problems=[x for x in visible if x[1][0]!=ACK_EXCEPTION and x[1][0] not in WARNING_KINDS]
    for _,(k,_,_,_) in problems:counts[k]+=1
    rows=[f'{k} {rel}:{i} {d}'+(' (write-once)' if w else '') for rel,(k,i,d,w) in visible]
    lines=rows[:LIMIT*4]+([f'... {len(rows)-LIMIT*4} more'] if len(rows)>LIMIT*4 else [])
    summary=', '.join(f'{v} {k.lower()}' for k,v in counts.items())
    warns=sum(x[1][0] in WARNING_KINDS for x in visible)
    summary+=f', {warns} warning(s)' if warns else ''
    summary+=f', {seen} acknowledged missing' if seen else ''
    summary+=f', {ack} acknowledged exception(s)' if ack else ''
    return (1 if problems else 0),([] if arch else ['NOTE: Archive Location unavailable; archived targets were not checked'])+lines+[('FINDINGS: ' if problems else 'OK: ')+summary+f' in {count} files']

def relof(root,arch,f):
    return f.relative_to(root).as_posix() if f.is_relative_to(root) else 'ARCHIVE/'+f.relative_to(arch).as_posix()

def links(root,scopes,with_archive):
    try:
        entries=load_exceptions(root)
        arch,known,names,texts=context(root,scopes,with_archive);found=[];raw={}
        reader=lambda rel:_working_source(root,rel,arch)
        for f,text in texts.items():
            rel=relof(root,arch,f)
            try:data=reader(rel)
            except ExceptionsError:data=None
            raw[rel]=scan(root,arch,known,names,f,data.decode('utf-8','replace') if data is not None else text,rel)
            findings=apply_exceptions(entries,rel,data,raw[rel]) if data is not None else raw[rel]
            found+=[(rel,x) for x in findings]
        code,lines=report(found,len(texts),arch)
        return code,exception_diagnostics(entries,reader,raw)+lines
    except ExceptionsError as error:return 1,['REFUSED: invalid '+EXCEPTIONS_PATH+': '+str(error)]

def in_scope(rel):
    return rel!=EXCEPTIONS_PATH and rel.endswith('.md') and any(rel==s or rel.startswith(s+'/') for s in SCOPE)

def links_range(root,span):
    """Handoff check (^resume): scan the in-scope files a received range changed."""
    if not exact_repo(root):return 2,['UNAVAILABLE: no Git repository at this root']
    if span.count('..')!=1 or '...' in span:return 2,['UNAVAILABLE: --range requires {old}..{new}']
    old,new=span.split('..');ends=[]
    for ref in (old or 'HEAD',new or 'HEAD'):
        oid=git(root,'rev-parse','--verify','--end-of-options',ref+'^{commit}')
        if oid is None:return 2,['UNAVAILABLE: range endpoint is not a commit']
        ends.append(oid.decode().strip())
    raw=git(root,'diff','--name-only','-z',*ends,'--')
    if raw is None:return 2,['UNAVAILABLE: git diff '+span+' failed']
    try:
        arch,known,names,_,reader,exists=snapshot_context(root,ends[1]);entries=load_exceptions(root,reader=reader)
        paths=set(raw.decode('utf-8','surrogateescape').split('\0'));found=[];findings={};n=0;warnings=[]
        if EXCEPTIONS_PATH in paths:
            paths.update(e['path'] for e in entries)
            try:paths.update(e['path'] for e in load_exceptions(root,revision=ends[0]))
            except ExceptionsError as error:warnings.append('NOTE: invalid prior exception registry: '+str(error))
        for rel in sorted(p for p in paths if p and in_scope(p)):
            data=reader(rel)
            if data is None:continue
            n+=1;findings[rel]=scan(root,arch,known,names,root/rel,data.decode('utf-8','replace'),rel,exists)
            found+=[(rel,x) for x in apply_exceptions(entries,rel,data,findings[rel])]
        code,lines=report(found,n,arch)
        return code,warnings+exception_diagnostics(entries,reader,findings)+lines
    except ExceptionsError as error:return 1,['REFUSED: invalid '+EXCEPTIONS_PATH+' or Git source view: '+str(error)]

def links_staged(root):
    """Commit check (^save): refuse a reference problem a staged record adds; problems already at HEAD are history."""
    if not exact_repo(root):return 2,['UNAVAILABLE: no Git repository at this root']
    raw=git(root,'diff','--cached','--name-only','-z','--diff-filter=AMRD')
    if raw is None:return 2,['UNAVAILABLE: git diff --cached failed']
    try:
        arch,known,names,_,reader,exists=snapshot_context(root,'INDEX');entries=load_exceptions(root,reader=reader)
        head_view=snapshot_context(root,'HEAD') if has_head(root) else None;head_entries=[];warnings=[];head_valid=True
        if head_view:
            try:head_entries=load_exceptions(root,reader=head_view[4])
            except ExceptionsError as error:
                head_valid=False;warnings=['NOTE: invalid HEAD exception registry; no historical baseline exemptions: '+str(error)]
        paths=set(raw.decode('utf-8','surrogateescape').split('\0'));new=[];findings={};n=0
        if EXCEPTIONS_PATH in paths:paths.update(e['path'] for e in entries+head_entries)
        for rel in sorted(p for p in paths if p and in_scope(p)):
            staged=reader(rel)
            if staged is None:continue
            n+=1;f=root/rel;head=head_view[4](rel) if head_view else None;before={}
            if head is not None and head_valid:
                ha,hk,hn,_,_,he=head_view
                prior=apply_exceptions(head_entries,rel,head,scan(root,ha,hk,hn,f,head.decode('utf-8','replace'),rel,he))
                for k,_,d,_ in prior:
                    if k not in ('ACKNOWLEDGED',ACK_EXCEPTION):before[(k,d)]=before.get((k,d),0)+1
            findings[rel]=scan(root,arch,known,names,f,staged.decode('utf-8','replace'),rel,exists)
            for x in apply_exceptions(entries,rel,staged,findings[rel]):
                if x[0]=='ACKNOWLEDGED':continue
                if x[0]!=ACK_EXCEPTION and before.get((x[0],x[2]),0):before[(x[0],x[2])]-=1
                else:new.append((rel,x))
        approvals=approved_paths(root,'links')
        new=[(rel,(ACK_EXCEPTION,x[1],x[2]+' (User-approved checkpoint override)',x[3])) if rel in approvals and x[0] not in WARNING_KINDS else (rel,x) for rel,x in new]
        diagnostics=warnings+exception_diagnostics(entries,reader,findings);code,lines=report(new,n,arch)
        if code:
            count=sum(x[0]!=ACK_EXCEPTION and x[0] not in WARNING_KINDS for _,x in new)
            return 1,diagnostics+lines[:-1]+[f'REFUSED: {count} new reference problem(s) in staged records; fix them (copy each identifier from disk) before committing']
        return 0,diagnostics+(lines if any(x[0]==ACK_EXCEPTION or x[0] in WARNING_KINDS for _,x in new) else ['OK'])
    except ExceptionsError as error:return 1,['REFUSED: invalid '+EXCEPTIONS_PATH+' or Git source view: '+str(error)]

def update_transaction(path):
    parts=PurePosixPath(path).parts
    return parts[2] if len(parts)>3 and parts[:2]==('_Axis','Updates') else None

def rename_entries(entries):
    """Update evidence has transaction-local identity, even when Git guesses a rename."""
    out=[]
    for status,path,new in entries:
        if status.startswith('R') and update_transaction(path) and update_transaction(new) and update_transaction(path)!=update_transaction(new):
            out.extend([('D',path,None),('A',new,None)])
        else:out.append((status,path,new))
    return out

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
    entries=rename_entries(entries)
    exempt=update_exempt(root,[p for s,p,_ in entries if s=='A'])|corrections(root,[p for s,p,_ in entries if s=='A'])
    # A move Git did not pair (heavy edit, rename limit) keeps its identity: pair a deletion and an addition by name.
    deleted={}
    for status,path,_ in entries:
        if status=='D':deleted.setdefault(Path(path).name,[]).append(path)
    for status,path,_ in list(entries):
        candidates=deleted.get(Path(path).name,[]) if status=='A' and not update_transaction(path) else []
        candidates=[old for old in candidates if not update_transaction(old) and (Path(old).parent==Path(path).parent or NAME.fullmatch(Path(path).name))]
        old=candidates[0] if len(candidates)==1 else None
        if old and git(root,'rev-parse','HEAD:'+old)!=git(root,'rev-parse',':'+path):entries.append(('R000',old,path))
    overrides=approved_paths(root,'write-once');refused=[]
    for status,path,new in entries:
        if path.startswith('_Axis/Merges/') and status[:1] in 'DR':why=rule(root,path);label=path+(' -> '+new if new else '')
        elif status[:1] in 'MT':why=rule(root,path);label=path
        elif status[:1]=='R' and status!='R100':why=rule(root,path);label=path+' -> '+new;why=why and why+' (renamed with changes)'
        else:continue
        if why and path not in exempt and not (path in overrides and (new is None or new in overrides)):refused.append('WRITE-ONCE '+label+': '+why)
    if refused:return 1,refused[:LIMIT]+[f'REFUSED: {len(refused)} write-once file(s) changed; do not commit; show User these paths and ask how to proceed']
    return 0,['OK']

def main():
    p=argparse.ArgumentParser(description='Axis pre-commit record checks');p.add_argument('--root',default='.')
    sub=p.add_subparsers(dest='check',required=True);n=sub.add_parser('names');n.add_argument('--since');sub.add_parser('write-once')
    c=sub.add_parser('correct');c.add_argument('--path',required=True);c.add_argument('--old',required=True);c.add_argument('--new',required=True);c.add_argument('--link',action='store_true')
    k=sub.add_parser('links');k.add_argument('--scope',action='append');k.add_argument('--archive',action='store_true')
    k.add_argument('--staged',action='store_true');k.add_argument('--range');k.add_argument('--log-warnings',action='store_true');k.add_argument('--session')
    m=sub.add_parser('record-move');m.add_argument('--session',required=True);m.add_argument('--path',required=True);m.add_argument('--to',required=True);m.add_argument('--reason',required=True);m.add_argument('--recover',action='store_true')
    o=sub.add_parser('approve');o.add_argument('--session',required=True);o.add_argument('--check',dest='approved_check',choices=('links','write-once'),required=True);o.add_argument('--path',action='append',required=True);o.add_argument('--reason',required=True);o.add_argument('--user-words',required=True)
    a=p.parse_args();root=Path(os.path.abspath(a.root))
    if a.check=='names' and a.since is not None and not re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',a.since):
        print('UNAVAILABLE: --since is not a Session ID');return 2
    if not (root/'_Axis').is_dir():print('UNAVAILABLE: run from the project root');return 2
    if a.check in ('record-move','approve'):
        try:
            path=move_receipt(root,a.session,a.path,a.to,a.reason,a.recover) if a.check=='record-move' else approval_receipt(root,a.session,a.approved_check,a.path,a.reason,a.user_words)
            print('RECORDED: '+path);return 0
        except (ValueError,OSError,RuntimeError,ExceptionsError) as error:print('REFUSED: '+str(error));return 1
    if a.check=='links' and a.log_warnings and (not a.staged or not a.session):p.error('--log-warnings requires --staged and --session')
    if a.check=='links':code,lines=links_staged(root) if a.staged else links_range(root,a.range) if a.range else links(root,a.scope or SCOPE,a.archive)
    else:code,lines=names(root,a.since) if a.check=='names' else correct(root,a.path,a.old,a.new,a.link) if a.check=='correct' else write_once(root)
    if a.check=='links' and a.log_warnings:
        try:
            logged=warning_receipt(root,a.session,lines)
            if logged:lines.append('RECORDED: '+logged+'; stage this Log and re-run the three checks before committing')
        except (ValueError,OSError,RuntimeError) as error:code=1;lines.append('REFUSED: warning Log could not be recorded: '+str(error))
    for line in lines:print(line)
    return code

if __name__=='__main__':sys.exit(main())
