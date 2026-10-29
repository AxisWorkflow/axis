#!/usr/bin/env python3
"""Main-owned, immutable Team reservations; ordinary spending stays Team-local."""
import copy
import secrets
from types import SimpleNamespace


def admit(store, value):
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    if 'budget' not in value.get('limits',{}) or store._proposal_control is not None:return value
    store.require_main() if store._proposal_control is None else store._control_guard()
    value=copy.deepcopy(value);grant=c._native_policy(value['limits']['budget'],store.now())
    pool=c._native_policy(value.pop('resource_pool',grant),store.now())
    c.need(grant['clock_start']==pool['clock_start'],'allocation-clock-reset')
    c.need(grant['routes']==pool['routes'],'allocation-route-conflict')
    if 'runtime_seconds' in pool:c.need('runtime_seconds' in grant and grant['runtime_seconds']<=pool['runtime_seconds'],'allocation-runtime')
    amount=grant.get('money',{}).get('ceiling_minor',0);ceiling=pool.get('money',{}).get('ceiling_minor')
    if ceiling is not None:
        c.need(grant.get('money',{}).get('currency')==pool['money']['currency'],'allocation-currency')
    configured=store.io.setting('Max Concurrent Sessions')
    capacity=int(configured) if str(configured).isdigit() and 1<=int(configured)<=100 else 10
    slots=value['limits'].get('concurrency',3);c._integer(slots,'allocation-slots',1,100)
    allocated=0;reserved_slots=0;predecessor=None
    records=store.records('Teams');messages=store.records('Messages')
    c.need(not any(t.get('resource_allocation') and t['limits']['budget']['key']==pool['key'] for t in records),'nested-Team-allocation-unavailable')
    for team in records:
        allocation=team.get('resource_allocation')
        if allocation:
            settlement=settled(store,team,messages)
            current=effective(store,team)
            reserved_slots+=0 if settlement else current['slots']
            if allocation['pool']['key']==pool['key']:
                c.need(allocation['pool']==pool,'allocation-pool-conflict')
                allocated+=settlement['known_minor'] if settlement else current['money_minor']
                predecessor=team['id']
        else:
            # Older charters keep their exact accounting; active/uncertain capacity
            # cannot be retroactively assumed free by a new allocation.
            state=store.project('Teams',team['id'])
            if state['held'] or state['state'] not in c.TERMINAL:reserved_slots+=team['limits']['concurrency']
    standalone=[]
    for job in store.records('Jobs'):
        if job.get('team'):continue
        state=store.project('Jobs',job['id'])
        c.need(not state['held'],'allocation-capacity-uncertain')
        standalone.extend(set(state.get('active',[]))|set(state.get('stop_unconfirmed',[])))
    c.need(reserved_slots+len(standalone)+slots<=max(0,capacity-1),'allocation-slots-exhausted')
    if ceiling is not None:c.need(allocated+amount<=ceiling,'allocation-money-exhausted')
    parent_records = [r for r in records+store.records('Jobs') if c._native(r) and r['limits']['budget']['key']==pool['key']]
    if parent_records:
        parent_state = store.native_budget_state(pool['key'])
        c.need(parent_state['policy']==pool,'allocation-pool-conflict')
        if ceiling is not None:c.need(parent_state['base_liability_minor']+allocated+amount<=ceiling,'allocation-money-exhausted')
    grant['key']=pool['key'][:80]+'.team.'+secrets.token_hex(12)
    value['limits']['budget']=grant
    value['resource_allocation']={'schema':1,'pool':pool,'money_minor':amount,'slots':slots,'predecessor':predecessor}
    return value


def settled(store,team,messages=None):
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    messages=store.records('Messages',team=team['id']) if messages is None else messages
    found=[m for m in messages if m.get('data',{}).get('allocation_settlement',{}).get('team')==team['id']]
    c.need(len(found)<=1,'allocation-settlement-fork')
    if not found:return None
    c._accepted(found[0]);value=found[0]['data']['allocation_settlement']
    c.need(value['grant_sha256']==c.digest(team.get('resource_allocation')) and type(value['known_minor']) is int and value['known_minor']>=0,'allocation-settlement-invalid')
    return value


