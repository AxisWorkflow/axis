#!/usr/bin/env python3
"""Optional archive accelerator. Records stay authoritative; no provider or Git-history mutations."""
import secrets, threading, time
import argparse, datetime as dt, hashlib, importlib.util, json, os, re, shutil, stat, subprocess, sys
from pathlib import Path
ID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z')
FAMILIES = ('Tasks','Ideas','Notes','Logs','Snapshots','CX','Audit','Reviews','Status','Supervision','Followups','Reminders','Messages','Teams','Jobs','Schedules')
LEVELS = {'never':'Never','default':'Default','aggressive':'Aggressive','agressive':'Aggressive'}
LIMIT = 1024 * 1024 * 1024

class Held(ValueError): pass

def need(value, why):
    if not value: raise Held(why)

def relative(value):
    need(isinstance(value,str) and value and not value.startswith('/') and '\\' not in value and all(c not in ('','.','..') for c in value.split('/')) and not any(ord(c)<32 for c in value),'unsafe relative path')
    return value

def local(root,value,missing=False):
    relative(value);return safe(Path(root)/value,missing)

def sha(data): return hashlib.sha256(data).hexdigest()
def encode(value): return (json.dumps(value,sort_keys=True,indent=2)+'\n').encode()
def safe(path, missing=False):
    path=Path(os.path.abspath(path)); parent=Path(path.anchor)
    for part in path.parts[1:]:
        need(part not in ('.','..') and '\\' not in part,'unsafe path')
        if parent.exists(): need(not any(p.name.casefold()==part.casefold() and p.name!=part for p in parent.iterdir()),'case collision')
        parent/=part
        if not parent.exists(): need(missing and not parent.is_symlink(),'missing path'); continue
        info=parent.lstat(); need(not stat.S_ISLNK(info.st_mode) and (stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode) and info.st_nlink==1),'unsafe filesystem object')
    return path

def read(path, limit=LIMIT):
    p=safe(path); need(p.is_file() and p.stat().st_size<=limit,'file size/type limit');return p.read_bytes()

def once(path,data):
    p=safe(path,True);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    need(read(p)==data,'copy readback mismatch')

def setting(root,name):
    text=read(Path(root)/'_Axis/SETTINGS.md').decode()
    sections=re.findall(r'^### '+re.escape(name)+r'\s*\n(.*?)(?=^### |^## |\Z)',text,re.M|re.S)
    need(len(sections)<=1,'ambiguous setting')
    values=re.findall(r'^\*\*Value:\*\* ([^\n]*)$',sections[0],re.M) if sections else []
    need(len(values)<=1,'ambiguous setting value');return values[0].strip() if values else None

def policy(root,override=None):
    value=override if override is not None else setting(root,'Archiving') or 'Default'
    need(value.lower() in LEVELS,'unknown Archiving level');return LEVELS[value.lower()]

def legacy_root(root):
    value=setting(root,'Archive Location') or '_Axis/Archive/'
    p=Path(value).expanduser();p=p if p.is_absolute() else Path(root)/p
    if not p.exists():return None
    return safe(p)

def family_roots(root,family):
    """Read all generations, but new writes always use the family-local Archive."""
    need(family in FAMILIES,'unknown record family');root=Path(root)
    roots=[root/'_Axis'/family,root/'_Axis'/family/'Archive',root/'_Axis/Archive'/family]
    old=legacy_root(root)
    if old is not None:roots.append(old/family)
    return list(dict.fromkeys(p for p in roots if p.is_dir() and safe(p)))

def locators(root):
    folder=Path(root)/'_Axis/ColdStorage'
    if not folder.exists():return []
    safe(folder);out=[]
    for p in sorted(folder.glob('*.md')):
        need(ID.fullmatch(p.stem),'invalid cold locator name');text=read(p).decode()
        blocks=re.findall(r'```axis-cold-storage\n(.*?)\n```',text,re.S)
        need(len(blocks)==1,'invalid cold locator');v=json.loads(blocks[0]);need(v.get('schema')==1 and v.get('id')==p.stem,'invalid cold identity')
        need(re.fullmatch('[A-Za-z0-9_-]+',v.get('location','')),'invalid cold destination')
        need(v.get('relative_path')=='AxisCold/'+p.stem and v.get('layout','bundle')=='bundle' or v.get('layout')=='legacy' and v.get('relative_path')=='.' and isinstance(v.get('existing_paths'),dict),'invalid cold layout')
        manifest=v.get('files');need(isinstance(manifest,list) and sha(encode(manifest))==v.get('manifest_sha256'),'cold manifest mismatch')
        names=set()
        for f in manifest:
            need(set(f)=={'source','sha256','bytes','mode','record_id'} and type(f['mode']) is int and 0<=f['mode']<=0o777 and (f['record_id'] is None or ID.fullmatch(f['record_id'])),'invalid cold member fields')
            n=relative(f['source']);need(isinstance(n,str) and not n.startswith('/') and all(c not in ('','.','..') for c in n.split('/')) and '\\' not in n,'unsafe cold source');need(n not in names,'duplicate cold member');names.add(n)
            need(re.fullmatch('[0-9a-f]{64}',f['sha256']) and type(f['bytes']) is int and f['bytes']>=0,'invalid cold member')
        if v.get('layout')=='legacy':
            need(set(v['existing_paths'])==names,'legacy mapping coverage');need(len(set(v['existing_paths'].values()))==len(names),'legacy path collision')
            for name in v['existing_paths'].values():relative(name)
        out.append((p,v))
    return out

