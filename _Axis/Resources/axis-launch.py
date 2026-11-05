#!/usr/bin/env python3
"""Optional tmux launcher. A deterministic session name makes reattach idempotent.

3.16: `axis [project] --role ROLE --surface NAME` starts a declared session. The child gets AXIS_ROLE and AXIS_SURFACE,
which the helpers and the guardrails hook read; on Claude it also carries the declaration as an appended system
prompt and, for roles that serve other people, the per-process tool limits. Other agents need the declaration in
their own standing configuration; the launcher says so.

3.17 (CC-15): on Claude the declaration and the role's own guidance (the prose in `_Axis/Roles/{Role}.md` after its
`axis-role` JSON fence, capped at 8,000 characters) travel through `--append-system-prompt-file`, in a file this
launcher writes under the project's `_Temp/Launch/`, so the text survives a host compaction that only re-sends the
system prompt. `--append-system-prompt-file` is undocumented in `claude --help`'s own options list (2.1.283) but
named in the `--bare` option's text and present in the installed binary; no equivalent documented one-shot flag was
found for Codex (`codex --help` / `codex exec --help`, 0.166.0), so Codex keeps printing the declaration line for
the user's own standing configuration, unchanged."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import secrets
import shutil
import stat
import subprocess
import sys


def module(name):
    spec = importlib.util.spec_from_file_location('axis_launcher_' + name.replace('-', '_'), Path(__file__).with_name(name + '.py'))
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


def project(value):
    p = Path(value).expanduser().resolve(strict=True)
    if not (p / '_Axis/PROJECT.md').is_file(): raise ValueError('not an Axis project')
    return p


def name(root, role=None, surface=None):
    base = 'axis-' + hashlib.sha256(os.fsencode(root)).hexdigest()[:24]
    return base if not role else base + '-' + hashlib.sha256(f'{role}\0{surface}'.encode()).hexdigest()[:8]


# Per-process limits for declared roles on Claude: roles serving other people get no outbound or agent tools, and an
# Observer no file-writing tools. The guardrails hook enforces the rest when installed.
CLAUDE_DENY = {'Auxiliary': ('Edit', 'MultiEdit', 'NotebookEdit'), 'Assistant': ('Edit', 'MultiEdit', 'NotebookEdit'),
               'GroupAgent': ('Edit', 'MultiEdit', 'NotebookEdit', 'WebFetch', 'WebSearch', 'Agent', 'Task'),
               'Observer': ('WebFetch', 'WebSearch', 'Agent', 'Task', 'Edit', 'Write', 'MultiEdit', 'NotebookEdit')}
# Roles serving other people load no MCP servers, so no connector can carry project content out.
NO_MCP = ['--strict-mcp-config', '--mcp-config', '{"mcpServers": {}}']
# CC-7/CC-15: the session-role guidance budget is characters, not bytes; a role file missing or without a fence
# contributes no guidance rather than failing the launch.
ROLE_GUIDANCE_LIMIT = 8000


def role_guidance(row, roles_dir=None):
    """The prose in `_Axis/Roles/{Role}.md` after its `axis-role` JSON fence, capped at ROLE_GUIDANCE_LIMIT
    characters; '' when the file is missing, unreadable or has no fence. `roles_dir` overrides the default sibling
    `_Axis/Roles/` next to this script, for testing."""
    path = Path(roles_dir if roles_dir is not None else Path(__file__).resolve().parents[1] / 'Roles') / (row['name'] + '.md')
    try:
        text = path.read_text(encoding='utf-8')
    except (OSError, UnicodeError):
        return ''
    parts = text.split('```', 2)
    prose = parts[2].lstrip('\n') if len(parts) == 3 else ''
    return prose[:ROLE_GUIDANCE_LIMIT]


# Names the origin, so a model can tell the launcher's configuration from injected text (3.17 live probe).
PROVENANCE = ('Set for this session by the person who started it, through the `axis --role` launcher (a host launch '
              'option, not text from a project file). The role guidance below comes from the role file.')


def system_prompt_file(root, row, surface, line, roles_dir=None):
    """Write the declaration line plus the role's guidance prose to a deterministic path under the project's
    `_Temp/Launch/`, for Claude's `--append-system-prompt-file`; returns the path. Deterministic per role and
    surface, so a later launch overwrites rather than accumulates. Needs a resolved project root and a validated
    surface name; call it only for a declared Claude launch (`child_command` guards this)."""
    if root is None or row is None or not surface: raise ValueError('system_prompt_file needs a project root, a declared role row and a surface name')
    guidance = role_guidance(row, roles_dir)
    text = line + '\n\n' + PROVENANCE + ('\n\n' + guidance if guidance else '') + '\n'
    # Never through a link: a declared role may create files in _Temp/, and this write runs with the User's rights.
    folder = Path(root); folder.mkdir(parents=True, exist_ok=True)
    for part in ('_Temp', 'Launch'):
        folder = folder / part
        try: os.mkdir(folder)
        except FileExistsError: pass
        if not stat.S_ISDIR(os.lstat(folder).st_mode): raise ValueError(f'{folder.relative_to(root).as_posix()} is a link or not a folder; remove it and launch again')
    path = folder / f"{row['name']}-{surface}.md"
    tmp = folder / f'.{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp'
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o644)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle: handle.write(text)
        os.replace(tmp, path)
    except BaseException:
        try: os.unlink(tmp)
        except OSError: pass
        raise
    return path


def hook_installed(root):
    """The guardrails hook is configured for Claude Code in the project's or the user's settings."""
    for p in (root / '.claude/settings.json', root / '.claude/settings.local.json', Path.home() / '.claude/settings.json'):
        try:
            if 'guardrails.py' in json.dumps(json.loads(p.read_text()).get('hooks', {})): return True
        except (OSError, ValueError, AttributeError): continue
    return False


def declaration(role, surface):
    """The declared role row and its declaration line, from the installed role table; a refusal raises ValueError."""
    state = module('startup-state')
    row = state.role_named(role)
    if row is None or row['name'] not in state.DECLARABLE: raise ValueError('--role names no declarable Axis role (Auxiliary, Assistant, Group Agent or Observer)')
    if not surface or not state.SURFACE_NAME.fullmatch(surface): raise ValueError('--surface needs a surface name (letters, digits, . _ -)')
    word = 'Auxiliary' if row['name'] == 'Auxiliary' else row['title']  # the documented form (Practices/Surfaces.md)
    return row, f"Axis role: {word}; surface: {surface}"


def child_command(agent, command, row, line, root=None, surface=None):
    """The agent command line for a declared child: Claude carries the declaration and the role's guidance through a
    system-prompt file, plus its tool limits. No change for an undeclared session (row is None) or a non-Claude
    agent: Codex has no documented one-shot equivalent to `--append-system-prompt-file` (checked in `codex --help`
    and `codex exec --help`, 0.166.0), so it keeps the standing-configuration route below, unchanged. Without a
    project root and surface (a caller that still wants the declaration line only, not a launched session) this
    keeps the plain `--append-system-prompt` form."""
    if row is None or agent != 'claude': return command
    if root is None or surface is None: extra = ['--append-system-prompt', line]
    else: extra = ['--append-system-prompt-file', str(system_prompt_file(root, row, surface, line))]
    deny = CLAUDE_DENY.get(row['name'])
    if deny: extra += ['--disallowedTools', ','.join(deny)]
    if row['serves'] != 'User': extra += NO_MCP
    return command + extra  # after the native authentication selector the launcher verifies


def discover(roots):
    found = set()
    for root in roots:
        p = Path(root).expanduser()
        if not p.is_dir() or p.is_symlink(): continue
        for child in [p, *sorted(p.iterdir())]:
            if child.is_dir() and not child.is_symlink() and (child / '_Axis/PROJECT.md').is_file(): found.add(str(child.resolve()))
    return sorted(found)


SUPERVISION = ('--source-root', '--session', '--authority', '--execute', '--explicit-start', '--operation', '--access-evidence')


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == 'retire':
        return module('axis-roles').main(argv)
    if argv and argv[0] == 'start' and not any(a.split('=')[0] in SUPERVISION for a in argv[1:]):
        # User mode: a fresh session in a project without a live Main. Agents start children through ^^start.
        roles = module('axis-roles')
        if roles.agent_shell():
            print('axis: an agent starts a child project only through ^^start, which passes --source-root, --session and --authority', file=sys.stderr); return 2
        rest = argv[1:]
        if any(a.split('=')[0] in ('--role', '--surface') for a in rest):
            print('axis: start opens a Main session; start a declared role with `axis [project] --role ROLE --surface NAME`', file=sys.stderr); return 2
        valued = {'--agent', '--access'}
        target = next((x for i, x in enumerate(rest) if not x.startswith('-') and not (i and rest[i - 1] in valued)), '.')
        try: roles.start(argparse.Namespace(project=target), lambda root, args: None)
        except roles.RoleActionError as exc:
            print('axis: ' + str(exc), file=sys.stderr); return 2
        # A fresh session: never reattach a terminal session an earlier run left open for this project.
        tmux = shutil.which('tmux')
        if tmux and subprocess.run([tmux, 'has-session', '-t', '=' + name(project(target))], capture_output=True).returncode == 0:
            print('axis: a terminal session for this project is still open; attach with `axis`, or close it first, then run `axis start` again', file=sys.stderr); return 2
        return main(rest)
    if argv and argv[0] in {'probe', 'status', 'start'}:
        return subprocess.call([sys.executable, str(Path(__file__).with_name('session-adapters.py')), *argv])
    parser = argparse.ArgumentParser(description='axis [project] [--agent codex|claude|none]; axis start [project]; axis retire [project]; axis ls; axis projects [roots]')
    parser.add_argument('target', nargs='?', default='.')
    parser.add_argument('roots', nargs='*')
    parser.add_argument('--agent', default='codex', choices=('codex', 'claude', 'none'))
    parser.add_argument('--access', choices=('subscription', 'api-key', 'either'))
    parser.add_argument('--allow-api', action='store_true', help='authorize paid API use for this interactive session; provider billing controls remain external')
    parser.add_argument('--detach', action='store_true')
    parser.add_argument('--role', help='start a declared session in this role (Auxiliary, Assistant, Group Agent or Observer)')
    parser.add_argument('--surface', help='the surface name the role is declared for; it needs a row in the surface table')
    parser.add_argument('--run-child', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.target == 'projects':
            print('\n'.join(discover(args.roots or os.environ.get('AXIS_PROJECT_ROOTS', str(Path.cwd())).split(os.pathsep))))
            return 0
        tmux = shutil.which('tmux')
        if args.target == 'ls':
            if not tmux: raise ValueError('tmux is unavailable; open the project in your agent normally')
            result = subprocess.run([tmux, 'list-sessions', '-F', '#{session_name}\t#{session_path}'], text=True, capture_output=True)
            print('\n'.join(line for line in result.stdout.splitlines() if line.startswith('axis-')))
            return 0
        if args.roots: raise ValueError('one project path is required')
        root = project(args.target)
        row = line = None
        if args.role or args.surface:
            row, line = declaration(args.role, args.surface)
            if row['serves'] != 'User' and args.agent == 'claude' and not hook_installed(root):
                raise ValueError('a ' + row['title'] + ' on Claude Code needs the guardrails hook to hold its read scope; run ^install guardrails in a Main session first')
            if row['serves'] != 'User' and args.agent != 'claude':
                print(f"axis: on {args.agent} a {row['title']}'s read scope and tool limits hold only through its role file", file=sys.stderr)
        if args.run_child:
            os.chdir(root)
            if args.agent == 'none': os.execv('/bin/sh', ['/bin/sh'])
            executable = shutil.which(args.agent)
            if not executable: raise ValueError('selected agent executable is unavailable')
            access = module('model-access')
            command, env, _ = access.prepare(root, args.agent, [executable], mode=args.access, paid_authorized=args.allow_api)
            if row is not None:
                env['AXIS_ROLE'], env['AXIS_SURFACE'] = row['name'], args.surface
                command = child_command(args.agent, command, row, line, root, args.surface)
                if args.agent != 'claude': print(f'axis: put the line "{line}" in this agent\'s standing configuration; the launcher sets AXIS_ROLE for the helpers', file=sys.stderr)
            verified = access.verify_cli(args.agent,command,env,str(root),allow_interactive_choice=True)
            if verified == 'interactive-approval-required':
                env['AXIS_MODEL_ACCESS'] = 'unverified'
                print('axis: approve the API key in Claude before sending a prompt; Axis will report access as unverified until the choice is confirmed.',file=sys.stderr)
            os.execve(executable, command, env)
        if not tmux: raise ValueError('tmux is unavailable; open the project in your agent normally, or opt in through ^install axis')
        # Credentials are read by the fresh child, never placed in tmux arguments/server settings.
        child = [sys.executable, str(Path(__file__).resolve()), str(root), '--agent', args.agent, '--run-child']
        if row is not None: child += ['--role', row['name'], '--surface', args.surface]
        if args.access: child += ['--access', args.access]
        if args.allow_api: child += ['--allow-api']
        session = name(root, row and row['name'], args.surface)
        if args.detach:
            # new-session -A attaches an existing session even with -d. A
            # detached reopen must never require a terminal or create a pane.
            exists = [tmux, 'has-session', '-t', '=' + session]
            if subprocess.run(exists, capture_output=True).returncode == 0: return 0
            created = subprocess.run([tmux, 'new-session', '-d', '-s', session, '-c', str(root), shlex.join(child)], capture_output=True)
            if created.returncode == 0: return 0
            # Another launcher may have created the same session concurrently.
            if subprocess.run(exists, capture_output=True).returncode == 0: return 0
            sys.stderr.buffer.write(created.stderr)
            return created.returncode
        return subprocess.call([tmux, 'new-session', '-A', '-s', session, '-c', str(root), shlex.join(child)])
    except (OSError, ValueError) as exc:
        print('axis: ' + str(exc), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