def settlement(store,team_id,integrated=False):
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    store.require_main();store.require_placement();c.need(integrated is True,'Main-integration-required')
    team=store.read('Teams',team_id);view=store.project('Teams',team_id)
    c.need(team.get('resource_allocation') and not view['held'] and view['state'] in c.TERMINAL,'allocation-not-terminal')
    previous=settled(store,team)
    if previous:return {'status':'settled','settlement':previous}
    for job in store.records('Jobs'):
        if job.get('team')!=team_id:continue
        state=store.project('Jobs',job['id'])
        c.need(not state['held'] and state['state'] in c.TERMINAL and not state['active'] and not state['stop_unconfirmed'],'allocation-job-unsettled')
        c.need(not any(a.get('route_pending') or a.get('route_uncertain') for a in state['attempts'].values()),'allocation-physical-exit-unverified')
    budget=store.native_budget_state(team['limits']['budget']['key'])
    c.need(not budget['reserved_minor'] and not budget['uncertain_minor'] and not budget['unpriced_attempts'],'allocation-liability-unsettled')
    current=effective(store,team)
    known=budget['known_minor'];c.need(known<=current['money_minor'],'allocation-overspend')
    data={'team':team_id,'grant_sha256':c.digest(team['resource_allocation']),'known_minor':known,'released_minor':current['money_minor']-known,'released_slots':current['slots'],'allocation_head':current['head'],'integration_complete':True,'team_head':view['head']}
    return store._record('Messages',{'subject':'Team allocation settled after Main integration','kind':'control','recipient':'main','body':'Known charges retained; proven unused allowance and physical capacity released.','team':team_id,'job':None,'correlation':'allocation:'+team_id,'epoch':view['epoch'],'data':{'allocation_settlement':data},'authority':team['authority'],'expires':team['authority']['expires'],'attachments':[]})


def pool_key(store,record):
    if record.get('resource_allocation'):return record['resource_allocation']['pool']['key']
    if record.get('team'):
        charter=store.read('Teams',record['team'])
        if charter.get('resource_allocation'):return charter['resource_allocation']['pool']['key']
    return record['limits']['budget']['key']


def reserved_money(store,key,teams=None):
    total=0
    for team in store.records('Teams') if teams is None else teams:
        allocation=team.get('resource_allocation')
        if allocation and allocation['pool']['key']==key:
            close=settled(store,team)
            total+=close['known_minor'] if close else effective(store,team)['money_minor']
    return total


def effective(store,team):
    """Follow one accepted revision chain; timestamps never select a winning fork."""
    c=SimpleNamespace(**store.create_team.__func__.__globals__)
    grant=team.get('resource_allocation')
    c.need(grant,'allocation-required')
    value={'money_minor':grant['money_minor'],'slots':grant['slots']};head=team['id']
    messages=store.records('Messages',team=team['id'])
    revisions=[m for m in messages if m.get('data',{}).get('allocation_revision',{}).get('team')==team['id']]
    used=set();closed_freezes=set()
    while True:
        children=[m for m in revisions if m['data']['allocation_revision']['predecessor']==head]
        if not children:break
        c.need(len(children)==1,'allocation-revision-fork');message=children[0];c._accepted(message);v=message['data']['allocation_revision']
        c.need(v['grant_sha256']==c.digest(grant) and v['previous']==value and message['id'] not in used,'allocation-revision-binding')
        c.need(message['authority']==team['authority'],'allocation-revision-authority')
        for key in ('money_minor','slots'):c._integer(v['total'][key],'allocation-revision-value',0,10**12 if key=='money_minor' else 100)
        if v.get('freeze'):closed_freezes.add(v['freeze'])
        value=copy.deepcopy(v['total']);head=message['id'];used.add(head)
    c.need(len(used)==len(revisions),'allocation-revision-gap')
    freezes=[m for m in messages if m.get('data',{}).get('allocation_freeze',{}).get('team')==team['id'] and m['id'] not in closed_freezes]
    for m in freezes:
        c._accepted(m);c.need(m['data']['allocation_freeze']['predecessor']==head,'allocation-freeze-predecessor')
    c.need(len(freezes)<=1,'allocation-freeze-fork')
    return dict(value,head=head,freeze=freezes[0]['id'] if freezes else None)


def freeze(store,team_id,operation):
    c=SimpleNamespace(**store.create_team.__func__.__globals__);c._attempt_token(operation)
    team=store.read('Teams',team_id);c.need(not settled(store,team),'allocation-already-settled')
    view=effective(store,team)
    if view['freeze']:
        prior=store.read('Messages',view['freeze'])
        c.need(prior['data']['allocation_freeze']['operation']==operation,'allocation-freeze-conflict')
        return {'status':'duplicate','id':prior['id']}
    return store._record('Messages',{'subject':'Team grant frozen for Main resource review','kind':'control','recipient':'main','body':'New Team effects stop; existing liabilities and physical holders remain until reconciled.','team':team_id,'job':None,'correlation':'allocation:'+team_id,'epoch':0,'data':{'allocation_freeze':{'team':team_id,'predecessor':view['head'],'operation':operation}},'authority':team['authority'],'expires':team['authority']['expires'],'attachments':[]})


