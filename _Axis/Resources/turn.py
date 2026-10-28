#!/usr/bin/env python3
"""Axis per-turn check: read and judge your own Marker, renew its lease, and glance at shared state.

Runs from the project root at the start of every later turn (and about every 30 minutes inside a long turn):
  python3 _Axis/Resources/turn.py --session {Session ID}
Exit 0 prints OK (plus any items to handle, then the reply-frame reminder for Main and External); 3 KILLED; 4 LOST LEASE (missing Marker); 6 FOREIGN MAIN or TAKEN OVER;
7 READ-ONLY (the host refused the renewal); 8 VERSION CHANGED or VERSION UNVERIFIED; 2 or 5 errors. It never recreates a missing Marker, never executes an
update helper, and never writes anything except the renewed Marker mtime."""
import argparse,errno,importlib.util,json,os,re,stat,sys,time
from pathlib import Path

a=argparse.ArgumentParser(description='Axis per-turn lease check');a.add_argument('--session',required=True);a.add_argument('--boot-version');o=a.parse_args()
root=Path.cwd().resolve();agents=root/'_Axis/Agents'
if not re.fullmatch(r'\d{4}(\.\d{2}){5}\.\d{3}Z',o.session):print('ERROR: not a Session ID.');sys.exit(2)
marker=agents/f'{o.session}.md'
def safe_file(path):
    try:
        current=root
        parts=path.relative_to(root).parts
        for i,part in enumerate(parts):
            current/=part;info=current.lstat()
            if stat.S_ISLNK(info.st_mode):return False
            if i<len(parts)-1:
                if not stat.S_ISDIR(info.st_mode):return False
            elif not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:return False
        return True
    except (OSError,ValueError):return False
# Never traverse a linked control directory, even to construct a diagnostic.
for directory in (root/'_Axis',agents,root/'_Axis/Flags',root/'_Axis/Tracking',root/'_Axis/Logs'):
    if directory.is_symlink() or (directory.exists() and not directory.is_dir()):
        print('LOST LEASE: control directory is linked or malformed. Make no writes; follow _Axis/Resources/Displaced-Session.md.');sys.exit(4)
# Merge state is checked before lease renewal, without running any source-project code.
if any(os.path.lexists(root/p) for p in ('_Axis/Flags/merge-pending','_Axis/Merges/retired.json')):
    try:
        helper=root/'_Axis/Resources/startup-state.py'
        if not safe_file(helper):raise ValueError('unsafe installed guard')
        spec=importlib.util.spec_from_file_location('axis_turn_merge',helper);state=importlib.util.module_from_spec(spec);spec.loader.exec_module(state);state.Session(root,o.session).merge_access()
    except Exception:
        print('MERGE HELD: no renewal or shared writes. Follow _Axis/Practices/Merging.md; a retired or pending source cannot resume ordinary work.');sys.exit(9)
def versions():
    try:
        path=root/'_Axis/CHANGELOG.md'
        if not safe_file(path):raise OSError('unsafe version source')
        matches=re.findall(r'^current-version: (\S+)$',path.read_text(),re.M)
        installed=matches[0] if len(matches)==1 else None
    except OSError:installed=None
    try:
        path=root/'_Axis/Tracking'/f'{o.session}.md'
        if not safe_file(path):raise OSError('unsafe own binding')
        with path.open() as stream:text=stream.read(65536)
        values=re.findall(r'^\S+ - '+re.escape(o.session)+r' - STATUS \[session\] Axis boot version: (\S+)$',text,re.M)
    except OSError:values=[]
    # Tracking may be disabled. A bounded scan of the first startup-era Logs supplies
    # the same own-session binding; another session's global Flag never supplies it.
    if not values:
        candidates=sorted(p for p in (root/'_Axis/Logs').glob('*Z.md') if p.stem>=o.session)[:2000]
        for p in candidates:
            try:
                if not safe_file(p):continue
                with p.open() as stream:body=stream.read(2048)
                lines=body.splitlines()
                if lines[:1]==['Session Started'] and 'session: '+o.session in lines[:8]:values+=re.findall(r'^axis-version: (\S+)$',body,re.M)
            except OSError:pass
    known=set(values+([o.boot_version] if o.boot_version else []))
    return installed,(next(iter(known)) if len(known)==1 else None)

def held(label,code,reason):
    live=[]
    for p in sorted(agents.glob('*Z.md')):
        if p.stem==o.session or not safe_file(p) or (agents/(p.stem+'.kill')).exists():continue
        try:
            lines=p.read_text().splitlines();age=time.time()-p.stat().st_mtime
            if lines[:1]==['Main: session'] and lines[2:3]==['session: '+p.stem] and 0<=age<3600:
                live.append({'session':p.stem,'host':next((v[6:] for v in lines if v.startswith('host: ')),'unverified'),'idle_seconds':int(age)})
        except OSError:pass
    installed,booted=versions()
    print(label+': '+reason+' Make no writes. Follow _Axis/Resources/Displaced-Session.md for the fixed notice and User-selected fresh-session procedure.')
    print(json.dumps({'state':'contested' if label=='FOREIGN MAIN' else 'displaced-or-context-held','reason':label,'session':o.session,'live_mains':live,'installed_version':installed,'boot_version':booted,'displacement_time':'unverified; consult actual takeover records','writes_allowed':False}))
    sys.exit(code)

