#!/usr/bin/env python3
"""Opt-in canonical Team closing. No process, capacity, billing or content acceptance."""
import copy
import importlib.util
from pathlib import Path
import sys

PROTOCOL = 'axis.closing/v1'

class ClosingError(ValueError):
    pass

def need(value, reason):
    if not value: raise ClosingError(reason)

def core():
    name = 'axis_closing_core'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name('coordination.py'))
        module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    return sys.modules[name]

def tag(record):
    value = record.get('data', {}).get('closing')
    return value if isinstance(value, dict) else {}

def artifact(store, team, view, value):
    need(isinstance(value, dict) and set(value) == {'slot', 'revision'}, 'closing-artifact')
    checked = store.artifact_check(team, value['slot'], value['revision'], _view=view)
    manifest = checked['manifest']
    need(type(manifest.get('schema')) is int and manifest['schema'] == 1, 'closing-artifact-schema')
    return checked['attachment'], manifest

def artifact_ref(store, team, view, ref):
    need(isinstance(ref, dict) and isinstance(ref.get('path'), str), 'closing-artifact-reference')
    parts = ref['path'].split('/')
    need(len(parts) == 8 and parts[:3] == ['_Axis','Teams',team] and parts[3] == 'members' and parts[5] == 'artifacts' and parts[7] == '_artifact.json', 'closing-artifact-reference')
    actual, manifest = artifact(store, team, view, {'slot':parts[4], 'revision':parts[6]})
    need(actual == ref, 'closing-artifact-changed')
    return manifest

def _contract(store, contract_id, historical=False):
    c = core(); store.require_history(); record = store.read('Messages', c.identity(contract_id)); value = tag(record)
    need(value.get('protocol') == PROTOCOL and value.get('action') == 'contract' and record['kind'] == 'control' and 'event' not in record, 'closing-contract')
    c._accepted(record)
    team = store.read('Teams', record['team']); job = store.read('Jobs', record['job'])
    tv = store.project('Teams', team['id']); jv = store.project('Jobs', job['id'])
    need(not tv['held'] and not jv['held'], 'closing-held')
    need(job.get('team') == team['id'] and team['acceptance_owner'] == job['acceptance_owner'] == record['issuer']['session'], 'closing-owner')
    need(record.get('authority') == job['authority'] and value.get('team_authority') == team['authority'], 'closing-authority-binding')
    need(type(value.get('team_epoch')) is int and type(record.get('epoch')) is int and value['team_epoch'] >= 0 and record['epoch'] >= 0, 'closing-epoch-shape')
    need(historical or (value['team_epoch'] == tv['epoch'] and record['epoch'] == jv['epoch']), 'closing-stale-epoch')
    required={'protocol','action','actors','participants','release_slot','final_slot','require_ack','phase','team_epoch','team_authority','supersedes'}
    need(required<=set(value)<=required|{'planned'} and isinstance(value.get('phase'),str) and 0<len(value['phase'].strip())<=256,'closing-contract-shape')
    need(record.get('correlation')=='closing:'+job['id'] and record.get('expires')==job['authority']['expires'],'closing-contract-binding')
    actors = value.get('actors'); participants = value.get('participants')
    need(isinstance(actors, dict) and isinstance(participants, list) and participants and len(set(participants)) == len(participants), 'closing-participants')
    need(isinstance(value.get('release_slot'), str) and value['release_slot'] in actors and set(actors) == set(participants)|{value['release_slot']}, 'closing-release-owner')
    need(type(value.get('require_ack')) is bool and value.get('final_slot') in tv['members'], 'closing-contract-shape')
    need(type(value.get('planned',False)) is bool,'closing-planned-shape')
    for slot, actor in actors.items():
        need(isinstance(actor, dict) and set(actor) == {'session','attempt','epoch'}, 'closing-actor')
        need(type(actor['epoch']) is int and actor['epoch']==record['epoch'],'closing-actor-epoch');c.identity(actor['session']);c._attempt_token(actor['attempt'])
        need(historical or actor['session']==tv['members'].get(slot,{}).get('session'),'closing-current-actor')
        item = jv['attempts'].get(actor['attempt'], {})
        if not item:
            need(value.get('planned') is True,'closing-attempt-unbound')
            continue
        need(type(actor['epoch']) is int and actor['epoch'] == record['epoch'] and item.get('epoch') == actor['epoch'] and item.get('team_epoch') == value['team_epoch'], 'closing-attempt-epoch')
        need(item.get('slot') == slot and item.get('session') == actor['session'], 'closing-actor-binding')
        need(historical or actor['session'] == tv['members'].get(slot,{}).get('session'), 'closing-current-actor')
    return record, value, team, job, tv, jv

