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
a.add_argument('--finish-adoption',metavar='SESSION',help='resume a startup that stopped with ADOPT after the listed record edits')
o=a.parse_args();root=Path.cwd().resolve();R=root/'_Axis/Resources'

def stamp():
    n=datetime.datetime.now(datetime.timezone.utc);return n.strftime('%Y.%m.%d.%H.%M.%S.')+'%03dZ'%(n.microsecond//1000)
def run(*args,timeout=120):
    r=subprocess.run([sys.executable,'-B',*map(str,args)],cwd=root,capture_output=True,text=True,timeout=timeout)
    out=r.stdout.strip().splitlines()
    try:return json.loads(out[-1]) if out else {'status':'error','stderr':r.stderr[-400:]}
    except ValueError:return {'status':'error','stdout':r.stdout[-400:],'stderr':r.stderr[-400:]}
def stop(why,guide='_Axis/Resources/Boot-Manual.md',**k):
    print(json.dumps({'axis_boot':'STOP','reason':why,'guide':guide,**k}));print(f'STOP: {why}. Follow {guide} instead.');sys.exit(2)

def ready_transaction():
    d=root/'_Axis/Updates'
    for e in sorted(d.iterdir()) if d.is_dir() else []:
        if e.is_dir() and not e.is_symlink():
            names={x.name for x in e.iterdir()}
            if 'consumed.json' not in names and {'ready.json','released.json'}<=names and 'rollback.json' not in names:return e
    return None

def adopt(sid):
    # Short adoption path (2.01): reconcile and consume a finished update inside this admitted startup, using the
    # FROZEN engine copy in the transaction folder - never a helper the update installed - and only after checking
    # its hash against the independent authorization Log (Check-Update-Handoff > Consume).
    import hashlib
    E=ready_transaction()
    if E is None:return None
    tx=E.name;start=json.loads((E/'start.json').read_text());plan=start['plan']
    auth=(root/plan['authorization']['record']).read_text()
    want=[l.split(':',1)[1].strip() for l in auth.splitlines() if l.startswith('engine_sha256:')]
    if want!=[hashlib.sha256((E/'engine.py').read_bytes()).hexdigest()]:interrupted('the update engine does not match its authorization; follow _Axis/Resources/Entry-Protocol.md',transaction=tx)
    b=run(E/'engine.py','begin-reconcile','--root',root,'--session',sid,'--transaction',tx)
    if b.get('state')!='reconciling':interrupted('update reconciliation could not start',transaction=tx,result=b)
    edits=[]
    for n,rules in plan['reconciliation'].items():
        text=(root/n).read_text() if (root/n).is_file() else ''
        miss=[x for x in rules['contains'] if x not in text];bad=[x for x in rules['absent'] if x in text]
        if miss or bad or 'archive_to' in rules:edits.append({'path':n,'must_contain':miss,'must_not_contain':bad,**({'archive_to':rules['archive_to']} if 'archive_to' in rules else {})})
    if edits:
        print(json.dumps({'axis_boot':'ADOPT','session':sid,'transaction':tx,'from':plan['from_version'],'to':plan['to_version'],'edits':edits}))
        print(f"ADOPT: this startup is adopting the finished update {plan['from_version']} -> {plan['to_version']}. Make the listed edits to those records (keep them true to the project), then run: python3 _Axis/Resources/boot.py --finish-adoption {sid} --host {o.host!r} --model {o.model!r} --harness {o.harness} --spawn {o.spawn} --parallel {o.parallel}. Do not answer or start other work until it prints READY.")
        sys.exit(4)
    records={}
    for n in plan['reconciliation']:
        body=(root/n).read_bytes();records[n]={'sha256':hashlib.sha256(body).hexdigest(),'bytes':len(body),'mode':(root/n).stat().st_mode&0o777}
    inp=root/'_Temp'/f'axis-adoption-{tx}.json'
    inp.write_text(json.dumps({'schema':1,'transaction':tx,'target_commit':plan['source']['commit'],'records':records}))
    try:c=run(E/'engine.py','consume','--root',root,'--session',sid,'--transaction',tx,'--reconciliation',inp)
    finally:
        try:inp.unlink()
        except OSError:pass
    if c.get('state')!='consumed':interrupted('update consumption failed',transaction=tx,result=c)
    return {'from':plan['from_version'],'to':plan['to_version'],'transaction':tx,'unrelated_changes':c.get('unrelated_changes') or []}

def update_state():
    # File-only read of _Axis/Updates/: this boot never executes an update helper that an unconsumed
    # update may have installed (Check-Update-Handoff > Inspect before serving, step 2).
    d=root/'_Axis/Updates'
    if not d.exists():return 'none'
    state='none'
    for e in d.iterdir():
        if e.name in ('.gitkeep','operation.lck','.DS_Store') and e.is_file() and not e.is_symlink():continue
        if not e.is_dir() or e.is_symlink():return 'unexpected'
        names={x.name for x in e.iterdir()}
        if 'consumed.json' in names or {'rollback.json','released.json'}<=names:continue
        state='ready' if {'ready.json','released.json'}<=names else 'pending'
        if state=='pending':return state
    return state

def secrets_guidance():
    # Encrypted Secrets: say exactly what to run when this computer cannot open them. Reads only the public
    # .recipient and whether files exist; never a Secret, the key, or the password (GIT.md > Password Unlock).
    import shlex,shutil
    sec=root/'_Axis/Secrets';rec=sec/'.recipient'
    if not ((sec/'.capsule.age').is_file() and rec.is_file()):return None
    kid=re.search(r'^key-id: ([0-9a-f]{40}(?:[0-9a-f]{24})?)$',rec.read_text(),re.M)
    if not kid:return None
    keys=Path(os.environ.get('AXIS_SECRETS_KEY_DIR') or os.path.expanduser('~/.axis/keys'))
    if (keys/f'{kid.group(1)}.agekey').is_file():
        if not (sec/'.binding').exists():later.append('receive the encrypted Secrets: _Axis/Practices/GIT.md > Receive automatically')
        return None
    go='cd '+shlex.quote(str(root))
    if not (shutil.which('age') and shutil.which('age-keygen')):
        inst='brew install age' if sys.platform=='darwin' else 'sudo apt install age'
        return f'This project keeps encrypted Secrets, but the age tool is not installed on this computer. In a terminal, run: {inst}  (other systems: https://github.com/FiloSottile/age#installation). Then start a new conversation here.'
    if (sec/'.identity.age').is_file():
        return f'This project\'s Secrets are locked on this computer. Open a terminal window (not this chat) and run: {go} && bash _Axis/Resources/secrets-capsule.sh unlock  -- then type your Secrets password at the prompt. Tell me when it says "unlocked" and I will finish receiving the Secrets.'
    return f'This project\'s Secrets cannot be opened on this computer: its key is not here and no password copy exists. On a computer that already opens them, run in a terminal: cd <that project folder> && bash _Axis/Resources/secrets-capsule.sh password-set  -- choose a password, save and push, then on this computer run: {go} && bash _Axis/Resources/secrets-capsule.sh unlock'

def network_folder():
    # A LAN share (SMB/CIFS/NFS/AFP) is one copy with several writers: folder locks work there, with brief busy
    # errors and short "missing" windows during renames (Lock-File > Shared Network Folders).
    try:out=subprocess.run(['mount'],capture_output=True,text=True,timeout=5).stdout
    except (OSError,subprocess.SubprocessError):return None
    best=None
    for line in out.splitlines():
        m=re.match(r'^(.*?) on (/.*?) (?:\(|type )([a-z0-9]+)',line)
        if not m:continue
        point,kind=m.group(2),m.group(3)
        if (str(root)==point or str(root).startswith(point.rstrip('/')+'/')) and (best is None or len(point)>len(best[0])):best=(point,kind)
    return best[1] if best and best[1] in ('smbfs','cifs','smb3','nfs','nfs4','afpfs','webdav') else None

def replace_shared(src, dst):
    """os.replace with a bounded retry. On shared network folders (SMB) a rename can fail briefly with EBUSY or
    EACCES while another computer reads the target (SMB lab, 2026-10-04: worst wait 1.05 s)."""
    import errno as _errno, time as _time
    deadline=_time.monotonic()+10
    while True:
        try:os.replace(src,dst);return
        except OSError as e:
            if e.errno not in (_errno.EBUSY,_errno.EACCES) or _time.monotonic()>deadline:raise
            _time.sleep(0.05)

def sync_directives():
    # Default Directives (2.04, User decision 2026-10-04): append each Directive shipped in the managed
    # Resources/Default-Directives.md that the project's DIRECTIVES.md lacks, unless the project opts out with
    # <!-- axis:omit-directive: {name} -->. Existing Directives are never edited, reordered or removed.
    src=R/'Default-Directives.md';dst=root/'_Axis/DIRECTIVES.md'
    if not src.is_file() or not dst.is_file() or src.is_symlink() or dst.is_symlink():return []
    def sections(text):
        parts=re.split(r'(?m)^(?=## )',text);return [(x.splitlines()[0][3:].strip(),x.rstrip('\n')+'\n') for x in parts if x.startswith('## ')]
    have=dst.read_text()
    known={n.casefold() for n,_ in sections(have)}|{m.strip().casefold() for m in re.findall(r'<!-- axis:omit-directive: (.+?) -->',have)}
    add=[(n,b) for n,b in sections(src.read_text()) if n.casefold() not in known]
    if not add:return []
    new=have.rstrip('\n')+'\n'+''.join('\n'+b for _,b in add)
    tmp=dst.with_name('.DIRECTIVES.md.axis-sync');tmp.write_text(new);replace_shared(tmp,dst)
    if dst.read_text()!=new:raise OSError('directive sync readback')
    return [n for n,_ in add]

def move_wiki():
    # Wiki folder move (2.05, User decision 2026-10-07): the Wiki moved from Wiki/ to _Wiki/. A project last updated
    # before 2.05 still keeps it in Wiki/, so the first startup on 2.05 renames the folder whole (one move; every file
    # inside unchanged) and points the two Wiki index files at the new path. The append-only Wiki records and the
    # User-approved schema are never rewritten. Runs under the startup admission; a later startup finds nothing to do.
    old,new=root/'Wiki',root/'_Wiki'
    if 'Wiki' not in os.listdir(root):return None,None  # exact name: a case-insensitive disk must not match a User's wiki/
    if old.is_symlink() or not old.is_dir():return 'The project root has a Wiki entry that is not a plain folder, so Axis did not move it. Since Axis 2.05 the Wiki lives in _Wiki/; move its content there yourself.',None
    if os.path.lexists(new):return 'This project has both Wiki/ and _Wiki/. Since Axis 2.05 the Wiki lives in _Wiki/: move anything you still need from Wiki/ into _Wiki/, then delete Wiki/.',None
    replace_shared(old,new)
    fixed=[]
    for n in ('Input-Index.md','Library-Index.md'):
        q=root/'_Axis/Wiki'/n
        if not q.is_file() or q.is_symlink():continue
        text=q.read_text(encoding='utf-8');new_text=re.sub(r'(?<![\w./-])((?:\.\./)*)Wiki/',r'\1_Wiki/',text)
        if new_text==text:continue
        tmp=q.with_name('.'+n+'.axis-wiki');tmp.write_text(new_text,encoding='utf-8');replace_shared(tmp,q)
        if q.read_text(encoding='utf-8')!=new_text:raise OSError('Wiki index readback')
        fixed.append(n)
    note='Moved the Wiki from Wiki/ to _Wiki/, where Axis 2.05 keeps it'+(' (its index files now name the new path)' if fixed else '')+'. If Obsidian or another tool saves files to Wiki/Inbox/, point it at _Wiki/Inbox/.'
    return note,'record one Log Event "Wiki moved to _Wiki/"'+(' naming the updated index files: '+', '.join(fixed) if fixed else '')

if not (root/'_Axis/Resources/startup-state.py').is_file():stop('run this from the project root')
if o.finish_adoption:
    # Resume the admitted startup that stopped at ADOPT: same session, same admission (read back from its OWNER).
    try:st=json.loads((root/'_Axis/Flags/starting.lock/OWNER').read_text())
    except (OSError,ValueError):stop('no admitted startup to resume','_Axis/Resources/Entry-Protocol.md')
    if st.get('session')!=o.finish_adoption or st.get('phase')!='initialized':stop('the startup to resume does not match this session','_Axis/Resources/Entry-Protocol.md')
    sid,owner,resume_log=st['session'],st['token'],st['starting_log'];us='ready'
else:
    us=update_state()
    if us!='none' and us!='ready':stop('an update handoff needs attention','_Axis/Resources/Entry-Protocol.md',update=us)
    c=run(R/'startup-state.py','--root',root,'claim','--initial',stamp(),'--host',o.host)
    if c.get('status')=='external':
        print(json.dumps({'axis_boot':'EXTERNAL','claim':c}));print('EXTERNAL: another Main session is live. Follow _Axis/Resources/Start-External.md.');sys.exit(3)
    if c.get('status')!='admitted':stop('session claim failed',claim=c)
    sid,owner=c['session'],c['owner']
def interrupted(why,**k):
    print(json.dumps({'axis_boot':'STOP','reason':why,'session':sid,'owner':owner,'guide':'_Axis/Resources/Lock-File.md','interrupted_after_claim':True,**k}))
    print(f'STOP: startup interrupted after the claim ({why}). Startup is incomplete: tell the user, leave _Axis/Flags/starting.lock, _Axis/Flags/starting and _Axis/Agents/{sid}.md in place, and do not retry or use Boot-Manual.md. Recovery needs a quiet moment under _Axis/Resources/Lock-File.md > Quiescent Recovery.');sys.exit(2)
try:
 if o.finish_adoption:i={'status':'initialized','starting_log':resume_log}
 else:i=run(R/'startup-state.py','--root',root,'initialize','--session',sid,'--owner',owner)
 if i.get('status')!='initialized':interrupted('initialize failed',initialize=i)
 adopted=adopt(sid) if us=='ready' else None
 try:wiki_note,wiki_log=move_wiki()
 except (OSError,UnicodeError) as e:wiki_note,wiki_log=f'Axis could not finish moving the Wiki from Wiki/ to _Wiki/ ({type(e).__name__}). Check both folders before using the Wiki.',None
 s=run(R/'startup-survey.py','--root',root,'survey','--session',sid,'--owner',owner,'--model',o.model,'--harness',o.harness,'--interaction',o.interaction,'--spawn',o.spawn,'--parallel',o.parallel)
 if s.get('status')!='surveyed':interrupted('startup survey failed',survey=s)

 notices=[x for x in (s.get('notices') or []) if x!='cloud-synced-folder'];pending=[];later=[]
 if wiki_note:notices.append(wiki_note)
 if wiki_log:later.append(wiki_log)
 if 'cloud-synced-folder' in (s.get('notices') or []):
     why=s.get('cloud_reason') or 'reason not recorded'
     notices.append(f'This folder looks cloud-synced ({why}), so agents here write one at a time. If it is really a local folder, say so and it will be corrected.')
     later.append(f'record one Log Event "Storage classified as cloud-synced" with the reason: {why}')
 if adopted:
     notices.append(f"Axis was updated from {adopted['from']} to {adopted['to']} and the update is now adopted.")
     if adopted['unrelated_changes']:notices.append('Project files changed after the update was applied (reported, not blocking): '+', '.join(adopted['unrelated_changes'][:5]))
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
 if mk.get('stale'):notices.append(f"{mk['stale']} idle or stale session record(s); ^refresh clears those over 24 hours old")
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
 rf=re.search(r'^\*\*Value:\*\* (on|auto)\s*$',(root/'_Axis/SETTINGS.md').read_text().split('### Remote Freshness',1)[-1].split('###',1)[0],re.M)
 if rf:
     # Check-Remote-Freshness.md, run here so that `auto` can bring the project up to date before the Agent reads it.
     try:f=run(R/'remote-freshness.py','--project-root',root,'--session',sid,timeout=600)
     except subprocess.TimeoutExpired:f={'status':'unverified','notice':'Remote freshness is unverified; Axis remains usable locally.'}
     if f.get('notice'):notices.append(f['notice'])
     elif f.get('status') not in ('disabled','already-checked','no-upstream','equal','local-ahead','fast-forwarded'):notices.append('Remote freshness is unverified; Axis remains usable locally.')
     if f.get('status')=='fast-forwarded':
         if f.get('workflow_changed'):pending.append("incoming commits changed Axis's own files: tell the user in one line and ask them to start a fresh conversation; do not continue this one (_Axis/Practices/GIT.md > Incoming Change Validation)")
         else:
             if (root/'_Axis/Secrets/.capsule.age').exists():later.append('receive the encrypted Secrets: _Axis/Practices/GIT.md > Receive automatically')
             later.append('quietly run _Axis/Practices/Portability.md > Always-On Resume Revalidation for the received commits')
 added=sync_directives()
 if added:
     notices.append('Added '+('a new default Directive' if len(added)==1 else f'{len(added)} new default Directives')+' from this Axis version: '+', '.join(added)+'.')
     later.append('record one Log Event "Default Directives added" naming: '+', '.join(added))
 nf=network_folder()
 if nf:notices.append(f'This project is on a shared network folder ({nf}). Axis lets one agent write at a time here, because file locks proved unreliable on some network servers (_Axis/Resources/Lock-File.md > Shared Network Folders).')
 sg=secrets_guidance()
 if sg:notices.append(sg)
 cm=re.search(r'^\*\*Value:\*\* (\S+)\s*$',(root/'_Axis/SETTINGS.md').read_text().split('### Context Management',1)[-1].split('###',1)[0],re.M) if '### Context Management' in (root/'_Axis/SETTINGS.md').read_text() else None
 if cm and cm.group(1)=='Two-Pass':pending.append('Context Management is Two-Pass: read _Axis/Practices/Context.md and follow its Two-Pass section for every request')
 # Default Directive "Suggest a Context Method", applied mechanically at startup because the model is known here.
 cmv=cm.group(1) if cm and cm.group(1) in ('Default','Two-Pass') else 'Default';mid=o.model.lower()
 if cmv=='Default' and any(k in mid for k in ('claude','sonnet','opus','haiku','fable')):notices.append('This project runs on Claude, where Two-Pass context loading used about 38% fewer tokens on question-and-lookup work in Axis\'s tests, with no loss of accuracy. Say "switch Context Management to Two-Pass" to turn it on.')
 elif cmv=='Two-Pass' and any(k in mid for k in ('codex','gpt')):notices.append('This project uses Two-Pass context loading, which did not save tokens on Codex in Axis\'s tests. Say "switch Context Management to Default" to turn it off.')
 later.append('check for a parent Project (Start-Session Step 5, Subproject detection)')

 name=re.match(r'# Project: (.+)',proj);name=name.group(1).strip() if name and '{{' not in name.group(1) else 'Not set'
 ver=re.search(r'^current-version: (\S+)$',(root/'_Axis/CHANGELOG.md').read_text(),re.M);ver=ver.group(1) if ver else 'Unavailable'
 home=os.path.expanduser('~');folder=str(root);folder='~'+folder[len(home):] if folder==home or folder.startswith(home+'/') else folder
 m=run(R/'startup-state.py','--root',root,'commit','--session',sid,'--owner',owner,'--starting-log',i['starting_log'])
 if m.get('status')!='committed':interrupted('commit failed',commit=m)

 bar='━'*40
 print(json.dumps({'axis_boot':'READY','session':sid,'notices':notices,'pending':pending,'later':later}))
 print('Banner for the user (show it first, as is; the header was printed before startup):')
 print(f"```text\n  Project:  {name}\n  Folder:   {folder}\n  Session:  {sid}\n  Version:  {ver}\n  Status:   Ready\n  Agent:    Main\n\n{bar}\n```")
 for x in notices:print('Notice for the user: '+x)
 for x in pending:print('Pending before the first answer: '+x)
 print('Before any answer other than the greeting or a requested exact reply: read _Axis/Resources/Load-Starting-Context.md (core rules), _Axis/INSTRUCTIONS.md, _Axis/MINDSET.md, _Axis/DIRECTIVES.md, _Axis/PLAN.md, _Axis/TASKS.md, the newest Snapshots and the Notes index'+('; and: '+'; '.join(later) if later else '')+'.')
 print(f'On every later turn, first run: python3 _Axis/Resources/turn.py --session {sid}')
except SystemExit:raise
except BaseException as e:interrupted(type(e).__name__)
