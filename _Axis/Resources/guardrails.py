#!/usr/bin/env python3
"""Optional host hook: refuse, before it happens, a tool call that breaks an Axis rule the host can see.

Installed by `^install guardrails` as a Claude Code PreToolUse hook. For every Agent: no edit to a write-once record
(Logs, Snapshots, CX, Audit, Supervision, Teams, Messages, Jobs, archived history, update evidence, finished Tasks, Follow-Ups and Reminders)
and no new record with a malformed name. A write to a record, index, Plan or Memo may not add an identifier that is
malformed or names nothing (record-check.py's scan; `(missing)` after an identifier reports it as missing). For a helper running as an Axis agent type
(the delegated role rows of the generated role table), also: writes only inside that role's folders, and no tool may touch `_Axis/Secrets/`.
For an OpenClaw agent listed under a guarded session role, the `axis-guardrails` plugin calls `--external {tool} {path}` or
`--role {name} {tool} {path}`: no `_Axis/Secrets/`, no change to an existing file, and new files only where the role's row
allows (today Project Subfolders, `_Axis/Submissions/` and `_Temp/`). The Claude Code hook reads JSON from stdin; both exit 2 with a reason to refuse, and 0 otherwise.
Python 3 standard library only; reads paths and status lines, never prints file contents. It does not see what a
shell command or helper script writes. Adoption repairs run only through the verified, scope-bound update engine; they do not disable this hook for ordinary edits. During an adoption's reconciliation, Main may edit the Tasks and Follow-Ups its frozen plan names. It never affects User's own editing.

Self-test without a host: python3 _Axis/Resources/guardrails.py --check {project-relative path} [--new] [--agent {type}]"""
import importlib.util,json,os,re,sys
from pathlib import Path

