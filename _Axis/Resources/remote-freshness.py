#!/usr/bin/env python3
"""Optional bounded startup notification. Never integrates or publishes project work."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import time
import uuid

class Unverified(Exception):
    pass

def require(value):
    if not value:
        raise Unverified()

def ordinary(path, missing=False, directory=False):
    require('..' not in path.parts)
    for part in reversed((path, *path.parents)):
        try:
            info=part.lstat()
        except FileNotFoundError:
            require(missing)
            continue
        require(not stat.S_ISLNK(info.st_mode))
        require(stat.S_ISDIR(info.st_mode) or (stat.S_ISREG(info.st_mode) and info.st_nlink==1))
    if path.exists():
        require(path.is_dir() if directory else path.is_file())
    return path

def setting(root, name):
    text=ordinary(root/'_Axis/SETTINGS.md').read_text()
    matches=re.findall(r'^### '+re.escape(name)+r'\n(.*?)(?=\n### |\n## |\Z)',text,re.M|re.S)
    require(len(matches)<=1)
    if not matches:return None
    values=re.findall(r'^\*\*Value:\*\* (\S+)\s*$',matches[0],re.M)
    require(len(values)==1)
    return values[0]

def lease(root, session):
    require(re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',session))
    marker=ordinary(root/'_Axis/Agents'/f'{session}.md')
    rows=marker.read_text().splitlines()
    require(len(rows)==4 and rows[:3]==['Main: session','',f'session: {session}'] and rows[3].startswith('host: ') and rows[3][6:].strip())
    require(not marker.with_suffix('.kill').exists() and time.time()-marker.stat().st_mtime<3600)
    # This enhancement runs only inside the already admitted, in-flight Main boot.
    require(ordinary(root/'_Axis/Flags/starting').read_text().splitlines()[0]==session)
    require(setting(root,'Storage Policy')=='auto' and os.name=='posix')
    for name,value in [('host-shell','yes'),('host-storage','atomic')]:
        rows=ordinary(root/'_Axis/Flags'/name).read_text().splitlines()
        require(len(rows)==2 and rows[0]==value and re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z',rows[1]))
        detected=datetime.strptime(rows[1],'%Y.%m.%d.%H.%M.%S.%fZ').replace(tzinfo=timezone.utc)
        require(0<=(datetime.now(timezone.utc)-detected).total_seconds()<300)
    for other in ordinary(root/'_Axis/Agents',directory=True).glob('*.md'):
        if other==marker:continue
        ordinary(other)
        if other.with_suffix('.kill').exists():continue
        require(not (time.time()-other.stat().st_mtime<3600 and other.read_text().splitlines()[0]=='Main: session'))

def result(status, **extra):
    return {'status':status,'notice':None,**extra}

def check(args):
    root=ordinary(Path(args.project_root).absolute(),directory=True)
    mode=setting(root,'Remote Freshness')
    if mode in (None,'off'):return result('disabled')
    require(mode=='on')
    lease(root,args.session)
    deadline=time.monotonic()+args.timeout
    executable=shutil.which('git')
    require(executable is not None)
    environment={k:v for k,v in os.environ.items() if not k.startswith('GIT_')}
    environment.update(GIT_TERMINAL_PROMPT='0',GCM_INTERACTIVE='Never',GIT_ASKPASS='/usr/bin/false',SSH_ASKPASS='/usr/bin/false',SSH_ASKPASS_REQUIRE='never',GIT_SSH_COMMAND='ssh -oBatchMode=yes -oConnectTimeout=5',GIT_NO_REPLACE_OBJECTS='1',GIT_NO_LAZY_FETCH='1',GIT_CONFIG_NOSYSTEM='1')
    prefix=[executable,'--no-optional-locks','--no-replace-objects','-C',str(root),'-c','core.fsmonitor=false','-c','core.hooksPath=/dev/null','-c','gc.auto=0','-c','maintenance.auto=false','-c','credential.interactive=false','-c','protocol.allow=never','-c','protocol.file.allow=always','-c','protocol.https.allow=always','-c','protocol.ssh.allow=always']
    def git(*command, optional=False, discard=False):
        remaining=deadline-time.monotonic()
        require(remaining>0)
        process=subprocess.Popen([*prefix,*command],env=environment,stdout=subprocess.DEVNULL if discard else subprocess.PIPE,stderr=subprocess.DEVNULL,start_new_session=True)
        try:output,_=process.communicate(timeout=remaining)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid,signal.SIGKILL);process.communicate();raise Unverified()
        if process.returncode and not optional:raise Unverified()
        output=output or b'';require(len(output)<=1048576)
        return output.decode('utf-8') if process.returncode==0 else None
    require(Path(git('rev-parse','--show-toplevel').strip())==root)
    metadata=ordinary(root/'.git',directory=True)
    require(not (metadata/'shallow').exists())
    require(not any((metadata/p).exists() for p in ['MERGE_HEAD','CHERRY_PICK_HEAD','REVERT_HEAD','BISECT_LOG','rebase-apply','rebase-merge','sequencer','index.lock','config.lock','packed-refs.lock']))
    for p in ('objects/info/alternates','info/grafts','commondir'):
        require(not (metadata/p).exists())
    head=git('rev-parse','--verify','HEAD').strip()
    index=ordinary(metadata/'index',missing=True)
    index_hash=hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None
    cache=ordinary(root/'_Temp/axis-remote-freshness',missing=True,directory=True)
    cache.mkdir(exist_ok=True)
    record=ordinary(cache/(args.session+'.json'),missing=True)
    if record.exists():
        old=json.loads(record.read_text())
        require(old.get('session')==args.session)
        if old.get('status')=='pending':return result('unverified',notice='Remote freshness is unverified after an interrupted check; use ^resume when connectivity is available.')
        return result('already-checked')
    lease(root,args.session)
    # Exclusive pending receipt deduplicates concurrent invocations before any fetch.
    with record.open('x') as f:
        json.dump({'session':args.session,'status':'pending','checked_utc':datetime.now(timezone.utc).isoformat()},f);f.write('\n');f.flush();os.fsync(f.fileno())
    def finish(value):
        lease(root,args.session)
        require(git('rev-parse','--verify','HEAD').strip()==head)
        require((hashlib.sha256(index.read_bytes()).hexdigest() if index.exists() else None)==index_hash)
        current=json.loads(ordinary(record).read_text());require(current.get('session')==args.session and current.get('status')=='pending')
        temp=record.with_name('.'+record.name+'.'+uuid.uuid4().hex)
        with temp.open('x') as f:
            json.dump({'session':args.session,'checked_utc':datetime.now(timezone.utc).isoformat(),'status':value['status']},f);f.write('\n');f.flush();os.fsync(f.fileno())
        os.replace(temp,record)
        return value
    branch=git('symbolic-ref','--quiet','--short','HEAD',optional=True)
    if not branch:return finish(result('no-upstream'))
    branch=branch.strip()
    remote=git('config','--get-all','branch.'+branch+'.remote',optional=True)
    source=git('config','--get-all','branch.'+branch+'.merge',optional=True)
    if not remote or not source:return finish(result('no-upstream'))
    require(len(remote.splitlines())==len(source.splitlines())==1)
    remote=remote.strip();source=source.strip()
    require(remote!='.' and not remote.startswith('-') and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._/-]*',remote) and '..' not in remote)
    require(source.startswith('refs/heads/') and git('check-ref-format',source,optional=True) is not None)
    target=git('rev-parse','--symbolic-full-name','@{upstream}',optional=True)
    if not target:return finish(result('no-upstream'))
    target=target.strip();require(target.startswith('refs/remotes/'+remote+'/'))
    require(git('remote','get-url',remote,optional=True) is not None)
    # Only the configured upstream is fetched; no tags, submodules, FETCH_HEAD or integration.
    lease(root,args.session)
    git('-c','remote.'+remote+'.uploadpack=git-upload-pack','fetch','--quiet','--no-tags','--no-recurse-submodules','--no-write-fetch-head','--no-auto-maintenance','--refmap=',remote,'+'+source+':'+target,discard=True)
    counts=git('rev-list','--left-right','--count',head+'...'+target).strip().split()
    require(len(counts)==2 and all(x.isdigit() for x in counts))
    left,right=map(int,counts)
    dirty=bool(git('status','--porcelain=v1','-z','--untracked-files=normal'))
    status='diverged' if left and right else 'remote-ahead' if right else 'local-ahead' if left else 'equal'
    notice=None
    if status=='remote-ahead':notice='Incoming Git commits are available; run ^resume before continuing.'+(' Local changes need to be preserved.' if dirty else '')
    if status=='diverged':notice='Local and remote Git histories have diverged; use ^resume to review reconciliation before continuing. Both sides are preserved.'
    return finish(result(status,local_ahead=left,remote_ahead=right,dirty=dirty,notice=notice))

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--project-root',required=True);parser.add_argument('--session',required=True);parser.add_argument('--timeout',type=float,default=10.0);args=parser.parse_args()
    try:
        require(0.1<=args.timeout<=10.0)
        value=check(args)
    except (Unverified,OSError,ValueError,IndexError,KeyError,subprocess.SubprocessError):
        value=result('unverified',notice='Remote freshness is unverified; Axis remains usable locally. Run ^resume when the connection and prerequisites are available.')
    print(json.dumps(value,sort_keys=True));return 0
if __name__=='__main__':raise SystemExit(main())