def project(store, contract_id, *, historical=False):
    """Replay canonical closing records; malformed/conflicting state refuses closed."""
    c=core(); need(not historical or store.io.lease[2], 'closing-history-main-only'); record, contract, team, job, tv, jv = _contract(store, contract_id, historical)
    members={slot:{'ready':None,'release':None,'ack':None,'result':None,'done':None,'state':'participating' if contract['actors'][slot]['attempt'] in jv['attempts'] else 'awaiting-dispatch'} for slot in contract['participants']}
    by_id={}; rows=[]
    messages=store.records('Messages',team=team['id'])
    for message in messages:
        if message.get('data',{}).get('protocol') == 'axis.team-route/v1': continue
        data=tag(message)
        if data.get('protocol') == PROTOCOL and data.get('action') == 'contract' and data.get('supersedes') == contract_id:
            c._accepted(message); need(False,'closing-contract-superseded')
        if data.get('contract') != contract_id: continue
        need(data.get('protocol') == PROTOCOL, 'closing-protocol')
        need(message.get('team') == team['id'] and message.get('job') == job['id'] and message['epoch'] == record['epoch'] and message.get('correlation') == contract_id, 'closing-message-binding')
        slot=message.get('delivery',{}).get('sender_slot'); actor=contract['actors'].get(slot,{})
        need(actor and actor['attempt'] in jv['attempts'] and message['issuer']['role']=='worker' and message['issuer']['session']==actor['session'] and message['data'].get('attempt')==actor['attempt'], 'closing-message-owner')
        need(message['delivery'].get('team_epoch')==contract['team_epoch'], 'closing-message-epoch')
        need(c.timestamp(message['created'])>c.timestamp(record['created']), 'closing-message-order')
        action=data.get('action'); need(action in {'ready','release','ack','result','done'}, 'closing-action')
        expected={'ready':{'artifact'},'release':{'artifact','targets','ready'},'ack':{'release'},'result':{'release','artifact'},'done':{'result','tracking'}}
        need(set(data)=={'protocol','contract','action'}|expected[action], 'closing-action-shape')
        state=members.get(slot)
        if action=='release':
            need(slot==contract['release_slot'] and message['kind']=='offer' and message['recipient']=='team', 'closing-release-owner')
            targets=data.get('targets'); need(isinstance(targets,list) and targets and len(set(targets))==len(targets) and set(targets)<=set(members), 'closing-release-targets')
            manifest=artifact_ref(store,team['id'],tv,data.get('artifact'));need(manifest['slot']==contract['final_slot'],'closing-final-owner')
            need(isinstance(data.get('ready'),dict) and set(data['ready'])==set(targets),'closing-ready-proof')
            for target in targets:
                need({'slot':target,'session':contract['actors'][target]['session']} in message['delivery'].get('recipients',[]),'closing-release-delivery')
                entry=members[target];need(entry['release'] is None and entry['ready']==data['ready'][target], 'closing-ready-proof')
                need(entry['ready'] in by_id and tag(by_id[entry['ready']]).get('artifact')==data['artifact'], 'closing-final-revision')
                entry['release']=message['id'];entry['state']='released'
        else:
            need(state is not None and state['done'] is None,'closing-participation-ended')
            if action=='ready':
                need(message['kind']=='offer' and message['recipient']==contract['release_slot'] and state['release'] is None,'closing-ready-state')
                manifest=artifact_ref(store,team['id'],tv,data.get('artifact'));need(manifest['slot']==contract['final_slot'],'closing-final-owner')
                state['ready']=message['id'];state['state']='report-ready'
            elif action=='ack':
                need(contract['require_ack'] and message['kind']=='receipt' and message['recipient']==contract['release_slot'],'closing-ack')
                need(state['release'] is not None and data.get('release')==state['release'] and state['ack'] is None,'closing-release-proof')
                state['ack']=message['id'];state['state']='release-observed'
            elif action=='result':
                need(message['kind']=='result' and message['recipient']=='main' and state['result'] is None,'closing-result')
                need(state['release'] is not None and data.get('release')==state['release'] and (not contract['require_ack'] or state['ack'] is not None),'closing-release-proof')
                manifest=artifact_ref(store,team['id'],tv,data.get('artifact'))
                need(manifest['slot']==slot and manifest['session']==actor['session'] and manifest['job']==job['id'] and manifest['attempt']==actor['attempt'],'closing-result-artifact')
                state['result']=message['id'];state['state']='result-recorded'
            else:
                need(message['kind']=='receipt' and message['recipient']=='main' and state['result'] is not None and data.get('result')==state['result'],'closing-done-order')
                tracking=data.get('tracking');need(isinstance(tracking,dict) and tracking.get('path')=='_Axis/Tracking/'+actor['session']+'.md' and tracking.get('type')=='DONE','closing-tracking')
                tracked=c.timestamp(tracking.get('timestamp'));need(c.timestamp(by_id[state['result']]['created']) <= tracked <= c.timestamp(message['created']), 'closing-tracking-order')
                line=tracking['timestamp']+' - '+actor['session']+' - DONE [closing '+contract_id+'] Result '+state['result']+'\n'
                need(line in store.io.read(tracking['path']).splitlines(keepends=True),'closing-tracking-proof')
                state['done']=message['id'];state['state']='done-awaiting-terminal'
        if action!='release':
            recipient=contract['release_slot'] if action in {'ready','ack'} else 'main'
            recipient_session=contract['actors'][recipient]['session'] if recipient!='main' else record['issuer']['session']
            need(message['delivery'].get('recipients')==[{'slot':recipient,'session':recipient_session}],'closing-delivery')
        if action in {'ready','release','result'}:
            attempt=jv['attempts'].get(manifest.get('attempt'),{})
            need(manifest.get('job')==job['id'] and type(manifest.get('epoch')) is int and manifest['epoch']==record['epoch'] and type(manifest.get('team_epoch')) is int and manifest['team_epoch']==contract['team_epoch'] and manifest.get('session')==attempt.get('session') and manifest.get('slot')==attempt.get('slot'),'closing-artifact-attempt')
        need(message.get('attachments')==([data['artifact']] if action in {'ready','release','result'} else []),'closing-attachments')
        by_id[message['id']]=message;rows.append(message)
    terminals={}
    for message in messages:
        data=message.get('data',{}); facts=data.get('closing')
        if data.get('protocol')!='axis.team-route/v1' or data.get('stage')!='result' or not isinstance(facts,dict) or facts.get('contract')!=contract_id: continue
        if message.get('issuer',{}).get('role')!='main': continue
        c._accepted(message)
        need(message.get('team')==team['id'] and message.get('epoch')==record['epoch'] and message['issuer']['session']==record['issuer']['session'] and message['kind']=='result' and message['recipient']=='main' and message.get('job')==job['id']==data.get('job'), 'closing-terminal-owner')
        actor_slots=[slot for slot,actor in contract['actors'].items() if actor['attempt']==data.get('attempt')]
        need(len(actor_slots)==1 and actor_slots[0] in members,'closing-terminal-attempt');slot=actor_slots[0]
        need(slot not in terminals,'closing-terminal-ambiguous')
        intent=store.read('Messages',c.identity(data.get('intent')));c._accepted(intent);intent_data=intent.get('data',{})
        need(intent.get('team')==team['id'] and intent.get('job')==job['id'] and intent.get('epoch')==record['epoch'] and intent['kind']=='control' and intent['recipient']=='main' and intent['issuer']['session']==record['issuer']['session'] and intent_data.get('protocol')=='axis.team-route/v1' and intent_data.get('stage')=='intent' and intent_data.get('closing_contract')==contract_id and intent_data.get('job')==job['id'] and intent_data.get('attempt')==data['attempt'],'closing-terminal-intent')
        ended=c.timestamp(data.get('ended_at'));need(c.timestamp(intent['created'])<=ended<=c.timestamp(message['created']),'closing-terminal-time')
        state=members[slot];done=by_id.get(state['done']);expected_facts={'validated':True,'released':state['release'] is not None and ended>=c.timestamp(by_id[state['release']]['created']),'result':state['result'] is not None and ended>=c.timestamp(by_id[state['result']]['created']),'done':done is not None and ended>=c.timestamp(done['created']),'contract':contract_id,'job':job['id'],'attempt':data['attempt'],'capacity_released':False}
        need(facts==expected_facts,'closing-terminal-facts')
        process=data.get('process');need(isinstance(process,dict),'closing-terminal-process')
        confirmed=process.get('execution_terminal') is True
        if confirmed:need(process.get('leader_terminal') is True and process.get('group_terminal') is True and type(process.get('returncode')) is int,'closing-terminal-proof')
        if process.get('outcome')=='graceful-return':need(confirmed and process['returncode']==0 and process.get('reason') is None and all(facts[k] for k in ('released','result','done')) and not any(sig.get('outcome')=='sent' for sig in process.get('signals',[])),'closing-graceful-proof')
        terminals[slot]={'message':message['id'],'outcome':process.get('outcome'),'execution_terminal':confirmed,'ended_at':data['ended_at']}
        state['terminal']=terminals[slot]
        if done is not None and confirmed and process.get('outcome')=='graceful-return':state['state']='closed'
    # Later physical-boundary proof is append-only and preserves original return time.
    for message in messages:
        data=message.get('data',{})
        if data.get('protocol')!='axis.team-route/v1' or data.get('stage')!='terminal-observation': continue
        if message.get('issuer',{}).get('role')!='main': continue
        if data.get('job')!=job['id'] and message.get('job')!=job['id']: continue
        intent=store.read('Messages',c.identity(data.get('intent')));intent_data=intent.get('data',{})
        if intent_data.get('closing_contract')!=contract_id: continue
        c._accepted(intent);c._accepted(message)
        need(message.get('team')==team['id'] and message.get('epoch')==record['epoch'] and message['issuer']['session']==record['issuer']['session']==intent['issuer']['session'] and message['kind']=='result' and message['recipient']=='main' and message.get('job')==job['id']==data.get('job'),'closing-terminal-owner')
        actor_slots=[slot for slot,actor in contract['actors'].items() if actor['attempt']==data.get('attempt')]
        need(len(actor_slots)==1 and actor_slots[0] in members,'closing-terminal-attempt');slot=actor_slots[0]
        need(intent.get('team')==team['id'] and intent.get('job')==job['id'] and intent.get('epoch')==record['epoch'] and intent['kind']=='control' and intent['recipient']=='main' and intent_data.get('protocol')=='axis.team-route/v1' and intent_data.get('stage')=='intent' and intent_data.get('job')==job['id'] and intent_data.get('attempt')==data['attempt'] and intent_data.get('request_sha256')==data.get('request_sha256'),'closing-terminal-intent')
        original=store.read('Messages',c.identity(data.get('route_result')));c._accepted(original);original_data=original.get('data',{})
        need(original.get('team')==team['id'] and original.get('epoch')==record['epoch'] and original['issuer']['session']==record['issuer']['session'] and original['kind']=='result' and original['recipient']=='main' and original.get('job')==job['id'] and original_data.get('protocol')=='axis.team-route/v1' and original_data.get('stage')=='result' and original_data.get('intent')==intent['id'] and original_data.get('job')==job['id'] and original_data.get('attempt')==data['attempt'],'closing-terminal-predecessor')
        need(slot not in terminals or terminals[slot]['message']==original['id'],'closing-terminal-ambiguous')
        need(data.get('ended_at')==original_data.get('ended_at'),'closing-terminal-time-substitution')
        observed=c.timestamp(data.get('observed_at'));need(c.timestamp(intent['created'])<=observed<=c.timestamp(message['created']),'closing-terminal-observation-time')
        boundary=data.get('boundary');need(isinstance(boundary,dict) and boundary.get('verified') is True and boundary.get('group_terminal') is True and isinstance(boundary.get('evidence'),str) and boundary['evidence'].strip() and boundary.get('intent')==intent['id'] and boundary.get('request_sha256')==intent_data['request_sha256'] and boundary.get('result')==data.get('requested_result'),'closing-terminal-boundary')
        need(data.get('requested_result')==original['id'] or (data.get('requested_result') is None and original_data.get('recovery_observation') is True),'closing-terminal-boundary-result')
        state=members[slot];done=by_id.get(state['done']);ended_value=data.get('ended_at')
        if ended_value is None:
            need(original_data.get('recovery_observation') is True and data.get('closing') is None,'closing-interrupted-unknown')
            facts=None
        else:
            ended=c.timestamp(ended_value);need(c.timestamp(intent['created'])<=ended<=c.timestamp(original['created']) and ended<=observed,'closing-terminal-time')
            facts={'validated':True,'released':state['release'] is not None and ended>=c.timestamp(by_id[state['release']]['created']),'result':state['result'] is not None and ended>=c.timestamp(by_id[state['result']]['created']),'done':done is not None and ended>=c.timestamp(done['created']),'contract':contract_id,'job':job['id'],'attempt':data['attempt'],'capacity_released':False}
            need(data.get('closing')==facts,'closing-terminal-facts')
        process=data.get('process');previous=original_data.get('process');need(isinstance(process,dict) and isinstance(previous,dict),'closing-terminal-process')
        need(all(process.get(k)==previous.get(k) for k in ('returncode','reason','signals','cleanup_errors')),'closing-terminal-outcome-substitution')
        need(process.get('group_terminal') is True,'closing-terminal-proof')
        confirmed=process.get('execution_terminal') is True
        if confirmed:need(previous.get('leader_terminal') is True and process.get('leader_terminal') is True and type(process.get('returncode')) is int,'closing-terminal-proof')
        if process.get('outcome')=='graceful-return':need(confirmed and ended_value is not None and process['returncode']==0 and process.get('reason') is None and facts is not None and all(facts[k] for k in ('released','result','done')) and not any(sig.get('outcome')=='sent' for sig in process.get('signals',[])) and not process.get('cleanup_errors'),'closing-graceful-proof')
        if ended_value is None:need(not confirmed and process.get('outcome')!='graceful-return','closing-interrupted-unknown')
        terminals[slot]={'message':message['id'],'route_result':original['id'],'outcome':process.get('outcome'),'execution_terminal':confirmed,'group_terminal':True,'ended_at':ended_value,'observed_at':data['observed_at']}
        state['terminal']=terminals[slot]
        if done is not None and confirmed and process.get('outcome')=='graceful-return':state['state']='closed'
        elif done is not None and ended_value is None:state['state']='done-terminal-outcome-unknown'
    store.guard()
    return {'contract':contract_id,'team':team['id'],'job':job['id'],'epoch':record['epoch'],'team_epoch':contract['team_epoch'],
            'actors':copy.deepcopy(contract['actors']),'members':members,'release_slot':contract['release_slot'],
            'require_ack':contract['require_ack'],'final_slot':contract['final_slot'],'records':rows,
            'capacity_released':False,'notice':'Closing is not process termination or substantive acceptance.'}

