#!/usr/bin/env python3
"""Axis per-turn check: read and judge your own Marker, renew its lease, and glance at shared state.

Runs from the project root at the start of every later turn:
  python3 _Axis/Resources/turn.py --session {Session ID}
Exit 0 prints OK (plus any items to handle); 3 KILLED; 4 LOST LEASE (missing or expired Marker); 6 FOREIGN MAIN; 2 or 5 errors. It never
recreates a missing Marker and never writes anything except the renewed Marker mtime."""
import argparse,json,os,re,subprocess,sys,time
from pathlib import Path

a=argparse.ArgumentParser(description='Axis per-turn lease check');a.add_argument('--session',required=True);o=a.parse_args()
root=Path.cwd().resolve();agents=root/'_Axis/Agents'
if not re.fullmatch(r'\d{4}(\.\d{2}){5}\.\d{3}Z',o.session):print('ERROR: not a Session ID.');sys.exit(2)
marker=agents/f'{o.session}.md'
if (agents/f'{o.session}.kill').exists():
    print('KILLED: User stopped this session. Log one final Event, append a final Tracking line, tell the user, and stop.');sys.exit(3)
if not marker.is_file():
    print('LOST LEASE: your Marker is missing. Make no shared writes and never recreate it; ask the user this turn.');sys.exit(4)
lost='LOST LEASE: your Marker is missing or expired. Make no shared writes and never recreate it; ask the user this turn.'
try:
    first=(marker.read_text().splitlines() or [''])[0];age=time.time()-marker.stat().st_mtime
except OSError:print(lost);sys.exit(4)
if not re.match(r'(Main: session|External: |Subagent: )',first):print('ERROR: your Marker is malformed; ask the user.');sys.exit(5)
# A Marker at or over one hour old is dead (Practices > Markers > Liveness): never revive it.
if age>=3600:print(lost);sys.exit(4)
now=time.time()
if first=='Main: session':
    for p in agents.glob('*Z.md'):
        if p==marker or (agents/(p.stem+'.kill')).exists():continue
        try:fresh=now-p.stat().st_mtime<3600;subject=(p.read_text().splitlines() or [''])[0]
        except OSError:continue
        if fresh and subject=='Main: session':
            print(f'FOREIGN MAIN: another Main session ({p.stem}) is live. STOP: make no shared writes and touch no Flag; tell the user, who can coordinate under _Axis/Resources/Lock-File.md or use ^promote / ^demote.');sys.exit(6)
try:os.utime(marker)
except OSError:print(lost);sys.exit(4)
items=[]
try:
    r=subprocess.run([sys.executable,'-B',str(root/'_Axis/Resources/update-transaction.py'),'inspect','--root',str(root)],capture_output=True,text=True,timeout=60)
    state=json.loads(r.stdout.strip().splitlines()[-1]).get('state')
    if state!='none':items.append('an update handoff needs attention: follow _Axis/Resources/Check-Update-Handoff.md before ordinary work')
except (OSError,ValueError,IndexError,subprocess.SubprocessError):items.append('update handoff state unverified: inspect _Axis/Updates/ under _Axis/Resources/Check-Update-Handoff.md')
if first=='Main: session':
    req=[p for p in (root/'_Axis/Requests').glob('*.md')] if (root/'_Axis/Requests').is_dir() else []
    if req:items.append(f'{len(req)} Request(s) in _Axis/Requests/: adjudicate under _Axis/Practices/Requests.md before answering')
print('OK: lease renewed.')
for x in items:print('Handle before answering: '+x)
