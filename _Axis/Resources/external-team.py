#!/usr/bin/env python3
"""Scoped External proposal Team operations. JSON arguments on stdin; no provider calls.

This does not launch processes. native-launch returns a checked envelope and recorded
attempt for the host's explicitly authorized native spawning tool. Shared project
acceptance, placement, schedules, indexes and budget expansion stay Main-only.
"""
import argparse, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('axis_external_coordination',Path(__file__).with_name('coordination.py'))
core=importlib.util.module_from_spec(spec);spec.loader.exec_module(core)
OPERATIONS={'team':'proposal_team','member':'proposal_member_create','job':'proposal_job','event':'proposal_event',
            'message':'proposal_message','inbox':'proposal_inbox','submit':'proposal_submit','native-launch':'proposal_native_launch'}
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',default='.')
    parser.add_argument('--session',required=True)
    parser.add_argument('operation',choices=OPERATIONS)
    args=parser.parse_args()
    try:
        store=core.Store(args.root,args.session);store._require_external()
        raw=sys.stdin.buffer.read(core.MAX_RECORD+1)
        core.need(len(raw)<=core.MAX_RECORD,'request-size')
        request=json.loads(raw,object_pairs_hook=core._unique_pairs,parse_constant=lambda value: (_ for _ in ()).throw(ValueError('nonfinite JSON')));core.need(type(request) is dict,'request-object')
        result=getattr(store,OPERATIONS[args.operation])(**request)
        print(json.dumps(result,ensure_ascii=False,sort_keys=True));return 0
    except (core.CoordinationError,ValueError,TypeError,OSError) as exc:
        print(json.dumps({'status':'refused','reason':getattr(exc,'code','invalid-request')}));return 2
if __name__=='__main__':sys.exit(main())
