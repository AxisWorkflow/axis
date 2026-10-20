#!/usr/bin/env python3
"""Optional portable Message transport. No network, model calls or execution of message text.
Only own Main imports into canonical records; direct neighbours receive bounded envelopes.
"""
from pathlib import Path
import argparse, contextlib, datetime as dt, hashlib, importlib.util, json, os, re, secrets, stat, sys, time
sys.dont_write_bytecode = True
spec=importlib.util.spec_from_file_location('coordination',Path(__file__).with_name('coordination.py'))
core=importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
MAX=131072
LEGACY_MAX=262144
SCHEMA='axis.submission/v1'
ANCHORS=('AGENTS.md','CLAUDE.md','GEMINI.md','_Axis/MANIFEST.md','_Axis/PROJECT.md','_Axis/PRACTICES.md','_Axis/RULES.md')

def safe(path, directory=False, missing=False):
 p=Path(os.path.abspath(path)); current=Path(p.anchor)
 for part in p.parts[1:]:
  current/=part
  try:info=current.lstat()
  except FileNotFoundError:
   if current==p and missing:return p
   raise ValueError('missing path') from None
  if stat.S_ISLNK(info.st_mode):raise ValueError('symlink path')
  if current!=p or directory:
   if not stat.S_ISDIR(info.st_mode):raise ValueError('not a directory')
  elif not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ValueError('unsafe file')
 return p

def read_bytes(path,limit=MAX):
 p=safe(path);fd=os.open(p,os.O_RDONLY|os.O_NOFOLLOW)
 try:
  info=os.fstat(fd)
  if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1 or info.st_size>limit:raise ValueError('unsafe/oversize file')
  chunks=[];size=0
  while True:
   chunk=os.read(fd,min(8192,limit+1-size))
   if not chunk:break
   chunks.append(chunk);size+=len(chunk)
   if size>limit:raise ValueError('oversize file')
  return b''.join(chunks)
 finally:os.close(fd)

def anchored(root):
 try:return safe(root,directory=True).is_dir() and all(safe(root/a).is_file() for a in ANCHORS) and safe(root/'_Temp',directory=True).is_dir()
 except (OSError,ValueError):return False

def neighbour(left,right):
 left=safe(left,directory=True);right=safe(right,directory=True)
 if left==right or not anchored(left) or not anchored(right):raise ValueError('unrecognized boundary')
 child,parent=(right,left) if left in right.parents else (left,right)
 nearest=next((p for p in child.parents if anchored(p)),None)
 if nearest!=parent:raise ValueError('not a direct boundary')
 return left,right

