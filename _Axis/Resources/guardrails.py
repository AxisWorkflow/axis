#!/usr/bin/env python3
"""Optional host hook: refuse, before it happens, a tool call that breaks an Axis rule the host can see.

Installed by `^install guardrails` as a Claude Code PreToolUse hook. For every Agent: no edit to a write-once record
(Logs, Snapshots, CX, Audit, Supervision, Teams, Messages, Jobs, archived history, update evidence, finished Tasks, Follow-Ups and Reminders)
and no new record with a malformed name. A write to a record, index, Plan or Memo may not add an identifier that is
malformed or names nothing (record-check.py's scan; `(missing)` after an identifier reports it as missing). For a helper running as an Axis agent type
(the delegated role rows of the generated role table), also: writes only inside that role's folders, and no tool may touch `_Axis/Secrets/`.
For every helper, Axis type or not: no write to a governing file, no Agent, Task or other tool that starts or schedules
agent work (helpers start no agents), and no shell call, Monitor or PowerShell command included, to a state-changing
`_Axis/Resources/*.py` helper (Tracking, envelope checks and read-only record checks pass).
For an OpenClaw agent listed under a guarded session role, the `axis-guardrails` plugin calls `--external {tool} {path}` or
`--role {name} {tool} {path}`: no `_Axis/Secrets/`, no change to an existing file, and new files only where the role's row
allows (today Project Subfolders, `_Axis/Submissions/` and `_Temp/`). The Claude Code hook reads JSON from stdin; both exit 2 with a reason to refuse, and 0 otherwise.
Python 3 standard library only; reads paths and status lines, never prints file contents. It does not see what a
shell command or helper script writes. Adoption repairs run only through the verified, scope-bound update engine; they do not disable this hook for ordinary edits. During an adoption's reconciliation, Main may edit the Tasks and Follow-Ups its frozen plan names. It never affects User's own editing.

3.16 role link: a Claude Code session the `axis` launcher started for a declared role carries AXIS_ROLE (and
AXIS_SURFACE); the hook then applies that role's guard to the session's own calls, and every declared role runs only
read-only git (log, status, diff, show and listing forms); a Monitor or PowerShell command of a role serving the User
gets the rules its Bash command has, and an Auxiliary Agent, whose row blocks starting agents, is refused Agent, Task
and the newer tools that start or schedule agent work. A role serving other people also reads only the Axis
workflow files and the folders that both its live surface row and the read scope the launcher pinned at launch
(AXIS_READ_SCOPE, checked at admission) name, has no outbound tools, is refused every other tool this hook receives
outside the tools its role is offered, and runs only Axis's own per-turn helpers and the request helper's `submit` in the shell;
an Observer writes nothing, and its shell runs only its own admission check. A Group Agent or Assistant sends requests to
Main only through that `submit`: it writes nothing into `_Axis/Submissions/`, and no other shell command of its names
that folder. Every agent session: the User-mode `axis retire` and `axis start` are refused (they are for the User's own
terminal; Main through Bash, its Monitor and PowerShell calls passing as before the matcher named them); agent mode
passes. Every Secrets refusal folds letter case fully, the --role and --external route's included (a long s reaches the
folder on a case-insensitive volume). The hook opens no script whose real path names any spelling of the folder that full
case folding maps to it. Where it parses a shell command (Bash for every session; Monitor and PowerShell for Main, a role
serving the User and a helper), it refuses running, sourcing or executing a script whose real path reaches this project's
own `_Axis/Secrets/` through a spelling other than the exact one, Main included, and a script it no longer reads because a
spelling only full case folding maps (such as a long s) names the folder elsewhere in its path; a declared role or helper
gets its own Secrets reason, and Main's exact spelling runs unread as before. It finds this project's own folder by
identity too, so a path through another mount (such as macOS's /System/Volumes/Data) counts. It parses each simple
command with its wrappers, compounds, pipes and same-command assignments, bash's `$'...'` quoting, a leading `$PWD`
(the project root, which relative paths are read from) or `~` (`$HOME`), and nested shell, eval, env -S and interpreter
text only on lines naming axis in any letter case; each line is read first as before, and a script it reaches only
through those added readings it opens only inside the project. For this refusal it does not follow: a change of
directory (`cd`, `pushd`, `env -C`); exported, inherited or other variables beyond a leading `$PWD` (`BASH_ENV`, `$HOME`
and `$IFS` included); variables set by builtins (`declare`, `local`, `readonly`, `printf -v`); parameter-expansion
operators (`${X:-F/q.sh}`, `${PWD%/}`); positional parameters (`set --`, `$1`, the arguments after `bash -c` text); a
redirection written before the command name (`>/dev/null sh F/q.sh`); links or files the command itself makes before the
run (`ln -s`); a link to the Secrets folder that exists before the command; command substitution, quoted or not; process
substitution; globs and brace expansion; a backslash-newline inside a word; a script file given to an interpreter
(`python3 F/q.py`); shells other than sh, bash, zsh, dash and ksh (fish, csh, tcsh, busybox, pwsh); a shell or wrapper name in another letter case (`SH`, `Bash`, `/BIN/SH`); a function defined with `function NAME { ...; }`; commands that run
another from their arguments or input, other than the wrappers it reads (`env`, `exec`, `nice`, `sudo`, `doas`,
`stdbuf`, `caffeinate`, `timeout`, `nohup`, `time`, `setsid`, `script`, `xargs` with its arguments), such as `find
-exec`, `xargs -I` or xargs input, `watch`, `osascript`, `arch`, `flock`, `sandbox-exec`, `su -c`, `trap` and `coproc`;
an option of one of those wrappers that takes a value, other than the ones it reads (`env -P`); `hash -p` and aliases;
nesting deeper than three levels; escapes, concatenation or encodings inside interpreter strings or piped input; bash's
`$'...'` quoting written with an escaped dollar sign inside double-quoted nested shell, eval or `env -S` text; `env -S`
with its text attached (`env -S'sh F/q.sh'`); `~user`, `~+` or `~-`; the runs inside a script's own text; or
PowerShell's own syntax (backslash separators, the backtick escape, `Invoke-Expression` or `iex`, `Start-Process`). Some
of these are still refused where the misspelled path also stands whole as a word the hook reads as a run, as in `` sh
`echo F/q.sh` ``, `echo F/q.sh | xargs sh`, `echo x | xargs -I{} sh F/q.sh`, `echo 'sh F/q.sh' | sh` and `sh F/q.s*`.
Its time is bounded and it fails closed: the Claude Code hook decides a Bash, Monitor or PowerShell call in a child
process of its own, started in a process group of its own and ending itself by SIGALRM 3.5 seconds after it starts
deciding, and refuses the call, naming the cause, when that child has not exited within 3.5 seconds (the installed entry
allows 10), cannot be started, writes more than a decision (the hook reads no more than one byte past 64 bytes of its
output or 64 KiB of its messages, and stops at once), or ends without an explicit allow or refusal (ended by a signal,
stopped by an error or any other exit, named as ending before it had read the whole call when it did, or with unreadable
output), and when the hook itself, while it reads or parses its event or waits, receives SIGINT or any other signal it
can catch whose default action ends a process (every signal `signal.valid_signals()` lists but SIGKILL, SIGSTOP, those
whose default is to ignore, continue or stop, such as SIGCHLD, SIGCONT, SIGWINCH and SIGTSTP, the fault signals SIGSEGV,
SIGBUS, SIGILL, SIGFPE and SIGTRAP, and any whose handler was set outside Python), naming the signal; each of these
refusals ends the child's whole process group, so a shell command it cannot finish reading is refused, never let through
unread. The limit: SIGKILL sent to the hook's own process; SIGSTOP, SIGTSTP, SIGTTIN or SIGTTOU past the host's 10
seconds; SIGSEGV, SIGBUS, SIGILL, SIGFPE or SIGTRAP, left at their default so that a fault inside the hook's own process
ends it at once instead of repeating; an abort inside the hook's own process (SIGABRT raised by a fatal error), which ends it at once; a signal whose handler was set outside Python (such as faulthandler's, under
PYTHONFAULTHANDLER), left as it was; or any signal in the start-up window before its handlers exist (Python's own start
and its reading of the hook, under 50 milliseconds measured on a Mac at rest): each ends it before it can refuse, and
the host then lets the call run, while a reading child it no longer ends still ends itself as above.

Self-test without a host: python3 _Axis/Resources/guardrails.py --check {project-relative path} [--new] [--agent {type}]"""
import importlib.util,json,os,re,shlex,stat,sys
from pathlib import Path

