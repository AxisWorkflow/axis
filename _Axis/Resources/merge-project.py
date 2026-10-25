#!/usr/bin/env python3
"""Bounded project merge support. Preview is read-only; approval and semantic reconciliation belong to Main.

Source files are never removed. Retirement is an explicit final marker after verification.
No network, credentials, subprocess payloads, automatic scheduling or imported-code execution.
"""
import argparse,base64,datetime as dt,hashlib,importlib.util,json,os,re,secrets,stat,subprocess,sys,time,unicodedata
from pathlib import Path
LIMIT_FILES=50000;LIMIT_BYTES=512*1024*1024;FILE_LIMIT=32*1024*1024
ID=re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z')
CONTROL={'Agents','Flags','Secrets','Tracking'}
EXCLUDE={'_Temp','_Trash','.git','.claude','.codex','.gemini','.cursor','.vscode'}
MUTABLE={'PROJECT.md','PLAN.md','TASKS.md','NOTES.md','IDEAS.md','FOLLOWUPS.md','REMINDERS.md','SUPERVISION.md','ENVIRONMENT.md','INITIATIVES.md'}
FAMILIES={'Tasks','Notes','Ideas','Followups','Reminders'}
class Held(Exception):pass
def need(value,why):
 if not value:raise Held(why)
def encode(value):return (json.dumps(value,sort_keys=True,separators=(',',':'))+'\n').encode()
def digest(data):return hashlib.sha256(data).hexdigest()
def plain(path,kind='file',missing=False,spelling=False):
 path=Path(os.path.abspath(path));current=Path(path.anchor)
 for part in path.parts[1:]:
  parent=current;current/=part
  if spelling and parent.is_dir():need(not any(n.name.casefold()==part.casefold() and n.name!=part for n in parent.iterdir()),'case alias path')
  try:info=current.lstat()
  except FileNotFoundError:
   need(missing,'missing path');return path
  need(not stat.S_ISLNK(info.st_mode),'linked path')
  if current!=path:need(stat.S_ISDIR(info.st_mode),'non-directory ancestor')
  else:need(stat.S_ISDIR(info.st_mode) if kind=='dir' else stat.S_ISREG(info.st_mode) and info.st_nlink==1,'unsafe path type')
 return path
def read(path,limit=FILE_LIMIT):
 plain(path)
 with Path(path).open('rb') as f:data=f.read(limit+1)
 need(len(data)<=limit,'file size limit');return data
def relative(name):
 need(isinstance(name,str) and name and '\\' not in name and not name.startswith('/'),'invalid relative path')
 parts=name.split('/');need(all(x not in ('','.','..') and x==unicodedata.normalize('NFC',x) and not x.endswith((' ','.')) and not any(ord(c)<32 or c in '<>:"|?*' for c in x) for x in parts),'unsafe path spelling')
 need(all(not re.fullmatch(r'(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?',x,re.I) for x in parts),'reserved path');return name
def protected(name,suffixes):return name.endswith(suffixes) or Path(name).stem.endswith(suffixes)
def project(root):
 need(not any(protected(p,('_U','_X')) for p in Path(os.path.abspath(root)).parts),'protected project root')
 root=plain(root,'dir',spelling=True);raw=read(root/'_Axis/PROJECT.md').decode('utf-8');ids=re.findall(r'^project-id: (\S+)\s*$',raw,re.M);need(len(ids)==1,'missing or ambiguous project identity')
 ver=re.findall(r'^current-version: (\d+)\.(\d+)\s*$',read(root/'_Axis/CHANGELOG.md').decode('utf-8'),re.M);need(len(ver)==1,'missing release identity');return root,ids[0],tuple(map(int,ver[0]))
def markers(root,own=None):
 folder=plain(root/'_Axis/Agents','dir');return [p.name for p in folder.iterdir() if p.suffix=='.md' and p.name!=str(own)+'.md']
