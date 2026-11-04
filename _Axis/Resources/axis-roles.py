#!/usr/bin/env python3
"""Role actions for the `axis` utility: end a live Main (`retire`) and open a fresh session (`start`).

  axis retire [project] [--session ID] [--reason TEXT] [--yes]
  axis retire CHILD --from PARENT --session-of-caller ID --instruction RECORD   (agent mode)
  axis start [project] [--agent codex|claude|none]

User mode is for the person at a terminal: it shows the target session and asks for the typed word RETIRE (or takes
--yes from the User's own scripts). Agent mode is required when the shell belongs to an agent: the caller names its own
Main session, the target must be a direct child of the caller's project, and a Log or Supervision record written by that
session must carry `requested-by: owner`, `action:` and the exact `target:` child path; Main writes it only for the
verified owner, never for another allowed sender. Both modes write the same tombstone `^kill` writes and remove the Marker;
the retired session stops at its next turn check. These checks catch mistakes; an agent with an unrestricted shell
could still pose as the User. The guardrails hook refuses User mode from a Claude Code agent shell; elsewhere only the
host's own command rules prevent it. No session ever changes its own role."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time

SID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\Z')
HOUR = 3600
# Environment markers that agent hosts set in the shells they run; best effort, documented as such.
AGENT_ENV = ('CLAUDECODE', 'CLAUDE_CODE_ENTRYPOINT', 'CODEX_SANDBOX', 'CODEX_SANDBOX_NETWORK_DISABLED', 'CODEX_THREAD_ID',
             'GEMINI_CLI', 'OPENCLAW_SESSION_KEY', 'OPENCLAW_AGENT_ID', 'AXIS_AGENT_SESSION', 'AXIS_ROLE', 'AXIS_SURFACE')
ANCHOR = '_Axis/PROJECT.md'
ACTIONS = {'retire': ('retire', 'stop', 'restart'), 'start': ('start', 'restart')}


class RoleActionError(Exception):
    pass


def need(ok, message):
    if not ok:
        raise RoleActionError(message)


def module(name):
    path = Path(__file__).with_name(name + '.py')
    need(path.is_file() and not path.is_symlink(), name + '.py is unavailable; follow the manual steps in the User Manual')
    spec = importlib.util.spec_from_file_location('axis_roles_' + name.replace('-', '_'), path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def agent_shell(env=None):
    env = os.environ if env is None else env
    return sorted(k for k in AGENT_ENV if env.get(k))


def project(value):
    p = Path(value).expanduser()
    need(p.is_dir() and not p.is_symlink(), 'not a project folder: ' + str(value))
    p = p.resolve(strict=True)
    need((p / ANCHOR).is_file(), 'not an Axis project: ' + str(p))
    return p


def nearest_project(path):
    for p in path.parents:
        if (p / ANCHOR).is_file():
            return p
    return None


def regular(path):
    return path.is_file() and not path.is_symlink() and path.stat().st_nlink == 1


def live_mains(root, now=None):
    """Fresh `Main: session` Markers without a tombstone, newest first."""
    now = time.time() if now is None else now
    found = []
    agents = root / '_Axis/Agents'
    if not agents.is_dir():
        return found
    for p in agents.glob('*.md'):
        if not SID.match(p.stem) or not regular(p) or p.with_suffix('.kill').exists():
            continue
        lines = p.read_text(errors='replace').splitlines()
        if lines[:1] != ['Main: session']:
            continue
        age = now - p.stat().st_mtime
        if 0 <= age < HOUR:
            host = next((l[6:] for l in lines if l.startswith('host: ')), 'unknown')
            found.append({'session': p.stem, 'host': host, 'idle_minutes': int(age // 60), 'marker': p})
    return sorted(found, key=lambda m: m['session'], reverse=True)


def tracking_tail(root, sid, count=5):
    p = root / '_Axis/Tracking' / (sid + '.md')
    if not regular(p):
        return []
    return [l for l in p.read_text(errors='replace').splitlines() if l.strip()][-count:]


def target_main(root, session):
    mains = live_mains(root)
    if session:
        need(SID.match(session), 'invalid Session ID')
        match = [m for m in mains if m['session'] == session]
        need(match, f'no live Main session {session} in {root}')
        return match[0]
    need(mains, f'no live Main in {root}; nothing to retire')
    need(len(mains) == 1, 'more than one live Main: ' + ', '.join(m['session'] for m in mains) + '; name one with --session')
    return mains[0]


def own_lease(root, sid):
    """The caller's Main lease, checked the way turn.py checks it."""
    need(SID.match(sid or ''), 'agent mode requires --session-of-caller with your Session ID')
    marker = root / '_Axis/Agents' / (sid + '.md')
    need(regular(marker), 'your Main Marker is missing; you hold no lease')
    need(not marker.with_suffix('.kill').exists(), 'your session was stopped by the User')
    lines = marker.read_text(errors='replace').splitlines()
    need(len(lines) == 4 and lines[:3] == ['Main: session', '', 'session: ' + sid] and lines[3].startswith('host: '), 'your Marker is not a Main lease')
    need(0 <= time.time() - marker.stat().st_mtime < HOUR, 'your Main lease has expired; renew it on your next turn first')
    flag = root / '_Axis/Flags/session-id'
    need(regular(flag) and (flag.read_text().splitlines() or [''])[0].strip() == sid, 'the project session-id names another session')