def validate_binding(store, contract_id, binding=None, *, job=None, attempt=None):
    value=project(store,contract_id)
    if binding is not None:
        need(isinstance(binding,dict) and set(binding)=={'team','job','attempt','epoch'},'closing-binding')
        need(binding['team']==value['team'] and binding['job']==value['job'] and type(binding['epoch']) is int and binding['epoch']==value['epoch'],'closing-binding')
        job=binding['job'];attempt=binding['attempt']
    need(job==value['job'],'closing-binding')
    slots=[slot for slot,actor in value['actors'].items() if actor['attempt']==attempt]
    need(len(slots)==1,'closing-binding');slot=slots[0]
    need(attempt in store.project('Jobs',job)['attempts'],'closing-attempt-unbound')
    need(store.io.lease[2] or value['actors'][slot]['session']==store.session,'closing-binding')
    value['slot']=slot;return value

def create_contract(store, *, team, job, participants, release_slot, final_slot, require_ack, phase, supersedes=None, attempts=None):
    c=core();store.require_main();store.require_placement()
    need(isinstance(participants,list) and participants and all(isinstance(x,str) for x in participants) and len(set(participants))==len(participants),'closing-participants')
    need(type(require_ack) is bool and isinstance(phase,str) and 0<len(phase.strip())<=256,'closing-policy')
    with store.locked(team=team):
        store.require_history();t=store.read('Teams',team);j=store.read('Jobs',job);tv=store.project('Teams',team);jv=store.project('Jobs',job)
        need(j.get('team')==team and store.session==t['acceptance_owner']==j['acceptance_owner'],'closing-owner')
        need(not tv['held'] and not jv['held'] and tv['state'] in {'ready','running'} and jv['state'] in {'admitted','running'},'closing-unavailable')
        store.validate_authority(t['authority']);store.validate_authority(j['authority'])
        need(set(participants)|{release_slot,final_slot}<=set(tv['members']),'closing-slots')
        actors={};slots=set(participants)|{release_slot}
        need(attempts is None or (isinstance(attempts,dict) and set(attempts)==slots and all(isinstance(a,str) for a in attempts.values()) and len(set(attempts.values()))==len(attempts)), 'closing-planned-attempts')
        for slot in slots:
            if attempts is not None:
                aid=attempts[slot];c._attempt_token(aid);need(aid not in jv['attempts'],'closing-planned-attempt-exists')
                session=tv['members'][slot].get('session');need(session is not None,'closing-unbound-member')
                store._worker_session(session);actors[slot]={'session':session,'attempt':aid,'epoch':jv['epoch']}
            else:
                available=[(aid,a) for aid,a in jv['attempts'].items() if a.get('slot')==slot and a.get('epoch')==jv['epoch'] and a.get('team_epoch')==tv['epoch'] and a.get('status') in {'dispatch-intent','received','result','validated'}]
                need(len(available)==1,'closing-attempt-binding');aid,a=available[0];actors[slot]={'session':a['session'],'attempt':aid,'epoch':a['epoch']}
        existing=[m for m in store.records('Messages') if m.get('job')==job and tag(m).get('protocol')==PROTOCOL and tag(m).get('action')=='contract']
        need((not existing and supersedes is None) or (existing and supersedes==existing[-1]['id']),'closing-contract-predecessor')
        if supersedes is not None:
            prior=project(store,supersedes,historical=True);need(not any(m['release'] for m in prior['members'].values()),'closing-already-released')
        data={'protocol':PROTOCOL,'action':'contract','actors':actors,'participants':sorted(participants),'release_slot':release_slot,'final_slot':final_slot,'require_ack':require_ack,'phase':phase,'team_epoch':tv['epoch'],'team_authority':t['authority'],'supersedes':supersedes,'planned':attempts is not None}
        return store._record('Messages',{'subject':'Selected Team closing contract','kind':'control','recipient':'team','body':'Selected closing obligations; no new execution or spending authority.','team':team,'job':job,'correlation':'closing:'+job,'epoch':jv['epoch'],'data':{'closing':data},'expires':j['authority']['expires'],'authority':j['authority'],'attachments':[],'delivery':dict(store._route(team,'team'),sender_slot='main')})