def cold_entries(root):
    return [(p,v,f) for p,v in locators(root) for f in v['files']]

def cold_lookup(root,identity):
    matches=[(p,v,f) for p,v,f in cold_entries(root) if f.get('record_id')==identity or f['source']==identity]
    need(len(matches)<=1,'ambiguous cold identity');return matches[0] if matches else None

def protected_temporary(root):
    """Protect exact owned recovery and still-needed staging, including legacy pending transactions."""
    root=Path(root);out=set()
    for family in ('Updates','Merges'):
        base=root/'_Axis'/family
        if not base.exists():continue
        safe(base)
        for directory in base.iterdir():
            if directory.name in ('.gitkeep','.DS_Store','operation.lck','retired.json'):continue
            need(ID.fullmatch(directory.name) and safe(directory).is_dir(),'invalid recovery directory')
            view=directory;pointer=directory/'recovery.json'
            if pointer.exists():
                value=json.loads(read(pointer,65536));name=value.get('path');need(name=='_Temp/'+('Update-' if family=='Updates' else 'Merge-')+directory.name,'invalid recovery pointer')
                view=local(root,name,True)
                if view.exists():out.add(name)
                else:
                    need((directory/('completed.json' if family=='Updates' else 'validated.json')).is_file(),'missing protected recovery')
                    continue
            start=view/'start.json'
            if not start.exists():continue
            value=json.loads(read(start));need(value.get('transaction')==directory.name,'invalid recovery identity')
            if family=='Merges':
                recovery=value.get('recovery')
                if recovery:
                    need(recovery=='_Temp/MergeRecovery-'+directory.name,'invalid merge quarantine')
                    if local(root,recovery,True).exists():out.add(recovery)
            elif not ((view/'consumed.json').exists() or (view/'rollback.json').exists() and (view/'released.json').exists()):
                plan=value['plan'];inputs=list(plan['source_checks'])+[c['staged'] for c in plan['changes'] if c.get('staged')]
                for name in inputs:
                    relative(name)
                    if name.startswith('_Temp/'):
                        # The first owned staging component may be a file or a bundle directory.
                        out.add('/'.join(name.split('/')[:2]))
    return sorted(out)

def fields(path):
    text=read(path).decode();values={}
    for key,value in re.findall(r'^([a-z][a-z-]*):[ \t]*(.*)$',text,re.M):values.setdefault(key,value.strip())
    for key,value in re.findall(r'^- \*\*(Status|Updated|Created):\*\* (.*)$',text,re.M):values[key.lower()]=value.strip()
    return text,values

def date(value):
    if not value or value in ('N/A','Unknown'):return None
    try:
        if ID.fullmatch(value):return dt.datetime.strptime(value,'%Y.%m.%d.%H.%M.%S.%fZ').replace(tzinfo=dt.timezone.utc)
        # Memo headers include an explicit UTC offset.
        match=re.fullmatch(r'(\d{4}-\d\d-\d\d \d\d:\d\d) \(UTC([+-]\d\d:\d\d)\)',value)
        if match:return dt.datetime.fromisoformat(match[1]+match[2]).astimezone(dt.timezone.utc)
        v=dt.datetime.fromisoformat(value.replace('Z','+00:00'));need(v.tzinfo is not None,'untrusted archive time');return v.astimezone(dt.timezone.utc)
    except (ValueError,Held):return None