# BEGIN GENERATED: role-table
# Compiled from _Axis/Roles/ at release; edit the role files, never this region.
ROLE_TABLE=(
    {'name': 'Main', 'cls': 'session', 'subject': 'Main: session', 'match': 'exact', 'shape': 'exact4', 'created_by': 'claim', 'exclusive': True, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': None, 'survey_key': None, 'notice': None, 'issuer': 'main', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Main', 'log_by': 'Main Agent', 'title': 'Main Agent', 'plural': 'Main Agents', 'article': 'the', 'serves': 'User', 'families': 'all', 'recovery': ('@core', '@role', '_Config/INSTRUCTIONS.md', '_Config/MINDSET.md', '_Config/DIRECTIVES.md', '@overlay', '@state')},
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
ROLE_LEDGER={'issuers': ('auxiliary', 'external', 'main', 'worker'), 'submission_schemas': ('axis.external-submission/v1', 'axis.external-submission/v2'), 'proposal_member_subject': 'Subagent: External proposal Team', 'survey_keys': ('fresh_assistant', 'fresh_auxiliary', 'fresh_external', 'fresh_groupagent', 'orphan_subagents'), 'proposal_owners': (('External:', 'external'), ('Auxiliary:', 'auxiliary'))}
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
           '_Config/DIRECTIVES.md','_Config/MINDSET.md','_Config/INSTRUCTIONS.md','_Config/PROJECT.md','_Config/SETTINGS.md',
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
WORKFLOW_READ=('_Axis/RULES.md','_Axis/PRACTICES.md','_Axis/PRINCIPLES.md','_Axis/GLOSSARY.md','_Axis/MANIFEST.md','_Axis/CHANGELOG.md','_Config/SETTINGS.md','_Axis/SETTINGS.md',
               '_Axis/Rules/','_Axis/Practices/','_Axis/Roles/','_Axis/Commands/','_Axis/Resources/','_Axis/Agents/','_Axis/Updates/',
               '_Axis/Merges/','_Axis/Flags/','AGENTS.md','CLAUDE.md','GEMINI.md','README.md')
# Their shell runs only Axis's own per-turn and record helpers and the request helper's submit; a role that writes nothing
# runs only its own admission check.
ROLE_SCRIPTS={'turn.py':('',),'startup-state.py':('admit','track','record'),'record-check.py':('names','links','write-once'),'coordination-submissions.py':('submit',)}
# Options of each of those helpers that take a value before its subcommand; every other helper takes only --root.
ROLE_SCRIPT_VALUES={'coordination-submissions.py':('--root','--session')}
# Declared roles that send requests to Main only through the request helper's submit, never by writing the queue.
SUBMIT_BY_HELPER=('GroupAgent','Assistant')
# A shell command naming the request queue, in any letter case and with any path separators.
QUEUE_NAMED=re.compile(r'_axis[\\/]+(?:\.[\\/]+)*submissions(?![a-z0-9_.-])',re.I)
# The newer Claude Code tools the installed matcher names besides the file, shell, agent, web and MCP tools, each with
# its decision for a helper: 'agents' starts or schedules agent work and is refused, as Agent and Task are; 'shell' runs
# a shell command, which gets a helper's shell checks; None passes. Main passes every one, as before the matcher named
# them, but its 'shell' commands get the spelling refusal its Bash commands have (unread_spelling()); a declared role
# serving the User passes them too, but its 'shell' command gets the rules its Bash command has
# and, where its row blocks starting agents (an Auxiliary Agent), an 'agents' tool is refused as Agent and Task are;
# a role serving other people is refused every one, as none is offered.
NEWER_TOOLS={'PowerShell':'shell','Monitor':'shell','SendMessage':'agents','Workflow':'agents','RemoteTrigger':'agents',
             'CronCreate':'agents','ScheduleWakeup':'agents','Skill':'agents','SendUserMessage':None,'ListAgents':None,
             'CronDelete':None,'PushNotification':None,'TaskCreate':None,'TaskStop':None,'EnterWorktree':None,
             'ExitWorktree':None,'Artifact':None,'ArtifactComments':None,'ArtifactData':None,'AskUserQuestion':None,
             'ToolSearch':None}
# The tools a role serving other people is offered, as the launcher's closed --tools list: the file tools for its reads
# and new files, and the shell for its own helpers. This hook refuses every other tool its installed matcher sends it,
# NEWER_TOOLS included; tools that matcher does not name are withheld by the launcher's --tools list alone.
def offered_tools(row):return ('Bash','Glob','Grep','Read')+(('Write',) if row['guard']['new_files'] else ())
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
AGENT_LAUNCH=re.compile(r'(?:^|[;&|(]|\bthen|\bdo|\bexec)\s*(?:env\s+(?:\S+=\S*\s+)*)?(?:\S*/)?(?:claude|codex|openclaw|gemini|agy|grok)(?:\s|$)')

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
    if folded_secret(rel):return who+' never uses _Axis/Secrets/'
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
        allowed=HELPER_SCRIPTS.get(m[2]);words=[w for w in m[3].split() if w]
        sub=subcommand(words,('--root','--candidate-root','--controller-root'))
        if allowed is None or sub not in allowed or '$(' in m[3] or '`' in m[3] or (m[2]=='envelope.py' and '--write' in words):
            return f'helpers never run state-changing Axis helpers ({m[2]})'
    return None

def verdict(root,rel,exists,agent,tool):
    if agent and folded_secret(rel):return 'helpers never read or write _Axis/Secrets/'
    if agent and rel in ('_Config/INSTRUCTIONS.md','_Axis/INSTRUCTIONS.md'):return 'helpers never read the User\'s Instructions; the contract carries the part meant for them'
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
        # Decided before the target is read: a file under any spelling of _Axis/Secrets/, or one outside record-check's
        # scope (but its exceptions file), gets no reference check and is never opened here.
        if folded_secret(rel) or rel!=rc.EXCEPTIONS_PATH and not rc.in_scope(rel):return None
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

SCOPE_FOLDER=re.compile(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,127}')

def scope_value(text):
    """Folders from a pinned AXIS_READ_SCOPE value (comma-separated Project Subfolders), or None when malformed."""
    folders=tuple(f.strip() for f in text.split(','))
    return folders if all(SCOPE_FOLDER.fullmatch(f) for f in folders) else None

def pinned_scope(live):
    """The read scope the `axis` launcher pinned for this session at launch (AXIS_READ_SCOPE; the admission helper
    refuses a pin that differs from the row), or LIVE, the live row, for a session no launcher pinned. It only narrows:
    a read must lie inside both this and the live row, so a widened row waits for the next launch and a narrowed one
    applies at once. The pin lives in the session's own environment, never in a file another session can read or
    rewrite, so no re-admission refreshes it."""
    pinned=os.environ.get('AXIS_READ_SCOPE')
    return live if pinned is None else scope_value(pinned)

def within(rel,scope):
    """True when REL lies inside SCOPE: 'project' is the whole project, None nothing, a tuple the folders it names."""
    return scope=='project' or bool(scope) and any(rel==f or rel.startswith(f+'/') for f in scope)

def secret(rel):
    """Secrets, compared without case: a case-insensitive volume reaches the same folder by any spelling."""
    return rel.lower()==SECRETS.lower() or rel.lower().startswith(SECRETS.lower()+'/')

def folded_secret(rel):
    """secret() after full case folding, for every Secrets refusal (the Claude Code hook, its --check and the --role and
    --external route): a case-insensitive volume also reaches the folder through a spelling lower() keeps apart, such as
    a long s (U+017F)."""
    return secret(rel.casefold())

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
    if (tool in SPAWN_TOOLS or (NEWER_TOOLS.get(tool)=='agents' and not others)) and row['guard']['block_spawn']:return who+' never starts agents'
    if others and (tool in OUTBOUND or str(tool).startswith('mcp__')):return who+' has no outbound tools'
    if tool=='Bash':
        command=ti.get('command') if isinstance(ti.get('command'),str) else ''
        if SECRETS.casefold() in command.casefold():return who+' never uses _Axis/Secrets/'
        if re.search(r'_Axis/Resources/boot\.py',command):return who+' never starts as Main'
        if queue_command(row,command):return submit_only(who)
        sub=git_change(command)
        if sub:return f'{who} makes no Git changes (git {sub}); Main does, and read-only git (log, status, diff, show) passes'
        if others:
            m=SCRIPT_CALL.match(command.strip())
            if not ROLE_COMMAND.fullmatch(command) or m is None:return who+' runs only Axis\'s own per-turn helpers in the shell, one call per command'
            words=[w.strip('"\'') for w in m[3].split() if w]
            sub=subcommand(words,ROLE_SCRIPT_VALUES.get(m[2],('--root',)))
            if not row['guard']['new_files']:
                # A role that writes nothing runs only its own admission check, which writes nothing for it.
                role=words[words.index('--role')+1].replace(' ','').lower() if '--role' in words[:-1] else ''
                if sub not in READ_ONLY_SCRIPTS.get(m[2],()) or role not in (row['name'].lower(),row['title'].replace(' ','').lower()):
                    return who+' runs only its own admission check in the shell (startup-state.py admit --role '+row['name']+')'
                return None
            if m[2] not in ROLE_SCRIPTS or (ROLE_SCRIPTS[m[2]]!=('',) and sub not in ROLE_SCRIPTS[m[2]]):return who+' runs only Axis\'s own per-turn helpers in the shell, one call per command'
        return None
    if NEWER_TOOLS.get(tool)=='shell' and isinstance(ti.get('command'),str) and queue_command(row,ti['command']):return submit_only(who)
    # A Monitor or PowerShell command of a role serving the User: the rules its Bash command has, the User-mode role
    # actions main() checks for every Bash command included. A role serving other people is offered neither tool.
    if NEWER_TOOLS.get(tool)=='shell' and isinstance(ti.get('command'),str) and not others:
        return own_secrets(role_action(ti['command'],root),who+' never uses _Axis/Secrets/') or role_refusal(root,row,'Bash',ti,event)
    closed=who+' uses only the tools its role is offered ('+', '.join(offered_tools(row))+')'
    if tool not in PATH_TOOLS:return closed if others and tool not in offered_tools(row) else None
    path=ti.get('file_path') or ti.get('notebook_path') or ti.get('path')
    if not isinstance(path,str) or not path:
        # A search with no path searches the project root, which a role serving others may not read whole.
        if others and tool in ('Grep','Glob'):return who+' searches only inside a folder its surface row names; give that folder as the path'
        return None
    rel=relative(root,path)
    if rel is None:return who+' stays inside this project' if others else None
    if folded_secret(rel):return who+' never uses _Axis/Secrets/'
    write=tool in WRITE_TOOLS;exists=(root/rel).exists()
    if write and row['name'] in SUBMIT_BY_HELPER and within(rel.lower(),('_axis/submissions',)):return submit_only(who)
    why=guarded(row,rel,exists,write) or (write_once(root,rel,exists) if write else None)
    if not why and others and tool not in offered_tools(row):why=closed
    if why or not others or write:return why
    if rel in ('','.'):return who+' reads only the folders its surface row names and the Axis workflow files'
    if any(rel==w or rel+'/'==w or (w.endswith('/') and rel.startswith(w)) for w in WORKFLOW_READ):return None
    live=read_scope(root)
    if within(rel,live) and within(rel,pinned_scope(live)):return None
    return who+' reads only the folders its surface row names and the Axis workflow files'

def queue_command(row,command):
    """True when a Group Agent's or Assistant's shell command names the request queue, unless it is one call of the
    request helper's submit and nothing else. A mistake-catcher: it reads the command text."""
    return row['name'] in SUBMIT_BY_HELPER and QUEUE_NAMED.search(command) is not None and not submit_call(command)

def submit_call(command):
    """True when COMMAND is one call of the request helper's `submit`, with nothing else on the line."""
    m=SCRIPT_CALL.match(command.strip()) if ROLE_COMMAND.fullmatch(command) else None
    if m is None or m[2]!='coordination-submissions.py':return False
    words=[w.strip('"\'') for w in m[3].split() if w]
    return subcommand(words,ROLE_SCRIPT_VALUES[m[2]])=='submit'

def subcommand(words,values):
    """The subcommand after an Axis helper's leading options, or None when they cannot be read for certain. An option in
    VALUES takes the next word as its value and its = form carries it; `--`, or an abbreviation of an option in VALUES
    (argparse expands it, so the next word may be its value), is refused rather than guessed."""
    i=0
    while i<len(words) and words[i].startswith('-'):
        name=words[i].split('=',1)[0]
        if name=='--' or (name.startswith('--') and name not in values and any(v.startswith(name) for v in values)):return None
        i+=1+(words[i] in values)
    return words[i] if i<len(words) else ''

def submit_only(who):
    return who+' sends requests to Main only through coordination-submissions.py submit, never by writing _Axis/Submissions/ itself'

def role_action(command,root=None):
    """A refusal reason when an agent runs a User-mode `axis retire` or `axis start`, or None."""
    for m in ROLE_ACTION.finditer(command):
        args=m[2]
        if m[1]=='retire' and '--session-of-caller' not in args:return 'User mode of `axis retire` is for your own terminal; a supervising Main uses agent mode (^^stop)'
        if m[1]=='start' and '--source-root' not in args:return 'User mode of `axis start` is for your own terminal; a supervising Main uses ^^start'
    return utility_forms(command,root)

# Defence in depth, never qualification: the User-mode forms the S6 R8 matrix ran past the pattern above. They hide the
# utility behind environment blanking (`env -i`, `env -u`, `NAME=` prefixes), a wrapper (`sh -c`, `eval`, `nohup`,
# `script`, `xargs`), a variable, an interpreter (`python3 axis-launch.py`, `python3 -c` with runpy) or a shell script
# file. This reads the command text and a named shell script only, never what the shell finally runs: an agent with an
# unrestricted shell can still pose as the User, so these patterns catch mistakes and prove no refusal.
UTILITY=('axis','axis-roles.py','axis-launch.py')
SHELLS=('sh','bash','zsh','dash','ksh')
INTERPRETER=re.compile(r'(python|pypy|node|nodejs|perl|ruby|php|osascript|bun)[0-9.]*')
# Each interpreter's options that take program text.
CODE_FLAGS={'python':r'-[BbdEhIiOqRSsuvx]*c','pypy':r'-[BbdEhIiOqRSsuvx]*c','node':r'-e|-p|--eval|--print','nodejs':r'-e|-p|--eval|--print',
            'bun':r'-e|-p|--eval|--print','perl':r'-[A-Za-z]*[eE]','ruby':r'-[A-Za-z]*e','php':r'-r','osascript':r'-e'}
# Wrappers before the program, with the options of each that take a value.
WRAPPER_VALUES={'env':('-u','--unset','-C','--chdir','-S','--split-string'),'exec':('-a',),'nice':('-n','--adjustment'),
                'sudo':('-u','-g','-h','-p','-C','-D','-R','-T','-U'),'doas':('-u','-C'),'stdbuf':('-i','-o','-e'),'caffeinate':('-t','-w'),
                'timeout':('-s','--signal','-k','--kill-after'),'command':(),'builtin':(),'nohup':(),'time':(),'then':(),'do':(),
                'else':(),'!':(),'if':(),'elif':(),'while':(),'until':(),'{':(),'unbuffer':(),'chronic':(),'setsid':()}
XARGS_VALUES=('-I','-i','-n','-L','-l','-P','-s','-E','-e','-d','-a','--max-args','--max-lines','--max-procs','--delimiter','--arg-file')
SCRIPT_VALUES=('-F','-t','-T','-I','-O','-B','-E','-o','-m')
UTILITY_TEXT=re.compile(r'axis-(?:roles|launch)\.py|Resources/axis\b|[\'"]axis[\'"]')
RUN_TEXT=re.compile(r'runpy|run_path|run_module|subprocess|os\.system|os\.exec|os\.spawn|os\.popen|\bexec\b|execfile|import_module|spec_from_file_location|__import__|child_process|execSync|spawnSync|\bsystem\b|`')
ACTION_TEXT=re.compile(r'[\'"](retire|start)[\'"]')
LITERAL=re.compile(r'\'([^\'\\\n]*)\'|"([^"\\\n]*)"')
ASSIGNMENT=re.compile(r'[A-Za-z_]\w*=.*',re.S)
SCRIPT_LIMIT=1048576

def utility_action(sub,args):
    """The refusal for a visible utility subcommand without the agent-mode arguments the utility itself requires."""
    names={a.split('=')[0] for a in args}
    if sub=='retire' and not {'--from','--session-of-caller','--instruction'}<=names:return 'User mode of `axis retire` is for your own terminal; a supervising Main uses agent mode (^^stop)'
    if sub=='start' and '--source-root' not in names:return 'User mode of `axis start` is for your own terminal; a supervising Main uses ^^start'
    return None

def code_forms(text,root,depth,files,only=False):
    """For an interpreter's program text that runs something (RUN_TEXT): a run of the utility with a quoted retire or
    start, or a quoted shell string that is one; else None. Text that runs nothing, such as a print, is not read. Each
    text is read once per depth and mode within one hook call (MEMO): many interpreters reading the same standard input
    cost one reading."""
    key=(text,str(root),depth,files,only)
    if key not in MEMO:MEMO[key]=program_forms(text,root,depth,files,only)
    return MEMO[key]

MEMO={}

def program_forms(text,root,depth,files,only):
    """code_forms() without its memo."""
    if not RUN_TEXT.search(text):return None
    if UTILITY_TEXT.search(text) and not only:
        for m in ACTION_TEXT.finditer(text):
            why=utility_action(m[1],re.findall(r'--[a-z-]+',text))
            if why:return why
    for m in LITERAL.finditer(text):
        why=utility_forms(m[1] if m[1] is not None else m[2],root,depth+1,files,only)
        if why:return why
    return None

def script_path(root,path):
    """PATH's real path, or None."""
    if root is None or not path:return None
    try:return Path(os.path.realpath(Path(path) if os.path.isabs(path) else Path(root)/path)).as_posix()
    except (OSError,ValueError):return None

def script_text(root,path,head=False,own=False):
    """A shell script's text (a regular file of at most SCRIPT_LIMIT bytes whose real path names no spelling of
    _Axis/Secrets/ that full case folding maps to it, in this project or elsewhere; with OWN, only one whose real path
    lies inside the project), or None; with head, only its first line."""
    real=script_path(root,path)
    if real is None or SECRETS.casefold() in real.casefold():return None
    top=script_path(root,'.') if own else None
    if own and not (top and (real==top or real.startswith(top.rstrip('/')+'/'))):return None
    try:
        info=os.stat(real)
        if not stat.S_ISREG(info.st_mode) or (info.st_size>SCRIPT_LIMIT and not head):return None
        with open(real,'rb') as handle:data=handle.read(256 if head else SCRIPT_LIMIT)
        text=data.decode('utf-8','replace');return text.split('\n',1)[0] if head else text
    except (OSError,ValueError):return None

SPELLING='the hook opens no script under _Axis/Secrets/, and one runs unread only through that exact spelling, not another letter case or a long s'
UNREAD='the hook opens no script under a folder that full case folding spells _Axis/Secrets/ (here through a long s or a similar character), so it cannot check this one'

def unread_spelling(root,path):
    """The refusal for running, sourcing or executing the script at PATH, or None: SPELLING when its real path reaches
    this project's own _Axis/Secrets/ through a spelling other than the exact one; UNREAD when script_text() no longer
    opens it because a spelling only full case folding maps (such as a long s) names the folder elsewhere in its real
    path, where lower() kept it apart and the hook read it before. A spelling lower() also maps, outside this project's
    own folder (an outer folder or a Project Subfolder), is neither opened nor refused, as before."""
    real=script_path(root,path)
    if real is None or SECRETS.casefold() not in real.casefold():return None
    # This project's own folder: the part of the real path below the project root, the root matched by its text (the
    # same folder when only its spelling differs) or by identity; a non-exact spelling below any of them is refused.
    rels=own_parts(root,real)
    if any(folded_secret(r) and not exact_secret(r) for r in rels):return SPELLING
    if any(folded_secret(r) for r in rels):return None
    return None if SECRETS.lower() in real.lower() else UNREAD

def exact_secret(rel):
    """True when project-relative REL is _Axis/Secrets or lies below it, spelled exactly."""
    return rel==SECRETS or rel.startswith(SECRETS+'/')

def own_parts(root,real):
    """The parts of the real path REAL below this project's root: below the prefix that names the root (in its letter
    case, or the same folder when only that differs) and below every ancestor that is the root's folder by identity
    (same device and inode), such as a path through another mount (macOS's /System/Volumes/Data, a bind mount). It reads
    metadata only and opens nothing."""
    top=script_path(root,'.')
    if not top:return []
    parts=real.split('/');n=len(top.rstrip('/').split('/'));head='/'.join(parts[:n]);out=[]
    try:
        if head==top or head.casefold()==top.casefold() and os.path.samefile(head,top):out.append('/'.join(parts[n:]))
    except (OSError,ValueError):pass
    try:
        mine=os.stat(top)
        for k in range(1,len(parts)):
            info=os.stat('/'.join(parts[:k]) or '/')
            if (info.st_dev,info.st_ino)==(mine.st_dev,mine.st_ino):out.append('/'.join(parts[k:]))
    except (OSError,ValueError):pass
    return out

def own_secrets(why,reason):
    """WHY, or REASON (a declared role's or helper's own Secrets reason) in place of a spelling refusal."""
    return reason if reason and why in (SPELLING,UNREAD) else why

def utility_forms(command,root=None,depth=0,files=True,only=False):
    """The utility_words refusal for any simple command in a shell command text, or None. Below the top level only
    lines whose case-folded text names axis are read, one naming it only in another letter case for unread_spelling()'s
    refusals alone, and a script file's own text opens no further file. With ONLY, just unread_spelling()'s refusals,
    and no file is opened (Main's Monitor and PowerShell commands). Every line is read first exactly as before, with its
    own map of assignments (KNOWN). A line holding bash's $'...' or $" quoting, and every later line once one has, is
    then read a second time: decoded (ansi_c()) and with a second map, copied at the first such line and updated only by
    second readings, so a decoded assignment never changes the first reading of a later line. A second reading opens a
    script only inside the project (FILES 'own')."""
    if depth>3 or not isinstance(command,str):return None
    if not depth:MEMO.clear()
    known={};second=None
    for raw in command.replace('\\\n',' ').splitlines():
        quoted="$'" in raw or '$"' in raw
        before=dict(known) if quoted and second is None else None
        why=utility_line(raw,root,depth,files,only,known,command)
        if why:return why
        line=(ansi_c(raw) or (raw,))[0] if quoted else raw
        if line is raw and second is None:continue
        if second is None:second=before
        why=utility_line(line,root,depth,files and 'own',only,second,command)
        if why:return why
    return None

def utility_line(line,root,depth,files,only,known,command):
    """utility_words() for each simple command on one line, its assignments kept in KNOWN; below the top level only a
    line whose case-folded text names axis is read."""
    if depth and 'axis' not in line.casefold():return None
    alone=only or bool(depth) and 'axis' not in line
    tokens=line_words(line.replace('`',' ; '));words=[];commands=[]
    for t in tokens+[';']:
        if t and all(ch in ';&|()`<>' for ch in t):commands.append(words);words=[]
        else:words.append(t)
    for words in commands:
        why=utility_words(words,root,depth,files,known,line,command,alone)
        if why:return why
    return None

def utility_words(words,root,depth,files,known,line,command,only=False):
    """A refusal for one simple command that runs the utility's User-mode retire or start, or None."""
    if not words:return None
    if all(ASSIGNMENT.fullmatch(w) for w in words):
        known.update(w.split('=',1) for w in words);return None
    words=[re.sub(r'\$\{?([A-Za-z_]\w*)\}?',lambda m:known.get(m[1],m[0]),w) for w in words];i=0
    while i<len(words):
        name=os.path.basename(words[i])
        if ASSIGNMENT.fullmatch(words[i]):i+=1;continue
        if name not in WRAPPER_VALUES:break
        i+=1
        if name=='env' and any(x in ('-S','--split-string') for x in words[i:]):
            j=next(k for k in range(i,len(words)) if words[k] in ('-S','--split-string'))
            return utility_forms(' '.join(words[j+1:]),root,depth+1,files,only)
        while i<len(words) and (words[i].startswith('-') or (name=='env' and ASSIGNMENT.fullmatch(words[i]))):i+=1+(words[i] in WRAPPER_VALUES[name])
        if name=='timeout' and i<len(words):i+=1
    if i>=len(words):return None
    name=os.path.basename(words[i]);rest=words[i+1:]
    nested=lambda text:utility_forms(text,root,depth+1,files,only)
    # A script run, sourced or executed: its spelling, then its text with MODE ('own': only inside the project).
    one=lambda path,mode:(unread_spelling(root,path) if mode else None) or (None if only else utility_forms(script_text(root,path,own=mode=='own') if mode else None,root,depth+1,False))
    # As typed with this reading's FILES first, then as the shell expands a leading $PWD or ~ (typed_paths()), read only
    # inside the project; the first refusal wins.
    opened=lambda path:next((why for why in (one(p,files if k==0 else files and 'own') for k,p in enumerate(typed_paths(root,path))) if why),None)
    if name in UTILITY:
        sub=next((w for w in rest if not w.startswith('-')),None)
        return utility_action(sub,rest) if sub in ('retire','start') and not only else None
    if name=='eval':return nested(' '.join(rest))
    if name in ('source','.'):return opened(rest[0]) if rest else None
    if name in SHELLS:
        flag=False;j=0
        while j<len(rest) and rest[j].startswith(('-','+')):
            flag=flag or (not rest[j].startswith('--') and 'c' in rest[j][1:]);j+=1+(rest[j] in ('-o','+o','-O','+O'))
        if j<len(rest):return nested(rest[j]) if flag else opened(rest[j])
        # A shell reading its commands from standard input: check every word on the line as a command.
        for w in line_words(line):
            why=nested(w)
            if why:return why
        return None
    if name=='script':
        if '-c' in rest or '--command' in rest:
            k=rest.index('-c') if '-c' in rest else rest.index('--command')
            return nested(rest[k+1]) if k+1<len(rest) else None
        j=0
        while j<len(rest) and rest[j].startswith('-'):j+=1+(rest[j] in SCRIPT_VALUES)
        return utility_words(rest[j+1:],root,depth+1,files,known,line,command,only)
    if name=='xargs':
        j=0
        while j<len(rest) and rest[j].startswith('-'):j+=1+(rest[j] in XARGS_VALUES)
        if not only and j<len(rest) and os.path.basename(rest[j]) in UTILITY and not [w for w in rest[j+1:] if not w.startswith('-')]:
            return 'the `axis` subcommand would come from xargs input, which this check cannot see; a supervising Main uses agent mode'
        return utility_words(rest[j:],root,depth+1,files,known,line,command,only)
    if INTERPRETER.fullmatch(name):
        j=0;code=CODE_FLAGS[INTERPRETER.fullmatch(name)[1]]
        while j<len(rest) and rest[j].startswith('-') and rest[j]!='-':
            opt=rest[j]
            if opt=='-m':
                if rest[j+1:j+2]!=['runpy']:return None
                j+=2;break
            if re.fullmatch(code,opt):return code_forms(rest[j+1],root,depth,files,only) if j+1<len(rest) else None
            j+=1+(opt in ('-W','-X'))
        if j>=len(rest) or rest[j]=='-':return code_forms(command,root,depth,files,only)
        return utility_words(rest[j:],root,depth+1,files,known,line,command,only) if os.path.basename(rest[j]) in UTILITY else None
    if '/' in words[i] and files:
        for k,path in enumerate(typed_paths(root,words[i])):
            why=unread_spelling(root,path)
            if why:return why
            if only:continue  # Main's Monitor and PowerShell: no file is opened, not even a first line
            mode=files if k==0 else 'own'
            first=script_text(root,path,head=True,own=mode=='own') or ''
            why=one(path,mode) if path.endswith('.sh') or (first.startswith('#!') and any(re.search(r'\b'+s+r'\b',first) for s in SHELLS)) else None
            if why:return why
    return None

def typed_paths(root,path):
    """A script path as typed, then as the shell expands a leading $PWD or ${PWD} (the project root, which relative
    paths are read from too) or a leading ~ or ~/ ($HOME, when it is absolute); ~user, ~+ and ~- are not followed."""
    out=[path];m=re.match(r'\$(?:PWD(?!\w)|\{PWD\})',path);home=os.environ.get('HOME','')
    if m and root is not None:out.append(str(root)+path[m.end():])
    if (path=='~' or path.startswith('~/')) and os.path.isabs(home):out.append(home.rstrip('/')+path[1:])
    return out

# bash's ANSI-C quoting: $'...' with its backslash escapes; $"..." (locale translation) reads as "...".
ANSI_C=re.compile(r"\$'((?:[^'\\]|\\.)*)'|\$\"",re.S)
ANSI_ESCAPES={'a':7,'b':8,'e':27,'E':27,'f':12,'n':10,'r':13,'t':9,'v':11,'\\':92,"'":39,'"':34,'?':63}
ANSI_DIGITS={'x':re.compile(r'[0-9A-Fa-f]{1,2}'),'u':re.compile(r'[0-9A-Fa-f]{1,4}'),'U':re.compile(r'[0-9A-Fa-f]{1,8}')}
ANSI_OCTAL=re.compile(r'[0-7]{1,3}')

def ansi_c(line):
    """LINE once more in a one-item tuple, each $'...' written as the single-quoted string bash makes of it (its bytes
    read as UTF-8) and each $" as "; () when LINE holds neither or cannot be decoded. Escapes are matched at their
    position, so the work grows with the line's length."""
    if "$'" not in line and '$"' not in line:return ()
    def decode(m):
        if m[1] is None:return '"'
        s=m[1];out=bytearray();i=0
        while i<len(s):
            if s[i]!='\\' or i+1==len(s):
                j=s.find('\\',i+1)
                if j<0 or j+1==len(s):j=len(s)
                out+=s[i:j].encode('utf-8','surrogateescape');i=j;continue
            e=s[i+1];hexa=ANSI_DIGITS[e].match(s,i+2) if e in ANSI_DIGITS else None;value=int(hexa[0],16) if hexa else None
            if e in ANSI_ESCAPES:out.append(ANSI_ESCAPES[e]);i+=2
            elif e in '01234567':k=ANSI_OCTAL.match(s,i+1)[0];out.append(int(k,8)&255);i+=1+len(k)
            elif hexa and e=='x':out.append(value);i+=2+len(hexa[0])
            elif hexa and value<0x110000 and not 0xD800<=value<0xE000:out+=chr(value).encode('utf-8');i+=2+len(hexa[0])
            elif e=='c' and i+2<len(s):out.append(ord(s[i+2])&31);i+=3
            else:out+=('\\'+e).encode('utf-8','surrogateescape');i+=2
        text=bytes(out).split(b'\0',1)[0].decode('utf-8','surrogateescape')
        return "'"+text.replace("'","'\\''")+"'"
    try:decoded=ANSI_C.sub(decode,line)
    except Exception:return ()
    return (decoded,) if decoded!=line else ()

def line_words(line):
    """A shell line's words, with the separators ; & | ( ) < > as their own tokens."""
    try:
        lexer=shlex.shlex(line,posix=True,punctuation_chars=True);lexer.whitespace_split=True;return list(lexer)
    except ValueError:return re.findall(r'[^\s;&|()`<>]+|[;&|()`<>]+',line)

def relative(root,path):
    p=Path(path)
    if not p.is_absolute():p=root/p
    try:return Path(os.path.realpath(p)).relative_to(root).as_posix()
    except ValueError:return None

# Strict read comparison (S4 M1), inert: `guardrails.py --strict-read` takes one explicit JSON context on stdin
# (project_root, role, principal, read_scope and a typed request) and compares it with the pure strict-read-policy.py
# beside this file. It consults no environment, working directory, surface table or legacy read scope, never falls
# back to the legacy path, and never grants a read: no qualified host adapter exists, so every answer exits 2.
STRICT_KEYS=frozenset(('project_root','role','principal','read_scope','request'))
STRICT_LIMIT=65536

def strict_policy():
    """The pure strict read comparator beside this file, or None when it cannot be loaded."""
    try:
        spec=importlib.util.spec_from_file_location('axis_strict_read_policy',Path(__file__).resolve().parent/'strict-read-policy.py')
        policy=importlib.util.module_from_spec(spec);sys.modules[spec.name]=policy;spec.loader.exec_module(policy)
        return policy if callable(getattr(policy,'compare_read',None)) else None
    except Exception:return None

def strict_context(raw):
    """One JSON object from raw bytes, or None: UTF-8, at most STRICT_LIMIT bytes, no duplicate key, no NaN or Infinity."""
    def pairs(items):
        if len({k for k,_ in items})!=len(items):raise ValueError('duplicate key')
        return dict(items)
    def constant(name):raise ValueError('non-finite number')
    if len(raw)>STRICT_LIMIT:return None
    try:return json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=constant)
    except (UnicodeDecodeError,ValueError,RecursionError):return None

