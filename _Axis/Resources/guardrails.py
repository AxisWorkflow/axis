#!/usr/bin/env python3
"""Optional host hook: refuse, before it happens, a tool call that breaks an Axis rule the host can see.

Installed by `^install guardrails` as a Claude Code PreToolUse hook. For every Agent: no edit to a write-once record
(Logs, Snapshots, CX, Audit, Supervision, archived history, update evidence, finished Tasks, Follow-Ups and Reminders)
and no new record with a malformed name. For a helper running as an Axis agent type (`axis-cx`, `axis-wiki`,
`axis-general`), also: writes only inside that role's folders, and no tool may touch `_Axis/Secrets/`.
For an OpenClaw agent listed as an External Agent, the `axis-guardrails` plugin calls `--external {tool} {path}`:
no `_Axis/Secrets/`, no change to an existing file, and new files only in Project Subfolders, `_Axis/Requests/` and
`_Temp/`. The Claude Code hook reads JSON from stdin; both exit 2 with a reason to refuse, and 0 otherwise.
Python 3 standard library only; reads paths and status lines, never prints file contents. It does not see what a
shell command or helper script writes, and it never affects User's own editing.

Self-test without a host: python3 _Axis/Resources/guardrails.py --check {project-relative path} [--new] [--agent {type}]"""
import json,os,re,sys
from pathlib import Path

NAME=re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md')
FAMILIES=('Agents','Audit','CX','Followups','Ideas','Logs','Notes','Reminders','Reviews','Snapshots','Status','Supervision','Tasks')
WORM={'Logs':'a Log','Snapshots':'a Snapshot','CX':'a CX report','Audit':'an Audit report','Reviews':'a legacy Review',
      'Status':'a legacy Status report','Supervision':'a Supervision record'}
IGNORED=('.gitkeep','.DS_Store')
WRITE_TOOLS=('Edit','Write','MultiEdit','NotebookEdit')
PATH_TOOLS=WRITE_TOOLS+('Read','Grep','Glob')
# Where each helper role may write: (folder prefix, new files only?).
ROLES={'axis-cx':[('_Axis/CX/',True),('_Temp/',False)],
       'axis-wiki':[('_Wiki/',False),('_Axis/Wiki/',False),('_Temp/',False)],
       'axis-general':None}  # anywhere except the folders below
GENERAL_DENY=('_Axis/Agents/','_Axis/Flags/','_Axis/Secrets/','_Axis/Requests/','_Axis/Updates/','.git/','.claude/','.codex/','.gemini/')
SECRETS='_Axis/Secrets'

def field(text,key):
    for line in text.splitlines():
        m=re.fullmatch(key+r':[ \t]*(.*)',line.strip())
        if m:return m[1].strip().strip('*').strip()
    return None

def write_once(root,rel,exists):
    """A refusal reason for writing project-relative rel under the record rules, or None."""
    parts=rel.split('/')
    if len(parts)<3 or parts[0]!='_Axis' or parts[-1] in IGNORED:return None
    family=parts[1]
    if family=='Archive':return 'archived history is write-once' if exists else None
    if family=='Updates':return None if parts[-1]=='operation.lck' or not exists else 'update evidence is write-once'
    if family not in FAMILIES or len(parts)!=3:return None
    if not exists:
        return None if NAME.fullmatch(parts[2]) else f'a new record in _Axis/{family}/ must be named yyyy.mm.dd.hh.mm.ss.xxxZ.md (_Axis/Practices/Timestamps.md)'
    if family in WORM:return WORM[family]+' is write-once: write a new record instead (a wrong identifier in it is fixed only with record-check.py correct, after User approves)'
    if family in ('Tasks','Followups','Reminders'):
        try:text=(root/rel).read_text(encoding='utf-8',errors='replace')
        except OSError:return None
        if family=='Tasks' and (field(text,'status') or '').casefold() in ('completed','cancelled'):
            return 'a Completed or Cancelled Task is write-once'
        if family!='Tasks' and (field(text,'outcome') or 'N/A') not in ('N/A',''):
            return ('a resolved Follow-Up' if family=='Followups' else 'a terminal Reminder')+' is write-once'
    return None

