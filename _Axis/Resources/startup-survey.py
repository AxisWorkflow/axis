#!/usr/bin/env python3
"""Optional one-call startup survey. Python3/POSIX only; one bounded localhost probe, no model calls.

Runs Start-Session's mechanical checks under the retained startup admission, using the
unchanged startup-state.py record operations for every Flag write. The Agent keeps
eligibility, instruction loading, semantic reads, queue handling and presentation.
Detect-Capabilities.md > Optional Startup Survey defines the contract; the numbered
Start-Session steps remain the complete fallback.
"""
from __future__ import annotations
import argparse,importlib.util,json,os,platform,re,secrets,subprocess,sys,time,urllib.request
from pathlib import Path
sys.dont_write_bytecode=True
_spec=importlib.util.spec_from_file_location('axis_startup_state',Path(__file__).with_name('startup-state.py'))
state=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(state)
Fault,need,stamp,parse_stamp=state.Fault,state.need,state.stamp,state.parse_stamp

def inventory(self, name):
    """Queue inventory under Start-Session: confirmed empty only for a readable ordinary directory holding at most an ordinary .gitkeep."""
    try:directory=self.path(name,kind='directory')
    except Fault as error:return {'state':'missing' if error.code=='missing_path' else 'unsafe','entries':[]}
    entries=[];unexpected=False
    for entry in sorted(os.scandir(directory),key=lambda e:e.name):
        if entry.name=='.gitkeep' and entry.is_file(follow_symlinks=False):continue
        entries.append(entry.name)
        if entry.is_symlink() or not entry.is_file(follow_symlinks=False) or entry.name.startswith('.'):unexpected=True
    return {'state':'empty' if not entries else 'unexpected' if unexpected else 'nonempty','entries':entries[:50],'count':len(entries)}

