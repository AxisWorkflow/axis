#!/usr/bin/env python3
"""Enforce a reviewed update plan with durable evidence and bounded recovery.

Python 3/POSIX is optional update acceleration, not an Axis core dependency.
Official-release verification and literal User authority are caller attestations.
This tool never fetches, executes target code, infers consent or rewrites project
planning records. Check-Update-Handoff.md owns the equivalent file-only contract.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse,datetime,hashlib,json,os,re,secrets,stat,sys,tempfile,time
try:
    import fcntl
except ImportError:
    print("Update accelerator unavailable: POSIX locking is absent; use the verified file-only procedure.",file=sys.stderr)
    raise SystemExit(2)
ID=r'\d{4}(?:\.\d{2}){5}\.\d{3}Z'
ENTRIES=('AGENTS.md','CLAUDE.md','GEMINI.md')
PROJECT=('_Axis/PROJECT.md','_Axis/SETTINGS.md','_Axis/MINDSET.md','_Axis/DIRECTIVES.md','_Axis/ENVIRONMENT.md')
MUTABLE=('_Axis/PLAN.md','_Axis/TASKS.md','_Axis/SNAPSHOTS.md',*PROJECT)
TOP=('.gitattributes','.gitignore','README.md','LICENSE',*ENTRIES)
MANAGED=('_Axis/CHANGELOG.md','_Axis/CLA.md','_Axis/CONTRIBUTING.md','_Axis/LICENSE','_Axis/README.md','_Axis/GLOSSARY.md','_Axis/MANIFEST.md','_Axis/PRACTICES.md','_Axis/PRINCIPLES.md','_Axis/RULES.md')
PREFIX=('_Axis/Commands/','_Axis/Practices/','_Axis/Rules/','_Axis/Resources/','_Axis/Dashboard/')

def require(v,m):
    if not v:raise ValueError(m)
def encode(v):return (json.dumps(v,sort_keys=True,indent=2)+'\n').encode()
def digest(b):return hashlib.sha256(b).hexdigest()
def parse(b):
    def unique(items):
        out={}
        for k,v in items:require(k not in out,'duplicate JSON field');out[k]=v
        return out
    return json.loads(b,object_pairs_hook=unique)
def safe(root,name):
    require(isinstance(name,str) and name and not name.startswith('/') and '\\' not in name and all(x not in ('','.','..') for x in name.split('/')),'unsafe path')
    p=root
    for part in name.split('/'):
        if p.exists():
            require(p.is_dir(),'non-directory parent');names=[q.name for q in p.iterdir()]
            require(not (p/part).exists() or part in names,'filesystem alias')
            require(not any(n.casefold()==part.casefold() and n!=part for n in names),'case collision')
        p/=part;require(not p.is_symlink(),'symbolic path')
        if p.exists():
            s=p.stat();require(stat.S_ISDIR(s.st_mode) or stat.S_ISREG(s.st_mode) and s.st_nlink==1,'unsafe object')
    return p

def read(p):require(p.is_file() and not p.is_symlink() and p.stat().st_nlink==1,'missing or unsafe file');return p.read_bytes()
def identity(p):
    if not p.exists():return None
    b=read(p);return {'sha256':digest(b),'bytes':len(b),'mode':stat.S_IMODE(p.stat().st_mode)}
def valid_identity(v):
    require(v is None or isinstance(v,dict) and set(v)=={'sha256','bytes','mode'} and re.fullmatch('[0-9a-f]{64}',str(v['sha256'])) and type(v['bytes']) is int and v['bytes']>=0 and type(v['mode']) is int and 0<=v['mode']<=0o777,'invalid file identity')
def syncdir(p):
    fd=os.open(p,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)
def once(p,v):
    data=v if isinstance(v,bytes) else encode(v);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
    syncdir(p.parent);require(read(p)==data,'evidence readback failed')
def replace(p,data,mode):
    p.parent.mkdir(parents=True,exist_ok=True)
    if data is None:p.unlink();syncdir(p.parent);return
    fd,n=tempfile.mkstemp(prefix='.'+p.name+'.update-',dir=p.parent)
    try:
        with os.fdopen(fd,'wb') as f:f.write(data);f.flush();os.fsync(f.fileno())
        os.chmod(n,mode);os.replace(n,p);syncdir(p.parent)
    finally:
        if os.path.exists(n):os.unlink(n)
    require(read(p)==data and stat.S_IMODE(p.stat().st_mode)==mode,'write readback failed')
def version(s):
    require(isinstance(s,str) and re.fullmatch(r'\d{2}\.\d{2}\.\d{2}(?:-[1-9]\d*)?',s),'invalid version')
    d,sep,n=s.partition('-');y,m,day=map(int,d.split('.'));datetime.date(2000+y,m,day);return y,m,day,int(n) if sep else 1

def classification(p):
    try:
        require(p.get('schema')==1 and p.get('origin_supported') is True,'unsupported origin')
        origin,target=version(p['from_version']),version(p['to_version']);s=p['source'];a=p['authorization'];c=p['checks']
        require(s['repository']=='AxisWorkflow/axis' and s['tag']=='v'+p['to_version'] and s['official_verified'] is True and s['draft'] is False and s['prerelease'] is False,'unverified official source')
        require(all(re.fullmatch('[0-9a-f]{40}',str(s[k])) for k in ('commit','tree')) and re.fullmatch('[0-9a-f]{64}',str(s['archive_sha256'])),'inexact source identity')
        require(a['kind']=='user-update' and c.get('integrity') is True and c.get('exclusive') is True and c=={'integrity':True,'storage':'atomic','policy':'auto','exclusive':True},'authority or safety precondition failed')
        impacts=p['impacts'];require(isinstance(impacts,list) and impacts and all(x in ('automatic','review','manual') for x in impacts),'unknown migration impact')
        require(target>=origin,'downgrade');require('manual' not in impacts,'manual migration required')
        if target==origin:return {'classification':'noop','reason':'already current'}
        choices=p['required_decisions'];require(isinstance(choices,list) and len(set(choices))==len(choices) and all(isinstance(x,str) and x for x in choices),'invalid decisions')
        decisions=a['decisions'];require(isinstance(decisions,dict) and not set(decisions)-set(choices),'unbound decision')
        if any(not isinstance(decisions.get(k),str) or not decisions[k].strip() for k in choices):return {'classification':'review','reason':'specific decisions remain'}
        if 'review' in impacts:
            require(bool(choices),'review migration needs explicit decisions');return {'classification':'approved-exception','reason':'all exact-plan decisions resolved'}
        return {'classification':'routine','reason':'expected automatic update authorized by User invocation'}
    except (ValueError,KeyError,TypeError) as e:return {'classification':'blocked','reason':str(e)}

def lease(root,sid,boot=False):
    require(re.fullmatch(ID,sid),'invalid session');p=safe(root,f'_Axis/Agents/{sid}.md');lines=read(p).decode().splitlines()
    require(len(lines)==4 and lines[:3]==['Main: session','','session: '+sid] and lines[3].startswith('host: ') and lines[3][6:],'Main authority required')
    require(not safe(root,f'_Axis/Agents/{sid}.kill').exists() and 0<=time.time()-p.stat().st_mtime<3600,'Main lease inactive')
    if boot:
        s=safe(root,'_Axis/Flags/starting');require(s.exists() and read(s).decode().splitlines()[0]==sid,'consumption requires current admitted startup')
    else:require(read(safe(root,'_Axis/Flags/session-id')).decode().splitlines()[0]==sid,'wrong session')
    for q in safe(root,'_Axis/Agents').glob('*.md'):
        if q!=p and not safe(root,str(q.relative_to(root).with_suffix('.kill'))).exists():require(time.time()-q.stat().st_mtime>=3600,'another writer may be active')
    require(read(safe(root,'_Axis/Flags/host-storage')).decode().splitlines()[0]=='atomic','atomic storage required')
    require(re.search(r'### Storage Policy\n(?:(?!\n### ).)*?\*\*Value:\*\* auto(?:\n|$)',read(safe(root,'_Axis/SETTINGS.md')).decode(),re.S),'storage policy forbids transaction')
    return p

def plan_scope(p):
    scope=parse(encode(p));scope['authorization'].pop('sha256',None);return digest(encode(scope))

def authorization(root,p,frozen=None,engine=None):
    a=p['authorization'];require(re.fullmatch('_Axis/Logs/'+ID+r'\.md',a['record']),'invalid authorization record')
    data=read(safe(root,a['record'])) if frozen is None else frozen
    require(digest(data)==a['sha256'],'authorization changed')
    fields=[v for v in data.decode().splitlines() if v.startswith('plan_scope_sha256:')]
    require(fields==['plan_scope_sha256: '+plan_scope(p)],'plan differs from independently recorded scope')
    engine_fields=[v for v in data.decode().splitlines() if v.startswith('engine_sha256:')]
    expected=digest(Path(__file__).read_bytes()) if engine is None else engine
    require(engine_fields==['engine_sha256: '+expected],'engine differs from independent authorization')
    return data

def validate_plan(root,p):
    require(classification(p)['classification'] in ('routine','approved-exception'),'update requires resolved authority and preconditions')
    authorization(root,p)
    require(isinstance(p['changes'],list) and p['changes'],'empty plan');seen=set();migrations=p.get('migration_paths',[]);require(isinstance(migrations,list) and all(n in PROJECT for n in migrations),'invalid semantic migration scope')
    for v in p['changes']:
        require(set(v)=={'path','before','after','staged'},'invalid change fields');n=v['path'];safe(root,n);require(n in TOP or n in MANAGED or n.startswith(PREFIX) or n in migrations or n=='.github/README.md' and v['after'] is None,'unmanaged or protected mutation target');require(n.casefold() not in seen,'duplicate target');seen.add(n.casefold());valid_identity(v['before']);valid_identity(v['after']);require(v['before']!=v['after'],'no-op change')
        if v['after'] is None:require(v['staged'] is None,'deletion has payload')
        else:require(v['staged'].startswith('_Temp/'),'payload must be reviewed local staging');require(identity(safe(root,v['staged']))==v['after'],'staged bytes changed')
    for field in ('preserved','source_checks'):
        require(isinstance(p[field],dict),'invalid identity map')
        for n,v in p[field].items():
            require(not n.casefold().startswith(('_axis/secrets/','_x/','.git/')),'protected private path');valid_identity(v);require(identity(safe(root,n))==v,field+' changed')
    require(re.search(r'^current-version: '+re.escape(p['from_version'])+r'$',read(safe(root,'_Axis/CHANGELOG.md')).decode(),re.M),'origin version differs from plan')
    replacements={v['path']:v for v in p['changes']}
    def proposed(name):
        v=replacements.get(name)
        if v is None:return read(safe(root,name))
        require(v['after'] is not None,'required core file cannot retire');return read(safe(root,v['staged']))
    require(len({proposed(n) for n in ENTRIES})==1,'planned entry mismatch')
    require(re.search(r'^current-version: '+re.escape(p['to_version'])+r'$',proposed('_Axis/CHANGELOG.md').decode(),re.M),'planned target version mismatch')
    if '_Axis/SETTINGS.md' in replacements:
        require(re.search(r'### Storage Policy\n(?:(?!\n### ).)*?\*\*Value:\*\* auto(?:\n|$)',proposed('_Axis/SETTINGS.md').decode(),re.S),'storage-policy transition requires reviewed manual migration')
    require(bool(p['source_checks']),'source identity checks required')
    require(p['source']['archive_sha256'] in [v['sha256'] for v in p['source_checks'].values() if v],'archive not pinned')
    require(isinstance(p['reconciliation'],dict),'invalid reconciliation set')
    for n,rules in p['reconciliation'].items():
        require(n in MUTABLE or n.startswith(('_Axis/Tasks/','_Axis/Followups/')) and n.endswith('.md'),'invalid reconciliation path')
        safe(root,n);require(not any(v['path']==n for v in p['changes']),'managed changes cannot also require reconciliation');require(set(rules) in ({'contains','absent'},{'contains','absent','archive_to'}) and all(isinstance(rules[k],list) and all(isinstance(x,str) and x for x in rules[k]) for k in ('contains','absent')),'invalid reconciliation conditions')
        if 'archive_to' in rules:
            target=rules['archive_to'];require(n.startswith('_Axis/Followups/') and target=='_Axis/Archive/Followups/'+Path(n).name,'invalid reconciliation archive');safe(root,target);require(target not in p['preserved'] and not any(v['path']==target for v in p['changes']),'archive destination has conflicting ownership')

def ordered(p):return sorted(p['changes'],key=lambda v:(2 if v['path']=='_Axis/CHANGELOG.md' else 1 if v['path'] in ENTRIES else 0,v['path']))
def live(root,p,which):return all(identity(safe(root,v['path']))==v[which] for v in p['changes'])
def preserved(root,p,reconciling=False):return all(identity(safe(root,n))==v for n,v in p['preserved'].items() if not (reconciling and n in p['reconciliation']))
def after(root,p,reconciling=False):
    require(live(root,p,'after') and preserved(root,p,reconciling),'applied or preserved state drift')
    require(len({read(safe(root,n)) for n in ENTRIES})==1,'entry parity failed')
    require(re.search(r'^current-version: '+re.escape(p['to_version'])+r'$',read(safe(root,'_Axis/CHANGELOG.md')).decode(),re.M),'installed version mismatch')

def load(root,tx):
    require(re.fullmatch(ID,tx),'invalid transaction ID');E=safe(root,'_Axis/Updates/'+tx);s=parse(read(safe(E,'start.json')));p=s['plan'];require(s['schema']==1 and s['transaction']==tx and digest(encode(p))==s['plan_sha256'],'invalid transaction start');evidence(root,E,s,p);return E,s,p

def evidence(root,E,s,p):
    require(re.fullmatch(ID,s['session']) and re.fullmatch('[0-9a-f]{48}',s['token']),'invalid transaction owner')
    closed=(E/'consumed.json').exists() or (E/'rollback.json').exists() and (E/'released.json').exists()
    authorization(root,p,read(safe(E,'authorization.md')) if closed else None,s['engine_sha256'])
    require(digest(read(safe(E,'authorization.md')))==p['authorization']['sha256'],'frozen authorization changed')
    require(digest(read(safe(E,'engine.py')))==s['engine_sha256'],'frozen engine changed')
    allowed={'start.json','engine.py','authorization.md','prepared.json','barrier-intent.json','barrier-result.json','rollback-intent.json','rollback.json','complete.json','ready.json','release-intent.json','released.json','consumed.json','reconciliation-start.json'}
    ready=(E/'prepared.json').exists()
    if ready:require(parse(read(safe(E,'prepared.json')))=={'plan_sha256':s['plan_sha256']},'prepared receipt changed')
    for i,v in enumerate(ordered(p),1):
        for side in ('before','after'):
            n=f'{side}-{i:04d}.bin';expected=v[side]
            if expected is not None:
                allowed.add(n);q=safe(E,n)
                if ready or q.exists():
                    data=read(q);require(digest(data)==expected['sha256'] and len(data)==expected['bytes'],'durable '+side+' evidence changed')
        allowed.update((f'{i:04d}-intent.json',f'{i:04d}-result.json'))
    for q in E.iterdir():require(q.name in allowed and safe(E,q.name).is_file(),'unknown transaction evidence')

def barrier(root,E,s,create=False):
    d=safe(root,'_Axis/Flags/starting.lock');flag=safe(root,'_Axis/Flags/starting');owner=encode({'kind':'update','transaction':s['transaction'],'session':s['session'],'token':s['token']})
    if create:
        require(not d.exists() and (not flag.exists() or not read(flag).strip() or read(flag).splitlines()[0]==b'cleared'),'startup admission occupied')
        once(E/'barrier-intent.json',{'owner_sha256':digest(owner),'session':s['session']});d.mkdir();once(d/'OWNER',owner)
        replace(flag,(s['session']+'\n').encode(),0o644);once(E/'barrier-result.json',{'outcome':'held','inode':d.stat().st_ino})
    else:
        require(d.is_dir() and read(safe(d,'OWNER'))==owner and read(flag).splitlines()[0].decode()==s['session'],'update admission ownership lost')
    return d,flag,owner

def release_barrier(root,E,s,fault):
    d=safe(root,'_Axis/Flags/starting.lock');flag=safe(root,'_Axis/Flags/starting')
    held=parse(read(safe(E,'barrier-result.json'))) if (E/'barrier-result.json').exists() else None
    owner=encode({'kind':'update','transaction':s['transaction'],'session':s['session'],'token':s['token']})
    intent={'plan_sha256':s['plan_sha256'],'owner_sha256':digest(owner),'inode':held['inode'] if held else None}
    if (E/'release-intent.json').exists():require(parse(read(safe(E,'release-intent.json')))==intent,'release intent changed')
    else:once(E/'release-intent.json',intent)
    fault('after-release-intent')
    cleared=not flag.exists() or not read(flag).strip() or read(flag).splitlines()[0]==b'cleared'
    if not d.exists():require(cleared,'foreign startup state');return
    require(held is not None and d.stat().st_ino==held['inode'],'replacement admission directory')
    own=safe(d,'OWNER')
    if own.exists():
        require(read(own)==owner and (cleared or read(flag).splitlines()[0].decode()==s['session']),'release ownership lost')
        if not cleared:replace(flag,b'cleared\n',0o644)
        fault('after-barrier-clear');require(read(own)==owner,'barrier owner changed');own.unlink();syncdir(d);fault('after-owner-remove')
    else:require(cleared and not list(d.iterdir()),'incomplete release ownership')
    d.rmdir();syncdir(d.parent);fault('after-barrier-remove')


def journal(E,s,p):
    for i,v in enumerate(ordered(p),1):
        intent=E/f'{i:04d}-intent.json';result=E/f'{i:04d}-result.json'
        if intent.exists():require(parse(read(intent))=={'index':i,'change':v,'plan_sha256':s['plan_sha256']},'changed write intent')
        if result.exists():require(intent.exists() and parse(read(result))=={'index':i,'path':v['path'],'identity':v['after']},'changed write result')


    def receipt(name,expected):
        q=E/(name+'.json')
        if q.exists():require(parse(read(q))==expected,name+' receipt changed')
        return q.exists()
    pin=s['plan_sha256'];owner=encode({'kind':'update','transaction':s['transaction'],'session':s['session'],'token':s['token']})
    receipt('barrier-intent',{'owner_sha256':digest(owner),'session':s['session']})
    held=None
    if (E/'barrier-result.json').exists():
        held=parse(read(E/'barrier-result.json'));require(set(held)=={'outcome','inode'} and held['outcome']=='held' and type(held['inode']) is int and held['inode']>0 and (E/'barrier-intent.json').exists(),'invalid barrier receipt')
    complete=receipt('complete',{'schema':1,'plan_sha256':pin,'target_commit':p['source']['commit'],'writes':len(p['changes'])})
    if complete:require((E/'prepared.json').exists() and held is not None and all((E/f'{i:04d}-result.json').exists() for i in range(1,len(p['changes'])+1)),'completion lacks full journal')
    receipt('rollback-intent',{'plan_sha256':pin})
    rolled=receipt('rollback',{'schema':1,'plan_sha256':pin,'outcome':'restored'})
    if rolled:require((E/'rollback-intent.json').exists(),'rollback lacks intent')
    ready=receipt('ready',{'plan_sha256':pin,'target_commit':p['source']['commit'],'shutdown_required':True})
    if ready:require(complete and not rolled,'ready lacks successful completion')
    releasing=receipt('release-intent',{'plan_sha256':pin,'owner_sha256':digest(owner),'inode':held['inode'] if held else None})
    released=receipt('released',{'plan_sha256':pin,'outcome':'admission released'})
    if released:require(releasing and (ready or rolled),'release lacks terminal prerequisites')
    if (E/'reconciliation-start.json').exists():
        phase=parse(read(E/'reconciliation-start.json'));require(set(phase)=={'schema','transaction','session','plan_sha256','records'} and phase['schema']==1 and phase['transaction']==s['transaction'] and phase['plan_sha256']==pin and re.fullmatch(ID,phase['session']) and phase['session']!=s['session'] and ready and released and not rolled and set(phase['records'])==set(p['reconciliation']),'invalid reconciliation phase')
        for n,value in phase['records'].items():
            valid_identity(value);require(value is not None,'missing pre-reconciliation identity')
            if n in p['preserved']:require(value==p['preserved'][n],'preservation phase binding changed')
    if (E/'consumed.json').exists():
        r=parse(read(E/'consumed.json'));require(set(r)=={'schema','transaction','session','plan_sha256','target_commit','reconciliation','consumed'} and r['schema']==1 and r['transaction']==s['transaction'] and r['plan_sha256']==pin and r['target_commit']==p['source']['commit'] and re.fullmatch(ID,r['session']) and r['session']!=s['session'] and ready and released and not rolled,'invalid consumption chain')
        datetime.datetime.fromisoformat(r['consumed']);rec=r['reconciliation'];require(set(rec)=={'schema','transaction','target_commit','records'} and rec['schema']==1 and rec['transaction']==s['transaction'] and rec['target_commit']==p['source']['commit'] and set(rec['records'])==set(p['reconciliation']),'invalid consumed reconciliation')
        for n,value in rec['records'].items():
            if 'archive_to' in p['reconciliation'][n]:
                require(isinstance(value,dict) and set(value)=={'path','identity'} and value['path']==p['reconciliation'][n]['archive_to'],'invalid consumed archive identity');value=value['identity']
            valid_identity(value);require(value is not None,'missing consumed record identity')
        if set(p['preserved'])&set(p['reconciliation']) or any('archive_to' in r for r in p['reconciliation'].values()):require((E/'reconciliation-start.json').exists(),'consumption lacks preservation transition')

def state(root,E,s,p):
    journal(E,s,p)
    if (E/'consumed.json').exists():
        r=parse(read(E/'consumed.json'));require(r['transaction']==s['transaction'] and r['plan_sha256']==s['plan_sha256'] and r['target_commit']==p['source']['commit'] and (E/'ready.json').exists(),'invalid consumption receipt');return 'closed'
    if (E/'rollback.json').exists():
        require(parse(read(E/'rollback.json'))['plan_sha256']==s['plan_sha256'],'invalid rollback receipt')
        if (E/'released.json').exists():return 'closed'
        require(live(root,p,'before') and preserved(root,p),'rolled-back state drift');return 'rolled-back'
    if (E/'complete.json').exists():
        require(parse(read(E/'complete.json'))=={'schema':1,'plan_sha256':s['plan_sha256'],'target_commit':p['source']['commit'],'writes':len(p['changes'])},'invalid completion')
        require(all((E/f'{i:04d}-result.json').is_file() for i in range(1,len(p['changes'])+1)),'incomplete journal');after(root,p,(E/'reconciliation-start.json').exists())
        return 'ready' if (E/'ready.json').exists() and (E/'released.json').exists() else 'complete'
    if (E/'barrier-intent.json').exists() or list(E.glob('*-intent.json')):return 'interrupted'
    return 'prepared' if (E/'prepared.json').exists() else 'preparing'

def inspect(root):
    U=safe(root,'_Axis/Updates')
    if not U.exists():return {'state':'none','next_action':'ordinary startup'}
    pending=[]
    for E in sorted(U.iterdir()):
        if E.name in ('.gitkeep','operation.lck'):continue
        require(E.is_dir() and re.fullmatch(ID,E.name),'unknown update evidence')
        E,s,p=load(root,E.name);value=state(root,E,s,p)
        if value!='closed':pending.append((E.name,value))
    require(len(pending)<=1,'multiple unconsumed updates')
    if not pending:return {'state':'none','next_action':'ordinary startup'}
    tx,value=pending[0];actions={'preparing':'owner aborts before apply','prepared':'owner applies or rolls back','interrupted':'owner or quiescent recovery restores exact preimages','rolled-back':'owner releases admission','complete':'owner verifies and finishes shutdown','ready':'fresh admitted Main reconciles and consumes before ordinary context'}
    return {'transaction':tx,'state':value,'next_action':actions[value]}

@contextmanager
def operation(root):
    U=safe(root,'_Axis/Updates');U.mkdir(exist_ok=True);p=safe(U,'operation.lck');fd=os.open(p,os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    try:
        require(os.fstat(fd).st_nlink==1 and stat.S_ISREG(os.fstat(fd).st_mode),'unsafe update lock');fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB);yield
    finally:os.close(fd)

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=('classify','prepare','apply','inspect','rollback','release','begin-reconcile','consume'));p.add_argument('--root',required=True);p.add_argument('--plan');p.add_argument('--session');p.add_argument('--transaction');p.add_argument('--token');p.add_argument('--fault');p.add_argument('--reconciliation');a=p.parse_args();root=Path(a.root).absolute();require(root==root.resolve() and root.is_dir(),'canonical root required')
    def localarg(name):
        q=Path(name).absolute();require(q.is_relative_to(root),'input outside project');return safe(root,q.relative_to(root).as_posix())
    if a.action in ('classify','prepare'):plan=parse(read(localarg(a.plan)))
    if a.action=='classify':print(json.dumps(classification(plan),sort_keys=True));return
    if a.action=='inspect':print(json.dumps(inspect(root),sort_keys=True));return
    require(a.session and a.transaction,'session and transaction required');lease(root,a.session,a.action in ('begin-reconcile','consume'))
    with operation(root):
        lease(root,a.session,a.action in ('begin-reconcile','consume'))
        if a.action=='prepare':
            validate_plan(root,plan);require(live(root,plan,'before'),'local state changed');require(inspect(root)['state']=='none','unconsumed update exists');require(re.fullmatch(ID,a.transaction) and a.transaction==Path(plan['authorization']['record']).stem,'transaction must use scoped authorization Event identity');E=safe(root,'_Axis/Updates/'+a.transaction);require(not E.exists(),'transaction exists');E.mkdir();token=secrets.token_hex(24);s={'schema':1,'transaction':a.transaction,'session':a.session,'token':token,'plan':plan,'plan_sha256':digest(encode(plan)),'engine_sha256':digest(Path(__file__).read_bytes()),'started':datetime.datetime.now(datetime.timezone.utc).isoformat()};once(E/'start.json',s);once(E/'engine.py',Path(__file__).read_bytes());once(E/'authorization.md',authorization(root,plan))
            for i,v in enumerate(ordered(plan),1):
                if v['before'] is not None:once(E/f'before-{i:04d}.bin',read(safe(root,v['path'])))
                if v['after'] is not None:once(E/f'after-{i:04d}.bin',read(safe(root,v['staged'])))
            require(live(root,plan,'before') and preserved(root,plan),'state changed while preparing');once(E/'prepared.json',{'plan_sha256':s['plan_sha256']});print(json.dumps({'transaction':a.transaction,'token':token,'state':'prepared','engine':str(E/'engine.py')}));return
        E,s,plan=load(root,a.transaction);journal(E,s,plan)
        if a.action not in ('begin-reconcile','consume'):
            require(s['session']==a.session and s['token']==a.token,'not the transaction owner');require(digest(Path(__file__).read_bytes())==s['engine_sha256'],'use the verified frozen transaction engine')
        def fault(point):
            if a.fault==point:
                require(a.action in ('apply','release','consume') and read(safe(root,'_Temp/disposable-update-fixture'))==b'disposable\n' and root.is_relative_to(Path(tempfile.gettempdir()).resolve()),'faults require disposable fixture');os._exit(73)
        if a.action=='apply':
            require(not (E/'rollback.json').exists() and not (E/'ready.json').exists(),'terminal update cannot apply')
            if (E/'complete.json').exists():after(root,plan);print(json.dumps({'state':'complete'}));return
            require((E/'prepared.json').exists() and not (E/'barrier-intent.json').exists(),'interrupted preparation/apply requires recovery');validate_plan(root,plan);require(live(root,plan,'before'),'local state changed');barrier(root,E,s,True)
            for i,v in enumerate(ordered(plan),1):
                lease(root,a.session);barrier(root,E,s);q=safe(root,v['path']);require(identity(q)==v['before'],'local state changed before write');data=read(E/f'after-{i:04d}.bin') if v['after'] is not None else None
                if data is not None:require(digest(data)==v['after']['sha256'] and len(data)==v['after']['bytes'],'durable payload drift')
                once(E/f'{i:04d}-intent.json',{'index':i,'change':v,'plan_sha256':s['plan_sha256']});fault(f'after-intent-{i}');replace(q,data,v['after']['mode'] if v['after'] else 0);fault(f'after-write-{i}');require(identity(q)==v['after'],'postimage mismatch');once(E/f'{i:04d}-result.json',{'index':i,'path':v['path'],'identity':v['after']});fault(f'after-result-{i}')
            after(root,plan);fault('before-complete');once(E/'complete.json',{'schema':1,'plan_sha256':s['plan_sha256'],'target_commit':plan['source']['commit'],'writes':len(plan['changes'])});fault('after-complete');print(json.dumps({'state':'complete'}));return
        if a.action=='rollback':
            require(not (E/'ready.json').exists() and not (E/'consumed.json').exists(),'released success cannot roll back');require(preserved(root,plan),'preserved state changed')
            for i,v in enumerate(ordered(plan),1):
                current=identity(safe(root,v['path']));require(current in (v['before'],v['after']),'third-value source; no recovery writes')
                if current!=v['before'] and v['before'] is not None:
                    b=read(E/f'before-{i:04d}.bin');require(digest(b)==v['before']['sha256'] and len(b)==v['before']['bytes'],'rollback evidence mismatch')
            if (E/'rollback.json').exists():require(live(root,plan,'before'),'recovered state drift');print(json.dumps({'state':'rolled-back'}));return
            if (E/'barrier-result.json').exists():barrier(root,E,s)
            if not (E/'rollback-intent.json').exists():once(E/'rollback-intent.json',{'plan_sha256':s['plan_sha256']})
            for i,v in reversed(list(enumerate(ordered(plan),1))):
                lease(root,a.session);q=safe(root,v['path']);current=identity(q);require(current in (v['before'],v['after']),'third-value during recovery')
                if current!=v['before']:replace(q,read(E/f'before-{i:04d}.bin') if v['before'] else None,v['before']['mode'] if v['before'] else 0)
            require(live(root,plan,'before') and preserved(root,plan),'rollback verification failed');once(E/'rollback.json',{'schema':1,'plan_sha256':s['plan_sha256'],'outcome':'restored'});print(json.dumps({'state':'rolled-back'}));return
        if a.action=='release':
            value=state(root,E,s,plan);require(value in ('complete','ready','rolled-back','closed'),'transaction not ready to release')
            if (E/'consumed.json').exists():raise ValueError('consumed transaction has no old-owner action')
            if (E/'rollback.json').exists():require(live(root,plan,'before'),'rollback changed before release')
            else:
                after(root,plan)
                if not (E/'ready.json').exists():once(E/'ready.json',{'plan_sha256':s['plan_sha256'],'target_commit':plan['source']['commit'],'shutdown_required':True})
            release_barrier(root,E,s,fault)
            if not (E/'released.json').exists():once(E/'released.json',{'plan_sha256':s['plan_sha256'],'outcome':'admission released'})
            print(json.dumps({'state':'rolled-back' if (E/'rollback.json').exists() else 'ready','shutdown_required':not (E/'rollback.json').exists()}));return
        if a.action=='begin-reconcile':
            require(a.session!=s['session'],'fresh Main required for reconciliation');value=state(root,E,s,plan);require(value=='ready','ready handoff required')
            if (E/'reconciliation-start.json').exists():print(json.dumps({'state':'reconciling','already_started':True}));return
            after(root,plan);records={n:identity(safe(root,n)) for n in plan['reconciliation']};require(all(v is not None for v in records.values()),'missing pre-reconciliation record')
            for rules in plan['reconciliation'].values():
                if 'archive_to' in rules:require(not safe(root,rules['archive_to']).exists(),'archive destination occupied')
            once(E/'reconciliation-start.json',{'schema':1,'transaction':s['transaction'],'session':a.session,'plan_sha256':s['plan_sha256'],'records':records});print(json.dumps({'state':'reconciling','already_started':False}));return
        require(a.action=='consume','unknown action');value=state(root,E,s,plan)
        if (E/'consumed.json').exists():print(json.dumps({'state':'consumed','already_consumed':True}));return
        require(value=='ready' and a.session!=s['session'],'fresh ready transaction required');rec=parse(read(localarg(a.reconciliation)));require(set(rec)=={'schema','transaction','target_commit','records'} and rec['schema']==1 and rec['transaction']==a.transaction and rec['target_commit']==plan['source']['commit'] and set(rec['records'])==set(plan['reconciliation']),'inexact reconciliation')
        for n,rules in plan['reconciliation'].items():
            q=safe(root,n);expected=rec['records'][n]
            if 'archive_to' in rules:
                require((E/'reconciliation-start.json').exists() and not q.exists(),'archived Follow-Up must be absent from live records');require(isinstance(expected,dict) and set(expected)=={'path','identity'} and expected['path']==rules['archive_to'],'wrong archive destination');q=safe(root,expected['path']);expected=expected['identity']
            require(identity(q)==expected,'reconciliation record changed');text=read(q).decode();require(all(v in text for v in rules['contains']) and not any(v in text for v in rules['absent']),'project reconciliation incomplete')
        if set(plan['preserved'])&set(plan['reconciliation']):require((E/'reconciliation-start.json').exists(),'begin reconciliation before changing preserved records')
        after(root,plan,(E/'reconciliation-start.json').exists());fault('before-consumed');once(E/'consumed.json',{'schema':1,'transaction':a.transaction,'session':a.session,'plan_sha256':s['plan_sha256'],'target_commit':plan['source']['commit'],'reconciliation':rec,'consumed':datetime.datetime.now(datetime.timezone.utc).isoformat()});fault('after-consumed');print(json.dumps({'state':'consumed','already_consumed':False}))

if __name__=='__main__':
    try:main()
    except (ValueError,OSError,KeyError,TypeError,IndexError,UnicodeError) as e:print('Update stopped: '+str(e),file=sys.stderr);raise SystemExit(2)