def inventory(root,exclude_child=None):
 files={};nested=[];count=0;total=0;folded=set();config_omissions=0;protected_count=[0]
 def walk(folder):
  nonlocal count,total,config_omissions
  for p in sorted(folder.iterdir(),key=lambda x:x.name):
   rel=p.relative_to(root).as_posix();parts=rel.split('/')
   if protected(p.name,('_X',)):protected_count[0]+=1;continue
   if p.name=='.env' or p.name.startswith('.env.') or p.name in ('.netrc','.npmrc','.pypirc') or (p.name.startswith('credentials') and p.name.endswith('.json')):
    config_omissions+=1;continue
   if p.name.startswith('.') and p.name not in ('.gitkeep','.gitignore','.gitattributes','.gitmodules','.editorconfig'):
    config_omissions+=1;continue
   need(not p.name.endswith('.lock'),'lock residue requires quiescent recovery before merging')
   if parts[0] in EXCLUDE or parts[:2] in [['_Axis',x] for x in CONTROL] or rel=='_Axis/Merges/retired.json':continue
   if exclude_child is not None and (p==exclude_child or exclude_child in p.parents):continue
   count+=1;need(count<=LIMIT_FILES,'inventory file limit')
   relative(rel);key=unicodedata.normalize('NFC',rel).casefold();need(key not in folded,'case/NFC collision');folded.add(key)
   info=p.lstat();need(not stat.S_ISLNK(info.st_mode),'linked inventory path')
   if stat.S_ISDIR(info.st_mode):
    if p!=root and (p/'_Axis/PROJECT.md').is_file():nested.append(rel);continue
    walk(p)
   else:
    plain(p);data=read(p);total+=len(data);need(total<=LIMIT_BYTES,'inventory byte limit');files[rel]={'sha256':digest(data),'bytes':len(data),'mode':stat.S_IMODE(info.st_mode)}
 walk(root)
 return {'files':files,'nested_projects':nested,'protected_config_omissions':config_omissions,'excluded_content_present':bool(protected_count[0]),'bytes':total,'digest':digest(encode(files))}
def preview(dest,source,own=None):
 d,did,dver=project(dest);s,sid,sver=project(d/source);need(d!=s and s not in d.parents,'destination cannot equal source or be inside it');need(did!=sid,'same project identity: replica reconciliation is not a merge')
 src=inventory(s);dst=inventory(d,exclude_child=s if d in s.parents else None)
 conflicts=[n for n,v in src['files'].items() if n in dst['files'] and dst['files'][n]['sha256']!=v['sha256']]
 blockers=[]
 if dver!=sver or dver<(3,4):blockers.append('align both projects on the same merge-capable release first')
 if markers(s):blockers.append('source has session markers; quiesce through its owner, never infer death from age')
 if own and markers(d,own):blockers.append('destination has other session markers')
 if src['nested_projects']:blockers.append('source has nested projects; explicitly relocate or merge them first')
 for root,label in ((s,'source'),(d,'destination')):
  updates=root/'_Axis/Updates'
  if updates.exists():
   plain(updates,'dir')
   if any(p.is_dir() and (p/'start.json').exists() and not (p/'consumed.json').exists() for p in updates.iterdir()):blockers.append(label+' has unconsumed update history')
  if os.path.lexists(root/'_Axis/Flags/merge-pending'):blockers.append(label+' has pending merge')
  if os.path.lexists(root/'_Axis/Merges/retired.json'):blockers.append(label+' is retired')
 return {'schema':1,'source':os.path.relpath(s,d),'destination':'.','source_id':sid,'destination_id':did,'source_version':'.'.join(map(str,sver)),'destination_version':'.'.join(map(str,dver)),'mode':'absorb-child' if d in s.parents else 'combine','source_inventory':src,'destination_inventory':dst,'conflicting_paths':conflicts,'blockers':blockers,'limitations':['Credentials, host bindings, session state and Git metadata are excluded; preserve their source originals.','External Archive completeness and stopped external jobs require Main verification.','Conflict choices and imported instruction meaning are not automated.']}