def dependency_holds(root):
    """Explicit local dependencies, never ordinary historical citations."""
    p=Path(root)/'_Axis/Archive-Holds.json'
    if not p.exists():v={'schema':1,'holds':[]}
    else:v=json.loads(read(p))
    need(v.get('schema')==1 and isinstance(v.get('holds'),list),'invalid archive holds')
    for h in v['holds']:
        need(set(h)=={'path','consumer','reason'} and all(isinstance(x,str) and x for x in h.values()),'invalid hold');relative(h['path'])
    holds=list(v['holds'])
    for family in ('Updates','Merges'):
        for receipt in (Path(root)/'_Axis'/family).glob('*/*.json'):
            value=json.loads(read(receipt))
            auth=value.get('authorization',{});record=auth.get('record') if isinstance(auth,dict) else None
            if record:holds.append({'path':relative(record),'consumer':str(receipt.relative_to(root)),'reason':'transaction authority'})
            if receipt.name=='recovery.json':holds.append({'path':'_Axis/Logs/'+receipt.parent.name+'.md','consumer':str(receipt.relative_to(root)),'reason':'recovery authority'})
    return holds

def held(name,holds):return any(name==h['path'] or name.startswith(h['path'].rstrip('/')+'/') or h['path'].startswith(name.rstrip('/')+'/') for h in holds)

def terminal(family,v):
    state=v.get('status',v.get('state','')).lower()
    if family=='Tasks':return state in ('completed','cancelled')
    if family in ('Memos','Ideas'):return state in ('done','superseded','closed','completed','cancelled')
    if family=='Followups':return date(v.get('resolved')) is not None and v.get('updated')==v.get('resolved') and v.get('outcome') in ('answered','completed','withdrawn','converted') and (v.get('outcome')=='withdrawn' or v.get('resolution-ref') not in (None,'','N/A'))
    if family=='Reminders':return v.get('outcome') in ('acknowledged','completed','cancelled') and date(v.get('updated')) is not None and date(v.get('created')) is not None and date(v['updated'])>=date(v['created'])
    if family in ('Messages','Teams','Jobs','Schedules'):return False # canonical consumer must prove settlement; no guessed status from prose
    if family=='Notes':return False # importance/overflow review belongs to Main
    return True

def inventory(root,level=None,now=None):
    root=safe(root);level=policy(root,level);now=now or dt.datetime.now(dt.timezone.utc);need(now.tzinfo is not None,'untrusted time');items=[];blocked=[]
    if level=='Never':return {'level':level,'items':[],'held':[],'protected_temporary':protected_temporary(root)}
    holds=dependency_holds(root)
    days=7 if level=='Aggressive' else 30;events=30 if level=='Aggressive' else 90;floor=3 if level=='Aggressive' else 10
    supervision=sorted((p.stem for p in (root/'_Axis/Supervision').glob('*.md') if ID.fullmatch(p.stem)),reverse=True)[:30]
    snaps=sorted((p.stem for p in (root/'_Axis/Snapshots').glob('*.md') if ID.fullmatch(p.stem)),reverse=True)[:floor]
    for family in (*FAMILIES,'Memos'):
        base=root/('_Memos' if family=='Memos' else '_Axis/'+family)
        if not base.exists():continue
        safe(base)
        for p in sorted(base.glob('*.md')):
            name=p.relative_to(root).as_posix()
            if family!='Memos' and not ID.fullmatch(p.stem):continue
            text,v=fields(p)
            if held(name,holds):blocked.append({'path':name,'reason':'explicit local dependency'});continue
            if not terminal(family,v):continue
            if family=='Snapshots' and p.stem in snaps:continue
            if family=='Supervision' and p.stem in supervision:continue
            if family=='Followups' and v.get('resolution-ref')!='N/A':
                ref=v.get('resolution-ref','')
                found=cold_lookup(root,ref) is not None
                if ID.fullmatch(ref):found=found or any((base/(ref+'.md')).is_file() for f in FAMILIES for base in family_roots(root,f))
                else:
                    try:found=found or local(root,ref,True).exists()
                    except Held:found=False
                if not found:blocked.append({'path':name,'reason':'terminal resolution reference unavailable'});continue
            when=date(v.get('completed')) or date(v.get('cancelled')) or date(v.get('closed')) or date(v.get('resolved')) or date(v.get('updated')) or date(v.get('created')) or date(p.stem)
            minimum=0 if family in ('Followups','Reminders','Supervision') else days if family in ('Tasks','Ideas','Memos','Snapshots') else events
            if when is None:blocked.append({'path':name,'reason':'no trustworthy lifecycle date'});continue
            if (now-when).total_seconds()<minimum*86400:continue
            # Relative Markdown references need reviewed destination-only rebasing, never a blind rename.
            if re.search(r'\]\((?![a-zA-Z][a-zA-Z0-9+.-]*:|/|#)[^)]+\)',text):blocked.append({'path':name,'reason':'relative links require reviewed rebasing under LinkMaintenance'});continue
            support=p.with_suffix('')
            if support.exists():blocked.append({'path':name,'reason':'owning support requires dependency-consistent batch'});continue
            dest=base/'Archive'/p.name
            items.append({'source':name,'destination':dest.relative_to(root).as_posix(),'sha256':sha(read(p)),'bytes':p.stat().st_size,'family':family})
    return {'level':level,'items':items,'held':blocked,'protected_temporary':protected_temporary(root)}