def instruction(root, sid, record, action, child_rel):
    """A Log or Supervision record by this session that carries the owner's request: `requested-by: owner`, an
    `action:` line naming this action and an exact `target:` line naming the child."""
    need(SID.match(record or ''), 'agent mode requires --instruction naming a Log or Supervision record')
    for family in ('Logs', 'Supervision'):
        p = root / '_Axis' / family / (record + '.md')
        if regular(p):
            text = p.read_text(errors='replace')
            need(re.search(r'(?m)^session: ' + re.escape(sid) + r'\s*$', text), 'the instruction record was not written by your session')
            need(re.search(r'(?m)^requested-by: owner\s*$', text), 'the instruction record does not show the verified owner asked (requested-by: owner)')
            need(re.search(r'(?m)^target: ' + re.escape(child_rel) + r'\s*$', text), 'the instruction record does not name exactly target: ' + child_rel)
            need(re.search(r'(?m)^action: (?:' + '|'.join(ACTIONS[action]) + r')\s*$', text), 'the instruction record does not name the ' + action + ' action')
            return family + '/' + record
    raise RoleActionError('instruction record not found: ' + record)


def merge_ready(root):
    """A merge source, a retired source or malformed merge state refuses before any fence."""
    state = module('startup-state')
    try:
        state.Startup(str(root)).merge_access()
    except state.Fault as exc:
        raise RoleActionError('the project is held by merge state (' + exc.code + '); nothing changed') from None


def agent_target(parent, child):
    """A direct child of the caller's project; never the caller's own project or an ancestor."""
    need(child != parent, 'agent mode never acts on its own project')
    need(child not in parent.parents, 'agent mode never acts on an ancestor')
    need(parent in child.parents, 'the target is not inside your project; unrelated projects are refused')
    need(nearest_project(child) == parent, 'only a direct child; route deeper actions through the child\'s Main')
    return child.relative_to(parent).as_posix()


