#!/usr/bin/env python3
"""Move the 2.09 Requests queue to Submissions; preserve bytes and completed outcomes.
Run after normal Main startup, after the update transaction is consumed. No model/network calls.
"""
from pathlib import Path
import argparse, importlib.util, json, os, re, sys
sys.dont_write_bytecode=True
sp=importlib.util.spec_from_file_location('submissions',Path(__file__).with_name('coordination-submissions.py'));submissions=importlib.util.module_from_spec(sp);sp.loader.exec_module(submissions);core=submissions.core

def parse_legacy(raw):
 text=raw.decode('utf-8');lines=text.splitlines()
 if len(lines)<6 or not lines[0].startswith('Request: ') or len(lines[0])>80 or lines[1]!='':raise ValueError('malformed legacy request')
 fields={}
 for line in lines[2:]:
  m=re.fullmatch(r'(from|asks|because|expires|resolved|outcome|kind|record|deliver|approved|reply): (.*)',line)
  if m:
   if m[1] in fields:raise ValueError('duplicate legacy field')
   fields[m[1]]=m[2]
 if not all(fields.get(k) for k in ('from','asks','because','expires')):raise ValueError('missing legacy field')
 if fields['expires']!='none':core.timestamp(fields['expires'])
 if 'resolved' in fields:
  match=re.fullmatch(r'(accepted|declined|referred) - (\S+) - (\S+)',fields['resolved'])
  if not match or not fields.get('outcome'):raise ValueError('invalid legacy outcome')
  core.identity(match[2]);core.timestamp(match[3]);fields['resolution']=match[1]
 if fields.get('kind')=='directive':
  if not all(fields.get(k) for k in ('record','deliver','approved','reply')) or fields['reply']!='required' or '\n## Task\n' not in text:raise ValueError('malformed legacy directive')
  fields['directive']={k:fields[k] for k in ('record','deliver','approved','reply')}
  fields['directive']['task']=text.split('\n## Task\n',1)[1].strip()
  if not fields['directive']['task']:raise ValueError('empty legacy directive')
 return text,fields

def _manifest(path):
 subject,value=core._FORMAT.decode(submissions.read_bytes(path,262144).decode('utf-8'),262144)
 return value

def validate_plan(plan,project):
 if set(plan)!={'schema','project','entries'} or plan.get('schema')!='axis.submissions-migration/v1' or plan.get('project')!=project or not isinstance(plan.get('entries'),list):raise ValueError('migration plan schema or project')
 names=set()
 for entry in plan['entries']:
  if not isinstance(entry,dict) or set(entry)!={'name','origin','digest','size'}:raise ValueError('migration entry fields')
  name=entry['name']
  if not isinstance(name,str) or not name.endswith('.md') or name in names or entry['origin']!='_Axis/Requests/'+name:raise ValueError('migration entry identity')
  core.identity(name[:-3]);names.add(name)
  if type(entry['size']) is not int or not 0<entry['size']<=262144 or not isinstance(entry['digest'],str) or not re.fullmatch(r'[0-9a-f]{64}',entry['digest']):raise ValueError('migration entry digest or size')
 return plan

