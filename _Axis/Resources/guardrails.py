#!/usr/bin/env python3
"""Optional host hook: refuse, before it happens, a tool call that breaks an Axis rule the host can see.

Installed by `^install guardrails` as a Claude Code PreToolUse hook. For every Agent: no edit to a write-once record
(Logs, Snapshots, CX, Audit, Supervision, Teams, Messages, Jobs, archived history, update evidence, finished Tasks, Follow-Ups and Reminders)
and no new record with a malformed name. A write to a record, index, Plan or Memo may not add an identifier that is
malformed or names nothing (record-check.py's scan; `(missing)` after an identifier reports it as missing). For a helper running as an Axis agent type
(the delegated role rows of the generated role table), also: writes only inside that role's folders, and no tool may touch `_Axis/Secrets/`.
For every helper, Axis type or not: no write to a governing file, no Agent or Task tool (helpers start no agents), and no
shell call to a state-changing `_Axis/Resources/*.py` helper (Tracking, envelope checks and read-only record checks pass).
For an OpenClaw agent listed under a guarded session role, the `axis-guardrails` plugin calls `--external {tool} {path}` or
`--role {name} {tool} {path}`: no `_Axis/Secrets/`, no change to an existing file, and new files only where the role's row
allows (today Project Subfolders, `_Axis/Submissions/` and `_Temp/`). The Claude Code hook reads JSON from stdin; both exit 2 with a reason to refuse, and 0 otherwise.
Python 3 standard library only; reads paths and status lines, never prints file contents. It does not see what a
shell command or helper script writes. Adoption repairs run only through the verified, scope-bound update engine; they do not disable this hook for ordinary edits. During an adoption's reconciliation, Main may edit the Tasks and Follow-Ups its frozen plan names. It never affects User's own editing.

3.16 role link: a Claude Code session the `axis` launcher started for a declared role carries AXIS_ROLE (and
AXIS_SURFACE); the hook then applies that role's guard to the session's own calls, and every declared role runs only
read-only git (log, status, diff, show and listing forms). A role serving other people also reads only its surface's
read scope and the Axis workflow files, has no outbound tools and runs only Axis's own per-turn helpers in the shell;
an Observer writes nothing, and its shell runs only its own admission check. Every agent session: the User-mode
`axis retire` and `axis start` are refused (they are for the User's own terminal); agent mode passes.

Self-test without a host: python3 _Axis/Resources/guardrails.py --check {project-relative path} [--new] [--agent {type}]"""
import importlib.util,json,os,re,shlex,sys
from pathlib import Path

