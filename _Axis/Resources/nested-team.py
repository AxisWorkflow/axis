#!/usr/bin/env python3
"""Sponsor operations on nested Teams. JSON arguments on stdin; no provider calls, no process launches.

A sponsor is the session bound to a slot that its own Team's accepted `delegation` grant names. Every operation
rechecks that binding and the whole parent chain. Results are local acceptance; Main alone integrates into the
shared project, and Main's own controls stay in coordination.py.

  status          {"team": ID}
  team            {"parent": ID, "charter": {...}, "operation_key": "..."}
  member          {"team": ID, "slot": "...", "operation_key": "..."}      repeat the same key after an interruption
  replace         {"team": ID, "slot": "...", "operation_key": "..."}      fence the bound member, bind a fresh one;
                                                                           the leader slot also needs "checkpoint"
  retire          {"team": ID, "session": ID}                              stop one member Marker of your own child Team
  renew           {"team": ID}                                             keep your own lease while your authority is live
  job             {"mandate": {"team": ID, ...}, "operation_key": "..."}
  event           {"family": "Teams"|"Jobs", "ident": ID, "action": "...", "data": {...}}
  message         {"team": ID, "recipient": "...", "body": "...", "kind": "question"}
  inbox           {"team": ID}
  checkpoint      {"team": ID}
  artifact-check  {"team": ID, "slot": "...", "revision": "..."}
  freeze          {"team": ID, "operation": "..."}
  revise          {"team": ID, "predecessor": ID, "money_minor": N, "slots": N, "operation": "..."}
  settle          {"team": ID}
  fence           {"team": ID, "wait_seconds": N}      finish fencing a changed grant or seat; Main or a sponsor above it

A changed grant or sponsoring seat is fenced in the call that changes it when it can be. When that call reports
`delegation_fence.status: pending`, nothing new starts beneath the Team until `fence` completes; repeat it.
"""
import argparse, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('axis_nested_coordination',Path(__file__).with_name('coordination.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
OPERATIONS=('status','team','member','replace','retire','renew','job','event','message','inbox','checkpoint','artifact-check','freeze','revise','settle','fence')
def main():
    parser=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root',default='.')
    parser.add_argument('--session',required=True)
    parser.add_argument('operation',choices=OPERATIONS)
    args=parser.parse_args()
    try:
        store=core.Store(args.root,args.session);store.guard()
        raw=sys.stdin.buffer.read(core.MAX_RECORD+1)
        core.need(len(raw)<=core.MAX_RECORD,'request-size')
        request=json.loads(raw,object_pairs_hook=core._unique_pairs,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')));core.need(type(request) is dict,'request-object')
        result=store.delegated(args.operation,**request)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True))
        return 3 if isinstance(result,dict) and result.get('status')=='budget-held' else 0
    except (core.CoordinationError,core._START.Fault,ValueError,TypeError,KeyError,OSError) as exc:
        print(json.dumps({'status':'refused','reason':getattr(exc,'code','invalid-request')}));return 2
if __name__=='__main__':sys.exit(main())
