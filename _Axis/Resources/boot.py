#!/usr/bin/env python3
"""Axis one-command boot: the mechanical Main startup in one call.

Runs from the project root. It composes the installed helpers (update-transaction.py inspect,
startup-state.py claim/initialize/commit and startup-survey.py survey), records the environment
binding on a project's first session, and prints the Ready banner followed by the items the Agent
still owes. It never answers for the Agent and never guesses: anything it cannot finish prints
STOP with the guide to follow (Boot-Manual.md, or Entry-Protocol.md for a pending update)."""
import argparse,datetime,json,os,re,subprocess,sys
from pathlib import Path

a=argparse.ArgumentParser(description='Axis one-command boot')
a.add_argument('--host',required=True);a.add_argument('--model',required=True)
a.add_argument('--harness',default='other');a.add_argument('--interaction',default='interactive')
a.add_argument('--spawn',choices=('yes','no'),default='no');a.add_argument('--parallel',choices=('yes','no'),default='no')
o=a.parse_args();root=Path.cwd().resolve();R=root/'_Axis/Resources'

def stamp():
    n=datetime.datetime.now(datetime.timezone.utc);return n.strftime('%Y.%m.%d.%H.%M.%S.')+'%03dZ'%(n.microsecond//1000)
def run(*args):
    r=subprocess.run([sys.executable,'-B',*map(str,args)],cwd=root,capture_output=True,text=True,timeout=120)
    out=r.stdout.strip().splitlines()
    try:return json.loads(out[-1]) if out else {'status':'error','stderr':r.stderr[-400:]}
    except ValueError:return {'status':'error','stdout':r.stdout[-400:],'stderr':r.stderr[-400:]}
def stop(why,guide='_Axis/Resources/Boot-Manual.md',**k):
    print(json.dumps({'axis_boot':'STOP','reason':why,'guide':guide,**k}));print(f'STOP: {why}. Follow {guide} instead.');sys.exit(2)

def update_state():
    # File-only read of _Axis/Updates/: this boot never executes an update helper that an unconsumed
    # update may have installed (Check-Update-Handoff > Inspect before serving, step 2).
    d=root/'_Axis/Updates'
    if not d.exists():return 'none'
    state='none'
    for e in d.iterdir():
        if e.name in ('.gitkeep','operation.lck') and e.is_file():continue
        if not e.is_dir() or e.is_symlink():return 'unexpected'
        names={x.name for x in e.iterdir()}
        if 'consumed.json' in names or {'rollback.json','released.json'}<=names:continue
        state='ready' if {'ready.json','released.json'}<=names else 'pending'
        if state=='pending':return state
    return state

if not (root/'_Axis/Resources/startup-state.py').is_file():stop('run this from the project root')
us=update_state()
if us=='ready':stop('an Axis update finished and a fresh Main must reconcile and consume it before ordinary startup','_Axis/Resources/Entry-Protocol.md',update=us)
if us!='none':stop('an update handoff needs attention','_Axis/Resources/Entry-Protocol.md',update=us)
c=run(R/'startup-state.py','--root',root,'claim','--initial',stamp(),'--host',o.host)
if c.get('status')=='external':
    print(json.dumps({'axis_boot':'EXTERNAL','claim':c}));print('EXTERNAL: another Main session is live. Follow _Axis/Resources/Start-External.md.');sys.exit(3)
if c.get('status')!='admitted':stop('session claim failed',claim=c)
sid,owner=c['session'],c['owner']
def interrupted(why,**k):
    print(json.dumps({'axis_boot':'STOP','reason':why,'session':sid,'owner':owner,'guide':'_Axis/Resources/Lock-File.md','interrupted_after_claim':True,**k}))
    print(f'STOP: startup interrupted after the claim ({why}). Startup is incomplete: tell the user, leave _Axis/Flags/starting.lock, _Axis/Flags/starting and _Axis/Agents/{sid}.md in place, and do not retry or use Boot-Manual.md. Recovery needs a quiet moment under _Axis/Resources/Lock-File.md > Quiescent Recovery.');sys.exit(2)
try:
 i=run(R/'startup-state.py','--root',root,'initialize','--session',sid,'--owner',owner)
 if i.get('status')!='initialized':interrupted('initialize failed',initialize=i)
 s=run(R/'startup-survey.py','--root',root,'survey','--session',sid,'--owner',owner,'--model',o.model,'--harness',o.harness,'--interaction',o.interaction,'--spawn',o.spawn,'--parallel',o.parallel)
 if s.get('status')!='surveyed':interrupted('startup survey failed',survey=s)

 notices=list(s.get('notices') or []);pending=[];later=[]
 if s.get('manifest_missing'):notices.append('Missing Workflow files: '+', '.join(s['manifest_missing']))
 env=s.get('environment') or {};bind=root/'_Axis/Flags/environment-binding'
 if env.get('state')=='changed' and env.get('fields')=='binding-missing-or-malformed' and not bind.exists() and not any((root/'_Axis/Snapshots').glob('*Z.md')):
     # First session of a new project: nothing earlier to validate, so record the binding now.
     try:
         opaque=Path(os.path.expanduser('~/.axis/instance-id')).read_text().strip()
         osclass={'darwin':'macos','linux':'linux','win32':'windows'}.get(sys.platform,'unknown')
         storage=(s.get('capabilities') or {}).get('host-storage','unknown')
         bind.write_text(f'{opaque}\nharness: {o.harness}\nos: {osclass}\ninteraction: {o.interaction}\nstorage: {storage}\nverified: {stamp()}\n');env={'state':'unchanged'}
     except OSError:pass
 if env.get('state')=='changed':later.append('quietly complete _Axis/Practices/Portability.md > Environment-Change Validation, then write the binding')
 elif env.get('state')=='unavailable':notices.append('Environment signature unavailable (not verified).')
 if s.get('mindset') not in (None,'current'):later.append('regenerate the Mindset with _Axis/Resources/Draft-Mindset.md')
 q=s.get('queues') or {}
 if (q.get('Requests') or {}).get('count'):pending.append('adjudicate every file in _Axis/Requests/ under _Axis/Practices/Requests.md > Adjudication')
 if (q.get('Followups') or {}).get('count'):notices.append(f"{q['Followups']['count']} open Follow-Ups (^followups lists them)")
 if (q.get('Reminders') or {}).get('count'):later.append('check open Reminders for due items under _Axis/Practices/Reminders.md')
 mk=s.get('markers') or {}
 if mk.get('stale'):notices.append(f"{mk['stale']} stale session record(s); ^refresh can clear them")
 if mk.get('orphan_subagents'):notices.append(f"{mk['orphan_subagents']} orphaned Subagent record(s) from a crashed spawn; ^refresh can clear them")
 for x in (mk.get('fresh_external') or []):notices.append(f'An External Agent is serving this project ({x}).')
 if (s.get('notes') or {}).get('over_limit'):later.append('archive the oldest Notes over Max Notes under _Axis/Practices/Archiving.md > Automatic Note Overflow')
 t=s.get('trash') or {}
 if t.get('count'):later.append('sweep _Trash/ under _Axis/Practices/Trash.md')
 ix=s.get('indexes') or {}
 if ix.get('outcome') not in (None,'clear'):notices.append('Task or Snapshot index mismatch; run ^refresh')
 locks=s.get('locks') or {}
 if locks.get('lock_dirs') or locks.get('timestamp_claims'):notices.append('Stale lock or claim directories found; recovery needs a quiet moment (^refresh)')
 proj=(root/'_Axis/PROJECT.md').read_text() if (root/'_Axis/PROJECT.md').is_file() else ''
 if 'axis:project-overlay:begin' in proj:pending.append('validate and activate the declared project overlay with _Axis/Resources/Load-Project-Overlay.md (confirm, then activate); its guidance applies only after that')
 ready=(root/'_Axis/Flags/project-ready');rv=ready.read_text().splitlines()[0].strip() if ready.exists() and ready.read_text().strip() else ''
 if not re.fullmatch(r'\d{4}(\.\d{2}){5}\.\d{3}Z',rv):pending.append('say "Your project needs to be set up." and follow _Axis/Resources/Start-Project.md')
 if re.search(r'^\*\*Value:\*\* on\s*$',(root/'_Axis/SETTINGS.md').read_text().split('### Remote Freshness',1)[-1].split('###',1)[0],re.M):later.append('run _Axis/Resources/Check-Remote-Freshness.md once')
 later.append('check for a parent Project (Start-Session Step 5, Subproject detection)')

 name=re.match(r'# Project: (.+)',proj);name=name.group(1).strip() if name and '{{' not in name.group(1) else 'Not set'
 ver=re.search(r'^current-version: (\S+)$',(root/'_Axis/CHANGELOG.md').read_text(),re.M);ver=ver.group(1) if ver else 'Unavailable'
 home=os.path.expanduser('~');folder=str(root);folder='~'+folder[len(home):] if folder==home or folder.startswith(home+'/') else folder
 m=run(R/'startup-state.py','--root',root,'commit','--session',sid,'--owner',owner,'--starting-log',i['starting_log'])
 if m.get('status')!='committed':interrupted('commit failed',commit=m)

 bar='━'*40
 print(json.dumps({'axis_boot':'READY','session':sid,'notices':notices,'pending':pending,'later':later}))
 print('Banner for the user (show it first, as is):')
 print(f"```text\n  {bar}\n  │\n  +   A X I S   W O R K F L O W\n  │\n  {bar}\n\n  │   Agent:    Main\n  │   Status:   Ready\n  │   Version:  {ver}\n  │   Project:  {name}\n  │   Folder:   {folder}\n  │   Session:  {sid}\n\n  {bar}\n```")
 for x in notices:print('Notice for the user: '+x)
 for x in pending:print('Pending before the first answer: '+x)
 print('Before any answer other than the greeting or a requested exact reply: read _Axis/Resources/Load-Starting-Context.md (core rules), _Axis/INSTRUCTIONS.md, _Axis/MINDSET.md, _Axis/DIRECTIVES.md, _Axis/PLAN.md, _Axis/TASKS.md, the newest Snapshots and the Notes index'+('; and: '+'; '.join(later) if later else '')+'.')
 print(f'On every later turn, first run: python3 _Axis/Resources/turn.py --session {sid}')
except SystemExit:raise
except BaseException as e:interrupted(type(e).__name__)
