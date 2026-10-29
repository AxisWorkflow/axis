#!/usr/bin/env python3
"""Explicit included-route execution for an already dispatched native Job attempt.

A trusted host verifier is mandatory; documents cannot establish authentication or
provider availability. This helper never creates workers, retries an attempt, settles
billing, accepts results, or declares a Team complete. Manual routes remain available.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import stat
import inspect


def _module(name):
    spec=importlib.util.spec_from_file_location('axis_'+name.replace('-','_'),Path(__file__).with_name(name+'.py'))
    module=importlib.util.module_from_spec(spec);sys.modules[spec.name]=module;spec.loader.exec_module(module);return module


def request_digest(request):
    return hashlib.sha256(json.dumps(request,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


class RouteStop(ValueError):
    def __init__(self, reason):
        self.process_reason=reason;super().__init__(reason)


class OwnedCapture:
    """Fresh, bounded capture prefix; never resume or overwrite an old capture.

    Each observed chunk is fsynced before returning to the process loop. A host
    interruption can lose unread pipe bytes, but not a successfully synced prefix.
    The initial descriptor stays incomplete; a separate result receipt records
    the supervisor observation. No cleanup deletes evidence or replacement paths.
    """
    def __init__(self, store, intent, binding, activation):
        self.store, self.activation = store, activation
        self.relative = _module('message-paths').resolve(store.root,intent).with_suffix('').relative_to(store.root).as_posix()
        self.directory = store.path(self.relative, missing=True, kind='directory')
        self.files = {}; self.dir_fd = None; self.failed = False; self.failure = None
        try:
            self._lease(); self.directory.mkdir(mode=0o700)
            self.dir_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            info = os.fstat(self.dir_fd); self.identity = (info.st_dev, info.st_ino)
            for name in ('stdout.txt', 'stderr.txt'):
                self._create(name)
            self.write_metadata('capture.json', dict(binding, protocol='axis.team-route-capture/v1',
                intent=intent, session=store.session, status='incomplete',
                notice='Synced bounded prefix only; unread or truncated suffix and process outcome may be unknown.'))
            self._guard(); os.fsync(self.dir_fd)
            # Persist the newly created capture directory entry as well.
            parent = os.open(self.directory.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try: self._guard(); os.fsync(parent)
            finally: os.close(parent)
        except BaseException:
            self.close(); raise

    def _lease(self):
        self.store.require_placement(expected=self.activation)
        self.store.require_main(); self.store.guard()

    def _guard(self):
        if self.failed: raise ValueError('capture unavailable: ' + str(self.failure))
        try:
            self._lease()
            if self.store.path(self.relative, kind='directory') != self.directory:
                raise ValueError('capture directory changed')
            info = self.directory.lstat()
            if (not stat.S_ISDIR(info.st_mode) or stat.S_IMODE(info.st_mode) != 0o700 or
                info.st_uid != os.geteuid() or (info.st_dev, info.st_ino) != self.identity):
                raise ValueError('capture directory replaced')
            for name, item in self.files.items():
                held = os.fstat(item['fd']); named = (self.directory / name).lstat()
                if (not stat.S_ISREG(named.st_mode) or stat.S_IMODE(held.st_mode) != 0o600 or
                    held.st_uid != os.geteuid() or held.st_nlink != 1 or
                    (named.st_dev, named.st_ino) != (held.st_dev, held.st_ino) or held.st_size != item['size']):
                    raise ValueError('capture file ownership changed')
                raw = os.pread(item['fd'], item['size'] + 1, 0)
                if len(raw) != item['size'] or hashlib.sha256(raw).hexdigest() != item['hash'].hexdigest():
                    raise ValueError('capture prefix changed')
        except BaseException as exc:
            self.failed = True; self.failure = str(exc); raise

    def _create(self, name):
        self._guard()
        fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.dir_fd)
        self.files[name] = {'fd': fd, 'size': 0, 'hash': hashlib.sha256()}
        self._guard(); os.fsync(fd); os.fsync(self.dir_fd)

    def _append(self, name, raw):
        try:
            if not isinstance(raw, bytes): raise ValueError('capture bytes required')
            pending = memoryview(raw)
            while pending:
                self._guard(); item = self.files[name]
                written = os.write(item['fd'], pending)
                if written <= 0: raise OSError('capture short write')
                item['hash'].update(pending[:written]); item['size'] += written
                pending = pending[written:]
            self._guard(); os.fsync(self.files[name]['fd'])
        except BaseException as exc:
            self.failed = True; self.failure = str(exc); raise

    def append(self, channel, raw):
        if channel not in {'stdout', 'stderr'}: raise ValueError('capture channel')
        self._append(channel + '.txt', raw)

    def write_metadata(self, name, value):
        if name not in {'capture.json', 'launch.json', 'result.json'}: raise ValueError('capture metadata name')
        raw = (json.dumps(value, sort_keys=True, allow_nan=False) + '\n').encode()
        self._create(name); self._append(name, raw)
        self._guard(); os.fsync(self.dir_fd)

    def outputs(self):
        self._guard()
        return {name: {'path': self.relative + '/' + name + '.txt',
            'size': self.files[name + '.txt']['size'], 'sha256': self.files[name + '.txt']['hash'].hexdigest()}
            for name in ('stdout', 'stderr')}

    def close(self):
        for item in self.files.values():
            try: os.close(item['fd'])
            except OSError: pass
        self.files = {}
        if self.dir_fd is not None:
            try: os.close(self.dir_fd)
            except OSError: pass
            self.dir_fd = None

    def __enter__(self): return self
    def __exit__(self, *_): self.close()


def execute_native_attempt(store, job, attempt, *, request, verify_access, explicit=False, closing_contract=None):
    """Run one pinned request. dispatch.route_request_sha256 must bind its digest.

    request contains adapter, route, argv, cwd, prompt, executable_sha256 and
    output_bytes (capture capacity, not a spending/token budget). verify_access is
    trusted host code returning the same request_sha256 plus authenticated/included/
    available True and nonempty evidence, based on current actual route observations.
    Paid routes require the exact incremental reservation, explicit authority and fresh route evidence. No automatic fallback. Authoritative charge reports remain separate.
    Optional closing_contract is a canonical Main-owned contract, validated before
    launch and observed at actual process return; caller booleans cannot certify it.
    """
    intent=None;launched={};result=None;capture=None;result_message=None
    try:
        if explicit is not True or not callable(verify_access):raise ValueError('explicit execution and trusted route verifier required')
        if not isinstance(request,dict) or set(request)!={'adapter','route','argv','cwd','prompt','executable_sha256','output_bytes'}:raise ValueError('route request shape')
        req=json.loads(json.dumps(request,allow_nan=False));digest=request_digest(req)
        argv=req['argv'];cwd=Path(req['cwd'])
        if req['adapter'] not in {'codex','claude'} or not isinstance(argv,list) or not argv or not all(isinstance(x,str) and x and '\x00' not in x for x in argv):raise ValueError('route command')
        executable=Path(argv[0])
        if not executable.is_absolute() or executable.is_symlink() or not executable.is_file():raise ValueError('exact regular executable required')
        if not cwd.is_absolute() or cwd.resolve()!=cwd or not cwd.is_dir():raise ValueError('canonical working directory required')
        if not isinstance(req['prompt'],str) or type(req['output_bytes']) is not int or not 1024<=req['output_bytes']<=4*1024*1024:raise ValueError('invalid prompt or capture capacity')
        founding=store.read('Jobs',job);policy=founding.get('limits',{}).get('budget')
        if not isinstance(policy,dict) or policy.get('version')!=1:raise ValueError('native Job required')
        state=store.project('Jobs',job);item=state.get('attempts',{}).get(attempt,{})
        if item.get('route_request_sha256')!=digest:raise ValueError('request differs from accepted dispatch')
        if item.get('charge',{}).get('basis') not in {'included','incremental'} or item['charge'].get('route')!=req['route']:raise ValueError('exact authorized charge route required')
        paid=item['charge']['basis']=='incremental'
        if paid and ('money' not in policy or not item['charge'].get('reserve_minor')):raise ValueError('paid route requires bounded money reservation')
        relative=cwd.relative_to(store.root).as_posix()
        scope=item.get('scope',founding['scope'])
        if not any(relative==p or relative.startswith(p+'/') for p in scope):raise ValueError('working directory outside attempt scope')
        activation=store.require_placement()['activation']
        if store.storage_profile()!='atomic':raise ValueError('automatic route storage is unqualified; use manual route')
        adapter=_module('session-adapters');observer=_module('team-route-observation')
        parameters=inspect.signature(adapter._bounded_process).parameters
        if not {'output_sink','on_launch'}<=set(parameters) and not any(p.kind==inspect.Parameter.VAR_KEYWORD for p in parameters.values()):raise ValueError('native capture transport unavailable; use manual route')
        if not all(callable(getattr(observer,name,None)) for name in ('process_observation','usage_observation')):raise ValueError('route observer unavailable; use manual route')
        closing=_module('team-closing') if closing_contract is not None else None
        if closing is not None:
            initial_closing=closing.validate_binding(store,closing_contract,job=job,attempt=attempt)
            if initial_closing['members'].get(initial_closing['slot'],{}).get('done') is not None:raise ValueError('closing already DONE; no new route launch')
        def check():
            store.require_placement(expected=activation);store.require_main();store.guard();store.require_history()
            store.validate_authority(founding['authority']);store._worker_session(item['session'])
            if closing is not None:
                closing_view=closing.validate_binding(store,closing_contract,job=job,attempt=attempt)
                if not launched.get('spawned') and closing_view['members'].get(closing_view['slot'],{}).get('done') is not None:raise RouteStop('closing already DONE; no new route launch')
            current=store.project('Jobs',job)
            permitted={'dispatch-intent','received'}
            if launched.get('spawned'):permitted.update({'result','validated'})
            if current['held'] or current['state'] not in {'running','admitted'} or current['attempts'].get(attempt,{}).get('status') not in permitted:raise RouteStop('job-or-attempt-unavailable')
            if founding.get('team'):
                team=store.project('Teams',founding['team'])
                if team['held'] or team['state'] not in {'ready','running'} or team['epoch']!=item.get('team_epoch'):raise RouteStop('team-or-epoch-unavailable')
            budget=store.native_budget_state(policy['key'])
            if budget['status']=='budget-held':raise RouteStop('native-budget-exhausted')
            if hashlib.sha256(executable.read_bytes()).hexdigest()!=req['executable_sha256']:raise RouteStop('executable-changed')
            observed=verify_access(json.loads(json.dumps(req)))
            if not isinstance(observed,dict) or observed.get('request_sha256')!=digest or any(observed.get(k) is not True for k in ('authenticated','available')) or observed.get('included') is not (not paid) or not isinstance(observed.get('evidence'),str) or not observed['evidence'].strip():raise RouteStop('route-access-unavailable')
            if paid and observed.get('paid_authorized') is not True:raise RouteStop('paid-route-not-confirmed')
        def hold():
            b=store.native_budget_state(policy['key'])
            store.event('Jobs',job,'budget_hold',{'summary':'Native route budget hold; preserve attempt and reconcile process before resume.','budget_key':policy['key'],'reasons':b['reasons'],'resume_action':'route'})
            return {'status':'budget-held','job':job,'attempt':attempt,'reasons':b['reasons'],'extension_required':any(x in {'money-exhausted','runtime-exhausted'} for x in b['reasons'])}
        try:check()
        except RouteStop as exc:
            if exc.process_reason=='native-budget-exhausted':return hold()
            raise
        with store.locked(team=founding.get('team')):
            for row in store.records('Messages'):
                if row.get('issuer',{}).get('role')!='main':continue
                d=row.get('data',{})
                if d.get('protocol')=='axis.team-route/v1' and d.get('stage')=='intent' and d.get('job')==job and d.get('attempt')==attempt:
                    _module('coordination').validate_acceptance(row)
                    raise ValueError('attempt already executed or uncertain; no replay')
            data={'protocol':'axis.team-route/v1','stage':'intent','job':job,'attempt':attempt,'request_sha256':digest,'adapter':req['adapter'],'route':req['route'],'closing_contract':closing_contract}
            rec=store._record('Messages',{'subject':'Native route intent: '+job,'kind':'control','recipient':'main','body':'Native route intent; no result acceptance implied.','job':job,'team':founding.get('team'),'epoch':item['epoch'],'correlation':founding['operation_key'],'data':data,'authority':founding['authority'],'expires':founding['authority']['expires'],'attachments':[]})
            intent=rec.get('record',rec)
        check()
        capture=OwnedCapture(store,intent['id'],{'job':job,'attempt':attempt,'request_sha256':digest,'capture_capacity_bytes':req['output_bytes']},activation)
        def launched_receipt(process):
            capture.write_metadata('launch.json',{'protocol':'axis.team-route-launch/v1','intent':intent['id'],'job':job,'attempt':attempt,'request_sha256':digest,'process':process,'notice':'Diagnostic identity only; saved PID absence or reuse is not verified process-group termination.'})
        auth=_module('model-access')
        mode=auth.selected(store.root,req['adapter'],{'included':not paid})
        if mode!=('api-key' if paid else 'subscription'):raise ValueError('Model Access differs from reserved route')
        # Custom checked Host transports retain their exact argument contract; the
        # trusted verifier owns their authentication behavior. Native CLIs also
        # receive provider-specific options. Both receive the same selected environment.
        native_cli=Path(argv[0]).stem==req['adapter']
        launch_argv,launch_env,access_metadata=auth.prepare(store.root,req['adapter'],argv,mode=mode,paid_authorized=paid,native_cli=native_cli)
        if native_cli:auth.verify_cli(req['adapter'],launch_argv,launch_env,str(cwd))
        secret_values=[launch_env[k] for k in auth.SELECTORS if k in launch_env]
        result=adapter._bounded_process(launch_argv,str(cwd),req['prompt'],None,req['output_bytes'],check,launch_state=launched,truncate_output=True,output_sink=capture.append,on_launch=launched_receipt,env=launch_env,redact_values=secret_values)
        ended=store.now()
        ended_at=ended.strftime('%Y.%m.%d.%H.%M.%S.')+f'{ended.microsecond//1000:03d}Z'
        outputs=capture.outputs()
        closing_facts=closing.observation(store,closing_contract,job,attempt,ended_at) if closing is not None else None
        observation=observer.process_observation(result,closing=closing_facts)
        usage=observer.usage_observation(req['adapter'],result['stdout'])
        if result.get('output_truncated'):
            usage['status']='partial' if usage['status'] in {'partial','measured'} else 'unavailable'
            usage['reason']='capture-truncated'
        abnormal=result['reason'] is not None or result['returncode']!=0 or not observation.get('execution_terminal',False)
        payload={'protocol':'axis.team-route/v1','stage':'result','job':job,'attempt':attempt,'intent':intent['id'],'request_sha256':digest,'status':'needs-reconciliation' if abnormal else 'returned','process':observation,'closing':closing_facts,'usage':usage,'outputs':outputs,'ended_at':ended_at,'elapsed_seconds':result['elapsed_seconds'],'output_truncated':result.get('output_truncated',False),'incremental_spend_minor':None}
        capture.write_metadata('result.json',payload)
        result_message=store.message('result','main','Native route observation; work acceptance and charge settlement remain separate.',job=job,team=founding.get('team'),epoch=item['epoch'],correlation=founding['operation_key'],data=payload)
        if abnormal:
            if result['reason']=='native-budget-exhausted':payload['budget_hold']=hold()
            store.event('Jobs',job,'route_boundary',{'attempt':attempt,'confirmed':False,'request_sha256':digest,'intent':intent['id'],'result':result_message['id'],'evidence':'Route observation retains unconfirmed physical boundary.'})
        payload['message']=result_message['id']
        return payload
    except Exception as exc:
        return {'status':'needs-reconciliation' if intent else 'denied','reason':str(exc),'intent':intent['id'] if intent else None,'process':launched,'job':job,'attempt':attempt,'manual_reconciliation_required':intent is not None,'result_message':result_message['id'] if result_message else None,'captured_output':{k:result[k] for k in ('stdout','stderr')} if result else None}
    finally:
        if capture is not None:capture.close()


def reconcile_native_route(store, intent_id, result_id=None, *, verify_boundary, explicit=False):
    """Append a trusted physical-boundary observation; never infer work or billing.

    The callback receives intent, request_sha256 and result (possibly None after a
    crash), and must return those exact fields, verified/group_terminal True and
    nonempty evidence from the actual host/native invocation. A saved PID, PID
    absence, a terminal core Job or an expired lease cannot establish that proof.
    The original return time and outcome are retained; later proof is observed_at.
    """
    try:
        if explicit is not True or not callable(verify_boundary):raise ValueError('explicit trusted boundary verification required')
        store.require_main();store.require_placement();store.guard();store.require_history()
        c=_module('coordination');observer=_module('team-route-observation')
        intent=store.read('Messages',intent_id);c.validate_acceptance(intent);data=intent.get('data',{})
        if data.get('protocol')!='axis.team-route/v1' or data.get('stage')!='intent':raise ValueError('exact route intent required')
        job=data['job'];attempt=data['attempt'];digest=data['request_sha256']
        founding=store.read('Jobs',job);state=store.project('Jobs',job);item=state.get('attempts',{}).get(attempt,{})
        if (state['held'] or founding.get('limits',{}).get('budget',{}).get('version')!=1 or
            item.get('route_request_sha256')!=digest or intent.get('job')!=job or
            intent.get('team')!=founding.get('team') or intent.get('epoch')!=item.get('epoch') or
            intent['issuer']['session']!=founding['acceptance_owner']):raise ValueError('route intent binding')
        store.validate_authority(founding['authority'],live=False)
        requested={'intent':intent_id,'request_sha256':digest,'result':result_id}
        def rows():
            selected=[]
            for m in store.records('Messages'):
                if m.get('issuer',{}).get('role')!='main':continue
                if m.get('data',{}).get('protocol')=='axis.team-route/v1' and m['data'].get('intent')==intent_id:
                    c.validate_acceptance(m);selected.append(m)
            return selected
        def prior(records):
            found=[m for m in records if m['data'].get('stage')=='terminal-observation']
            if len(found)>1:raise ValueError('ambiguous route terminal observations')
            if found:
                m=found[0];c.validate_acceptance(m)
                if (m['data'].get('requested_result')!=result_id or m['data'].get('job')!=job or
                    m['data'].get('attempt')!=attempt or m['data'].get('request_sha256')!=digest):raise ValueError('route reconciliation identity conflict')
                return m
        original=None
        if result_id is not None:
            original=store.read('Messages',result_id);c.validate_acceptance(original);value=original.get('data',{})
            if (value.get('protocol')!='axis.team-route/v1' or value.get('stage')!='result' or
                value.get('intent')!=intent_id or value.get('job')!=job or value.get('attempt')!=attempt or
                value.get('request_sha256')!=digest or original.get('kind')!='result' or original.get('recipient')!='main' or
                original.get('team')!=founding.get('team') or original.get('job')!=job or
                original.get('epoch')!=item['epoch'] or original['issuer']['session']!=intent['issuer']['session']):raise ValueError('route result binding')
        existing=prior(rows())
        if existing is None:
            if original is None and any(m['data'].get('stage')=='result' for m in rows()):raise ValueError('route result already exists; identify its exact ID')
            boundary=verify_boundary(dict(requested))
            if (not isinstance(boundary,dict) or any(boundary.get(k)!=v for k,v in requested.items()) or
                boundary.get('verified') is not True or boundary.get('group_terminal') is not True or
                not isinstance(boundary.get('evidence'),str) or not boundary['evidence'].strip()):raise ValueError('exact physical boundary remains unverified')
            boundary=dict(requested,verified=True,group_terminal=True,evidence=boundary['evidence'])
            observed_at=c.stamp(store.now())
            def publish(value,body):
                return store._record('Messages',{'subject':body,'kind':'result','recipient':'main','body':body,
                    'team':founding.get('team'),'job':job,'epoch':item['epoch'],'correlation':founding['operation_key'],
                    'data':value,'authority':None,'expires':founding['authority']['expires'],'attachments':[]})
            with store.locked(team=founding.get('team')):
                existing=prior(rows())
                if existing is None:
                    if original is None:
                        if any(m['data'].get('stage')=='result' for m in rows()):raise ValueError('route result appeared; identify its exact ID')
                        unknown=observer.process_observation({})
                        unknown.update(returncode=None,signals=[],cleanup_errors=[],execution_terminal=False,capacity_released=False)
                        value={'protocol':'axis.team-route/v1','stage':'result','job':job,'attempt':attempt,'intent':intent_id,
                            'request_sha256':digest,'status':'needs-reconciliation','ended_at':None,'process':unknown,'closing':None,
                            'recovery_observation':True,'notice':'Original process outcome and unread output are unknown; no return time inferred.'}
                        rec=publish(value,'Interrupted native route observation');original=rec.get('record',rec)
                    source=original['data'];process=source['process'];ended_at=source.get('ended_at');facts=None
                    if data.get('closing_contract') is not None and ended_at is not None:
                        closing=_module('team-closing')
                        facts=closing.observation(store,data['closing_contract'],job,attempt,ended_at)
                    raw={'returncode':process.get('returncode'),'reason':process.get('reason'),
                        'process':{'launched':True,'leader_reaped':process.get('leader_terminal') is True,
                            'group_stop_confirmed':True,'signals':process.get('signals',[]),'cleanup_errors':process.get('cleanup_errors',[])}}
                    observed=observer.process_observation(raw,closing=facts)
                    value={'protocol':'axis.team-route/v1','stage':'terminal-observation','job':job,'attempt':attempt,'intent':intent_id,
                        'request_sha256':digest,'route_result':original['id'],'requested_result':result_id,
                        'ended_at':ended_at,'observed_at':observed_at,'process':observed,'closing':facts,'boundary':boundary,
                        'notice':'Physical observation only; original work outcome, charges and acceptance remain separate.'}
                    rec=publish(value,'Native route physical boundary observation');existing=rec.get('record',rec)
            status='observed'
        else:status='duplicate'
        event=store.event('Jobs',job,'route_boundary',{'attempt':attempt,'confirmed':True,'request_sha256':digest,
            'intent':intent_id,'result':existing['id'],'evidence':existing['data']['boundary']['evidence']})
        return {'status':status,'message':existing['id'],'route_result':existing['data']['route_result'],
            'intent':intent_id,'boundary':event,'work_accepted':False,'charges_settled':False}
    except Exception as exc:
        return {'status':'denied','reason':str(exc),'intent':intent_id,'result':result_id,'manual_reconciliation_required':True}