def strict_read(policy,context):
    """The strict read record for one context: the pure comparison's lexical match and fixed reason code. It carries no
    execution authority; a malformed context, a missing policy or an unexpected result refuses with its own code."""
    record={'schema':'axis.strict-read-result/v1','service':'unavailable','lexical_match':False,'reason':'context_invalid',
            'execution_authority':False,'physical_evidence':'unresolved'}
    if type(context) is not dict or set(context)!=STRICT_KEYS:return record
    if policy is None:record['reason']='policy_unavailable';return record
    try:
        result=policy.compare_read(context['project_root'],context['role'],context['principal'],context['read_scope'],context['request'])
        match,reason=result.lexical_match,result.reason
        valid=(type(match) is bool and type(reason) is str and re.fullmatch(r'[a-z_]{1,40}',reason) is not None and match==(reason=='match')
               and result.execution_authority is False and result.physical_evidence=='unresolved' and result.kind=='read-status-comparison-only')
    except Exception:valid=False
    if not valid:record['reason']='policy_error';return record
    record.update(lexical_match=match,reason=reason);return record

def strict_main():
    """--strict-read: print the record as one JSON line and refuse."""
    sys.dont_write_bytecode=True
    try:raw=sys.stdin.buffer.read(STRICT_LIMIT+1)
    except (OSError,ValueError,AttributeError):raw=b''
    record=strict_read(strict_policy(),strict_context(raw))
    print(json.dumps(record,sort_keys=True))
    print('Axis guardrail: strict read service is unavailable; no qualified host adapter meets the strict read obligations (comparison: '+record['reason']+').',file=sys.stderr)
    return 2