if (agents/f'{o.session}.kill').exists():
    held('KILLED',3,'User stopped this Axis identity; it must not resume.')
def missing():
    # A takeover clears the idle Main's Marker. When the session-id Flag names a newer, live Main, this session was
    # replaced: report TAKEN OVER, because re-registering a lost lease here would briefly make two Mains.
    try:
        flag=root/'_Axis/Flags/session-id'
        owner=((flag.read_text().splitlines() or [''])[0].strip() if safe_file(flag) else '');p=agents/f'{owner}.md'
        newer=re.fullmatch(r'\d{4}(\.\d{2}){5}\.\d{3}Z',owner) and owner>o.session and not (agents/f'{owner}.kill').exists()
        if newer and safe_file(p) and p.read_text().splitlines()[:3]==['Main: session','','session: '+owner] and 0<=time.time()-p.stat().st_mtime<3600:
            held('TAKEN OVER',6,f'your Marker was cleared and a newer Main session ({owner}) now holds the project.')
    except OSError:pass
    held('LOST LEASE',4,'Your Marker is missing; never recreate it.')
if not safe_file(marker) and marker.exists():held('LOST LEASE',4,'Your Marker path is linked or malformed; ownership cannot be verified.')
if not marker.is_file():missing()
try:
    marker_info=marker.stat();marker_bytes=marker.read_bytes()
    if marker_info.st_nlink!=1:held('LOST LEASE',4,'Your Marker has multiple links; ownership cannot be verified.')
    first=(marker_bytes.decode().splitlines() or [''])[0];age=time.time()-marker_info.st_mtime
except OSError:missing()
if not (first=='Main: session' or re.fullmatch(r'(External|Subagent): [^\r\n]+',first)):
    held('LOST LEASE',4,'Your Marker role is malformed.')
if first=='Main: session':
    lines=marker_bytes.decode().splitlines()
    if len(lines)!=4 or lines[1]!='' or not lines[3].startswith('host: ') or not lines[3][6:].strip():
        held('LOST LEASE',4,'Your Main Marker shape is malformed.')
if first=='Main: session' or first.startswith('External: '):
    own_sessions=re.findall(r'^session: (.+)$',marker_bytes.decode(),re.M)
    if own_sessions!=[o.session]:held('LOST LEASE',4,'Your Marker session does not exactly match your own identity.')
if first=='Main: session':
    try:
        flag=root/'_Axis/Flags/session-id'
        owner=((flag.read_text().splitlines() or [''])[0].strip() if safe_file(flag) else '')
    except OSError:owner=''
    if owner!=o.session:held('TAKEN OVER',6,f'session-id no longer names this Main ({owner or "missing or unsafe"}); ownership is unverified.')
now=time.time();items=[]
if first=='Main: session':
    for p in agents.glob('*Z.md'):
        if p==marker or (agents/(p.stem+'.kill')).exists():continue
        if not safe_file(p):held('FOREIGN MAIN',6,'Another Marker is unsafe; ownership is unverified.')
        try:fresh=now-p.stat().st_mtime<3600;subject=(p.read_text().splitlines() or [''])[0]
        except OSError:continue
        if fresh and subject=='Main: session':
            held('FOREIGN MAIN',6,f'another Main session ({p.stem}) is live; ownership is contested.')
# Idle is not lost (2.01): a Marker at or over one hour old counts as dead for OTHER sessions deciding whether they may
# become Main, but its own session may resume when nothing replaced it - no tombstone (checked above), no live foreign
# Main (checked above), and for Main the session-id Flag still names this session.
if age>=3600:
    items.append(f'this session was idle {int(age//60)} minutes; its lease was renewed because no other session replaced it - mention it to the user in one line')
# Renewal refused by a read-only host (sandbox or file system) is not a missing Marker: report it, fail closed.
readonly='READ-ONLY: this host refused to renew your Marker (read-only sandbox or file system); the Marker is still present. Make no shared writes and do not create or repair any Marker; ask the user to rerun this session with write access.'
installed,booted=versions()
if first.startswith(('Main: session','External: ')) and (root/'_Axis/CHANGELOG.md').exists():
    if not installed or not booted:held('VERSION UNVERIFIED',8,'The installed or own boot version cannot be verified.')
    if installed!=booted:held('VERSION CHANGED',8,'Loaded Axis rules differ from the installed version; a fresh Axis session is required.')