def helper_scope(agent,rel,exists):
    """A refusal reason for an Axis helper role writing rel, or None."""
    if agent not in ROLES:return None
    if rel.startswith('_Wiki/_Inbox/'):return 'helpers never create or edit files in _Wiki/_Inbox/'
    allowed=ROLES[agent]
    if allowed is None:
        hit=next((d for d in GENERAL_DENY if rel.startswith(d) or rel+'/'==d),None)
        return f'a General helper does not write in {hit}' if hit else None
    for prefix,new_only in allowed:
        if rel.startswith(prefix):return 'this helper only adds new files there' if new_only and exists else None
    return f'the {agent[5:].upper()} helper writes only in '+', '.join(p for p,_ in allowed)

def external(rel,exists,write):
    """A refusal reason for an External Agent's file tool on rel, or None."""
    if rel==SECRETS or rel.startswith(SECRETS+'/'):return 'an External Agent never uses _Axis/Secrets/'
    if not write:return None
    if exists:return 'an External Agent adds new files only and never changes an existing file'
    parts=rel.split('/')
    if rel.startswith(('_Axis/Requests/','_Temp/')) or (len(parts)>=2 and not parts[0].startswith(('_','.'))):return None
    return 'an External Agent writes new files only in Project Subfolders, _Axis/Requests/ or _Temp/'

def verdict(root,rel,exists,agent,tool):
    if agent and (rel==SECRETS or rel.startswith(SECRETS+'/')):return 'helpers never read or write _Axis/Secrets/'
    if tool not in WRITE_TOOLS:return None
    return write_once(root,rel,exists) or (helper_scope(agent,rel,exists) if agent else None)

def relative(root,path):
    p=Path(path)
    if not p.is_absolute():p=root/p
    try:return Path(os.path.realpath(p)).relative_to(root).as_posix()
    except ValueError:return None

def main():
    if len(sys.argv)>=3 and sys.argv[1]=='--check':
        root=Path.cwd().resolve();rel=sys.argv[2].strip('/');rest=sys.argv[3:]
        agent=rest[rest.index('--agent')+1] if '--agent' in rest and rest.index('--agent')+1<len(rest) else None
        why=verdict(root,rel,'--new' not in rest and (root/rel).exists(),agent,'Write')
        print(('REFUSED: '+why) if why else 'ALLOWED');return 2 if why else 0
    if len(sys.argv)==4 and sys.argv[1]=='--external':
        tool,path=sys.argv[2].lower(),sys.argv[3];root=Path.cwd().resolve();rel=relative(root,path)
        if rel is None:return 0
        exists=(root/rel).exists();write=tool not in ('read','grep','glob','ls','find')
        why=external(rel,exists,write) or (write_once(root,rel,exists) if write else None)
        if why:print(f'Axis guardrail: {why} ({rel}).');return 2
        return 0
    try:event=json.load(sys.stdin)
    except ValueError:return 0
    if not isinstance(event,dict):return 0
    tool=event.get('tool_name');ti=event.get('tool_input') or {}
    root=Path(os.environ.get('CLAUDE_PROJECT_DIR') or event.get('cwd') or os.getcwd()).resolve()
    if not (root/'_Axis/Resources/guardrails.py').is_file():return 0
    agent=event.get('agent_type') if event.get('agent_id') or event.get('agent_type') else None
    agent=agent or ('helper' if event.get('agent_id') else None)
    if tool=='Bash' and agent and isinstance(ti.get('command'),str) and SECRETS in ti['command']:
        print('Axis guardrail: helpers never read or write _Axis/Secrets/.',file=sys.stderr);return 2
    if tool not in PATH_TOOLS:return 0
    path=ti.get('file_path') or ti.get('notebook_path') or ti.get('path')
    if not isinstance(path,str) or not path:return 0
    rel=relative(root,path)
    if rel is None:return 0
    why=verdict(root,rel,(root/rel).exists(),agent,tool)
    if why:
        print(f'Axis guardrail: {why} ({rel}). See _Axis/Rules/RecordsAndWORM.md and _Axis/Rules/Subagents.md.',file=sys.stderr);return 2
    return 0

if __name__=='__main__':sys.exit(main())