def main():
    if sys.argv[1:]==['--strict-read']:return strict_main()
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
    row=declared_row() if not agent else None
    if tool=='Bash' and isinstance(ti.get('command'),str):
        # A declared role or helper keeps its own Secrets reason for a script run through a spelling of the folder.
        mine='helpers never read or write _Axis/Secrets/' if agent else row['article']+' '+row['title']+' never uses _Axis/Secrets/' if isinstance(row,dict) else None
        why=own_secrets(role_action(ti['command'],root),mine)
        # A declared role's own Secrets reason points at its role file, as its role_refusal() reasons do.
        if why:print(f'Axis guardrail: {why}.'+(f' See _Axis/Roles/{row["name"]}.md.' if isinstance(row,dict) and why==mine else ''),file=sys.stderr);return 2
    if row=='unknown':print('Axis guardrail: AXIS_ROLE names no Axis role; this session gets no service until the declaration is corrected.',file=sys.stderr);return 2
    if row is not None:
        why=role_refusal(root,row,tool,ti,event)
        if why:print(f'Axis guardrail: {why}. See _Axis/Roles/{row["name"]}.md.',file=sys.stderr);return 2
    if row is None and not agent and NEWER_TOOLS.get(tool)=='shell' and isinstance(ti.get('command'),str):
        # Main's Monitor and PowerShell commands: option C as on its Bash commands; their User-mode axis retire and
        # start pass as before, and no file is opened.
        why=utility_forms(ti['command'],root,only=True)
        if why:print(f'Axis guardrail: {why}.',file=sys.stderr);return 2
    if tool=='Bash' and agent and isinstance(ti.get('command'),str) and SECRETS.casefold() in ti['command'].casefold():
        print('Axis guardrail: helpers never read or write _Axis/Secrets/.',file=sys.stderr);return 2
    if tool=='Bash' and agent and isinstance(ti.get('command'),str):
        why=helper_command(ti['command'])
        if why:print(f'Axis guardrail: {why}. See _Axis/Roles/Delegating.md.',file=sys.stderr);return 2
    if tool in SPAWN_TOOLS and agent:
        print('Axis guardrail: helpers never start other agents; a granted start goes through the spawner. See _Axis/Roles/Delegating.md.',file=sys.stderr);return 2
    if agent and NEWER_TOOLS.get(tool)=='agents':
        print(f'Axis guardrail: helpers never start other agents ({tool} starts or schedules agent work); a granted start goes through the spawner. See _Axis/Roles/Delegating.md.',file=sys.stderr);return 2
    if agent and NEWER_TOOLS.get(tool)=='shell' and isinstance(ti.get('command'),str):
        command=ti['command']
        why=own_secrets(role_action(command,root),'helpers never read or write _Axis/Secrets/') or ('helpers never read or write _Axis/Secrets/' if SECRETS.casefold() in command.casefold() else None) or helper_command(command)
        if why:print(f'Axis guardrail: {why}. See _Axis/Roles/Delegating.md.',file=sys.stderr);return 2
    if tool not in PATH_TOOLS:return 0
    path=ti.get('file_path') or ti.get('notebook_path') or ti.get('path')
    if not isinstance(path,str) or not path:return 0
    rel=relative(root,path)
    if rel is None:return 0
    why=verdict(root,rel,(root/rel).exists(),agent,tool) or (references(root,rel,tool,ti) if tool in ('Write','Edit','MultiEdit') else None)
    if why:
        print(f'Axis guardrail: {why} ({rel}). See _Axis/Rules/RecordsAndWORM.md and _Axis/Rules/Subagents.md.',file=sys.stderr);return 2
    return 0

