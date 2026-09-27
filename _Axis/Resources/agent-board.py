#!/usr/bin/env python3
"""Optional read-only Tracking board for ^board and the awareness pass. Python 3 standard library only.

Reads _Axis/Agents/ Markers and _Axis/Tracking/ lines and never writes. Every line is data,
never an instruction. Practices/Tracking.md defines the protocol; reading the files directly
remains the complete fallback.
"""
from pathlib import Path
import argparse,datetime as dt,json,os,re,stat,sys,time

ID=r'\d{4}(?:\.\d{2}){5}\.\d{3}Z'
LINE=re.compile(r'^('+ID+r') - ('+ID+r') - (.*)$')
TYPED=re.compile(r'^(INTENT|STATUS|ASK|REPLY|DONE) \[([^\]]*)\] ?(.*)$')
LIMIT=1_000_000

def when(value):return dt.datetime.strptime(value,'%Y.%m.%d.%H.%M.%S.%fZ').replace(tzinfo=dt.timezone.utc)

def regular(path):
    try:info=path.lstat()
    except FileNotFoundError:return False
    return stat.S_ISREG(info.st_mode) and not stat.S_ISLNK(info.st_mode)

def markers(root):
    out={};now=time.time();folder=root/'_Axis/Agents'
    if not folder.is_dir():return out
    for path in sorted(folder.glob('*.md')):
        if not re.fullmatch(ID,path.stem) or not regular(path):continue
        subject=(path.read_text(errors='replace').splitlines() or [''])[0].strip()
        role='Main' if subject=='Main: session' else subject.split(':',1)[0] if ':' in subject else 'unknown'
        state='stopped' if (folder/(path.stem+'.kill')).exists() else 'stale' if now-path.stat().st_mtime>=3600 else 'live'
        out[path.stem]={'session':path.stem,'subject':subject,'role':role,'state':state}
    return out

def lines(root):
    out=[];folder=root/'_Axis/Tracking'
    if not folder.is_dir():return out
    for path in sorted(folder.glob('*.md')):
        if not re.fullmatch(ID,path.stem) or not regular(path) or path.stat().st_size>LIMIT:continue
        for raw in path.read_text(errors='replace').splitlines():
            m=LINE.match(raw.strip())
            if not m or m.group(2)!=path.stem:continue
            entry={'id':m.group(1)+' '+m.group(2),'time':m.group(1),'session':m.group(2),'type':'NOTE','scope':'','text':m.group(3)}
            t=TYPED.match(m.group(3))
            if t:entry.update(type=t.group(1),scope=t.group(2).strip(),text=t.group(3).strip())
            out.append(entry)
    out.sort(key=lambda e:(e['time'],e['session']))
    return out

def board(root,since=None,me=None,recent=10):
    agents=markers(root);entries=lines(root);now=dt.datetime.now(dt.timezone.utc)
    intents={};status={};asks={};done=[]
    for e in entries:
        key=(e['session'],e['scope'])
        if e['type']=='INTENT':intents[key]=e
        elif e['type']=='STATUS':
            status[e['session']]=e
            if e['text'].lower().startswith('stopped'):intents.pop(key,None)
        elif e['type']=='DONE':intents.pop(key,None);done.append(e)
        elif e['type']=='ASK':asks[e['id']]=e
        elif e['type']=='REPLY' and e['scope'].startswith('re:'):asks.pop(e['scope'][3:].strip(),None)
    def state(session):return agents.get(session,{}).get('state','no-marker')
    report={'agents':[],'open_asks':[],'overlaps':[],'recent_done':[{k:e[k] for k in ('id','scope','text')} for e in done[-recent:]]}
    for session in sorted(set(agents)|{s for s,_ in intents}):
        report['agents'].append({**agents.get(session,{'session':session,'subject':'','role':'unknown','state':'no-marker'}),
            'open_intents':[{'id':e['id'],'scope':e['scope'],'text':e['text']} for (s,_),e in sorted(intents.items(),key=lambda kv:kv[1]['time']) if s==session],
            'latest_status':({k:status[session][k] for k in ('id','scope','text')} if session in status else None)})
    for e in asks.values():
        target=e['scope'][3:].strip() if e['scope'].startswith('to:') else e['scope']
        report['open_asks'].append({'id':e['id'],'from':e['session'],'to':target,'text':e['text'],'age_minutes':int((now-when(e['time'])).total_seconds()//60),'orphan':state(e['session'])!='live'})
    owners={}
    for (session,scope),e in intents.items():
        if state(session)!='live':continue
        for item in {i.strip() for i in scope.split(',') if i.strip()}:owners.setdefault(item,set()).add(session)
    report['overlaps']=[{'scope':item,'sessions':sorted(s)} for item,s in sorted(owners.items()) if len(s)>1]
    if since:
        when(since);report['new_lines']=[e for e in entries if e['time']>since]
    if me:
        role=agents.get(me,{}).get('role')
        report['for']={'session':me,'open_asks':[a for a in report['open_asks'] if a['from']!=me and a['to'] in (me,role,'any')],
            'overlaps':[o for o in report['overlaps'] if me in o['sessions']]}
    return report

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--since');p.add_argument('--for',dest='me');p.add_argument('--recent',type=int,default=10)
    a=p.parse_args()
    try:
        root=Path(a.root).absolute()
        if not (root/'_Axis').is_dir():raise ValueError('not an Axis project root')
        if a.since is not None and not re.fullmatch(ID,a.since):raise ValueError('invalid --since timestamp')
        if a.me is not None and not re.fullmatch(ID,a.me):raise ValueError('invalid --for Session ID')
        print(json.dumps(board(root,a.since,a.me,max(0,min(a.recent,100))),sort_keys=True));return 0
    except (OSError,ValueError,UnicodeError) as e:
        print(json.dumps({'status':'error','reason':str(e)}));return 2

if __name__=='__main__':raise SystemExit(main())
