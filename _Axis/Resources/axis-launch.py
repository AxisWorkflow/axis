#!/usr/bin/env python3
"""Optional tmux launcher. A deterministic session name makes reattach idempotent.

3.16: `axis [project] --role ROLE --surface NAME` starts a declared session. The child gets AXIS_ROLE and AXIS_SURFACE,
which the helpers and the guardrails hook read; on Claude it also carries the declaration as an appended system
prompt and, for roles that serve other people, the per-process tool limits. Other agents need the declaration in
their own standing configuration; the launcher says so."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shlex
import shutil
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
    return row, f"Axis role: {row['title']}; surface: {surface}"


def child_command(agent, command, row, line):
    """The agent command line for a declared child: Claude carries the declaration and its tool limits."""
    if row is None or agent != 'claude': return command
    extra = ['--append-system-prompt', line]
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
                command = child_command(args.agent, command, row, line)
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