# The hook's own time: the installed entry allows it 10 seconds, and reading a long or contrived shell command (its
# patterns, a script it reads, nested text) can take longer. A shell call is decided in a child process and refused when
# that child has not exited within BOUND_SECONDS, well inside the entry's time, when it cannot be started, writes more
# than a decision or ends without its decision (a signal, an error, any other exit, unreadable output), and when the
# hook itself, while it reads or parses its event or waits, receives SIGINT or another signal of ending_signals(); each
# such refusal ends the child's process group, and a child the hook no longer ends still ends itself by SIGALRM past the
# bound: never let through unread.
BOUND_SECONDS=3.5
BOUND=('the hook could not finish reading this shell command within its 3.5-second bound, so it refuses it rather than '
       'let it run unread; split the command, or put long text in a file')
UNFINISHED='the hook could not finish reading this shell command ({}), so it refuses it rather than let it run unread'
# The child's one line of standard output once main() has decided: this word and the exit it returns.
DECIDED='axis-guardrails-decided'
# The most bytes of messages passed on from the child; its reasons are one short line.
CHILD_OUTPUT=65536
# The most bytes of the child's standard output held (its DECIDED line is at most 26). With CHILD_OUTPUT this caps what
# the hook holds of its child's output: each read asks for at most one byte past what is left, and the child is ended
# the moment either cap is passed, so output without end is refused at once, never gathered until the bound.
DECISION_OUTPUT=64
OVERFLOW='its reading process gave more output than a decision'
# The signals whose default action does not end a process (it ignores, continues or stops it) and the two no process
# can catch (SIGKILL, SIGSTOP: the stated limit); SIGIO's default ends a process on Linux only. bounded() turns every
# other signal the platform lists into a refusal, SIGINT included, but FAULTS and any whose handler was set outside
# Python (signal.getsignal() gives None, as for faulthandler's), which it leaves as they were.
NOT_ENDING=('SIGKILL','SIGSTOP','SIGTSTP','SIGTTIN','SIGTTOU','SIGCONT','SIGCHLD','SIGCLD','SIGURG','SIGWINCH','SIGINFO')
# The signals a fault inside the hook's own process raises synchronously. A Python handler only marks the signal and
# returns, so the faulting instruction runs again and the hook would spin until SIGKILL; at their default action such a
# crash ends the hook at once (a stated limit). SIGSYS from a bad system call returns an error instead, and abort() ends
# the process even after a handler returns, so SIGSYS and SIGABRT stay refused.
FAULTS=('SIGSEGV','SIGBUS','SIGILL','SIGFPE','SIGTRAP')