def tombstone(root, sid, killed_by, reason):
    agents = root / '_Axis/Agents'
    kill = agents / (sid + '.kill')
    stamp = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    body = f'killed-by: {killed_by}\n{stamp}\n{reason}\n'
    need(not agents.is_symlink() and agents.is_dir(), 'unsafe _Axis/Agents folder')
    try:
        fd = os.open(kill, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    except FileExistsError:
        raise RoleActionError(f'session {sid} was already stopped') from None
    with os.fdopen(fd, 'w') as h:
        h.write(body)
    need(kill.read_text() == body, 'tombstone readback failed')
    marker = agents / (sid + '.md')
    try:
        marker.unlink()
        removed = True
    except OSError:
        removed = False
    return {'tombstone': kill.relative_to(root).as_posix(), 'marker_removed': removed}


def log_writer(root):
    """The target project's Log writer, prepared before any fence so a missing helper or folder refuses first. It mints
    under the ordinary timestamp claim without a session lease, because the User holds none."""
    state = module('startup-state')

    class UserWriter(state.Startup):
        sid = 'user'

        def guard(self, starting=True, foreign=True):
            self.merge_access()  # no session lease; the merge barrier still applies to every write

    try:
        writer = UserWriter(str(root))
        writer.merge_access()  # a merge source or retired source refuses here, before any fence
    except state.Fault as exc:
        raise RoleActionError('the project cannot record the retirement (' + exc.code + '); nothing changed') from None

    def write(subject, body):
        content = subject + '\n\nby: User (axis utility)\n\n' + body.rstrip('\n') + '\n'
        return writer.record('Logs', lambda _: content, renew_lease=False)[1]
    return write


def retire(args):
    shell = agent_shell()
    if args.from_root or args.session_of_caller or args.instruction or shell:
        need(args.from_root and args.session_of_caller, 'agent mode requires --from (your project root), --session-of-caller (your Session ID) and --instruction')
        parent = project(args.from_root)
        child = project(args.project)
        rel = agent_target(parent, child)
        own_lease(parent, args.session_of_caller)
        ref = instruction(parent, args.session_of_caller, args.instruction, 'retire', rel)
        target = target_main(child, args.session)
        merge_ready(child)
        result = tombstone(child, target['session'], args.session_of_caller, args.reason or 'supervisor stop requested by User')
        return {'status': 'retired', 'mode': 'agent', 'agent_shell': shell, 'target': rel, 'session': target['session'], 'instruction': ref, **result}
    root = project(args.project)
    target = target_main(root, args.session)
    tail = tracking_tail(root, target['session'])
    print(f"Live Main {target['session']} on {target['host']}, last active {target['idle_minutes']} minutes ago.", file=sys.stderr)
    for line in tail or ['(no Tracking lines)']:
        print('  ' + line, file=sys.stderr)
    if not args.yes:
        need(sys.stdin.isatty() or args.confirm_from_stdin, 'type RETIRE at a terminal, or pass --yes from your own script')
        print('Type RETIRE to end this session (its records stay; it stops at its next turn): ', end='', file=sys.stderr, flush=True)
        need(sys.stdin.readline().strip() == 'RETIRE', 'not confirmed; nothing changed')
    reason = args.reason or 'retired by User (axis retire)'
    write = log_writer(root)
    result = tombstone(root, target['session'], 'user (axis retire)', reason)
    try:
        log = write('Main retired by User (axis retire)',
                    f"session: {target['session']}\nhost: {target['host']}\nreason: {reason}\n\n"
                    'The User ended this Main session from a terminal with `axis retire`. It stops at its next turn check; '
                    'its records are unchanged. The next new session becomes Main by the normal rule.')
    except Exception as exc:
        # The fence already holds: report the retirement truthfully and name the missing record.
        return {'status': 'retired', 'mode': 'user', 'session': target['session'], 'log': None, 'log_error': f'{type(exc).__name__}: {exc}', 'tracking_tail': tail, **result}
    return {'status': 'retired', 'mode': 'user', 'session': target['session'], 'log': log, 'tracking_tail': tail, **result}


def start(args, launch):
    root = project(args.project)
    mains = live_mains(root)
    need(not mains, f"{root} has a live Main {mains[0]['session'] if mains else ''}; end it with `axis retire` first, or open the project to join as Auxiliary")
    return launch(root, args)


def parser():
    p = argparse.ArgumentParser(prog='axis', description='Axis role actions: retire a live Main, or start a fresh session.')
    sub = p.add_subparsers(dest='action', required=True)
    r = sub.add_parser('retire', help='end a live Main session from a terminal')
    r.add_argument('project', nargs='?', default='.')
    r.add_argument('--session', help='the exact Main Session ID to retire when more than one is live')
    r.add_argument('--reason')
    r.add_argument('--yes', action='store_true', help='skip the typed confirmation (for the User\'s own scripts)')
    r.add_argument('--confirm-from-stdin', action='store_true', help=argparse.SUPPRESS)
    r.add_argument('--from', dest='from_root', help='agent mode: the calling (parent) project root')
    r.add_argument('--session-of-caller', help='agent mode: your own Main Session ID')
    r.add_argument('--instruction', help='agent mode: the Log or Supervision record naming this action and child')
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        result = retire(args)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except RoleActionError as exc:
        print(json.dumps({'status': 'refused', 'reason': str(exc)}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
