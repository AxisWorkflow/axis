#!/usr/bin/env python3
"""Closure-driven local Message archive; no cold copy or historical deletion."""
import hashlib
import json
import os
from pathlib import Path
import stat
from types import SimpleNamespace


def tree(path):
    rows=[]
    for parent,dirs,files in os.walk(path,followlinks=False):
        for name in dirs:
            p=Path(parent)/name
            if p.is_symlink():raise ValueError('linked Message support')
        for name in sorted(files):
            p=Path(parent)/name;info=p.lstat()
            if not stat.S_ISREG(info.st_mode) or info.st_nlink!=1:raise ValueError('unsafe Message archive input')
            rows.append([p.relative_to(path).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest(),info.st_size])
    return hashlib.sha256(json.dumps(sorted(rows),separators=(',',':')).encode()).hexdigest(),len(rows)


def archive(store,team,prepared):
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    store.require_main();store._check_lock()
    if (store.io.setting('Archiving') or 'Default')=='Never':return {'status':'disabled'}
    charter=store.read('Teams',team)
    settlement=integration(store,team)
    c.need(settlement and settlement['integration_complete'],'Main-integration-and-settlement-required')
    if prepared['path'] is not None:c.need(inventory_token(prepared['path'])==prepared['inventory'],'archive-input-changed')
    state=store.project('Teams',team)
    c.need(not state['held'] and state['state'] in c.TERMINAL,'Team-still-active')
    for job in store.records('Jobs'):
        if job.get('team')!=team:continue
        view=store.project('Jobs',job['id'])
        c.need(not view['held'] and view['state'] in c.TERMINAL and not view['active'] and not view['stop_unconfirmed'],'unfinished-sibling-Job')
        c.need(not any(a.get('route_pending') or a.get('route_uncertain') for a in view['attempts'].values()),'physical-settlement-required')
    messages=store.records('Messages',team=team)
    for message in messages:
        if message.get('team')!=team or message.get('event') is not None or message['kind'] not in {'request','question','offer','assignment'}:continue
        resolved=any(m.get('data',{}).get('reply_to')==message['id'] and m['kind'] in {'answer','result'} or m.get('data',{}).get('disposition_of')==message['id'] and m['data'].get('outcome') in {'declined','referred','validated','rejected','closed'} for m in messages)
        c.need(resolved,'unresolved-message-obligation')
    source=store.root/'_Axis/Messages/Teams'/team
    target=store.root/'_Axis/Messages/Archive/Teams'/team
    receipt=store.root/'_Axis/Teams'/team/'state/message-archive.json'
    receipt.parent.mkdir(exist_ok=True)
    if receipt.exists():
        record=json.loads(receipt.read_text());c.need(record['team']==team,'archive-owner')
        c.need(not source.exists() and target.is_dir() and prepared['tree']==(record['sha256'],record['files']),'archive-content-changed')
        return {'status':'archived','path':target.relative_to(store.root).as_posix()}
    if not source.exists():
        intent=receipt.with_name('message-archive-intent.json')
        if intent.exists():
            record=json.loads(intent.read_text())
            c.need(record['team']==team and target.is_dir() and prepared['tree']==(record['sha256'],record['files']),'archive-interruption-content-changed')
            store._write_bytes(receipt.relative_to(store.root).as_posix(),c.canonical(record)+b'\n',None)
            return {'status':'archived','path':target.relative_to(store.root).as_posix(),'recovered':True}
        return {'status':'empty'}
    c.need(not target.exists(),'archive-destination-collision')
    before,count=prepared['tree'];intent=receipt.with_name('message-archive-intent.json')
    value={'schema':1,'team':team,'source':source.relative_to(store.root).as_posix(),'destination':target.relative_to(store.root).as_posix(),'sha256':before,'files':count,'settlement':settlement}
    if intent.exists():c.need(json.loads(intent.read_text())==value,'archive-intent-changed')
    else:store._write_bytes(intent.relative_to(store.root).as_posix(),c.canonical(value)+b'\n',None)
    target.parent.mkdir(parents=True,exist_ok=True);store.path(target.parent.relative_to(store.root).as_posix(),kind='directory')
    store._check_lock();c.need(inventory_token(source)==prepared['inventory'],'archive-input-changed')
    os.rename(source,target)
    c.need(inventory_token(target)==prepared['inventory'],'archive-readback')
    store._write_bytes(receipt.relative_to(store.root).as_posix(),c.canonical(value)+b'\n',None)
    return {'status':'archived','path':target.relative_to(store.root).as_posix(),'files':count}


def inventory_token(path):
    rows=[]
    for parent,dirs,files in os.walk(path,followlinks=False):
        for name in sorted(dirs+files):
            p=Path(parent)/name;v=p.lstat()
            if stat.S_ISLNK(v.st_mode) or not (stat.S_ISDIR(v.st_mode) or stat.S_ISREG(v.st_mode) and v.st_nlink==1):raise ValueError('unsafe Message archive tree')
            rows.append([p.relative_to(path).as_posix(),v.st_dev,v.st_ino,v.st_mode,v.st_size,v.st_mtime_ns,v.st_ctime_ns])
    return sorted(rows)