def step(store, *, contract_id, binding, action, body, targets=None, artifact=None, release_id=None):
    c=core();need(action in {'ready','release','ack','result','done'} and isinstance(body,str) and body.strip() and len(body.encode())<=c.MAX_BODY,'closing-step')
    need(targets is None or isinstance(targets,list),'closing-targets')
    with store.locked(worker=True, team=binding['team']):
        charter,tv,job,jv,item=store._direct_context(**binding)
        view=validate_binding(store,contract_id,binding);slot=view['slot'];state=view['members'].get(slot)
        data={'protocol':PROTOCOL,'contract':contract_id,'action':action};attachments=[]
        if action in {'ready','release','result'}:
            ref,manifest=globals()['artifact'](store,binding['team'],tv,artifact);data['artifact']=ref;attachments=[ref]
            source_attempt=jv['attempts'].get(manifest.get('attempt'),{});need(manifest.get('job')==binding['job'] and type(manifest.get('epoch')) is int and manifest['epoch']==binding['epoch'] and type(manifest.get('team_epoch')) is int and manifest['team_epoch']==tv['epoch'] and manifest.get('session')==source_attempt.get('session') and manifest.get('slot')==source_attempt.get('slot'),'closing-artifact-attempt')
        else:need(artifact is None,'closing-unused-argument')
        if action=='release':
            need(slot==view['release_slot'] and targets and all(isinstance(x,str) for x in targets) and len(set(targets))==len(targets) and set(targets)<=set(view['members']),'closing-release-targets')
            data['targets']=sorted(targets);data['ready']={target:view['members'][target]['ready'] for target in targets};recipient='team';kind='offer'
        else:
            need(not targets,'closing-unused-argument');need(state is not None,'closing-not-participant')
            recipient=view['release_slot'] if action in {'ready','ack'} else 'main';kind={'ready':'offer','ack':'receipt','result':'result','done':'receipt'}[action]
        if action in {'ack','result'}:data['release']=release_id
        else:need(release_id is None,'closing-unused-argument')
        # Exact retry returns the retained act; changed payload is never a reset.
        same=[m for m in view['records'] if m['issuer']['session']==store.session and tag(m).get('action')==action]
        comparable=lambda d:{k:v for k,v in d.items() if k not in {'tracking','result'}}
        for prior in reversed(same):
            if comparable(tag(prior))==data and prior['body']==body:
                return {'status':'duplicate','id':prior['id'],'record':prior}
        need(state is None or state['done'] is None,'closing-participation-ended')
        if action=='ready':need(state['release'] is None and manifest['slot']==view['final_slot'],'closing-ready-state')
        elif action=='release':
            need(manifest['slot']==view['final_slot'],'closing-final-owner')
            for target in targets:
                row=view['members'][target];need(row['release'] is None and row['ready'] is not None,'closing-ready-proof')
                ready=next(m for m in view['records'] if m['id']==row['ready']);need(tag(ready)['artifact']==data['artifact'],'closing-final-revision')
        elif action=='ack':need(view['require_ack'] and state['release']==release_id and release_id is not None and state['ack'] is None,'closing-release-proof')
        elif action=='result':
            need(state['release']==release_id and release_id is not None and (not view['require_ack'] or state['ack']) and state['result'] is None,'closing-release-proof')
            need(manifest['slot']==slot and manifest['job']==binding['job'] and manifest['attempt']==binding['attempt'] and manifest['session']==store.session,'closing-result-artifact')
        else:
            need(state['result'] is not None,'closing-done-order');data['result']=state['result']
            path='_Axis/Tracking/'+store.session+'.md'
            text=store.io.read(path,optional=True) or ''
            suffix=' - '+store.session+' - DONE [closing '+contract_id+'] Result '+state['result']
            result_record=next(m for m in view['records'] if m['id']==state['result'])
            matches=[line[:-len(suffix)] for line in text.splitlines() if line.endswith(suffix)]
            need(len(matches)<=1,'closing-tracking-ambiguous')
            if matches:
                need(c.timestamp(matches[0])>=c.timestamp(result_record['created']),'closing-tracking-order')
                data['tracking']={'status':'appended','path':path,'timestamp':matches[0],'type':'DONE'}
            else:
                data['tracking']=store.io.track('DONE','closing '+contract_id,'Result '+state['result'])
        history=store.records('Messages');need(c._native(charter) or sum(m['issuer']['session']==store.session and m.get('team')==binding['team'] for m in history)<charter['collaboration']['max_messages_per_member'],'message-budget')
        store._check_lock();store._direct_context(**binding)
        payload={'subject':'Closing '+action,'kind':kind,'recipient':recipient,'body':body,'team':binding['team'],'job':binding['job'],'correlation':contract_id,'epoch':binding['epoch'],'data':{'attempt':binding['attempt'],'closing':data},'expires':min(charter['limits']['deadline'],job['limits']['deadline'],charter['authority']['expires'],job['authority']['expires']),'authority':None,'attachments':store.validate_attachments(attachments),'delivery':dict(store._route(binding['team'],recipient),sender_slot=slot)}
        return store._record('Messages',payload,worker=True)

def observation(store, contract_id, job, attempt, ended_at):
    c=core();view=validate_binding(store,contract_id,job=job,attempt=attempt);state=view['members'].get(view['slot'])
    need(state is not None,'closing-not-participant');ended=c.timestamp(ended_at)
    done=next((m for m in view['records'] if m['id']==state['done']),None)
    records={m['id']:m for m in view['records']}
    return {'validated':True,'released':state['release'] is not None and ended>=c.timestamp(records[state['release']]['created']),'result':state['result'] is not None and ended>=c.timestamp(records[state['result']]['created']),
            'done':done is not None and ended>=c.timestamp(done['created']),
            'contract':contract_id,'job':job,'attempt':attempt,'capacity_released':False}