def migrate(store):
 """Move the 2.09 queue into Submissions, preserving bytes and doing no work."""
 store.require_main();store.initialize();store.require_placement()
 source=store.root/'_Axis/Requests';queue=store.path('_Axis/Submissions',kind='directory')
 plan=queue/'_migration.md';complete=queue/'_migration-complete.md'
 with submissions.submissions_lock(store):
  if complete.exists():
   completed=_manifest(complete);planned=validate_plan(_manifest(plan),store.project_id())
   if completed!={'schema':'axis.submissions-migration-complete/v1','plan_digest':core.digest(planned)}:raise ValueError('migration completion mismatch')
   if source.exists():
    submissions.safe(source,directory=True)
    if any(p.name!='.gitkeep' for p in source.iterdir()):raise ValueError('late legacy traffic held for reviewed reconciliation')
   return {'status':'complete','moved':0,'imported':0,'already_migrated':True}
  if plan.exists():
   planned=validate_plan(_manifest(plan),store.project_id())
  else:
   if source.is_symlink():raise ValueError('unsafe legacy queue')
   if not source.exists():return {'status':'not-needed','moved':0,'imported':0}
   submissions.safe(source,directory=True);entries=[]
   for path in sorted(source.iterdir()):
    if path.name=='.gitkeep':
     if submissions.read_bytes(path)!=b'':raise ValueError('unexpected placeholder content')
     continue
    if not core._START.ID.fullmatch(path.stem) or path.suffix!='.md':raise ValueError('unexpected legacy queue entry')
    raw=submissions.read_bytes(path,262144);parse_legacy(raw)
    if (queue/path.name).exists() or (queue/'_received'/path.name).exists():raise ValueError('Submissions destination collision')
    entries.append({'name':path.name,'origin':'_Axis/Requests/'+path.name,'digest':core.digest(raw),'size':len(raw)})
   planned={'schema':'axis.submissions-migration/v1','project':store.project_id(),'entries':entries}
   raw=core._FORMAT.render('Submissions migration from 2.09',planned).encode()
   if len(raw)>262144:raise ValueError('migration plan too large; reviewed batching required')
   submissions.write_new(plan,raw)
  if planned.get('project')!=store.project_id():raise ValueError('migration project mismatch')
  names=set();moved=0
  for entry in planned['entries']:
   if set(entry)!={'name','origin','digest','size'} or not core._START.ID.fullmatch(entry['name'][:-3]) or not entry['name'].endswith('.md') or entry['name'] in names or entry['origin']!='_Axis/Requests/'+entry['name']:raise ValueError('migration entry identity')
   names.add(entry['name']);old=source/entry['name'];new=queue/entry['name']
   raw=submissions.read_bytes(old if old.exists() else new,262144)
   if len(raw)!=entry['size'] or core.digest(raw)!=entry['digest']:raise ValueError('legacy bytes changed; reconciliation required')
   if new.exists():
    if submissions.read_bytes(new,262144)!=raw:raise ValueError('Submissions destination collision')
   else:submissions.write_new(new,raw)
   if submissions.read_bytes(new,262144)!=raw:raise ValueError('migration readback')
   if old.exists():
    if submissions.read_bytes(old,262144)!=raw:raise ValueError('legacy bytes changed')
    store.require_placement();old.unlink();moved+=1
  if source.exists():
   submissions.safe(source,directory=True)
   for item in source.iterdir():
    if item.name!='.gitkeep' or submissions.read_bytes(item)!=b'':raise ValueError('late legacy arrival; migration held')
    item.unlink()
   store.require_placement();source.rmdir()
  receipt={'schema':'axis.submissions-migration-complete/v1','plan_digest':core.digest(planned)}
  submissions.write_new(complete,core._FORMAT.render('Submissions migration complete',receipt).encode())
  return {'status':'complete','moved':moved,'imported':0,'pending':len(names)}

def import_legacy(store,name,raw):
 """Main's normal submission processing, after migration; never execute content."""
 store.require_main();store.require_placement();store.require_history()
 queue=store.path('_Axis/Submissions',kind='directory');plan=_manifest(queue/'_migration.md');complete=_manifest(queue/'_migration-complete.md')
 validate_plan(plan,store.project_id())
 if complete!={'schema':'axis.submissions-migration-complete/v1','plan_digest':core.digest(plan)}:raise ValueError('legacy migration provenance')
 entries=[e for e in plan.get('entries',[]) if e.get('name')==name]
 if len(entries)!=1 or entries[0].get('digest')!=core.digest(raw) or entries[0].get('size')!=len(raw):raise ValueError('unmapped or changed legacy submission')
 text,fields=parse_legacy(raw);origin=entries[0]['origin'];sha=core.digest(raw)
 previous=[r for r in store.records('Messages') if r.get('data',{}).get('legacy',{}).get('origin')==origin]
 if previous:
  if len(previous)!=1 or previous[0]['data']['legacy']['digest']!=sha:raise ValueError('changed legacy origin; reconciliation required')
  return {'status':'already-imported','id':previous[0]['id'],'submission':name,'envelope':name}
 meta={'origin':origin,'digest':sha,'size':len(raw),'resolution':fields.get('resolution'),'outcome':fields.get('outcome'),'expires':fields['expires'],'from':fields['from'],'retained':'_Axis/Submissions/_received/'+name,'directive':fields.get('directive')}
 body=text if len(raw)<=core.MAX_BODY else 'Legacy submission retained as support; inspect the linked original and its digest before disposition.'
 created=store.message('receipt' if fields.get('resolution') else 'request','main',body,correlation='legacy:'+core.digest(origin.encode()),expires=None if fields['expires']=='none' else fields['expires'],data={'legacy':meta})
 return {'status':'imported','id':created['id'],'submission':name,'envelope':name}

def main(argv=None):
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',default='.');p.add_argument('--session',required=True);a=p.parse_args(argv)
 try:print(json.dumps(migrate(core.Store(a.root,a.session))));return 0
 except (ValueError,OSError,core.CoordinationError) as e:print(json.dumps({'status':'held','reason':str(e)}));return 2
if __name__=='__main__':sys.exit(main())