def load_state(root,session):
 spec=importlib.util.spec_from_file_location('merge_axis_state',root/'_Axis/Resources/startup-state.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);engine=module.Session(root,session);engine.guard();need(engine.lease[2],'Main only');return module,engine
def once(path,data):
 plain(path,missing=True);fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
 try:
  with os.fdopen(fd,'wb',closefd=False) as stream:stream.write(data);stream.flush();os.fsync(fd)
 finally:os.close(fd)
 need(read(path,max(FILE_LIMIT,len(data)))==data,'write readback failed')
def mkdirs(root,path):
 relative(path);current=root
 for part in path.split('/'):
  current/=part
  if not os.path.lexists(current):current.mkdir()
  plain(current,'dir',spelling=True)
def allowed(name):
 relative(name);parts=name.split('/');need(not any(protected(x,('_U','_X')) for x in parts),'protected destination');need(all(not x.startswith('.') and x not in EXCLUDE for x in parts),'host or hidden path excluded');need(not any(x.casefold() in ('agents.md','claude.md','gemini.md') for x in parts),'entry files are protected')
 if parts[0]=='_Axis':
  need((len(parts)==2 and parts[1] in MUTABLE) or (len(parts)==3 and parts[1] in FAMILIES and ID.fullmatch(Path(parts[2]).stem) and parts[2].endswith('.md')),'protected Axis path')
 elif parts[0].startswith('_'):need(parts[0] in ('_Memos','_Wiki','_Inbox'),'unsupported project root')
 need([x.casefold() for x in parts[:2]]!=['_wiki','_inbox'],'raw Wiki inputs are immutable')
 need(not any(p in ('.git','_Axis') for p in parts[1:]),'nested control tree excluded');need(parts[0] not in ('AGENTS.md','CLAUDE.md','GEMINI.md'),'entry files are protected')
def target_hash(root,name):
 allowed(name)
 for ancestor in (root/name).parents:
  if ancestor==root:break
  need(not any(os.path.lexists(ancestor/x) for x in ('_Axis/PROJECT.md','AGENTS.md','CLAUDE.md','GEMINI.md')),'destination crosses a nested project')
 p=plain(root/name,missing=True,spelling=True)
 return digest(read(p)) if p.exists() else None
def current_inventory(root,source):return inventory(root,exclude_child=source if root in source.parents else None)
def archive_boundary(root,name,module,engine):
 local,external=module.archive_root(engine);need(local is not None or external is not None,'configured Archive unavailable')
 folder=plain(root/local if local is not None else external,'dir',missing=True);target=root/name
 need(target!=folder and folder not in target.parents,'configured Archive is retained history')
def merge_guard(root,engine,tx):
 engine.guard();start=json.loads(read(tx/'start.json',4*1024*1024));source=plain(root/start['preview']['source'],'dir')
 need(start['transaction']==tx.name and not markers(root,engine.sid) and not markers(source),'merge quiescence lost')
 check_barriers(root,source,tx.name,start)
def checkpoint_file(root,checkpoint,name,expected,mode):
 need(checkpoint is not None and re.fullmatch('[0-9a-f]{40}',checkpoint),'exact local checkpoint required')
 base=['git','-C',str(root)]
 result=subprocess.run(base+['cat-file','-t',checkpoint],capture_output=True);need(result.returncode==0 and result.stdout==b'commit\n','checkpoint must name a commit')
 need(subprocess.run(base+['merge-base','--is-ancestor',checkpoint,'HEAD'],capture_output=True).returncode==0,'checkpoint must be retained in current history')
 result=subprocess.run(base+['ls-tree','-z',checkpoint,'--',name],capture_output=True);prefix=('100755' if mode & 0o111 else '100644')+' blob '
 need(result.returncode==0 and result.stdout.count(b'\0')==1 and result.stdout.startswith(prefix.encode()) and result.stdout.split(b'\t',1)[-1]==name.encode()+b'\0','checkpoint file mode/type differs')
 result=subprocess.run(base+['show',checkpoint+':'+name],capture_output=True);need(result.returncode==0 and digest(result.stdout)==expected,'checkpoint does not contain merged bytes')
def prepare(root,session,plan_path,approval):
 module,engine=load_state(root,session);data=read(plan_path,2*1024*1024);plan=json.loads(data);need(set(plan)=={'schema','preview','operations','engine_sha256','external_archive_verified','external_jobs_stopped','source_authority','destination_authority'},'plan schema');need(plan['schema']==1,'plan version');need(plan['engine_sha256']==digest(Path(__file__).read_bytes()),'plan engine identity');need(Path(os.path.abspath(plan_path)).is_relative_to(root/'_Temp'),'prepare the plan under destination _Temp')
 for field in ('external_archive_verified','external_jobs_stopped','source_authority','destination_authority'):need(plan[field] is True,'Main must establish '+field)
 expected=plan['preview'];fresh=preview(root,expected['source'],session);need(not fresh['blockers'],'merge preview has blockers');need(ID.fullmatch(approval),'approval Log identity')
 # Approval is written after preview; exclude exactly that one new destination Log from the comparison.
 approval_path='_Axis/Logs/'+approval+'.md';need(approval_path not in expected['destination_inventory']['files'],'approval must be a new scoped Log')
 fresh['destination_inventory']['files'].pop(approval_path,None);fresh['destination_inventory']['bytes']=sum(v['bytes'] for v in fresh['destination_inventory']['files'].values());fresh['destination_inventory']['digest']=digest(encode(fresh['destination_inventory']['files']))
 need(fresh==expected,'source or destination changed since preview')
 auth=read(root/'_Axis/Logs'/(approval+'.md')).decode('utf-8');ph=digest(encode(plan));need('\nmerge-plan-sha256: '+ph+'\n' in auth,'approval Log must bind the exact canonical plan digest')
 need('\nmerge-source-id: '+fresh['source_id']+'\n' in auth and '\nmerge-destination-id: '+fresh['destination_id']+'\n' in auth,'approval project identity binding')
 operations=plan['operations'];need(isinstance(operations,list) and 0<len(operations)<=1000,'operation count');seen=set();prepared=[];objects={};base=plain(Path(plan_path).parent,'dir')
 for op in operations:
  need(isinstance(op,dict) and set(op)=={'path','before','after','mode','payload'},'operation schema');name=op['path'];allowed(name);archive_boundary(root,name,module,engine);fold=unicodedata.normalize('NFC',name).casefold();need(fold not in seen,'duplicate destination');seen.add(fold);need(not any(n.casefold()==fold and n!=name for n in fresh['destination_inventory']['files']),'destination case collision');need(type(op['mode']) is int and op['mode'] in (0o600,0o644,0o755),'unsupported output mode')
  target=root/name;source=plain(root/fresh['source'],'dir');need(target!=source and source not in target.parents,'cannot mutate the source tree')
  before=target_hash(root,name);need(before==op['before'],'destination changed');relative(op['payload']);need(op['payload'].startswith('payloads/'),'payload must be in prepared payloads');payload=base/op['payload'];after=read(payload);need(digest(after)==op['after'],'approved payload changed')
  need(before!=digest(after),'no-op operation');parts=name.split('/')
  if name=='_Axis/PROJECT.md':need(re.findall(r'^project-id: (\S+)\s*$',after.decode('utf-8'),re.M)==[fresh['destination_id']],'destination project identity must survive')
  if parts[0]=='_Memos':need(before is None and len(parts)==2 and re.fullmatch(ID.pattern+r' - .+\.md',parts[1]),'import Memo with a fresh timestamp; never overwrite or rewrite archived Memos')
  if parts[0]=='_Axis' and len(parts)==3:need(before is None,'import records with fresh IDs, never overwrite destination records')
  if before:objects[before]=read(target)
  objects[digest(after)]=after;prepared.append({'path':name,'before':before,'after':digest(after),'mode':op['mode'],'before_mode':stat.S_IMODE(target.stat().st_mode) if before else None})
 need(sum(map(len,objects.values()))<=LIMIT_BYTES,'payload byte limit')
 tx=root/'_Axis/Merges'/approval;need(not os.path.lexists(tx),'transaction exists');engine.guard();mkdirs(root,'_Axis/Merges/'+approval+'/objects')
 # Preserve every eligible source byte before any material destination edit. Blobs are not canonical records.
 for name,item in fresh['source_inventory']['files'].items():
  engine.guard();raw=read(root/fresh['source']/name);need(digest(raw)==item['sha256'],'source changed during preservation');objects[item['sha256']]=raw
 for sha,raw in objects.items():engine.guard();once(tx/'objects'/sha,raw)
 start={'schema':1,'transaction':approval,'plan_sha256':ph,'approval_log':approval,'preview':fresh,'operations':prepared,'engine_sha256':digest(Path(__file__).read_bytes()),'session':session}
 engine.guard();once(tx/'start.json',encode(start));once(tx/'engine.py',Path(__file__).read_bytes());once(tx/'plan.json',encode(plan))
 need(inventory(plain(root/fresh['source'],'dir'))==fresh['source_inventory'],'source changed after preservation')
 flag=encode({'schema':1,'transaction':approval,'plan_sha256':ph,'destination_id':fresh['destination_id'],'source_id':fresh['source_id']})
 engine.guard();once(root/'_Axis/Flags/merge-pending',flag)
 # The source flag is an explicit approved maintenance/retirement boundary, not a borrowed Main lease.
 once(root/fresh['source']/'_Axis/Flags/merge-pending',flag)
 need(not markers(root/fresh['source']) and inventory(root/fresh['source'])==fresh['source_inventory'],'source changed while installing barriers; preserve and reconcile')
 return {'status':'prepared','transaction':approval,'plan_sha256':ph}
def transaction(root,session,txid):
 module,engine=load_state(root,session);need(ID.fullmatch(txid),'transaction identity');tx=plain(root/'_Axis/Merges'/txid,'dir');start=json.loads(read(tx/'start.json',4*1024*1024));need(start['schema']==1 and start['transaction']==txid,'transaction binding')
 plan_bytes=read(tx/'plan.json',2*1024*1024);need(digest(plan_bytes)==start['plan_sha256'],'plan changed');plan=json.loads(plan_bytes)
 need(start['preview']==plan['preview'] and start['operations']==[{**{k:op[k] for k in ('path','before','after','mode')},'before_mode':plan['preview']['destination_inventory']['files'].get(op['path'],{}).get('mode')} for op in plan['operations']],'transaction differs from approved plan');need(start['engine_sha256']==plan['engine_sha256'],'engine not approved');need(digest(read(tx/'engine.py'))==start['engine_sha256'] and digest(Path(__file__).read_bytes())==start['engine_sha256'],'run the pinned merge engine')
 auth=read(root/'_Axis/Logs'/(txid+'.md')).decode();need('\nmerge-plan-sha256: '+start['plan_sha256']+'\n' in auth,'approval binding changed')
 _,did,_=project(root);source,sid,_=project(root/start['preview']['source']);need(did==start['preview']['destination_id'] and sid==start['preview']['source_id'],'project identity changed')
 need(not markers(root,session) and not markers(source),'quiescence lost')
 need(inventory(source)==start['preview']['source_inventory'],'source changed')
 for op in start['operations']:
  allowed(op['path']);archive_boundary(root,op['path'],module,engine);need(digest(read(tx/'objects'/op['after']))==op['after'],'payload changed')
  if op['before']:need(digest(read(tx/'objects'/op['before']))==op['before'],'preimage changed')
 return module,engine,tx,start,source

def replace(root,engine,tx,op,reverse=False):
 guard=lambda:merge_guard(root,engine,tx)
 name=op['path'];claim=None;expected=op['after'] if reverse else op['before'];wanted=op['before'] if reverse else op['after'];actual=target_hash(root,name)
 if actual==wanted:
  if actual is not None:need(stat.S_IMODE((root/name).stat().st_mode)==(op['before_mode'] if reverse else op['mode']),'destination mode diverged')
  return
 need(actual==expected,'destination diverged: '+name)
 if actual is not None:need(stat.S_IMODE((root/name).stat().st_mode)==(op['mode'] if reverse else op['before_mode']),'destination mode changed')
 guard();parent=Path(name).parent.as_posix()
 if parent!='.':mkdirs(root,parent)
 p=root/name;lock=p.with_name(p.name+'.lock');lock.mkdir();token=secrets.token_hex(16);once(lock/'OWNER',token.encode());started=time.monotonic()
 try:
  guard();need(read(lock/'OWNER')==token.encode() and target_hash(root,name)==expected,'write ownership or bytes changed')
  if not reverse and expected is None:
   match=ID.match(Path(name).name) if name.startswith(('_Axis/','_Memos/')) else None
   if match:
    value=match[0];dt.datetime.strptime(value,'%Y.%m.%d.%H.%M.%S.%fZ');relative_claim='_Temp/'+value+'.tsclaim';cp=engine.path(relative_claim,missing=True,kind='directory');cp.mkdir();claim=(relative_claim,token, (cp.stat().st_dev,cp.stat().st_ino),time.monotonic());once(cp/'OWNER',token.encode());need(not engine.collision(value),'import identity is occupied; replan without overwriting')
  if wanted is None:p.unlink()
  else:
   raw=read(tx/'objects'/wanted);need(digest(raw)==wanted,'payload digest');temporary=p.with_name('.'+p.name+'.merge-'+token);once(temporary,raw);os.chmod(temporary,op['before_mode'] if reverse else op['mode'])
   need(time.monotonic()-started<10,'write lock expired');guard();need(target_hash(root,name)==expected,'destination changed before replace')
   if expected is None:os.link(temporary,p,follow_symlinks=False);temporary.unlink()
   else:os.replace(temporary,p)
  need(target_hash(root,name)==wanted,'destination readback failed')
 finally:
  if claim is not None:engine.release_timestamp(*claim)
  if time.monotonic()-started<10 and read(lock/'OWNER')==token.encode():os.unlink(lock/'OWNER');lock.rmdir()

def apply(root,session,txid,reverse=False):
 module,engine,tx,start,source=transaction(root,session,txid)
 need(not (tx/'accepted.json').exists(),'accepted merge cannot be blindly rolled back');need(reverse or not (tx/'aborted.json').exists(),'aborted transaction')
 # Exact flag readback binds both maintenance barriers. A missing flag is not recreated here.
 if not (reverse and (tx/'aborted.json').exists()):check_barriers(root,source,txid,start)
 ops=list(reversed(start['operations'])) if reverse else start['operations']
 for op in ops:replace(root,engine,tx,op,reverse)
 if reverse:
  if not (tx/'aborted.json').exists():merge_guard(root,engine,tx)
  if not (tx/'aborted.json').exists():once(tx/'aborted.json',encode({'schema':1,'transaction':txid,'restored':True}))
  for directory in (source,root):
   flag=directory/'_Axis/Flags/merge-pending'
   if flag.exists():need(json.loads(read(flag))['transaction']==txid,'foreign pending merge');flag.unlink()
 else:
  if not (tx/'applied.json').exists():merge_guard(root,engine,tx);once(tx/'applied.json',encode({'schema':1,'transaction':txid,'applied':len(ops)}))
 return {'status':'aborted' if reverse else 'applied-awaiting-validation','transaction':txid}

def finish(root,session,txid,checkpoint):
 module,engine,tx,start,source=transaction(root,session,txid);check_barriers(root,source,txid,start);need((tx/'applied.json').exists() and not (tx/'aborted.json').exists(),'transaction not applied')
 for op in start['operations']:
  need(target_hash(root,op['path'])==op['after'],'applied content changed');need(stat.S_IMODE((root/op['path']).stat().st_mode)==op['mode'],'applied file mode changed')
 # Live working-tree checks, then exact Git checkpoint proof where this is a repository.
 checker=root/'_Axis/Resources/record-check.py'
 for args in (['names'],['links',*sum((['--scope',x['path']] for x in start['operations'] if x['path'].endswith('.md')),[]) ]):
  result=subprocess.run([sys.executable,'-B',str(checker),'--root',str(root),*args],capture_output=True,text=True,timeout=120);need(result.returncode==0,'record validation held; inspect record-check diagnostics')
 if (root/'.git').exists():
  need(checkpoint is not None and re.fullmatch('[0-9a-f]{40}',checkpoint),'exact local checkpoint required')
  for op in start['operations']:checkpoint_file(root,checkpoint,op['path'],op['after'],op['mode'])
 need(not (tx/'accepted.json').exists(),'already accepted')
 # Acceptance precedes retirement; after this point recovery completes retirement, not blind rollback.
 merge_guard(root,engine,tx);once(tx/'accepted.json',encode({'schema':1,'transaction':txid,'checkpoint':checkpoint,'source_id':start['preview']['source_id'],'destination_id':start['preview']['destination_id']}))
 return retire(root,session,txid)

def retire(root,session,txid,source_checkpoint=None):
 module,engine,tx,start,source=transaction(root,session,txid);need((tx/'accepted.json').exists(),'acceptance required')
 retired=encode({'schema':1,'transaction':txid,'destination_id':start['preview']['destination_id'],'source_id':start['preview']['source_id'],'source_preserved':True})
 engine.guard();mkdirs(source,'_Axis/Merges');p=source/'_Axis/Merges/retired.json'
 if p.exists():need(read(p)==retired,'retirement marker changed')
 else:merge_guard(root,engine,tx);once(p,retired)
 # Retirement is canonical and must travel in a source repository checkpoint, including parent-tracked children.
 repo=subprocess.run(['git','-C',str(source),'rev-parse','--show-toplevel'],capture_output=True,text=True)
 if repo.returncode==0:
  gitroot=Path(repo.stdout.strip()).resolve();need(source.is_relative_to(gitroot),'source repository boundary');relative_retirement=p.relative_to(gitroot).as_posix()
  if source_checkpoint is None:return {'status':'retired-awaiting-source-checkpoint','transaction':txid,'source_preserved':True}
  need(re.fullmatch('[0-9a-f]{40}',source_checkpoint),'exact source checkpoint required')
  try:checkpoint_file(gitroot,source_checkpoint,relative_retirement,digest(retired),0o600)
  except Held as error:raise Held('source checkpoint lacks retirement marker or mode proof: '+str(error)) from None
 for directory in (source,root):
  flag=directory/'_Axis/Flags/merge-pending'
  if flag.exists():need(json.loads(read(flag))['transaction']==txid,'foreign pending merge');engine.guard();flag.unlink()
 if not (tx/'retired.json').exists():engine.guard();once(tx/'retired.json',retired)
 return {'status':'complete','transaction':txid,'source':'retired in place; originals retained, no files deleted'}

def flag_bytes(start):
 return encode({'schema':1,'transaction':start['transaction'],'plan_sha256':start['plan_sha256'],'destination_id':start['preview']['destination_id'],'source_id':start['preview']['source_id']})
def check_barriers(root,source,txid,start):
 wanted=flag_bytes(start)
 for directory in (root,source):need(read(directory/'_Axis/Flags/merge-pending')==wanted,'maintenance barrier changed')
def repair_barriers(root,session,txid):
 module,engine,tx,start,source=transaction(root,session,txid)
 need(not any((tx/n).exists() for n in ('applied.json','accepted.json','aborted.json')),'barrier repair only before application')
 for op in start['operations']:need(target_hash(root,op['path'])==op['before'],'cannot repair barriers after material changes')
 wanted=flag_bytes(start)
 for directory in (root,source):
  flag=directory/'_Axis/Flags/merge-pending'
  if os.path.lexists(flag):need(read(flag)==wanted,'foreign maintenance barrier')
  else:engine.guard();once(flag,wanted)
 return {'status':'prepared','transaction':txid,'barriers':'verified'}

def status(root):
 root=plain(root,'dir');flags=root/'_Axis/Flags';retired=root/'_Axis/Merges/retired.json';pending=flags/'merge-pending';rows=[]
 folder=root/'_Axis/Merges'
 if not os.path.lexists(retired) and not os.path.lexists(pending) and (not os.path.lexists(folder) or (plain(folder,'dir') and not any(p.name!='.gitkeep' for p in folder.iterdir()))):return {'status':'clear','transactions':[]}
 root,pid,version=project(root)
 if os.path.lexists(retired):
  value=json.loads(read(retired));need(value.get('schema')==1 and value.get('source_id')==pid and value.get('source_preserved') is True and ID.fullmatch(value.get('transaction','')),'invalid retirement marker');return {'status':'retired','destination_id':value['destination_id']}
 if os.path.lexists(pending):
  value=json.loads(read(pending));need(value.get('schema')==1 and pid in (value.get('source_id'),value.get('destination_id')) and ID.fullmatch(value.get('transaction','')),'invalid pending merge');rows.append(value['transaction'])
  if pid==value['source_id']:return {'status':'source-held','destination_id':value['destination_id'],'transaction':value['transaction']}
 folder=root/'_Axis/Merges'
 if os.path.lexists(folder):
  plain(folder,'dir');entries=list(folder.iterdir());need(len(entries)<=1000,'merge journal inventory limit')
  for path in entries:
   if path.name in ('.gitkeep','retired.json'):continue
   need(ID.fullmatch(path.name),'unexpected merge journal entry');plain(path,'dir')
   terminal=[]
   for receipt,field in (('retired.json','source_preserved'),('aborted.json','restored')):
    q=path/receipt
    if os.path.lexists(q):
     value=json.loads(read(q,4096));need(value.get('schema')==1 and value.get('transaction')==path.name and value.get(field) is True,'invalid terminal merge receipt');terminal.append(receipt)
   need(len(terminal)<=1,'conflicting terminal merge receipts')
   if not terminal:rows.append(path.name)
 return {'status':'recovery' if rows else 'clear','transactions':sorted(set(rows))}

def main():
 p=argparse.ArgumentParser();p.add_argument('--root',required=True);sub=p.add_subparsers(dest='command',required=True)
 a=sub.add_parser('preview');a.add_argument('--source',required=True);a.add_argument('--session')
 a=sub.add_parser('prepare');a.add_argument('--session',required=True);a.add_argument('--plan',required=True);a.add_argument('--approval-log',required=True)
 for name in ('apply','abort','finish','retire','repair-barriers'):
  a=sub.add_parser(name);a.add_argument('--session',required=True);a.add_argument('--transaction',required=True)
  if name=='finish':a.add_argument('--checkpoint')
  if name=='retire':a.add_argument('--source-checkpoint')
 sub.add_parser('status')
 a=p.parse_args();root=plain(a.root,'dir')
 try:
  if a.command=='status':value=status(root)
  elif a.command=='repair-barriers':value=repair_barriers(root,a.session,a.transaction)
  elif a.command=='preview':value=preview(root,Path(a.source),a.session)
  elif a.command=='prepare':value=prepare(root,a.session,Path(a.plan),a.approval_log)
  elif a.command in ('apply','abort'):value=apply(root,a.session,a.transaction,a.command=='abort')
  elif a.command=='finish':value=finish(root,a.session,a.transaction,a.checkpoint)
  else:value=retire(root,a.session,a.transaction,a.source_checkpoint)
  print(json.dumps(value,sort_keys=True));return 0
 except (Held,OSError,ValueError,KeyError,TypeError,UnicodeError) as error:print(json.dumps({'status':'held','reason':str(error)[:240]}));return 2
if __name__=='__main__':raise SystemExit(main())