def prepare(store,team):
    source=store.root/'_Axis/Messages/Teams'/team;target=store.root/'_Axis/Messages/Archive/Teams'/team
    path=source if source.exists() else target
    if not path.exists():return {'path':None,'tree':None,'inventory':[]}
    store.path(path.relative_to(store.root).as_posix(),kind='directory')
    before=inventory_token(path);value=tree(path)
    if inventory_token(path)!=before:raise ValueError('Message archive changed during preparation')
    return {'path':path,'tree':value,'inventory':before}


def integration(store,team):
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    charter=store.read('Teams',team)
    result=c.allocation_module().settled(store,charter) if charter.get('resource_allocation') else None
    if result:return result
    receipts=[m for m in store.records('Messages',team=team) if m.get('data',{}).get('legacy_team_integration',{}).get('team')==team]
    c.need(len(receipts)<=1,'integration-receipt-fork')
    if receipts:
        c._accepted(receipts[0]);result=receipts[0]['data']['legacy_team_integration']
        c.need(result['charter_sha256']==c.digest(charter),'integration-charter-changed')
        return result
    return None


def close_legacy(store,team,integrated):
    c=SimpleNamespace(**store.create_team.__func__.__globals__);store.require_main();store.require_placement()
    c.need(integrated is True,'Main-integration-required')
    charter=store.read('Teams',team);state=store.project('Teams',team)
    c.need(not charter.get('resource_allocation') and not state['held'] and state['state'] in c.TERMINAL,'legacy-Team-not-terminal')
    prior=integration(store,team)
    if prior:return {'status':'settled','settlement':prior}
    heads={}
    for job in store.records('Jobs'):
        if job.get('team')!=team:continue
        view=store.project('Jobs',job['id'])
        c.need(not view['held'] and view['state'] in c.TERMINAL and not view['active'] and not view['stop_unconfirmed'],'legacy-Job-not-terminal')
        c.need(not any(a.get('route_pending') or a.get('route_uncertain') for a in view['attempts'].values()),'legacy-physical-settlement-required')
        if c._native(job):
            budget=store.native_budget_state(job['limits']['budget']['key'])
            c.need(not budget['reserved_minor'] and not budget['uncertain_minor'] and not budget['unpriced_attempts'],'legacy-liability-unsettled')
        heads[job['id']]=view['head']
    data={'team':team,'charter_sha256':c.digest(charter),'team_head':state['head'],'job_heads':heads,'integration_complete':True,'accounting':'historical ledgers retained; no resources reset or released'}
    return store._record('Messages',{'subject':'Main completed legacy Team integration','kind':'control','recipient':'main','body':'Terminal work integrated; historical accounting remains locally readable.','team':team,'job':None,'correlation':'integration:'+team,'epoch':state['epoch'],'data':{'legacy_team_integration':data},'authority':charter['authority'],'expires':charter['authority']['expires'],'attachments':[]})


def individual(store):
    """Move completed simple correspondence; execution/accounting support stays held."""
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    store.require_main();store._check_lock()
    if (store.io.setting('Archiving') or 'Default')=='Never':return {'status':'disabled','moved':[]}
    messages=store.records('Messages');pending={m['id'] for m in store.pending_messages()}
    candidates={m['id']:m for m in messages if not m.get('team') and not m.get('job') and not m.get('event') and m['kind'] not in {'control','transfer'} and not m.get('attachments') and set(m.get('data',{}))<={'disposition_of','outcome','reference','predecessor','reply_to','observed'}}
    selected=set()
    for ident,message in candidates.items():
        if ident in pending or message['kind']=='decision':continue
        closure=[m for m in candidates.values() if m.get('data',{}).get('disposition_of')==ident]
        if not any(m['data'].get('outcome') in {'declined','referred','validated','rejected','closed'} for m in closure):continue
        group={ident}|{m['id'] for m in closure}
        correlated=[m for m in messages if message.get('correlation') and m.get('correlation')==message['correlation']]
        if any(m['id'] in pending or m['id'] not in candidates for m in correlated):continue
        selected.update(group)
    moved=[];target=store.root/'_Axis/Messages/Archive/Individual'
    for ident in sorted(selected):
        source=c.message_paths().resolve(store.root,ident)
        if source.parent!=store.root/'_Axis/Messages/Individual' or source.with_suffix('').exists():continue
        dest=target/source.name
        target.mkdir(parents=True,exist_ok=True);store.path(target.relative_to(store.root).as_posix(),kind='directory')
        c.need(not dest.exists(),'archive-destination-collision');before=source.read_bytes()
        store._check_lock();c.need(source.read_bytes()==before,'archive-input-changed')
        os.rename(source,dest);c.need(dest.read_bytes()==before,'archive-readback');moved.append(ident)
    return {'status':'archived','moved':moved}