def survey(self, model, harness, interaction, spawn, parallel):
    """Mechanical Start-Session checks in one call; the Agent keeps every semantic, queue-handling and overlay step."""
    need(self.state['phase']=='initialized','phase',self.owner_name);self.guard()
    for value in (model,harness,interaction):need(isinstance(value,str) and 0<len(value)<=128 and value.strip()==value and '\n' not in value,'arguments')
    need(spawn in ('yes','no') and parallel in ('yes','no') and interaction in ('interactive','headless','channel','unknown'),'arguments')
    import platform,subprocess,urllib.request
    report={'status':'surveyed','session':self.sid,'notices':[]}
    # Capabilities (Detect-Capabilities Step 2): the Agent supplies model, spawn and parallel from its own tool inventory.
    try:shell='yes' if subprocess.run(['/bin/sh','-c','uname -s && date -u +"%Y.%m.%d"'],capture_output=True,timeout=5).returncode==0 else 'no'
    except (OSError,subprocess.SubprocessError):shell='no'
    local='no'
    if shell=='yes':
        try:
            with urllib.request.urlopen('http://localhost:11434/v1/models',timeout=2) as response:local='yes' if response.status==200 else 'no'
        except Exception:local='no'
    # Cloud-sync classification keeps a nonsecret reason (2.02) so a wrong verdict can be diagnosed and corrected.
    path=str(self.root).lower();term=next((k for k in ('Library/CloudStorage','Mobile Documents','com~apple~CloudDocs','Dropbox','OneDrive','Google Drive') if k.lower() in path),'')
    cloud,reason=('yes',f"the folder path contains '{term}'") if term else ('no','no cloud-storage term in the folder path and no sync marker above it')
    if cloud=='no':
        mark=next((f"{m} beside an enclosing folder" for parent in self.root.parents for m in ('.dropbox','.dropbox.cache') if (parent/m).exists()),'')
        if mark:cloud,reason='yes',f'a Dropbox marker ({mark})'
    policy=self.setting('Storage Policy')
    if policy!='auto':
        storage='serialized'
        if policy!='single-writer':report['notices'].append('storage-policy-missing-or-malformed')
    elif cloud=='yes':storage='serialized'
    else:
        probe=self.path('_Temp/.startup-survey-'+secrets.token_hex(8),missing=True);moved=probe.with_name(probe.name+'.moved')
        try:
            probe.write_bytes(b'probe\n');need(probe.read_bytes()==b'probe\n','probe');os.replace(probe,moved)
            need(moved.read_bytes()==b'probe\n' and moved.stat().st_mtime>0,'probe');storage='atomic'
        except (OSError,Fault):storage='unknown'
        finally:
            for q in (probe,moved):
                try:q.unlink()
                except FileNotFoundError:pass
    caps={'model':model,'host-spawn':spawn,'host-parallel':parallel,'host-shell':shell,'host-local-llm':local,'host-cloud-sync':cloud,'host-storage':storage}
    self.record_capabilities(json.dumps(caps));report['capabilities']=caps
    if shell=='no':report['notices'].append('non-posix-shell')
    report['cloud_reason']=reason
    if cloud=='yes':report['notices'].append('cloud-synced-folder')
    # Environment signature (Portability > Optional Environment Signature): write only when unchanged; a change is returned for the Agent's validation.
    osclass={'Darwin':'macos','Linux':'linux','Windows':'windows'}.get(platform.system(),'unknown')
    current={'harness':harness,'os':osclass,'interaction':interaction,'storage':storage}
    environment={'state':'unavailable'}
    try:
        home=Path(os.path.expanduser('~/.axis'));instance=home/'instance-id'
        if not instance.exists():
            home.mkdir(mode=0o700,exist_ok=True);value=stamp()
            with open(instance,'x') as f:f.write(value+'\n')
        opaque=instance.read_text().strip();parse_stamp(opaque)
        old=(self.read('_Axis/Flags/environment-binding',optional=True) or '').splitlines()
        fields=dict(line.split(': ',1) for line in old[1:] if ': ' in line)
        changed=[k for k in current if fields.get(k)!=current[k]]
        if len(old)!=6 or old[0]!=opaque or 'verified' not in fields:environment={'state':'changed','fields':'binding-missing-or-malformed'}
        elif changed:environment={'state':'changed','fields':changed,'current':current}
        else:
            self.write_flag('environment-binding',opaque+'\n'+''.join(f'{k}: {v}\n' for k,v in current.items())+'verified: '+stamp()+'\n');environment={'state':'unchanged'}
    except (OSError,ValueError,Fault):environment={'state':'unavailable'}
    report['environment']=environment
    # Manifest presence (literal paths only) and Mindset provenance stamp.
    missing=[]
    manifest=re.split(r'^### Optional project files\n.*?(?=^### )',self.read('_Axis/MANIFEST.md'),flags=re.M|re.S)
    for literal in re.findall(r'^- (?:\*\*)?`([^`{}*|]+)`',''.join(manifest),re.M):
        if literal in ('README.md','LICENSE'):continue
        if not (self.root/literal.rstrip('/')).exists():missing.append(literal)
    report['manifest_missing']=missing
    mindset=self.read('_Axis/MINDSET.md',optional=True) or '';stampline=re.findall(r'<!-- generated-from: (.*?) -->',mindset)
    settings=self.read('_Axis/SETTINGS.md');mindset_part=settings.split('## Mindset Settings',1)[1] if '## Mindset Settings' in settings else ''
    expected=' '.join(f'{n}={v}' for n,v in re.findall(r'^### (\w+)\s*\n.*?^\*\*Value:\*\* ([^\n]*)$',mindset_part,re.M|re.S))
    report['mindset']='current' if stampline and stampline[-1]==expected else 'regenerate'
    # Markers: informational counts only; admission already excluded a fresh foreign Main.
    now=time.time();stale=0;externals=[];subagents=0
    for path in sorted(self.path('_Axis/Agents',kind='directory').glob('*.md')):
        if path.stem==self.sid:continue
        first=(path.read_text(errors='replace').splitlines() or [''])[0];dead=(path.with_suffix('.kill')).exists()
        if now-path.stat().st_mtime>=3600:stale+=1
        elif not dead and first.startswith('External:'):externals.append(path.stem)
        elif not dead and first.startswith('Subagent:'):subagents+=1
    report['markers']={'stale':stale,'fresh_external':externals,'orphan_subagents':subagents}
    # Queues and Trash (inventory only), stale locks and claims, Notes count.
    report['queues']={name:inventory(self,'_Axis/'+name) for name in ('Followups','Reminders','Requests')}
    report['trash']=inventory(self,'_Trash')
    locks=[q.relative_to(self.root).as_posix() for q in self.root.joinpath('_Axis').rglob('*.lock') if q.is_dir() and q.relative_to(self.root).as_posix()!=self.claim_name]
    report['locks']={'lock_dirs':locks,'timestamp_claims':[q.name for q in self.path('_Temp',kind='directory').glob('*.tsclaim')]}
    notes=[q for q in self.path('_Axis/Notes',kind='directory').glob('*.md')]
    limit=self.setting('Max Notes');report['notes']={'count':len(notes),'over_limit':bool(limit and limit.replace(',','').isdigit() and len(notes)>int(limit.replace(',','')))}
    report['indexes']=self.check_indexes()
    # Reminder checkpoint for a confirmed empty healthy queue only; a nonempty queue needs the Reminders Practice.
    if report['queues']['Reminders']['state']=='empty':
        self.write_flag('reminder-check',self.sid+'\n'+stamp()+'\n');report['reminder_checkpoint']='advanced'
    else:report['reminder_checkpoint']='agent'
    self.guard();return report


def main():
    engine=None
    try:
        parser=state.Parser();parser.add_argument('--root',required=True);sub=parser.add_subparsers(dest='operation',required=True,parser_class=state.Parser)
        command=sub.add_parser('survey')
        for option in ('--session','--owner','--model','--harness','--interaction','--spawn','--parallel'):command.add_argument(option,required=True)
        args=parser.parse_args()
        if state.fcntl is None or not hasattr(os,'O_NOFOLLOW') or os.utime not in os.supports_fd:
            print(json.dumps({'status':'unavailable','code':'platform'}));return 3
        engine=state.Startup(args.root);engine.load(args.session,args.owner)
        print(json.dumps(survey(engine,args.model,args.harness,args.interaction,args.spawn,args.parallel),sort_keys=True));return 0
    except Fault as error:
        print(json.dumps({'status':'error','code':error.code,'path':error.path},sort_keys=True));return 2
    except (OSError,UnicodeError,ValueError,KeyError,TypeError):
        print(json.dumps({'status':'error','code':'io_or_record','path':''},sort_keys=True));return 2
    finally:
        if engine is not None:engine.close()

if __name__=='__main__':raise SystemExit(main())
