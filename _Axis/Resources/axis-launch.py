#!/usr/bin/env python3
"""Optional tmux launcher. A deterministic session name makes reattach idempotent."""
import argparse
import hashlib
import importlib.util
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


def name(root):
    return 'axis-' + hashlib.sha256(os.fsencode(root)).hexdigest()[:24]


def discover(roots):
    found = set()
    for root in roots:
        p = Path(root).expanduser()
        if not p.is_dir() or p.is_symlink(): continue
        for child in [p, *sorted(p.iterdir())]:
            if child.is_dir() and not child.is_symlink() and (child / '_Axis/PROJECT.md').is_file(): found.add(str(child.resolve()))
    return sorted(found)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in {'probe', 'status', 'start'}:
        return subprocess.call([sys.executable, str(Path(__file__).with_name('session-adapters.py')), *argv])
    parser = argparse.ArgumentParser(description='axis [project] [--agent codex|claude|none]; axis ls; axis projects [roots]')
    parser.add_argument('target', nargs='?', default='.')
    parser.add_argument('roots', nargs='*')
    parser.add_argument('--agent', default='codex', choices=('codex', 'claude', 'none'))
    parser.add_argument('--access', choices=('subscription', 'api-key', 'either'))
    parser.add_argument('--allow-api', action='store_true', help='authorize paid API use for this interactive session; provider billing controls remain external')
    parser.add_argument('--detach', action='store_true')
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
        if args.run_child:
            os.chdir(root)
            if args.agent == 'none': os.execv('/bin/sh', ['/bin/sh'])
            executable = shutil.which(args.agent)
            if not executable: raise ValueError('selected agent executable is unavailable')
            access = module('model-access')
            command, env, _ = access.prepare(root, args.agent, [executable], mode=args.access, paid_authorized=args.allow_api)
            verified = access.verify_cli(args.agent,command,env,str(root),allow_interactive_choice=True)
            if verified == 'interactive-approval-required':
                env['AXIS_MODEL_ACCESS'] = 'unverified'
                print('axis: approve the API key in Claude before sending a prompt; Axis will report access as unverified until the choice is confirmed.',file=sys.stderr)
            os.execve(executable, command, env)
        if not tmux: raise ValueError('tmux is unavailable; open the project in your agent normally, or opt in through ^install axis')
        # Credentials are read by the fresh child, never placed in tmux arguments/server settings.
        child = [sys.executable, str(Path(__file__).resolve()), str(root), '--agent', args.agent, '--run-child']
        if args.access: child += ['--access', args.access]
        if args.allow_api: child += ['--allow-api']
        session = name(root)
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