def revise(store,team_id,predecessor,money_minor,slots,operation,source_release=None):
    """Main dispatcher owns pool admission; a second guard excludes this Team only."""
    c=SimpleNamespace(**store.create_team.__func__.__globals__);c._attempt_token(operation)
    team=store.read('Teams',team_id);c.need(not settled(store,team),'allocation-already-settled')
    grant=team['resource_allocation'];view=effective(store,team)
    total={'money_minor':money_minor,'slots':slots}
    for key in total:c._integer(total[key],'allocation-revision-value',0,10**12 if key=='money_minor' else 100)
    prior=[m for m in store.records('Messages',team=team_id) if m.get('data',{}).get('allocation_revision',{}).get('operation')==operation]
    if prior:
        c.need(len(prior)==1 and prior[0]['data']['allocation_revision']['total']==total and prior[0]['data']['allocation_revision']['predecessor']==predecessor and prior[0]['data']['allocation_revision'].get('source_release')==source_release,'allocation-operation-conflict')
        return {'status':'duplicate','id':prior[0]['id']}
    c.need(view['head']==predecessor,'allocation-stale-predecessor')
    c.need(slots<=team['limits']['concurrency'],'allocation-charter-slot-ceiling')
    budget=store.native_budget_state(team['limits']['budget']['key'])
    reduction=money_minor<view['money_minor'] or slots<view['slots']
    if reduction:
        c.need(view['freeze'],'allocation-freeze-required')
        for job in store.records('Jobs'):
            if job.get('team')!=team_id:continue
            state=store.project('Jobs',job['id'])
            c.need(not state['held'] and state['state'] in c.TERMINAL|{'paused'} and not state['active'] and not state['stop_unconfirmed'],'allocation-source-not-quiescent')
            c.need(not any(a.get('route_pending') or a.get('route_uncertain') for a in state['attempts'].values()),'allocation-source-physical-uncertainty')
        c.need(not budget['reserved_minor'] and not budget['uncertain_minor'] and not budget['unpriced_attempts'],'allocation-source-liability')
    c.need(money_minor>=budget['base_liability_minor'],'allocation-below-liability')
    teams=store.records('Teams');money=0;reserved_slots=0
    for other in teams:
        a=other.get('resource_allocation')
        if not a:
            state=store.project('Teams',other['id'])
            if state['held'] or state['state'] not in c.TERMINAL:reserved_slots+=other['limits']['concurrency']
            continue
        end=settled(store,other);current=effective(store,other)
        reserved_slots+=0 if end else slots if other['id']==team_id else current['slots']
        if a['pool']['key']==grant['pool']['key']:
            c.need(a['pool']==grant['pool'],'allocation-pool-conflict')
            money+=end['known_minor'] if end else money_minor if other['id']==team_id else current['money_minor']
    standalone=0
    for job in store.records('Jobs'):
        if job.get('team'):continue
        state=store.project('Jobs',job['id']);c.need(not state['held'],'allocation-capacity-uncertain')
        standalone+=len(set(state['active'])|set(state['stop_unconfirmed'])|{a for a,v in state['attempts'].items() if v.get('route_pending')})
    configured=store.io.setting('Max Concurrent Sessions');capacity=int(configured) if str(configured).isdigit() and 1<=int(configured)<=100 else 10
    c.need(reserved_slots+standalone<=capacity-1,'allocation-slots-exhausted')
    key=grant['pool']['key']
    parent=[r for r in teams+store.records('Jobs') if c._native(r) and r['limits']['budget']['key']==key]
    if parent:money+=store.native_budget_state(key)['base_liability_minor']
    ceiling=grant['pool'].get('money',{}).get('ceiling_minor')
    if ceiling is not None:c.need(money<=ceiling,'allocation-money-exhausted')
    if source_release:
        source=store.read('Messages',source_release);c._accepted(source);r=source.get('data',{}).get('allocation_revision',{})
        source_team=store.read('Teams',r.get('team'))
        c.need(source_team['resource_allocation']['pool']==grant['pool'] and r['previous']['money_minor']>=r['total']['money_minor'] and r['previous']['slots']>=r['total']['slots'],'allocation-source-release')
    revision={'team':team_id,'grant_sha256':c.digest(grant),'predecessor':view['head'],'previous':{k:view[k] for k in total},'total':total,'freeze':view['freeze'],'operation':operation,'source_release':source_release}
    return store._record('Messages',{'subject':'Main revised an independent Team allocation','kind':'control','recipient':'main','body':'Pool conservation checked; original clock, spending and authority retained. Source release precedes any destination increase.','team':team_id,'job':None,'correlation':'allocation:'+team_id,'epoch':0,'data':{'allocation_revision':revision},'authority':team['authority'],'expires':team['authority']['expires'],'attachments':[]})


def pool_totals(store,key,teams):
    known=reserved=0
    for team in teams:
        allocation=team.get('resource_allocation')
        if not allocation or allocation['pool']['key']!=key:continue
        close=settled(store,team)
        if close:known+=close['known_minor']
        else:reserved+=effective(store,team)['money_minor']
    return known,reserved
