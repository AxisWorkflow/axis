#!/usr/bin/env python3
"""Axis per-turn check: read and judge your own Marker, renew its lease, and glance at shared state.

Runs from the project root at the start of every later turn (and about every 30 minutes inside a long turn):
  python3 _Axis/Resources/turn.py --session {Session ID}
Exit 0 prints OK (plus any items to handle); 3 KILLED; 4 LOST LEASE (missing Marker); 6 FOREIGN MAIN or TAKEN OVER;
2 or 5 errors. It never recreates a missing Marker, never executes an update helper, and never writes anything
except the renewed Marker mtime."""
import argparse,os,re,sys,time
from pathlib import Path

a=argparse.ArgumentParser(description='Axis per-turn lease check');a.add_argument('--session',required=True);o=a.parse_args()
root=Path.cwd().resolve();agents=root/'_Axis/Agents'
if not re.fullmatch(r'\d{4}(\.\d{2}){5}\.\d{3}Z',o.session):print('ERROR: not a Session ID.');sys.exit(2)
marker=agents/f'{o.session}.md'
if (agents/f'{o.session}.kill').exists():
    print('KILLED: User stopped this session. Log one final Event, append a final Tracking line, tell the user, and stop.');sys.exit(3)
lost='LOST LEASE: your Marker is missing. Make no shared writes and never recreate it on your own; ask the user this turn. On their word you may re-register it (Practices > Markers > The Lease).'
if not marker.is_file():print(lost);sys.exit(4)
try:
    first=(marker.read_text().splitlines() or [''])[0];age=time.time()-marker.stat().st_mtime
except OSError:print(lost);sys.exit(4)
if not re.match(r'(Main: session|External: |Subagent: )',first):print('ERROR: your Marker is malformed; ask the user.');sys.exit(5)
now=time.time();items=[]
taken='TAKEN OVER: {why} Make no shared writes and touch no Flag; tell the user this session has ended and that a new one can be started, or ^promote used from an External session.'
if first=='Main: session':
    for p in agents.glob('*Z.md'):
        if p==marker or (agents/(p.stem+'.kill')).exists():continue
        try:fresh=now-p.stat().st_mtime<3600;subject=(p.read_text().splitlines() or [''])[0]
        except OSError:continue
        if fresh and subject=='Main: session':
            print(f'FOREIGN MAIN: another Main session ({p.stem}) is live. STOP: make no shared writes and touch no Flag; tell the user, who can coordinate under _Axis/Resources/Lock-File.md or use ^promote / ^demote.');sys.exit(6)
# Idle is not lost (2.01): a Marker at or over one hour old counts as dead for OTHER sessions deciding whether they may
# become Main, but its own session may resume when nothing replaced it - no tombstone (checked above), no live foreign
# Main (checked above), and for Main the session-id Flag still names this session.
if age>=3600:
    if first=='Main: session':
        try:owner=((root/'_Axis/Flags/session-id').read_text().splitlines() or [''])[0].strip()
        except OSError:owner=''
        if owner!=o.session:
            print(taken.format(why=f'this session was idle {int(age//60)} minutes and the session-id Flag no longer names it ({owner or "missing"}): another Main started meanwhile.'));sys.exit(6)
    items.append(f'this session was idle {int(age//60)} minutes; its lease was renewed because no other session replaced it - mention it to the user in one line')
try:os.utime(marker)
except OSError:print(lost);sys.exit(4)
# Update handoff: file-only, like boot.py - never execute an update helper that an unconsumed update may have installed.
d=root/'_Axis/Updates'
try:
    for e in (d.iterdir() if d.is_dir() else []):
        if e.name in ('.gitkeep','operation.lck') and e.is_file():continue
        if not e.is_dir() or e.is_symlink():items.append('unexpected entry in _Axis/Updates/: follow _Axis/Resources/Check-Update-Handoff.md before ordinary work');break
        names={x.name for x in e.iterdir()}
        if 'consumed.json' in names or {'rollback.json','released.json'}<=names:continue
        items.append('an update handoff needs attention: follow _Axis/Resources/Check-Update-Handoff.md before ordinary work');break
except OSError:items.append('update handoff state unverified: inspect _Axis/Updates/ under _Axis/Resources/Check-Update-Handoff.md')
if first=='Main: session':
    req=[p for p in (root/'_Axis/Requests').glob('*.md')] if (root/'_Axis/Requests').is_dir() else []
    if req:items.append(f'{len(req)} Request(s) in _Axis/Requests/: adjudicate under _Axis/Practices/Requests.md before answering')
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