def lease(root,session):
    spec=importlib.util.spec_from_file_location('axis_archive_state',Path(__file__).with_name('startup-state.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    io=m.Session(root,session);io.guard();need(io.lease[2],'Main required')
    # This one operation lock covers every Main archive writer, including the manual equivalent.
    # It is never reclaimed automatically. On non-atomic storage, require the sole-writer lane.
    flag=Path(root)/'_Axis/Flags/host-storage'
    atomic=setting(root,'Storage Policy')=='auto' and flag.exists() and read(flag).decode().splitlines()[:2]==['atomic',session]
    if not atomic:
        others=[p for p in (Path(root)/'_Axis/Agents').glob('*.md') if p.stem!=session]
        need(not others,'serialize all writers before archiving on degraded storage')
        return io
    lock=local(root,'_Axis/Archive-Operation.lock',True);lock.mkdir()
    owner=secrets.token_hex(24)+'\n'+session+'\n';once(lock/'OWNER',owner.encode());once(lock/'BATCH',b'archiving\n');identity=(lock.stat().st_dev,lock.stat().st_ino)
    old_guard,old_close=io.guard,io.close;stopped=threading.Event();errors=[]
    def owned():
        info=safe(lock).stat();need((info.st_dev,info.st_ino)==identity and read(lock/'OWNER').decode()==owner,'archive ownership changed')
        need(time.time()-info.st_mtime<10,'archive heartbeat expired')
    def guarded(*args,**kwargs):
        need(not errors,'archive heartbeat failed');old_guard(*args,**kwargs);owned()
    def beat():
        while not stopped.wait(3):
            try:old_guard();owned();os.utime(lock,None)
            except Exception as exc:errors.append(str(exc));return
    io.guard=guarded;thread=threading.Thread(target=beat,daemon=True);thread.start()
    def close():
        stopped.set();thread.join(timeout=5)
        try:
            owned();(lock/'BATCH').unlink();(lock/'OWNER').unlink();lock.rmdir()
        finally:io.guard=old_guard;old_close()
    io.close=close;return io

def persist_level(root,io,level):
    p=Path(root)/'_Axis/SETTINGS.md';text=read(p).decode();value=policy(root,level)
    section=re.search(r'(^### Archiving\s*\n.*?)(?=^### |^## |\Z)',text,re.M|re.S)
    if section:
        need(len(re.findall(r'^\*\*Value:\*\*',section[1],re.M))==1,'Archiving setting malformed')
        replacement=re.sub(r'^\*\*Value:\*\*.*$', '**Value:** '+value,section[1],flags=re.M);text=text[:section.start()]+replacement+text[section.end():]
    else:text+='\n### Archiving\n\n**Description:** Policy for family-local history and external cold storage; temporary operational cleanup is independent.\n\n**Range:** Never, Default, Aggressive\n\n**Value:** '+value+'\n'
    io.guard(starting=False);p.write_text(text);need(read(p).decode()==text,'setting readback')

def apply_local(root,io,plan):
    need(plan['level']!='Never' or not plan['items'],'disabled archive');moves=[]
    # Preflight the whole selection before writing.
    for item in plan['items']:
        src=safe(Path(root)/item['source']);dst=safe(Path(root)/item['destination'],True)
        need(sha(read(src))==item['sha256'] and not dst.exists(),'changed source or occupied archive destination')
    for item in plan['items']:
        io.guard(starting=False);src=safe(Path(root)/item['source']);dst=safe(Path(root)/item['destination'],True);need(sha(read(src))==item['sha256'] and not dst.exists(),'archive changed')
        # The established move receipt makes historical references resolvable.
        tool=Path(__file__).with_name('record-check.py')
        subprocess.run([sys.executable,str(tool),'--root',str(root),'record-move','--session',io.sid,'--path',item['source'],'--to',item['destination'],'--reason','Archiving '+plan['level']+' lifecycle policy'],check=True,capture_output=True)
        dst.parent.mkdir(exist_ok=True);os.rename(src,dst);need(sha(read(dst))==item['sha256'] and not src.exists(),'archive move readback');moves.append(item)
        for index in ('TASKS.md','SNAPSHOTS.md'):
            p=Path(root)/'_Axis'/index
            if not p.exists():continue
            old=read(p).decode();parts=re.split(r'(?m)(?=^## )',old);needle=']('+item['source'].removeprefix('_Axis/')+')'
            removed=[part for part in parts[1:] if needle in part]
            if removed:
                need(len(removed)==1,'ambiguous active index entry');new=''.join(part for part in parts if part not in removed)
                pointer='Archived history: ['+item['family']+'/Archive]('+item['family']+'/Archive/). Cold bundles are indexed there when present.\n\n'
                if pointer not in new:
                    at=new.find('\n## ');at=at if at>=0 else len(new);new=new[:at]+'\n'+pointer+new[at:]
                io.guard();p.write_text(new)
        initiative=Path(root)/'_Axis/INITIATIVES.md'
        if initiative.exists():
            old=read(initiative).decode();new=old.replace(']('+item['source'].removeprefix('_Axis/')+')',']('+item['destination'].removeprefix('_Axis/')+')')
            if new!=old:io.guard();initiative.write_text(new)
    return moves

def destination(root):
    name=setting(root,'Cold Storage Location') or 'default'
    need(re.fullmatch('[A-Za-z0-9_-]+',name),'cold location must be a logical name')
    binding=Path(root)/'_Axis/Flags/cold-storage-location'
    need(binding.exists(),'cold destination unavailable; bind an approved existing external folder')
    v=json.loads(read(binding,65536));need(v.get('schema')==1 and v.get('name')==name and v.get('durability') in ('verified-local','verified-remote'),'invalid cold binding')
    p=safe(Path(v['path']).expanduser());need(p.is_dir() and not p.is_relative_to(Path(root)) and not Path(root).is_relative_to(p),'cold destination must be outside the project')
    need(not v.get('require_remote',False) or v['durability']=='verified-remote','remote upload not verified');return name,p,v['durability']

def catalogs(files):
    return sorted(set('_Memos/Archive/COLD.md' if f['source'].startswith('_Memos/') else '_Dev/Evidence/COLD.md' if f['source'].startswith('_Dev/Evidence/') else '_Axis/'+(Path(f['source']).parts[2] if f['source'].startswith('_Axis/Archive/') else Path(f['source']).parts[1])+'/Archive/COLD.md' for f in files))

def eligibility(root,rel,review,level):
    relative(rel);need(level!='Never','Archiving Never disables cold offload')
    need(not any(x in ('Secrets','.git','_X','_U') or x.endswith('_X') for x in Path(rel).parts),'private/protected path')
    p=local(root,rel);need(p.is_file(),'select exact files')
    for parent in p.parents:
        if parent==Path(root):break
        need(not (parent/'AGENTS.md').exists() and not (parent/'_Axis/PROJECT.md').exists(),'nested project boundary')
    now=dt.datetime.now(dt.timezone.utc)
    if rel.startswith('_Dev/Evidence/'):
        need(review.get('schema')==1 and review.get('session') and isinstance(review.get('files'),dict),'diagnostic dependency review required')
        item=review['files'].get(rel,{})
        need(item.get('sha256')==sha(read(p)) and item.get('closed') is True and item.get('local_dependencies')==[] and item.get('reconstruction') in ('unique','unavailable') and isinstance(item.get('retrieval_references'),list),'unclassified, reproducible, active or locally required evidence')
        when=date(item.get('closed_at'));need(when is not None,'diagnostic closure time required')
        need(p.stat().st_size>1024*1024 or item.get('bundle_bytes',0)>10*1024*1024,'keep small result summaries local')
        days=7 if level=='Aggressive' else 30
    else:
        need((rel.startswith('_Axis/') and '/Archive/' in rel) or rel.startswith('_Memos/Archive/'),'only archived records can become cold')
        family='Memos' if rel.startswith('_Memos/') else Path(rel).parts[1]
        need(family in FAMILIES or family=='Memos','unknown family')
        text,v=fields(p);need(terminal(family,v),'active or replay-critical record')
        when=date(v.get('completed')) or date(v.get('resolved')) or date(v.get('updated')) or date(v.get('created')) or date(p.stem.split(' - ')[0])
        days=90 if level=='Aggressive' else 365
    need(when is not None and (now-when).total_seconds()>=days*86400,'cold retention age not reached')

def export(root,io,paths,ident=None,review=None):
    name,base,durability=destination(root);hold=dependency_holds(root);files=[];review=review or {};level=policy(root)
    if ident:
        found=[(p,v) for p,v in locators(root) if v['id']==ident];need(len(found)==1,'unknown resumed cold bundle');locator,box=found[0];locator=locator.relative_to(root).as_posix();files=box['files']
        if retirement_done(root,ident,box['manifest_sha256']):return {'status':'retired','id':ident,'already_complete':True}
        need(name==box['location'] and durability==box['durability'],'cold binding changed');need(not paths or set(paths)=={f['source'] for f in files},'resume selection differs')
    else:
        need(paths and len(paths)<=100,'select 1–100 exact files per bundle')
        for rel in sorted(set(paths)):
            eligibility(root,rel,review,level);need(not held(rel,hold),'local dependency holds payload');p=local(root,rel);data=read(p)
            need(cold_lookup(root,rel) is None,'already catalogued; resume existing bundle')
            record_id=p.stem.split(' - ')[0];files.append({'source':rel,'sha256':sha(data),'bytes':len(data),'mode':stat.S_IMODE(p.stat().st_mode),'record_id':record_id if ID.fullmatch(record_id) else None})
        box={}
        def body(identity):
            value={'schema':1,'id':identity,'location':name,'relative_path':'AxisCold/'+identity,'durability':durability,'files':files,'manifest_sha256':sha(encode(files)),'created':dt.datetime.now(dt.timezone.utc).isoformat()};box.update(value)
            return 'Cold storage: '+str(len(files))+' historical files\n\nRetrieval: use archive-storage.py retrieve --id with an original identity or path.\nThe copied receipt proves completion; absent receipt means pending, sources retained.\n\n```axis-cold-storage\n'+json.dumps(value,sort_keys=True,indent=2)+'\n```\n'
        folder=local(root,'_Axis/ColdStorage',True);folder.mkdir(exist_ok=True)
        ident,locator=io.record('ColdStorage',body,renew_lease=True)
    target=safe(base/box['relative_path'],True);target.mkdir(parents=True,exist_ok=True)
    expected={n for f in files for n in (f['source'],f['source']+'.axis-copy-part')}|{'manifest.json'}
    need(not any(f['source'].endswith('.axis-copy-part') for f in files),'reserved copy suffix')
    for p in target.rglob('*'):
        safe(p);need(p.is_dir() or p.relative_to(target).as_posix() in expected,'unexpected cold destination file')
    for item in files:
        io.guard();need(not held(item['source'],dependency_holds(root)),'new dependency hold');data=read(local(root,item['source']));need(len(data)==item['bytes'] and sha(data)==item['sha256'] and stat.S_IMODE(local(root,item['source']).stat().st_mode)==item['mode'],'source changed during cold copy');dest=local(target,item['source'],True)
        if dest.exists():need(read(dest)==data,'cold destination collision')
        else:
            part=local(target,item['source']+'.axis-copy-part',True);part.parent.mkdir(parents=True,exist_ok=True)
            if part.exists():
                partial=read(part);need(len(partial)<=len(data) and data.startswith(partial),'changed partial cold copy')
                with part.open('ab') as stream:stream.write(data[len(partial):]);stream.flush();os.fsync(stream.fileno())
            else:once(part,data)
            need(read(part)==data and not dest.exists(),'copy readback or collision');os.chmod(part,item['mode']);os.rename(part,dest)
    if (target/'manifest.json').exists():need(read(target/'manifest.json')==encode(files),'manifest collision')
    else:once(target/'manifest.json',encode(files))
    for f in files:need(matches(local(target,f['source']),f),'cold readback mismatch')
    receipt=local(root,'_Axis/ColdStorage/'+ident+'/copied.json',True);proof=encode({'schema':1,'id':ident,'manifest_sha256':box['manifest_sha256']})
    if receipt.exists():need(read(receipt)==proof,'copy receipt mismatch')
    else:once(receipt,proof)
    for cat in catalogs(files):
        p=local(root,cat,True);p.parent.mkdir(parents=True,exist_ok=True);old=read(p).decode() if p.exists() else '# Cold history\n\n| Bundle | Files | Bytes | Retrieval detail |\n| --- | ---: | ---: | --- |\n';link=os.path.relpath(Path(root)/locator,p.parent)
        row='| '+ident+' | '+str(len(files))+' | '+str(sum(f['bytes'] for f in files))+' | [Details]('+link+') |\n'
        if row not in old:io.guard();p.write_text(old+row)
    return {'status':'copied','id':ident,'locator':locator,'next':'checkpoint locator, copied receipt and catalogs, then retire-cold; sources remain intact'}

def catalog_legacy(root,io,paths,ident=None):
    name,base,durability=destination(root);old=legacy_root(root)
    need(old is not None and old==base and not old.is_relative_to(root),'binding must name the existing external legacy archive')
    if ident:
        found=[(p,v) for p,v in locators(root) if v['id']==ident];need(len(found)==1,'unknown legacy locator');locator,value=found[0]
        need(value.get('layout')=='legacy' and value['location']==name,'wrong legacy binding');files=value['files'];mapping=value['existing_paths'];locator=locator.relative_to(root).as_posix()
        need(not paths or set(paths)==set(mapping),'resume selection changed')
    else:
        need(paths and len(paths)<=100,'select 1–100 legacy files');files=[];mapping={}
        for rel in sorted(set(paths)):
            relative(rel);need(rel.startswith('_Axis/Archive/'),'legacy logical path required');physical=rel.removeprefix('_Axis/Archive/');relative(physical)
            parts=Path(physical).parts;need(len(parts)==2 and parts[0] in FAMILIES and ID.fullmatch(Path(physical).stem),'select one canonical legacy record')
            need(cold_lookup(root,rel) is None and cold_lookup(root,Path(physical).stem) is None,'legacy identity already catalogued')
            p=local(base,physical);data=read(p);files.append({'source':rel,'record_id':p.stem,'sha256':sha(data),'bytes':len(data),'mode':stat.S_IMODE(p.stat().st_mode)});mapping[rel]=physical
    box={}
    def body(ident):
        box.update({'schema':1,'id':ident,'layout':'legacy','location':name,'relative_path':'.','existing_paths':mapping,'durability':durability,'files':files,'manifest_sha256':sha(encode(files)),'created':dt.datetime.now(dt.timezone.utc).isoformat()})
        return 'Cold storage: verified existing legacy history\n\nNo payload moved or copied. Legacy replay/accounting consumers still require this history.\n\n```axis-cold-storage\n'+json.dumps(box,sort_keys=True,indent=2)+'\n```\n'
    if ident:box.update(value)
    else:
        local(root,'_Axis/ColdStorage',True).mkdir(exist_ok=True);ident,locator=io.record('ColdStorage',body)
    for f in files:need(sha(read(local(base,mapping[f['source']])))==f['sha256'],'legacy source changed during cataloguing')
    receipt=local(root,'_Axis/ColdStorage/'+ident+'/copied.json',True);proof=encode({'schema':1,'id':ident,'manifest_sha256':box['manifest_sha256']})
    if receipt.exists():need(read(receipt)==proof,'legacy copy proof differs')
    else:once(receipt,proof)
    for cat in catalogs(files):
        p=local(root,cat,True);p.parent.mkdir(parents=True,exist_ok=True);oldtext=read(p).decode() if p.exists() else '# Cold history\n\n'
        row='- '+ident+': '+str(len(files))+' legacy records, '+str(sum(f['bytes'] for f in files))+' bytes; [retrieval detail]('+os.path.relpath(Path(root)/locator,p.parent)+').\n'
        if row not in oldtext:io.guard();p.write_text(oldtext+row)
    return {'status':'catalogued-in-place','id':ident,'files':len(files),'payload_bytes_copied':0}

def verified_cold_target(root,v):
    name,base,_=destination(root);need(name==v['location'],'cold destination unavailable')
    if v.get('layout')=='legacy':return base
    target=local(base,v['relative_path']);need(json.loads(read(target/'manifest.json'))==v['files'],'manifest mismatch');return target


def matches(path,item):
    data=read(path)
    return sha(data)==item['sha256'] and len(data)==item['bytes'] and stat.S_IMODE(path.stat().st_mode)==item['mode']

def retirement_done(root,ident,manifest):
    path=local(root,'_Axis/ColdStorage/'+ident+'/retired.json',True)
    if not path.exists():return False
    need(read(path)==encode({'schema':1,'id':ident,'manifest_sha256':manifest}),'invalid completed retirement')
    return True

def retire(root,io,ident):
    found=[(p,v) for p,v in locators(root) if v['id']==ident];need(len(found)==1,'unknown cold bundle');p,v=found[0];need(v.get('layout','bundle')=='bundle','legacy payload is already external; no retirement');name,base,_=destination(root);need(name==v['location'],'different cold destination');target=safe(base/v['relative_path']);need(json.loads(read(target/'manifest.json'))==v['files'],'external manifest mismatch')
    if retirement_done(root,ident,v['manifest_sha256']):return {'status':'retired','id':ident,'already_complete':True,'trash':json.loads(read(local(root,'_Axis/ColdStorage/'+ident+'/retirement.json')))['trash']}
    copied=json.loads(read(Path(root)/'_Axis/ColdStorage'/ident/'copied.json'));need(copied.get('manifest_sha256')==v['manifest_sha256'],'copy incomplete')
    g=subprocess.run(['git','-C',str(root),'rev-parse','--show-toplevel'],capture_output=True)
    if g.returncode==0 and Path(g.stdout.decode().strip())==Path(root):
        for rel in [p.relative_to(root).as_posix(),'_Axis/ColdStorage/'+ident+'/copied.json',*catalogs(v['files'])]:
            q=subprocess.run(['git','-C',str(root),'show','HEAD:'+rel],capture_output=True);need(q.returncode==0 and q.stdout==read(local(root,rel)),'checkpoint locator, receipt and catalogs before retiring source')
    else:
        for rel in [p.relative_to(root).as_posix(),'_Axis/ColdStorage/'+ident+'/copied.json',*catalogs(v['files'])]:
            copy=local(target,'catalog/'+rel,True);data=read(local(root,rel))
            if copy.exists():need(read(copy)==data,'external catalog backup differs')
            else:once(copy,data)
    holds=dependency_holds(root);need(all(not held(f['source'],holds) for f in v['files']),'new local dependency holds bundle')
    retirement=local(root,'_Axis/ColdStorage/'+ident+'/retirement.json',True)
    if not retirement.exists():once(retirement,encode({'schema':1,'id':ident,'manifest_sha256':v['manifest_sha256'],'trash':'_Trash/'+dt.datetime.now(dt.timezone.utc).date().isoformat()+'--Cold-'+ident}))
    receipt=json.loads(read(retirement));need(receipt.get('schema')==1 and receipt.get('id')==ident and receipt.get('manifest_sha256')==v['manifest_sha256'] and re.fullmatch(r'_Trash/\d{4}-\d{2}-\d{2}--Cold-'+re.escape(ident),receipt.get('trash','')),'invalid cold retirement')
    trash=local(root,receipt['trash'],True)
    for f in v['files']:
        need(matches(local(target,f['source']),f),'cold content changed');src=safe(Path(root)/f['source'],True);dst=safe(trash/f['source'],True)
        if src.exists():need(matches(src,f) and not dst.exists(),'source changed or retirement collision')
        else:need(dst.exists() and matches(dst,f),'missing source without retirement proof')
    for f in v['files']:
        io.guard(starting=False);src=Path(root)/f['source'];dst=trash/f['source']
        if src.exists():
            need(matches(safe(src),f) and not dst.exists(),'source changed during retirement');dst.parent.mkdir(parents=True,exist_ok=True);os.rename(src,dst)
    io.guard(starting=False);once(local(root,'_Axis/ColdStorage/'+ident+'/retired.json',True),encode({'schema':1,'id':ident,'manifest_sha256':v['manifest_sha256']}))
    return {'status':'retired','id':ident,'files':len(v['files']),'bytes':sum(f['bytes'] for f in v['files']),'trash':str(trash.relative_to(root))}

def retrieve(root,io,identity):
    match=cold_lookup(root,identity);need(match is not None,'cold record not found');p,v,f=match;target=verified_cold_target(root,v);data=read(local(target,v.get('existing_paths',{}).get(f['source'],f['source'])));need(sha(data)==f['sha256'] and len(data)==f['bytes'],'retrieval hash mismatch')
    dest=Path(root)/'_Temp'/('ColdRead-'+v['id'])/f['source'];io.guard(starting=False)
    if dest.exists():need(read(dest)==data,'retrieval collision')
    else:once(dest,data);os.chmod(dest,f['mode'])
    need(matches(dest,f),'retrieved mode or content differs')
    return {'status':'retrieved','path':str(dest.relative_to(root)),'sha256':f['sha256'],'terminal_state_unchanged':True}

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--session');p.add_argument('action',choices=('plan','run','export','retire-cold','retrieve','protected','catalog-legacy'));p.add_argument('--level');p.add_argument('--dry-run',action='store_true');p.add_argument('--path',action='append');p.add_argument('--id');p.add_argument('--selection');a=p.parse_args();root=safe(a.root)
    if a.level:policy(root,a.level)
    if a.action=='protected':result={'protected':protected_temporary(root)}
    elif a.action=='plan' or a.dry_run:
        need(a.action in ('plan','run'),'dry-run is available for plan/run');result=inventory(root,a.level)
    else:
        need(a.session,'Main session required');io=lease(root,a.session)
        try:
            if a.action=='run':
                if a.level:persist_level(root,io,a.level)
                result=inventory(root,a.level)
                result['moved']=apply_local(root,io,result)
            elif a.action=='export':result=export(root,io,a.path or [],a.id,json.loads(read(local(root,a.selection))) if a.selection else {})
            elif a.action=='catalog-legacy':result=catalog_legacy(root,io,a.path or [],a.id)
            elif a.action=='retire-cold':result=retire(root,io,a.id)
            else:result=retrieve(root,io,a.id)
        finally:io.close()
    print(json.dumps(result,sort_keys=True));return 0
if __name__=='__main__':
    try:raise SystemExit(main())
    except (Held,OSError,ValueError,KeyError,subprocess.SubprocessError) as e:print(json.dumps({'status':'held','reason':str(e)}));raise SystemExit(2)