def write_new(path,raw):
 if len(raw)>LEGACY_MAX:raise ValueError('oversize retained data')
 p=safe(path,missing=True);safe(p.parent,directory=True)
 fd=os.open(p,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  with os.fdopen(fd,'wb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 except Exception:
  # A partial created file stays held for explicit recovery, never silently overwritten.
  raise
 if read_bytes(p,LEGACY_MAX)!=raw:raise ValueError('write readback')

@contextlib.contextmanager
def submissions_lock(store):
 store.require_placement();path=store.path('_Axis/submissions.lock',missing=True,kind='directory');path.mkdir()
 token=secrets.token_hex(16);owner=json.dumps({'session':store.session,'nonce':token}).encode();write_new(path/'OWNER',owner)
 try:
  started=time.monotonic();store.require_placement();yield;store.require_placement()
  if time.monotonic()-started>10:raise ValueError('submissions lock exceeded ten seconds; inspect persisted outcome')
 finally:
  if read_bytes(path/'OWNER')==owner:(path/'OWNER').unlink();path.rmdir()

def _key(envelope):
 if envelope.get('schema')==SCHEMA:
  return hashlib.sha256((envelope['origin_project']+':'+envelope['origin_message']).encode()).hexdigest()
 if envelope.get('schema')=='axis.external-submission/v1':
  return hashlib.sha256((envelope['destination']+':'+envelope['origin_log']).encode()).hexdigest()
 raise ValueError('unknown submission schema')

def _subject(envelope):
 content=envelope.get('record',{}).get('subject') or envelope.get('body','').split('\n')[0] or 'Information for Main'
 return ('Submission: '+content)[:80].strip()

def encode(envelope):
 raw=core._FORMAT.render(_subject(envelope),envelope).encode('utf-8')
 if len(raw)>MAX:raise ValueError('oversize submission; reference a scoped artifact')
 return raw

def decode(raw):
 subject,envelope=core._FORMAT.decode(raw.decode('utf-8'),MAX)
 required={'schema','submission','origin_project','origin_message','destination','digest','expires','route','record'} if envelope.get('schema')==SCHEMA else {'schema','submission','destination','origin_session','origin_log','log_digest','body','expires'} if envelope.get('schema')=='axis.external-submission/v1' else set()
 if not required or set(envelope)!=required:raise ValueError('incompatible submission schema')
 if envelope['schema']==SCHEMA:
  if not isinstance(envelope['record'],dict) or not isinstance(envelope['record'].get('subject'),str):raise ValueError('invalid source record')
  core._envelope(envelope['record']);core.identity(envelope['origin_message'])
  if not isinstance(envelope['origin_project'],str) or not isinstance(envelope['route'],list) or not all(isinstance(v,str) for v in envelope['route']):raise ValueError('invalid source identity')
  if not isinstance(envelope['digest'],str) or not re.fullmatch(r'[0-9a-f]{64}',envelope['digest']):raise ValueError('invalid source digest')
 else:
  core.identity(envelope['origin_session']);core.identity(envelope['origin_log'])
  if not isinstance(envelope['body'],str) or not isinstance(envelope['log_digest'],str) or not re.fullmatch(r'[0-9a-f]{64}',envelope['log_digest']):raise ValueError('invalid proposal data')
 if not isinstance(envelope['destination'],str):raise ValueError('invalid destination')
 core.timestamp(envelope['expires'])
 if subject!=_subject(envelope):raise ValueError('submission Subject mismatch')
 core.identity(envelope.get('submission'))
 return envelope

def _deliver(store,directory,envelope,initial):
 # Sender identities are handles in this queue, outside receiver record IDs.
 # Check just the queue and its retained copy; never claim receiver timestamps.
 ident=initial
 for _ in range(1000):
  name=ident+'.md';path=directory/name;retained=directory/'_received'/name
  candidate=dict(envelope,submission=ident)
  found=None
  for existing in (path,retained):
   if existing.exists() or existing.is_symlink():
    raw_existing=read_bytes(existing,LEGACY_MAX)
    if raw_existing.startswith(b'Request: '):found=False;break
    old=decode(raw_existing)
    if _key(old)==_key(candidate):
     if old!=candidate:raise ValueError('changed submission for existing origin')
     found=existing
    else:found=False;break
  if found is False:ident=core._START.advance(ident);continue
  if found is not None:return {'status':'already-delivered','submission':name,'envelope':name}
  store.guard()
  if store.io.lease[2]:store.require_placement()
  write_new(path,encode(candidate))
  return {'status':'queued','submission':name,'envelope':name}
 raise ValueError('submission timestamp collisions')

def export_message(store,destination,message,expires=None):
 store.require_placement();left,right=neighbour(store.root,Path(destination))
 target=core.Store(right);destination_id=target.project_id()
 if destination_id==store.project_id():raise ValueError('copied project identity')
 incoming=safe(right/'_Axis/Submissions',directory=True)
 record=store.read('Messages',message);expiry=expires or record['expires']
 if core.timestamp(expiry)<=store.now():raise ValueError('expired submission')
 if core.timestamp(expiry)>core.timestamp(record['expires']):raise ValueError('submission cannot extend source expiry')
 envelope={'schema':SCHEMA,'origin_project':store.project_id(),'origin_message':message,'destination':destination_id,'digest':core.digest(record),'expires':expiry,'route':[store.project_id(),destination_id],'record':record}
 store.require_placement()
 return _deliver(store,incoming,envelope,message)

def validate(envelope,destination,now):
 if not isinstance(envelope,dict) or set(envelope)!={'schema','submission','origin_project','origin_message','destination','digest','expires','route','record'} or envelope['schema']!=SCHEMA:raise ValueError('incompatible submission schema; upgrade required')
 core.identity(envelope['submission'])
 if envelope['destination']!=destination:raise ValueError('destination mismatch')
 record=envelope['record'];core._envelope(record)
 if record['family']!='Messages' or record['id']!=envelope['origin_message'] or record['project']!=envelope['origin_project'] or core.digest(record)!=envelope['digest']:raise ValueError('origin integrity mismatch')
 if envelope['route']!=[envelope['origin_project'],destination] or len(set(envelope['route']))!=2:raise ValueError('cycle or hop limit')
 if core.timestamp(envelope['expires'])<=now or core.timestamp(record['expires'])<=now:raise ValueError('expired submission')
 if core.timestamp(envelope['expires'])>core.timestamp(record['expires']):raise ValueError('submission extends source expiry')
 return record

def submit_proposal(store,log_id,body,expires=None):
 store.guard();marker=store.io.read(store.io.marker_name)
 if not marker.startswith('External: '):raise ValueError('external-only proposal route')
 core.identity(log_id)
 if not isinstance(body,str) or len(body.encode())>core.MAX_BODY:raise ValueError('proposal size')
 raw_log=read_bytes(store.path('_Axis/Logs/'+log_id+'.md'))
 expiry=expires or core.stamp(core.timestamp(log_id)+dt.timedelta(hours=24))
 if core.timestamp(expiry)<=store.now():raise ValueError('expired proposal')
 envelope={'schema':'axis.external-submission/v1','destination':store.project_id(),'origin_session':store.session,'origin_log':log_id,'log_digest':core.digest(raw_log),'body':body,'expires':expiry}
 return _deliver(store,store.path('_Axis/Submissions',kind='directory'),envelope,log_id)

def import_proposal(store,name,envelope):
 required={'schema','submission','destination','origin_session','origin_log','log_digest','body','expires'}
 if set(envelope)!=required or envelope['destination']!=store.project_id():raise ValueError('invalid proposal')
 core.identity(envelope['origin_session']);core.identity(envelope['origin_log'])
 if not isinstance(envelope['body'],str) or len(envelope['body'].encode())>core.MAX_BODY:raise ValueError('proposal size')
 if core.timestamp(envelope['expires'])<=store.now():raise ValueError('expired proposal')
 raw=read_bytes(store.path('_Axis/Logs/'+envelope['origin_log']+'.md'))
 if core.digest(raw)!=envelope['log_digest']:raise ValueError('proposal source changed')
 key=_key(envelope);digest=core.digest(envelope)
 previous=[r for r in store.records('Messages') if r.get('data',{}).get('proposal',{}).get('key')==key]
 if previous:
  if len(previous)!=1 or previous[0]['data']['proposal']['digest']!=digest:raise ValueError('proposal import conflict')
  return {'status':'already-imported','id':previous[0]['id'],'submission':name,'envelope':name}
 result=store.message('request','main',envelope['body'],correlation='proposal:'+key,expires=envelope['expires'],data={'proposal':{'key':key,'digest':digest,'submission':name,'origin_session':envelope['origin_session'],'origin_log':envelope['origin_log'],'expires':envelope['expires']}})
 return {'status':'imported','id':result['id'],'submission':name,'envelope':name}

def finish_import(store,name,raw,result):
 # Import is recording, not approval to execute or validation of a Result.
 store.require_main();store.require_placement();record=store.read('Messages',result['id'])
 if not core.accepted(record):raise ValueError('unaccepted import')
 source=store.path('_Axis/Submissions/'+name,missing=True)
 received=store.path('_Axis/Submissions/_received',missing=True,kind='directory')
 received.mkdir(exist_ok=True);safe(received,directory=True);target=received/name
 if target.exists():
  if read_bytes(target,LEGACY_MAX)!=raw:raise ValueError('retained submission collision')
 else:write_new(target,raw)
 if read_bytes(target,LEGACY_MAX)!=raw:raise ValueError('retained submission readback')
 if source.exists():
  if read_bytes(source,LEGACY_MAX)!=raw:raise ValueError('submission changed before retention')
  store.require_placement();source.unlink()
 return result

def _legacy():
 spec=importlib.util.spec_from_file_location('axis_submission_legacy',Path(__file__).with_name('coordination-migrate.py'))
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def import_message(store,name):
 store.require_main();store.require_history()
 if not re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md',name):raise ValueError('invalid submission name')
 core.identity(name[:-3])
 with submissions_lock(store):
  queue=store.path('_Axis/Submissions',kind='directory')
  if (queue/'_migration.md').exists() and not (queue/'_migration-complete.md').exists():raise ValueError('complete queue migration before processing submissions')
  path=store.path('_Axis/Submissions/'+name,missing=True)
  if not path.exists():path=store.path('_Axis/Submissions/_received/'+name)
  raw=read_bytes(path,LEGACY_MAX)
  rejected=[r for r in store.records('Messages') if r.get('data',{}).get('submission_disposition',{}).get('submission')==name]
  if rejected:
   if len(rejected)!=1 or rejected[0]['data']['submission_disposition']['digest']!=core.digest(raw):raise ValueError('changed rejected submission')
   return finish_import(store,name,raw,{'status':'already-declined','id':rejected[0]['id'],'submission':name})
  if raw.startswith(b'Request: '):
   result=_legacy().import_legacy(store,name,raw)
   return finish_import(store,name,raw,result)
  envelope=decode(raw)
  if name!=envelope['submission']+'.md':raise ValueError('submission name mismatch')
  if envelope.get('schema')=='axis.external-submission/v1':
   key=_key(envelope)
   prior=[r for r in store.records('Messages') if r.get('data',{}).get('proposal',{}).get('key')==key]
   if prior:
    if len(prior)!=1 or prior[0]['data']['proposal']['digest']!=core.digest(envelope):raise ValueError('changed proposal import')
    return finish_import(store,name,raw,{'status':'already-imported','id':prior[0]['id'],'submission':name,'envelope':name})
   return finish_import(store,name,raw,import_proposal(store,name,envelope))
  # Replays of already recorded, now expired submissions do not become new work.
  key=_key(envelope)
  prior=[r for r in store.records('Messages') if r.get('data',{}).get('transport',{}).get('key')==key]
  if prior:
   if len(prior)!=1 or prior[0]['data']['transport']['submission_digest']!=core.digest(envelope):raise ValueError('changed origin or duplicate import')
   return finish_import(store,name,raw,{'status':'already-imported','id':prior[0]['id'],'submission':name,'envelope':name})
  source=validate(envelope,store.project_id(),store.now())
  result=store.message(source['kind'],'main',source['body'],correlation='transport:'+key,expires=envelope['expires'],data={'transport':{'key':key,'digest':envelope['digest'],'submission_digest':core.digest(envelope),'origin_project':envelope['origin_project'],'origin_message':envelope['origin_message'],'submission':name,'envelope':name,'expires':envelope['expires'],'source_kind':source['kind'],'recorded_only':True,'retained':'_Axis/Submissions/_received/'+name,'source_attachments':source.get('attachments',[]),'source_data':source.get('data',{})}})
  return finish_import(store,name,raw,{'status':'imported','id':result['id'],'submission':name,'envelope':name})

def decline(store,name,reason):
 store.require_main();store.require_placement();store.require_history()
 if not re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md',name):raise ValueError('invalid submission name')
 core.identity(name[:-3])
 if not isinstance(reason,str) or not reason.strip() or len(reason.encode())>core.MAX_BODY:raise ValueError('decline reason required')
 with submissions_lock(store):
  queue=store.path('_Axis/Submissions',kind='directory')
  if (queue/'_migration.md').exists() and not (queue/'_migration-complete.md').exists():raise ValueError('complete queue migration before processing submissions')
  path=store.path('_Axis/Submissions/'+name,missing=True)
  if not path.exists():path=store.path('_Axis/Submissions/_received/'+name)
  raw=read_bytes(path,LEGACY_MAX);sha=core.digest(raw)
  messages=store.records('Messages')
  prior=[m for m in messages if m.get('data',{}).get('submission_disposition',{}).get('submission')==name]
  if prior:
   if len(prior)!=1 or prior[0]['data']['submission_disposition']['digest']!=sha:raise ValueError('changed submission disposition')
   return finish_import(store,name,raw,{'status':'already-declined','id':prior[0]['id'],'submission':name})
  if any(m.get('data',{}).get('transport',{}).get('submission')==name or m.get('data',{}).get('proposal',{}).get('submission')==name or m.get('data',{}).get('legacy',{}).get('origin')=='_Axis/Requests/'+name for m in messages):raise ValueError('submission already recorded; use Message disposition')
  record=store.message('decision','main',reason,correlation='submission:'+name,data={'submission_disposition':{'submission':name,'digest':sha,'size':len(raw),'outcome':'declined','retained':'_Axis/Submissions/_received/'+name}})
  return finish_import(store,name,raw,{'status':'declined','id':record['id'],'submission':name})

def main(argv=None):
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',default='.');parser.add_argument('--session',required=True);sub=parser.add_subparsers(dest='action',required=True)
 e=sub.add_parser('export');e.add_argument('--destination',required=True);e.add_argument('--message',required=True);e.add_argument('--expires')
 i=sub.add_parser('import');i.add_argument('submission')
 d=sub.add_parser('decline');d.add_argument('submission');d.add_argument('--reason',required=True)
 p=sub.add_parser('submit');p.add_argument('--log',required=True);p.add_argument('--body',required=True);p.add_argument('--expires')
 args=parser.parse_args(argv)
 try:
  store=core.Store(args.root,args.session)
  if args.action=='export':result=export_message(store,args.destination,args.message,args.expires)
  elif args.action=='submit':result=submit_proposal(store,args.log,args.body,args.expires)
  elif args.action=='decline':result=decline(store,args.submission,args.reason)
  else:result=import_message(store,args.submission)
  print(json.dumps(result));return 0
 except (ValueError,OSError,core.CoordinationError) as exc:print(json.dumps({'status':'held','reason':str(exc)}));return 2
if __name__=='__main__':sys.exit(main())