def ending_signals():
    """The signals bounded() turns into a refusal: every one signal.valid_signals() lists but NOT_ENDING and FAULTS (and
    SIGIO and SIGPOLL outside Linux, where their default is to ignore)."""
    import signal
    skip={getattr(signal,n) for n in NOT_ENDING+FAULTS+(() if sys.platform.startswith('linux') else ('SIGIO','SIGPOLL')) if hasattr(signal,n)}
    return sorted(s for s in signal.valid_signals() if s not in skip)

def within_bound():
    """The child of bounded(): main()'s decision, then DECIDED and that exit as its one line of standard output (main()
    prints nothing there for a host call), so the parent passes on only a decision reached in full. It ends itself by
    SIGALRM at its default action BOUND_SECONDS after it starts deciding, later than the parent's deadline, so a child the
    hook no longer ends (only the hook's own process group ended) still ends within the bound of its own start."""
    import signal
    try:
        if hasattr(signal,'setitimer'):signal.signal(signal.SIGALRM,signal.SIG_DFL);signal.setitimer(signal.ITIMER_REAL,BOUND_SECONDS)
    except (OSError,ValueError,AttributeError):pass
    code=main()
    sys.stdout.write(f'{DECIDED} {code}\n');sys.stdout.flush()
    return code

def unfinished(q):
    """Why the finished child Q gave no explicit allow (exit 0) or refusal (exit 2): a signal, another exit (with the
    last line of its messages, such as an exception), no DECIDED line for its exit, or messages that are too long or
    not UTF-8; None when it gave one."""
    import signal
    if q.returncode<0:
        try:name=signal.Signals(-q.returncode).name
        except ValueError:name=str(-q.returncode)
        return f'its reading process was ended by signal {name}'
    if q.returncode not in (0,2):
        last=(q.stderr or b'')[-4096:].decode('utf-8','replace').strip().splitlines()[-1:]
        return f'its reading process stopped with exit code {q.returncode}'+(': '+''.join(c if c.isprintable() else '?' for c in last[0][:160]) if last else '')
    if q.stdout!=f'{DECIDED} {q.returncode}\n'.encode():return 'its reading process gave no readable decision'
    if len(q.stderr)>CHILD_OUTPUT:return OVERFLOW
    try:q.stderr.decode('utf-8')
    except UnicodeDecodeError:return 'its reading process gave unreadable output'
    return None