# BEGIN GENERATED: role-table
# Compiled from _Axis/Roles/ at release; edit the role files, never this region.
ROLE_TABLE=(
    {'name': 'Main', 'cls': 'session', 'subject': 'Main: session', 'match': 'exact', 'shape': 'exact4', 'created_by': 'claim', 'exclusive': True, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': None, 'survey_key': None, 'notice': None, 'issuer': 'main', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Main', 'log_by': 'Main Agent', 'title': 'Main Agent', 'plural': 'Main Agents', 'article': 'the', 'serves': 'User', 'families': 'all', 'recovery': ('@core', '@role', '_Axis/INSTRUCTIONS.md', '_Axis/MINDSET.md', '_Axis/DIRECTIVES.md', '@overlay', '@state')},
    {'name': 'Auxiliary', 'cls': 'session', 'subject': 'Auxiliary: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'helper', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_auxiliary', 'notice': 'An Auxiliary Agent is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': True, 'proposal_issuer': 'auxiliary', 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'externalAgents', 'flag': '--external', 'block_spawn': True, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'Auxiliary', 'log_by': 'Auxiliary Agent', 'title': 'Auxiliary Agent', 'plural': 'Auxiliary Agents', 'article': 'an', 'serves': 'User', 'families': ('Ideas', 'Logs', 'Notes'), 'recovery': ('@core', '@role', '_Axis/Practices/Agents.md > Auxiliary Agent', '@state')},
    {'name': 'Assistant', 'cls': 'session', 'subject': 'Assistant: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'helper', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_assistant', 'notice': 'An Assistant is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'assistantAgents', 'flag': None, 'block_spawn': False, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'Assistant', 'log_by': 'Assistant', 'title': 'Assistant', 'plural': 'Assistants', 'article': 'an', 'serves': 'User', 'families': ('Ideas', 'Logs', 'Notes'), 'recovery': ('@core', '@role', '@state')},
    {'name': 'GroupAgent', 'cls': 'session', 'subject': 'Group Agent: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'helper', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_groupagent', 'notice': 'A Group Agent is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'groupAgents', 'flag': None, 'block_spawn': True, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'GroupAgent', 'log_by': 'Group Agent', 'title': 'Group Agent', 'plural': 'Group Agents', 'article': 'a', 'serves': 'User and named participants', 'families': ('Ideas', 'Logs', 'Notes'), 'recovery': ('@core', '@role', '@state')},
    {'name': 'Observer', 'cls': 'session', 'subject': 'Observer: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'none', 'exclusive': False, 'version_bound': False, 'reply_frame': True, 'blocks_save': False, 'survey': None, 'survey_key': None, 'notice': None, 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': {'config_key': 'observerAgents', 'flag': None, 'block_spawn': True, 'new_files': ()}, 'reference_word': 'Observer', 'log_by': None, 'title': 'Observer', 'plural': 'Observers', 'article': 'an', 'serves': 'anyone on the surface', 'families': (), 'recovery': ('@core', '@role')},
    {'name': 'Subagent', 'cls': 'session', 'subject': 'Subagent: ', 'match': 'prefix', 'shape': 'free', 'created_by': 'spawner', 'exclusive': False, 'version_bound': False, 'reply_frame': False, 'blocks_save': True, 'survey': 'count', 'survey_key': 'orphan_subagents', 'notice': '{count} orphaned Subagent record(s) from a crashed spawn; ^refresh can clear them', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Subagent', 'log_by': None, 'title': 'Subagent', 'plural': 'Subagents', 'article': 'a', 'serves': 'spawner', 'families': 'delegated', 'recovery': None},
    {'name': 'CX', 'cls': 'delegated', 'token': 'CX', 'carries_blocks': True, 'agent_type': 'axis-cx', 'write_scope': (('_Axis/CX/', True), ('_Temp/', False)), 'deny': None},
    {'name': 'Wiki', 'cls': 'delegated', 'token': 'WIKI', 'carries_blocks': True, 'agent_type': 'axis-wiki', 'write_scope': (('_Wiki/', False), ('_Axis/Wiki/', False), ('_Temp/', False)), 'deny': None},
    {'name': 'Local', 'cls': 'delegated', 'token': 'LOCAL', 'carries_blocks': False, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'General', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': 'axis-general', 'write_scope': None, 'deny': ('_Axis/Agents/', '_Axis/Flags/', '_Axis/Secrets/', '_Axis/Submissions/', '_Axis/Messages/', '_Axis/Teams/', '_Axis/Jobs/', '_Axis/Schedules/', '_Axis/Updates/', '.git/', '.claude/', '.codex/', '.gemini/')},
    {'name': 'Lookup', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': 'axis-lookup', 'write_scope': (), 'deny': None},
    {'name': 'Worker', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'TeamMember', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'TeamLeader', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': None, 'write_scope': None, 'deny': None},
)
ROLE_LEDGER={'issuers': ('auxiliary', 'external', 'main', 'worker'), 'submission_schemas': ('axis.external-submission/v1',), 'proposal_member_subject': 'Subagent: External proposal Team', 'survey_keys': ('fresh_assistant', 'fresh_auxiliary', 'fresh_external', 'fresh_groupagent', 'orphan_subagents'), 'proposal_owners': (('External:', 'external'), ('Auxiliary:', 'auxiliary'))}
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
# Governing files: what delegated agents follow. Helpers never write them; Main applies a granted change.
GOVERNING=('_Axis/PRINCIPLES.md','_Axis/RULES.md','_Axis/Rules/','_Axis/PRACTICES.md','_Axis/Practices/','_Axis/DIRECTIVES.md','_Axis/MINDSET.md',
           '_Axis/GLOSSARY.md','_Axis/MANIFEST.md','_Axis/Roles/','_Axis/Resources/','_Axis/Commands/','_Axis/INSTRUCTIONS.md','_Axis/PROJECT.md',
           '_Axis/SETTINGS.md','_Axis/SURFACES.md','AGENTS.md','CLAUDE.md','GEMINI.md')
SPAWN_TOOLS=('Agent','Task')
# Shell calls a helper may make to Axis's own scripts: script -> subcommands that change no shared state.
HELPER_SCRIPTS={'startup-state.py':('track',),'envelope.py':('new','check','assemble','instructions','governance'),'guardrails.py':('--check',),'record-check.py':('names','links','write-once')}
# A run of an Axis helper: an interpreter (or ./) followed by a path ending in _Axis/Resources/{script}.py, outside a
# development copy (_Dev/...), then its arguments up to the next shell separator.
SCRIPT_CALL=re.compile(r'(?:\bpython3?|\bsh|\bbash|(?:^|[\s;&|(])\.)(?:\s+-[A-Za-z]+)*\s*(\S*?)_Axis/Resources/([A-Za-z0-9_.-]+\.py)([^;&|\n]*)')
# User-mode role actions belong to the User's own terminal; agent mode names --session-of-caller or --source-root.
ROLE_ACTION=re.compile(r'(?:^|[;&|(\n]|\bthen|\bdo|\bexec)\s*(?:env\s+(?:\S+=\S*\s+)*)?(?:(?:\S*/)?python3?\s+(?:-\S+\s+)*)?(?:\S*/)?(?:axis|axis-roles\.py)\s+(retire|start)\b([^;&|\n]*)')
# Declared roles serving other people: the Axis workflow files they may read besides their surface's read scope.
WORKFLOW_READ=('_Axis/RULES.md','_Axis/PRACTICES.md','_Axis/PRINCIPLES.md','_Axis/GLOSSARY.md','_Axis/MANIFEST.md','_Axis/CHANGELOG.md','_Axis/SETTINGS.md',
               '_Axis/Rules/','_Axis/Practices/','_Axis/Roles/','_Axis/Commands/','_Axis/Resources/','_Axis/Agents/','_Axis/Updates/',
               '_Axis/Merges/','_Axis/Flags/','AGENTS.md','CLAUDE.md','GEMINI.md','README.md')
# Their shell runs only Axis's own per-turn and record helpers; a role that writes nothing runs only its own admission check.
ROLE_SCRIPTS={'turn.py':('',),'startup-state.py':('admit','track','record'),'record-check.py':('names','links','write-once')}
READ_ONLY_SCRIPTS={'startup-state.py':('admit',)}
# One helper call per command: no separators, newlines, redirections, substitutions or environment changes.
ROLE_COMMAND=re.compile(r'[ \t]*python3?[ \t]+(?:-B[ \t]+)?_Axis/Resources/[A-Za-z-]+\.py(?:[ \t]+[A-Za-z0-9._:/@=+,-]+|[ \t]+\'[^\'\r\n]*\'|[ \t]+"[^"$`\\\r\n]*")*[ \t]*')
# Git for a declared role: read-only subcommands pass; every other subcommand is Main's. Listing forms of branch, tag,
# remote, stash, worktree and reflog pass too.
GIT_READ=('log','status','diff','show','blame','shortlog','describe','rev-parse','rev-list','ls-files','ls-tree','cat-file','grep','help','version')
GIT_LIST_FLAGS={'branch':('-a','-r','-v','-vv','-l','--list','--all','--remotes','--verbose','--show-current'),'tag':('-l','--list'),'remote':('-v','--verbose'),'reflog':()}
GIT_LIST_FIRST={'stash':('list','show'),'worktree':('list',),'reflog':('show',)}
GIT_VALUE_OPTS=('-C','-c','--git-dir','--work-tree','--namespace','--exec-path','--config-env')
WRAPPERS=('env','command','exec','sudo','nohup','time','nice','xargs','builtin','then','do','else','!')
OUTBOUND=('WebFetch','WebSearch')
AGENT_LAUNCH=re.compile(r'(?:^|[;&|(]|\bthen|\bdo|\bexec)\s*(?:env\s+(?:\S+=\S*\s+)*)?(?:\S*/)?(?:claude|codex|openclaw|gemini)(?:\s|$)')

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
    if not allowed:return f'a {row["name"]} helper writes nothing'
    return f'the {agent[5:].upper()} helper writes only in '+', '.join(p for p,_ in allowed)

PLACES={'subfolders':'Project Subfolders','_Axis/Submissions/':'_Axis/Submissions/','_Temp/':'_Temp/'}

def guarded(row,rel,exists,write):
    """A refusal reason for a guarded session role's file tool on rel, or None."""
    who=row['article']+' '+row['title'];places=row['guard']['new_files']
    if secret(rel):return who+' never uses _Axis/Secrets/'
    if not write:return None
    if not places:return who+' writes nothing'
    if exists:return who+' adds new files only and never changes an existing file'
    parts=rel.split('/')
    if rel.startswith('_Axis/Submissions/') and '_Axis/Submissions/' in places:
        return None if len(parts)==3 and re.fullmatch(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\.md',parts[-1]) else 'Submissions permits only a new timestamped detail in the queue'
    if ('_Temp/' in places and rel.startswith('_Temp/')) or ('subfolders' in places and len(parts)>=2 and not parts[0].startswith(('_','.'))):return None
    if not places:return who+' writes nothing'
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

def governing(rel):
    return any(rel==g or (g.endswith('/') and rel.startswith(g)) for g in GOVERNING)

def helper_command(command):
    """A refusal reason when a helper's shell command runs a state-changing Axis helper script or starts an agent from
    the command line, or None. A mistake-catcher: it reads the command text, not what the shell finally runs."""
    if AGENT_LAUNCH.search(command):return 'helpers never start other agents, including from the command line'
    for m in SCRIPT_CALL.finditer(command):
        if '_Dev/' in m[1]:continue  # a development copy, not this project's helpers
        allowed=HELPER_SCRIPTS.get(m[2]);words=[w for w in m[3].split() if w];i=0
        while i<len(words) and words[i].startswith('-'):i+=1+(words[i] in ('--root','--candidate-root','--controller-root'))
        sub=words[i] if i<len(words) else ''
        if allowed is None or sub not in allowed or '$(' in m[3] or '`' in m[3] or (m[2]=='envelope.py' and '--write' in words):
            return f'helpers never run state-changing Axis helpers ({m[2]})'
    return None

def verdict(root,rel,exists,agent,tool):
    if agent and secret(rel):return 'helpers never read or write _Axis/Secrets/'
    if agent and rel=='_Axis/INSTRUCTIONS.md':return 'helpers never read the User\'s Instructions; the contract carries the part meant for them'
    if tool not in WRITE_TOOLS:return None
    if agent and governing(rel):return 'helpers never write governing files; the spawner applies a change the contract grants'
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

def declared_row():
    """The guarded session row the launcher declared for this Claude Code session (AXIS_ROLE), or None; 'unknown' when
    AXIS_ROLE names no role."""
    value=re.sub(r'\s+','',os.environ.get('AXIS_ROLE','')).lower()
    if not value:return None
    value='auxiliary' if value=='external' else value
    row=next((r for r in ROLE_TABLE if r['cls']=='session' and value in (r['name'].lower(),r['title'].replace(' ','').lower())),None)
    if row is None:return 'unknown'
    return row if row['guard'] else None

def read_scope(root):
    """The read scope of AXIS_SURFACE's row in the surface table: a tuple of Project Subfolders, 'project', or None when
    it cannot be established (which refuses every read outside the workflow files)."""
    surface=os.environ.get('AXIS_SURFACE','').strip()
    try:
        spec=importlib.util.spec_from_file_location('startup_state_scope',root/'_Axis/Resources/startup-state.py')
        state=importlib.util.module_from_spec(spec);spec.loader.exec_module(state)
        row=state.Admission(str(root)).surfaces().get(surface)
    except Exception:return None
    if row is None:return None
    return 'project' if row[1] is None else row[1]

def secret(rel):
    """Secrets, compared without case: a case-insensitive volume reaches the same folder by any spelling."""
    return rel.lower()==SECRETS.lower() or rel.lower().startswith(SECRETS.lower()+'/')

def git_change(command,depth=0):
    """The first git subcommand in a shell command that may change state (anything outside the read-only forms), or
    None. A mistake-catcher: it reads the command text, not what the shell finally runs."""
    for line in command.splitlines():
        try:tokens=list(shlex.shlex(line,posix=True,punctuation_chars=True))
        except ValueError:tokens=re.findall(r'[^\s;&|()`<>]+|[;&|()`<>]+',line)
        words=[]
        for t in tokens+[';']:
            if t and all(ch in ';&|()`<>' for ch in t):
                hit=git_words(words,depth)
                if hit:return hit
                words=[]
            else:words.append(t)
    return None

def git_words(words,depth):
    """git_change for one simple command's words."""
    i=0;wrapped=False
    while i<len(words):
        w=words[i]
        if w in WRAPPERS or re.fullmatch(r'[A-Za-z_]\w*=.*',w):wrapped=wrapped or w in WRAPPERS;i+=1
        elif wrapped and w.startswith('-'):i+=1+(w in ('-u','-n'))
        else:break
    if i>=len(words):return None
    name=os.path.basename(words[i])
    if name in ('sh','bash','zsh','dash','eval') and depth<3:
        text=words[words.index('-c',i+1)+1] if '-c' in words[i+1:-1] else ' '.join(words[i+1:]) if name=='eval' else ''
        return git_change(text,depth+1) if text else None
    if name!='git':return None
    j=i+1
    while j<len(words) and words[j].startswith('-'):j+=1+(words[j] in GIT_VALUE_OPTS)
    if j>=len(words):return None
    sub,rest=words[j],words[j+1:]
    if sub in GIT_READ or (sub in GIT_LIST_FLAGS and all(w in GIT_LIST_FLAGS[sub] for w in rest)):return None
    if sub in GIT_LIST_FIRST and rest[:1] and rest[0] in GIT_LIST_FIRST[sub]:return None
    return sub

def role_refusal(root,row,tool,ti,event):
    """A refusal reason for a declared session's own call under its role row, or None."""
    others=row['serves']!='User';who=row['article']+' '+row['title']
    if tool in SPAWN_TOOLS and row['guard']['block_spawn']:return who+' never starts agents'
    if others and (tool in OUTBOUND or str(tool).startswith('mcp__')):return who+' has no outbound tools'
    if tool=='Bash':
        command=ti.get('command') if isinstance(ti.get('command'),str) else ''
        if SECRETS.lower() in command.lower():return who+' never uses _Axis/Secrets/'
        if re.search(r'_Axis/Resources/boot\.py',command):return who+' never starts as Main'
        sub=git_change(command)
        if sub:return f'{who} makes no Git changes (git {sub}); Main does, and read-only git (log, status, diff, show) passes'
        if others:
            m=SCRIPT_CALL.match(command.strip())
            if not ROLE_COMMAND.fullmatch(command) or m is None:return who+' runs only Axis\'s own per-turn helpers in the shell, one call per command'
            words=[w.strip('"\'') for w in m[3].split() if w];i=0
            while i<len(words) and words[i].startswith('-'):i+=1+(words[i] in ('--root',))
            sub=words[i] if i<len(words) else ''
            if not row['guard']['new_files']:
                # A role that writes nothing runs only its own admission check, which writes nothing for it.
                role=words[words.index('--role')+1].replace(' ','').lower() if '--role' in words[:-1] else ''
                if sub not in READ_ONLY_SCRIPTS.get(m[2],()) or role not in (row['name'].lower(),row['title'].replace(' ','').lower()):
                    return who+' runs only its own admission check in the shell (startup-state.py admit --role '+row['name']+')'
                return None
            if m[2] not in ROLE_SCRIPTS or (ROLE_SCRIPTS[m[2]]!=('',) and sub not in ROLE_SCRIPTS[m[2]]):return who+' runs only Axis\'s own per-turn helpers in the shell, one call per command'
        return None
    if tool not in PATH_TOOLS:return None
    path=ti.get('file_path') or ti.get('notebook_path') or ti.get('path')
    if not isinstance(path,str) or not path:
        # A search with no path searches the project root, which a role serving others may not read whole.
        if others and tool in ('Grep','Glob'):return who+' searches only inside a folder its surface row names; give that folder as the path'
        return None
    rel=relative(root,path)
    if rel is None:return who+' stays inside this project' if others else None
    if secret(rel):return who+' never uses _Axis/Secrets/'
    write=tool in WRITE_TOOLS;exists=(root/rel).exists()
    why=guarded(row,rel,exists,write) or (write_once(root,rel,exists) if write else None)
    if why or not others or write:return why
    if rel in ('','.'):return who+' reads only the folders its surface row names and the Axis workflow files'
    scope=read_scope(root)
    if any(rel==w or rel+'/'==w or (w.endswith('/') and rel.startswith(w)) for w in WORKFLOW_READ):return None
    if scope=='project':return None
    if scope and any(rel==f or rel.startswith(f+'/') for f in scope):return None
    return who+' reads only the folders its surface row names and the Axis workflow files'

def role_action(command):
    """A refusal reason when an agent runs a User-mode `axis retire` or `axis start`, or None."""
    for m in ROLE_ACTION.finditer(command):
        args=m[2]
        if m[1]=='retire' and '--session-of-caller' not in args:return 'User mode of `axis retire` is for your own terminal; a supervising Main uses agent mode (^^stop)'
        if m[1]=='start' and '--source-root' not in args:return 'User mode of `axis start` is for your own terminal; a supervising Main uses ^^start'
    return None

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
    # A helper is a call from a spawned agent (agent_id); agent_type only picks its row. A session run as an agent type
    # without agent_id is a top-level session, not a helper.
    agent=(event.get('agent_type') or 'helper') if event.get('agent_id') else None
    if tool=='Bash' and isinstance(ti.get('command'),str):
        why=role_action(ti['command'])
        if why:print(f'Axis guardrail: {why}.',file=sys.stderr);return 2
    row=declared_row() if not agent else None
    if row=='unknown':print('Axis guardrail: AXIS_ROLE names no Axis role; this session gets no service until the declaration is corrected.',file=sys.stderr);return 2
    if row is not None:
        why=role_refusal(root,row,tool,ti,event)
        if why:print(f'Axis guardrail: {why}. See _Axis/Roles/{row["name"]}.md.',file=sys.stderr);return 2
    if tool=='Bash' and agent and isinstance(ti.get('command'),str) and SECRETS.lower() in ti['command'].lower():
        print('Axis guardrail: helpers never read or write _Axis/Secrets/.',file=sys.stderr);return 2
    if tool=='Bash' and agent and isinstance(ti.get('command'),str):
        why=helper_command(ti['command'])
        if why:print(f'Axis guardrail: {why}. See _Axis/Roles/Delegating.md.',file=sys.stderr);return 2
    if tool in SPAWN_TOOLS and agent:
        print('Axis guardrail: helpers never start other agents; a granted start goes through the spawner. See _Axis/Roles/Delegating.md.',file=sys.stderr);return 2
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