try:
    fd=os.open(marker,os.O_RDONLY|os.O_NOFOLLOW)
    try:
        current=os.fstat(fd)
        if (current.st_dev,current.st_ino)!=(marker_info.st_dev,marker_info.st_ino) or current.st_nlink!=1 or os.read(fd,len(marker_bytes)+1)!=marker_bytes:
            held('LOST LEASE',4,'Your Marker changed during validation.')
        if (agents/f'{o.session}.kill').exists():held('KILLED',3,'User stopped this Axis identity; it must not resume.')
        os.utime(fd)
        after=marker.stat()
        if (agents/f'{o.session}.kill').exists():held('KILLED',3,'User stopped this Axis identity during renewal; it must not resume.')
        if (after.st_dev,after.st_ino)!=(current.st_dev,current.st_ino):held('LOST LEASE',4,'Your Marker changed during renewal.')
    finally:os.close(fd)
except FileNotFoundError:missing()
except OSError as e:
    if isinstance(e,PermissionError) or e.errno in (errno.EROFS,errno.EPERM,errno.EACCES):print(readonly);sys.exit(7)
    held('LOST LEASE',4,'Your Marker is missing; never recreate it.')
# Update handoff: file-only, like boot.py - never execute an update helper that an unconsumed update may have installed.
d=root/'_Axis/Updates'
try:
    for e in (d.iterdir() if d.is_dir() else []):
        if e.name in ('.gitkeep','operation.lck','.DS_Store') and e.is_file() and not e.is_symlink():continue
        if not e.is_dir() or e.is_symlink():items.append('unexpected entry in _Axis/Updates/: follow _Axis/Resources/Check-Update-Handoff.md before ordinary work');break
        names={x.name for x in e.iterdir()}
        if 'consumed.json' in names or {'rollback.json','released.json'}<=names:continue
        items.append('an update handoff needs attention: follow _Axis/Resources/Check-Update-Handoff.md before ordinary work');break
except OSError:items.append('update handoff state unverified: inspect _Axis/Updates/ under _Axis/Resources/Check-Update-Handoff.md')
if first=='Main: session':
    incoming=root/'_Axis/Submissions'
    if incoming.is_symlink():items.append('unsafe Submissions queue; hold import')
    elif incoming.is_dir() and any(p.name not in ('.gitkeep','_migration.md','_migration-complete.md') and not (p.name=='_received' and p.is_dir() and not p.is_symlink()) for p in incoming.iterdir()):items.append('Submissions await Main review: process once under _Axis/Practices/Submissions.md; inspect the compact MESSAGES.md view')
    index=root/'_Axis/MESSAGES.md'
    try:
        if index.is_symlink() or index.stat().st_size>65536:raise ValueError('unsafe index')
        text=index.read_text(); pending=re.search(r'^main-pending-count: ([0-9]+)$',text,re.M)
        uncertain=re.search(r'^main-uncertain-count: ([0-9]+)$',text,re.M)
        if pending and uncertain and 'main-view: recipient-lifecycle/v1' in text:
            if int(pending[1]):items.append(f'{pending[1]} pending Main Message(s); validate the cached view under _Axis/Practices/Messages.md before acting')
            if int(uncertain[1]):items.append(f'{uncertain[1]} Message classification(s) uncertain; inspect canonical routing and lifecycle')
        else:
            global_pending=re.search(r'^pending-count: ([0-9]+)$',text,re.M)
            if global_pending and int(global_pending[1]):items.append('Message view lacks Main classification; rebuild the cached view before treating global pending records as Main work')
    except FileNotFoundError:pass
    except (OSError,ValueError):items.append('Message view unverified; inspect canonical records before acting')
    legacy=root/'_Axis/Requests'
    if legacy.is_symlink() or (legacy.is_dir() and any(p.name!='.gitkeep' for p in legacy.iterdir())):items.append('legacy Requests held for explicit migration or upgrade; no active compatibility queue')
    # Project overlay: cheap per-turn check that the declaration and overlay file did not change since activation.
    flag=root/'_Axis/Flags/project-overlay'
    try:lines=flag.read_text().splitlines()
    except OSError:lines=[]
    if len(lines)>=4 and lines[0].strip()==o.session:
        try:
            since=flag.stat().st_mtime
            changed=any((root/n).stat().st_mtime>since for n in ('_Axis/PROJECT.md',lines[3].strip()))
        except OSError:changed=True
        if changed:items.append('the project overlay or its declaration changed since activation: revalidate it under _Axis/Resources/Load-Project-Overlay.md (activate phase) before applying its guidance')
print('OK: lease renewed.')
for x in items:print('Handle before answering: '+x)
if first.startswith(('Main: session','External: ')):
    home=os.path.expanduser('~');folder=str(root);folder='~'+folder[len(home):] if folder==home or folder.startswith(home+'/') else folder
    print(f'Reply frame: start your reply with the Axis header, with nothing before it, and end with one blank line, no divider, then > READY {folder}: (or > READY {folder} (background tasks running): while background tasks run) - progress notes get neither.')