def finished(child,data,deadline):
    """Give CHILD the event DATA on its standard input and read its standard output and messages until both close and it
    exits: then an object with its returncode, stdout, stderr and unread (true when the child closed its input before
    taking the whole event). BOUND when DEADLINE (time.monotonic()) passes first (or the child's own SIGALRM, which comes
    after DEADLINE, ended it),
    OVERFLOW the moment its output passes DECISION_OUTPUT or its messages CHILD_OUTPUT: the hook never holds more than
    one byte past either cap. Plain threads with blocking reads, so it works on every platform the hook runs on."""
    import signal,subprocess,threading,time,types
    got={'out':bytearray(),'err':bytearray()};state={'over':False,'open':2,'unread':False};lock=threading.Lock();done=threading.Event()
    # A child that ends before reading the whole event breaks this pipe: the write then fails here instead of raising
    # SIGPIPE in the hook, which would be refused as a signal to the hook. The pipe is marked not to raise it where the
    # platform allows (macOS); where a write raises it in the writing thread (Linux), that thread blocks it.
    try:
        import fcntl
        nosig=getattr(fcntl,'F_SETNOSIGPIPE',73 if sys.platform=='darwin' else None)
        if nosig is not None:fcntl.fcntl(child.stdin.fileno(),nosig,1)
    except (ImportError,OSError,ValueError):pass
    def feed():
        try:
            if hasattr(signal,'pthread_sigmask'):signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGPIPE})
        except (OSError,ValueError,AttributeError):pass
        try:child.stdin.write(data);child.stdin.close()
        except (OSError,ValueError):state['unread']=True
    def drain(key,fd,cap):
        buf=got[key]
        try:
            while True:
                chunk=os.read(fd,cap-len(buf)+1)
                if not chunk:break
                buf+=chunk
                if len(buf)>cap:state['over']=True;break
        except (OSError,ValueError):pass
        with lock:
            state['open']-=1
            if state['over'] or not state['open']:done.set()
    threads=[threading.Thread(target=target,args=args,daemon=True) for target,args in ((feed,()),(drain,('out',child.stdout.fileno(),DECISION_OUTPUT)),(drain,('err',child.stderr.fileno(),CHILD_OUTPUT)))]
    for thread in threads:thread.start()
    if not done.wait(max(0.0,deadline-time.monotonic())):return BOUND
    if state['over']:return OVERFLOW
    try:code=child.wait(max(0.0,deadline-time.monotonic()))
    except subprocess.TimeoutExpired:return BOUND
    if hasattr(signal,'SIGALRM') and code==-signal.SIGALRM and time.monotonic()>=deadline:return BOUND
    threads[0].join(max(0.0,deadline-time.monotonic()))
    return types.SimpleNamespace(returncode=code,stdout=bytes(got['out']),stderr=bytes(got['err']),unread=state['unread'])