# BEGIN GENERATED: role-table
# Compiled from _Axis/Roles/ at release; edit the role files, never this region.
ROLE_TABLE=(
    {'name': 'Main', 'cls': 'session', 'subject': 'Main: session', 'match': 'exact', 'shape': 'exact4', 'created_by': 'claim', 'exclusive': True, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': None, 'survey_key': None, 'notice': None, 'issuer': 'main', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Main', 'log_by': 'Main Agent', 'title': 'Main Agent', 'plural': 'Main Agents', 'article': 'the'},
    {'name': 'External', 'cls': 'session', 'subject': 'External: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'self', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_external', 'notice': 'An External Agent is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': True, 'proposal_issuer': 'external', 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'externalAgents', 'flag': '--external', 'block_spawn': True, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'External', 'log_by': 'External Agent', 'title': 'External Agent', 'plural': 'External Agents', 'article': 'an'},
    {'name': 'Subagent', 'cls': 'session', 'subject': 'Subagent: ', 'match': 'prefix', 'shape': 'free', 'created_by': 'spawner', 'exclusive': False, 'version_bound': False, 'reply_frame': False, 'blocks_save': True, 'survey': 'count', 'survey_key': 'orphan_subagents', 'notice': '{count} orphaned Subagent record(s) from a crashed spawn; ^refresh can clear them', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Subagent', 'log_by': None, 'title': 'Subagent', 'plural': 'Subagents', 'article': 'a'},
    {'name': 'CX', 'cls': 'delegated', 'token': 'CX', 'carries_blocks': True, 'agent_type': 'axis-cx', 'write_scope': (('_Axis/CX/', True), ('_Temp/', False)), 'deny': None},
    {'name': 'Wiki', 'cls': 'delegated', 'token': 'WIKI', 'carries_blocks': True, 'agent_type': 'axis-wiki', 'write_scope': (('_Wiki/', False), ('_Axis/Wiki/', False), ('_Temp/', False)), 'deny': None},
    {'name': 'Local', 'cls': 'delegated', 'token': 'LOCAL', 'carries_blocks': False, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'General', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': 'axis-general', 'write_scope': None, 'deny': ('_Axis/Agents/', '_Axis/Flags/', '_Axis/Secrets/', '_Axis/Submissions/', '_Axis/Messages/', '_Axis/Teams/', '_Axis/Jobs/', '_Axis/Schedules/', '_Axis/Updates/', '.git/', '.claude/', '.codex/', '.gemini/')},
)
ROLE_LEDGER={'issuers': ('external', 'main', 'worker'), 'submission_schemas': ('axis.external-submission/v1',), 'proposal_member_subject': 'Subagent: External proposal Team', 'survey_keys': ('fresh_external', 'orphan_subagents'), 'proposal_owners': (('External:', 'external'),)}
# END GENERATED: role-table

NAME=re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md')
FAMILIES=('Agents','Audit','CX','Followups','Ideas','Logs','Notes','Reminders','Reviews','Snapshots','Status','Supervision','Tasks','Teams','Messages','Jobs','Schedules')
WORM={'Logs':'a Log','Snapshots':'a Snapshot','CX':'a CX report','Audit':'an Audit report','Reviews':'a legacy Review',
      'Status':'a legacy Status report','Supervision':'a Supervision record','Teams':'a Team charter','Messages':'a Message','Jobs':'a Job mandate'}
IGNORED=('.gitkeep','.DS_Store')
WRITE_TOOLS=('Edit','Write','MultiEdit','NotebookEdit')
PATH_TOOLS=WRITE_TOOLS+('Read','Grep','Glob')
# Delegated helper rows by host agent type: a write scope of (folder prefix, new files only?) or a deny list.
HELPERS={r['agent_type']:r for r in ROLE_TABLE if r['cls']=='delegated' and r['agent_type']}
# Guarded session rows: the OpenClaw plugin's --external flag or --role {lower-case name}.
GUARDED={r['name'].lower():r for r in ROLE_TABLE if r['cls']=='session' and r['guard']}
FLAGS={r['guard']['flag']:r for r in GUARDED.values() if r['guard']['flag']}
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
    if family=='ColdStorage':return 'cold locators are write-once' if exists else None
    if len(parts)>3 and parts[2]=='Archive' and parts[-1]!='COLD.md':return 'archived history is write-once' if exists else None
    if family=='Archive':return 'archived history is write-once' if exists else None
    if family=='Updates':return None if parts[-1]=='operation.lck' or not exists else 'update evidence is write-once'
    if family=='Messages' and len(parts)>3:
        if exists:return 'a Message and its retained support are write-once; adoption repairs use the verified transaction engine'
        if parts[-1].endswith('.md') and not NAME.fullmatch(parts[-1]):return 'a new Message requires a valid timestamp identity'
        return None
    if family not in FAMILIES or len(parts)!=3:return None
    if not exists:
        return None if NAME.fullmatch(parts[2]) else f'a new record in _Axis/{family}/ must be named yyyy.mm.dd.hh.mm.ss.xxxZ.md (_Axis/Practices/Timestamps.md)'
    if family in WORM:return WORM[family]+' is write-once: use the exact record-check.py correct protocol and LinkMaintenance Permissions for reference repairs; otherwise write a new record'
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
    if agent not in HELPERS:return None
    if rel.startswith('_Wiki/_Inbox/'):return 'helpers never create or edit files in _Wiki/_Inbox/'
    row=HELPERS[agent];allowed=row['write_scope']
    if allowed is None:
        hit=next((d for d in row['deny'] if rel.startswith(d) or rel+'/'==d),None)
        return f'a {row["name"]} helper does not write in {hit}' if hit else None
    for prefix,new_only in allowed:
        if rel.startswith(prefix):return 'this helper only adds new files there' if new_only and exists else None
    return f'the {agent[5:].upper()} helper writes only in '+', '.join(p for p,_ in allowed)

PLACES={'subfolders':'Project Subfolders','_Axis/Submissions/':'_Axis/Submissions/','_Temp/':'_Temp/'}

def guarded(row,rel,exists,write):
    """A refusal reason for a guarded session role's file tool on rel, or None."""
    who=row['article']+' '+row['title'];places=row['guard']['new_files']
    if rel==SECRETS or rel.startswith(SECRETS+'/'):return who+' never uses _Axis/Secrets/'
    if not write:return None
    if exists:return who+' adds new files only and never changes an existing file'
    parts=rel.split('/')
    if rel.startswith('_Axis/Submissions/') and '_Axis/Submissions/' in places:
        return None if len(parts)==3 and re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md',parts[-1]) else 'Submissions permits only a new timestamped detail in the queue'
    if ('_Temp/' in places and rel.startswith('_Temp/')) or ('subfolders' in places and len(parts)>=2 and not parts[0].startswith(('_','.'))):return None
    names=[PLACES[x] for x in places]
    return who+' writes new files only in '+(names[0] if len(names)==1 else ', '.join(names[:-1])+' or '+names[-1])

def external(rel,exists,write):
    """The --external profile (kept for callers of the earlier helper API)."""
    return guarded(FLAGS['--external'],rel,exists,write)

def reconciling(root,rel):
    """An adoption has begun reconciliation (started, not consumed) and its frozen plan names rel."""
    temp=root/'_Temp'
    if not temp.is_dir() or temp.is_symlink():return False
    for journal in temp.glob('Update-*'):
        if journal.is_symlink() or not journal.is_dir() or not (journal/'reconciliation-start.json').is_file() or (journal/'consumed.json').exists():continue
        try:plan=json.loads((journal/'start.json').read_text())['plan']
        except (OSError,ValueError,KeyError,TypeError):continue
        if isinstance(plan.get('reconciliation'),dict) and rel in plan['reconciliation']:return True
    return False

def verdict(root,rel,exists,agent,tool):
    if agent and (rel==SECRETS or rel.startswith(SECRETS+'/')):return 'helpers never read or write _Axis/Secrets/'
    if tool not in WRITE_TOOLS:return None
    refusal=write_once(root,rel,exists)
    # Main's reconciliation edit is bound later by the completion receipt; nothing else is exempt.
    if refusal and not agent and rel.split('/')[1:2] in (['Tasks'],['Followups']) and reconciling(root,rel):refusal=None
    return refusal or (helper_scope(agent,rel,exists) if agent else None)

def new_text(root,rel,tool,ti):
    """The file's text after this Write, Edit or MultiEdit, or None when it cannot be known."""
    if tool=='Write':return ti.get('content') if isinstance(ti.get('content'),str) else None
    try:text=(root/rel).read_text(encoding='utf-8',errors='replace')
    except OSError:return None
    edits=ti.get('edits') if tool=='MultiEdit' else [ti]
    for e in edits or []:
        old,new=e.get('old_string'),e.get('new_string')
        if not isinstance(old,str) or not isinstance(new,str) or old not in text:return None
        text=text.replace(old,new) if e.get('replace_all') else text.replace(old,new,1)
    return text

def references(root,rel,tool,ti):
    """A refusal reason when the write adds a malformed or dangling identifier, or None."""
    try:
        spec=importlib.util.spec_from_file_location('record_check',root/'_Axis/Resources/record-check.py')
        rc=importlib.util.module_from_spec(spec);spec.loader.exec_module(rc)
        after=new_text(root,rel,tool,ti)
        if after is None:return None
        if rel==rc.EXCEPTIONS_PATH:
            try:rc.load_exceptions(root,reader=lambda _:after.encode('utf-8'))
            except rc.ExceptionsError as error:return 'invalid reference exceptions: '+str(error)
            return None
        if not rc.in_scope(rel):return None
        try:entries=rc.load_exceptions(root)
        except rc.ExceptionsError as error:return 'invalid reference exceptions: '+str(error)
        arch,known,names,_=rc.context(root,[],False);f=root/rel
        try:before_bytes=f.read_bytes()
        except OSError:before_bytes=b''
        before=before_bytes.decode('utf-8','replace')
        old={}
        for k,_,d,_ in rc.apply_exceptions(entries,rel,before_bytes,rc.scan(root,arch,known,names,f,before,rel)):
            if k in ('MALFORMED','UNRESOLVED'):old[(k,d)]=old.get((k,d),0)+1
        bad=[]
        for k,i,d,_ in rc.apply_exceptions(entries,rel,after.encode('utf-8'),rc.scan(root,arch,known,names,f,after,rel)):
            if k not in ('MALFORMED','UNRESOLVED'):continue
            if old.get((k,d),0):old[(k,d)]-=1
            else:bad.append(f'{d} (line {i}, {"malformed" if k=="MALFORMED" else "names nothing"})')
    except Exception:return None
    if not bad:return None
    return 'this write adds record identifiers that are malformed or name nothing: '+', '.join(bad[:5])+'. Copy each identifier from disk, or write (missing) right after one you mean to report as missing'

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
    row=FLAGS.get(sys.argv[1]) if len(sys.argv)==4 else GUARDED.get(sys.argv[2]) if len(sys.argv)==5 and sys.argv[1]=='--role' else None
    if row is not None:
        tool,path=sys.argv[-2].lower(),sys.argv[-1];root=Path.cwd().resolve();rel=relative(root,path)
        if rel is None:return 0
        exists=(root/rel).exists();write=tool not in ('read','grep','glob','ls','find')
        why=guarded(row,rel,exists,write) or (write_once(root,rel,exists) if write else None)
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
    why=verdict(root,rel,(root/rel).exists(),agent,tool) or (references(root,rel,tool,ti) if tool in ('Write','Edit','MultiEdit') else None)
    if why:
        print(f'Axis guardrail: {why} ({rel}). See _Axis/Rules/RecordsAndWORM.md and _Axis/Rules/Subagents.md.',file=sys.stderr);return 2
    return 0

if __name__=='__main__':sys.exit(main())