def bounded():
    """The Claude Code hook with its time bound. A Bash, Monitor or PowerShell call is decided by this script in a child
    process given the same input, environment and folder (within_bound()); its messages and exit are passed on only when
    it gives an explicit allow or refusal within BOUND_SECONDS, holding no more of its output than the caps allow
    (finished(); unfinished() finds none wanting). Otherwise the call is refused, naming the cause: BOUND when the child
    has not exited in time, UNFINISHED when it cannot be started, writes more than a decision, ends without its decision,
    or the hook fails or receives a signal of ending_signals(), SIGINT included, while it reads or parses its event or
    waits (the child's whole process group is then ended; the handlers go in before the event is read, none where a
    handler was set outside Python, and are put back as they were for any other call; FAULTS keep their default, so a
    fault inside the hook ends it at once); so a fault in
    the hook or the machine shows as a refusal, never as a call run unread. Every other call and every other mode (any
    argument) is decided here, as before."""
    if sys.argv[1:]==['--within-bound']:return within_bound()
    if sys.argv[1:]:return main()
    import io,signal,subprocess,time
    child=[]
    def ended(c):
        """End child C and every process it started: its own process group (C alone where there are no groups)."""
        try:os.killpg(c.pid,signal.SIGKILL)
        except (AttributeError,OSError):
            try:c.kill()
            except OSError:pass
    def caught(number,frame):
        """A signal of ending_signals() to the hook while it reads its event or waits: end the child's process group,
        refuse naming the signal, and exit at once."""
        for c in child:ended(c)
        try:name=signal.Signals(number).name
        except ValueError:name=str(number)
        try:os.write(2,('Axis guardrail: '+UNFINISHED.format(f'the hook itself received signal {name} while it waited')+'.\n').encode())
        except OSError:pass
        os._exit(2)
    # The handlers go in before the event is read, so a signal while the host is still writing it, or while the hook
    # parses it, is refused too; none goes in where a handler was set outside Python (getsignal() gives None, as for
    # faulthandler's), which stays as it was; they are put back as they were for a call that is not a shell call.
    before={}
    try:
        for number in ending_signals():
            try:
                if signal.getsignal(number) is None:continue
                before[number]=signal.signal(number,caught)
            except (OSError,ValueError,RuntimeError):pass
        data=sys.stdin.buffer.read()
    except BaseException as error:
        print('Axis guardrail: '+UNFINISHED.format(f'the hook was stopped while reading its call: {type(error).__name__}')+'.',file=sys.stderr);return 2
    try:event=json.loads(data)
    except ValueError:event=None
    tool=event.get('tool_name') if isinstance(event,dict) else None;ti=event.get('tool_input') if isinstance(event,dict) else None
    if isinstance(tool,str) and (tool=='Bash' or NEWER_TOOLS.get(tool)=='shell') and isinstance(ti,dict) and isinstance(ti.get('command'),str):
        try:
            try:
                deadline=time.monotonic()+BOUND_SECONDS
                try:child.append(subprocess.Popen([sys.executable,'-B',os.path.abspath(__file__),'--within-bound'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True))
                except (OSError,ValueError,subprocess.SubprocessError) as error:why=f'its reading process could not be started: {type(error).__name__}'
                else:
                    q=finished(child[0],data,deadline)
                    if q==BOUND:print(f'Axis guardrail: {BOUND}.',file=sys.stderr);return 2
                    why=q if isinstance(q,str) else unfinished(q)
                    if why is None:sys.stderr.write(q.stderr.decode('utf-8'));return q.returncode
                    if not isinstance(q,str) and q.unread:why+=', before it had read the whole call'
            except BaseException as error:why=f'the hook failed while waiting for its reading process: {type(error).__name__}'
        finally:
            for c in child:
                ended(c)
                if c.poll() is None:
                    try:c.wait(1)
                    except BaseException:pass
        print('Axis guardrail: '+UNFINISHED.format(why)+'.',file=sys.stderr);return 2
    for number,handler in before.items():
        try:signal.signal(number,handler)
        except (OSError,ValueError,RuntimeError,TypeError):pass
    sys.stdin=io.TextIOWrapper(io.BytesIO(data),encoding='utf-8')
    return main()

if __name__=='__main__':sys.exit(bounded())
