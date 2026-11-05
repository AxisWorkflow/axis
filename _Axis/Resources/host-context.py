#!/usr/bin/env python3
"""Optional host hook: mark a context compaction, and give a resumed or compacted session its Axis identity back.

`^install context hooks` makes this the one hook command on each host: Claude Code SessionStart (startup|resume|compact) and
PreCompact; Codex SessionStart and PostCompact. It reads the host's hook JSON on stdin.
- A compaction event (PreCompact, PostCompact, SessionStart `compact`, or another host's compaction event) appends
  `{UTC identifier timestamp} {host} {12 hex of sha256(host session ID) or -}` to `_Temp/Context/compactions.log`.
- SessionStart `resume` or `compact` prints the Card (the bound Axis Session ID, its role, and the instruction to run
  turn.py and reload before answering), then that role's guidance from `_Axis/Roles/{Role}.md`, when both fit the
  host's cap: on Claude Code one string of at most 9,500 characters, on Codex the 4,000-token additionalContextLimit
  its entry sets. Over the cap it prints the Card only, never cut text.
- Without a binding it prints one role-neutral line. A Codex `compact` always gets only that line, because a spawned
  agent's hook carries its parent's session ID; a Claude Code call from a spawned agent (agent_id) gets nothing.
- `startup` prints nothing. Every call exits 0, blocks nothing, never prints Secrets or absolute paths, and stays
  silent on a missing Marker, a kill tombstone, an unknown role or malformed input.

Subcommands:
  bind --session {Session ID} [--host claude|codex]
      Map this host session (CLAUDE_CODE_SESSION_ID or CODEX_THREAD_ID) to its Axis Session ID in
      `_Temp/Context/bindings/`; writes nothing unless exactly one such variable is set. Prints one JSON line; exit 0.
  whoami [--host claude|codex]
      Print the Axis Session ID and role bound to this host session when its Marker is live (exit 0); otherwise UNBOUND
      (exit 4). This binding is the verified native-session binding Continue-Session.md accepts.
  install|uninstall --host claude|codex [--dry-run]
      Print the exact change to `.claude/settings.json` or `.codex/hooks.json`; without --dry-run, apply it (exactly one
      Axis entry per event, every other byte kept) and read it back. Exit 0 done or unchanged, 2 refused.
Without hooks, the entry file's after-compaction rule and turn.py recover on every host. Standard library only."""
import argparse, datetime as dt, hashlib, json, os, re, stat, sys
from pathlib import Path

ROOT = Path(os.path.abspath(__file__)).parents[2]
SCRIPT = '_Axis/Resources/host-context.py'
SESSION = re.compile(r'\d{4}(\.\d{2}){5}\.\d{3}Z')
HOST = re.compile(r'[a-z][a-z0-9-]{0,31}')
HOST_SESSION = {'claude': 'CLAUDE_CODE_SESSION_ID', 'codex': 'CODEX_THREAD_ID'}
CLAUDE_CAP = 9500     # characters (UTF-16 units) in the one printed string; Claude Code's own cap is 10,000
CODEX_TOKENS = 4000   # the additionalContextLimit the Codex entry sets; printed text is counted at 3 bytes per token
COMPACTION = ('precompact', 'postcompact', 'precompress', 'postcompaction')
ROLE_ROW = re.compile(r'^```axis-role\n(.*?)^```$', re.M | re.S)
NOFOLLOW, NONBLOCK = getattr(os, 'O_NOFOLLOW', 0), getattr(os, 'O_NONBLOCK', 0)
NEUTRAL = 'if you serve this project under an Axis Session ID, run turn.py with it before answering; if you no longer know it, follow _Axis/Resources/Continue-Session.md; a delegated helper follows its envelope instead.'


def card(session, title, name, compacted):
    lead = 'Axis: context was compacted. Your' if compacted else 'Axis: your'
    return (f'{lead} Axis Session ID is {session} and your role is {title} (_Axis/Roles/{name}.md); run turn.py and reload '
            f'before answering: python3 _Axis/Resources/turn.py --session {session}, then re-read in full every file it lists.')


def neutral(compacted):
    return ('Axis: context was compacted; ' if compacted else 'Axis: ') + NEUTRAL


def fits(host, text):
    if host == 'claude': return len(text.encode('utf-16-le')) // 2 <= CLAUDE_CAP
    return (len(text.encode('utf-8')) + 2) // 3 <= CODEX_TOKENS


def plain_dir(path):
    try: return stat.S_ISDIR(os.lstat(path).st_mode)
    except OSError: return False


def small(path, limit=65536):
    """A regular, singly linked file's UTF-8 text, never through a link; None otherwise."""
    try: fd = os.open(path, os.O_RDONLY | NOFOLLOW | NONBLOCK)
    except OSError: return None
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit: return None
        data = b''
        while len(data) <= limit:
            chunk = os.read(fd, limit + 1 - len(data))
            if not chunk: break
            data += chunk
        return data.decode('utf-8') if len(data) <= limit else None
    except (OSError, UnicodeError): return None
    finally: os.close(fd)


def roles(root):
    """(name, Marker subject, subject match, title) for each session role that holds a Marker, from its role file."""
    found, folder = [], root / '_Axis/Roles'
    if not plain_dir(folder): return found
    for path in sorted(folder.glob('*.md')):
        blocks = ROLE_ROW.findall(small(path) or '')
        try: row = json.loads(blocks[0]) if len(blocks) == 1 else None
        except ValueError: continue
        admission = row.get('admission') if isinstance(row, dict) else None
        if not isinstance(admission, dict) or row.get('class') != 'session' or admission.get('created_by') not in ('claim', 'helper'): continue
        subject, title = admission.get('marker_subject'), (row.get('presentation') or {}).get('title')
        if isinstance(subject, str) and subject and row.get('name') == path.stem:
            found.append((path.stem, subject, admission.get('subject_match'), title if isinstance(title, str) else path.stem))
    return found


def identity(root, session):
    """(role name, title) for this Session ID's own Marker; None for a missing or malformed Marker, a tombstone or an unknown role."""
    agents = root / '_Axis/Agents'
    if not SESSION.fullmatch(session) or not plain_dir(root / '_Axis') or not plain_dir(agents) or os.path.lexists(agents / f'{session}.kill'): return None
    text = small(agents / f'{session}.md')
    if text is None or re.findall(r'^session: (.+)$', text, re.M) != [session]: return None
    first = (text.splitlines() or [''])[0]
    for name, subject, match, title in roles(root):
        if (first == subject) if match == 'exact' else re.fullmatch(re.escape(subject) + r'[^\r\n]+', first): return name, title
    return None


def guidance(root, name):
    """The role file's prose after its axis-role block, as written."""
    text = small(root / '_Axis/Roles' / f'{name}.md') or ''
    blocks = list(ROLE_ROW.finditer(text))
    return text[blocks[0].end():].strip() if len(blocks) == 1 else ''


def digest(host_session):
    return hashlib.sha256(host_session.encode('utf-8')).hexdigest()[:12]


def context_dir(root, *parts, create=False):
    """_Temp/Context (or a folder in it) as a real directory; None when _Temp or any part is a link or not a folder."""
    path = root
    for part in ('_Temp', 'Context') + parts:
        path = path / part
        if create:
            try: os.mkdir(path)
            except FileExistsError: pass
        if not plain_dir(path): return None
    return path


def bound(root, host_session):
    folder = context_dir(root, 'bindings')
    value = ((small(folder / digest(host_session), 64) if folder else None) or '').strip()
    return value if SESSION.fullmatch(value) else None


def stamp():
    now = dt.datetime.now(dt.timezone.utc)
    return now.strftime('%Y.%m.%d.%H.%M.%S.') + f'{now.microsecond // 1000:03d}Z'


def mark(root, host, host_session):
    folder = context_dir(root, create=True)
    if folder is None: return
    line = f'{stamp()} {host} {digest(host_session) if host_session else "-"}\n'.encode()
    fd = os.open(folder / 'compactions.log', os.O_WRONLY | os.O_APPEND | os.O_CREAT | NOFOLLOW | NONBLOCK, 0o644)
    try:
        info = os.fstat(fd)
        if stat.S_ISREG(info.st_mode) and info.st_nlink == 1: os.write(fd, line)
    finally: os.close(fd)


def hook(root, host, raw):
    """What to print for one hook call ('' for nothing); a compaction event also appends its mark."""
    try: event = json.loads(raw)
    except ValueError: return ''
    name = event.get('hook_event_name') if isinstance(event, dict) else None
    if not isinstance(name, str) or not (plain_dir(root / '_Axis') and plain_dir(root / '_Axis/Agents')): return ''
    source = event.get('source') if name == 'SessionStart' else None
    compacted = name.lower() in COMPACTION or source == 'compact'
    host_session = event.get('session_id') if isinstance(event.get('session_id'), str) and event['session_id'].strip() else None
    spawned = host == 'claude' and bool(event.get('agent_id'))
    if compacted and not spawned:  # a spawned agent's compaction is not its parent's
        try: mark(root, host, host_session)
        except OSError: pass
    if source not in ('resume', 'compact') or host not in HOST_SESSION: return ''
    if spawned: return ''
    if host == 'codex' and compacted: return neutral(True)
    session = bound(root, host_session) if host_session else None
    if session is None: return neutral(compacted)
    found = identity(root, session)
    if found is None: return ''
    head, text = card(session, found[1], found[0], compacted), guidance(root, found[0])
    full = f'{head}\nRole guidance from _Axis/Roles/{found[0]}.md:\n\n{text}'
    return full if text and fits(host, full + '\n') else head


def bind(root, session, host=None, environ=None):
    """Record which Axis session this host session runs, for the hook; returns a status dict."""
    environ = os.environ if environ is None else environ
    if not isinstance(session, str) or not SESSION.fullmatch(session): return {'status': 'refused', 'reason': 'not a Session ID'}
    if host is not None and host not in HOST_SESSION: return {'status': 'refused', 'reason': 'unknown host'}
    values = [environ.get(var, '').strip() for key, var in HOST_SESSION.items() if host in (None, key)]
    values = [v for v in values if v]
    if len(values) != 1:
        return {'status': 'skipped', 'reason': 'two host session variables; name --host' if values else 'no host session variable'}
    if identity(root, session) is None: return {'status': 'refused', 'reason': 'no live Marker for a session role'}
    folder = context_dir(root, 'bindings', create=True)
    if folder is None: return {'status': 'refused', 'reason': '_Temp/Context is a link or not a folder'}
    target = folder / digest(values[0])
    temp = folder / f'.{target.name}.{os.getpid()}.tmp'
    try:
        fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o644)
        try: os.write(fd, (session + '\n').encode())
        finally: os.close(fd)
        os.replace(temp, target)
    except OSError:
        try: os.unlink(temp)
        except OSError: pass
        return {'status': 'refused', 'reason': 'binding not written'}
    return {'status': 'bound'}


# Install and uninstall: one Axis hook group per event, spliced into the settings text so every other byte stays.
TARGET = {'claude': '.claude/settings.json', 'codex': '.codex/hooks.json'}
TITLE = {'claude': 'Claude Code', 'codex': 'Codex'}
# '|| true': a missing or broken script must never block the host; Claude Code reads exit 2 on PreCompact as "block".
CLAUDE_COMMAND = 'python3 "$CLAUDE_PROJECT_DIR/_Axis/Resources/host-context.py" --host claude || true'
CODEX_COMMAND = 'python3 _Axis/Resources/host-context.py --host codex || true'
DECODER = json.JSONDecoder()


def entries(host):
    if host == 'claude':
        handler = {'type': 'command', 'command': CLAUDE_COMMAND, 'timeout': 10}
        return {'SessionStart': {'matcher': 'startup|resume|compact', 'hooks': [handler]}, 'PreCompact': {'hooks': [handler]}}
    handler = {'type': 'command', 'command': CODEX_COMMAND}
    return {'SessionStart': {'matcher': 'startup|resume|compact', 'hooks': [dict(handler, additionalContextLimit=CODEX_TOKENS)]},
            'PostCompact': {'hooks': [handler]}}


def axis_group(group):
    """True when every handler in this hook group runs this script, None when only some do, False otherwise."""
    handlers = group.get('hooks') if isinstance(group, dict) else None
    ours = [isinstance(h, dict) and isinstance(h.get('command'), str) and SCRIPT in h['command'] for h in handlers] if isinstance(handlers, list) else []
    return (True if all(ours) else None) if any(ours) else False


def skip(t, i):
    while t[i:i + 1] in (' ', '\t', '\n', '\r'): i += 1
    return i


class Box:
    """A JSON object or array in the text: each item's leading separator, text, key and spans; the text before its close."""
    def __init__(self, t, start):
        self.t, self.start, self.obj, self.items = t, start, t[start] == '{', []
        close, j, prev = '}' if t[start] == '{' else ']', skip(t, start + 1), start + 1
        while t[j:j + 1] != close:
            item, key = j, None
            if self.obj:
                if t[j:j + 1] != '"': raise ValueError('it is not valid JSON')
                key, j = DECODER.raw_decode(t, j)
                j = skip(t, j)
                if t[j:j + 1] != ':': raise ValueError('it is not valid JSON')
                j = skip(t, j + 1)
            value = j
            _, j = DECODER.raw_decode(t, j)
            self.items.append({'sep': t[prev:item], 'text': t[item:j], 'key': key, 'start': item, 'value': value})
            prev, j = j, skip(t, j)
            if t[j:j + 1] == ',': j = skip(t, j + 1)
            elif t[j:j + 1] != close: raise ValueError('it is not valid JSON')
        self.tail, self.end = t[prev:j], j + 1

    def keys(self, key): return [i for i, x in enumerate(self.items) if x['key'] == key]

    def base(self, i):
        sep = self.items[i]['sep']
        return sep.rsplit('\n', 1)[1] if '\n' in sep else None

    def child(self, i): return Box(self.t, self.items[i]['value'])

    def put(self, i, box):
        x = self.items[i]
        x['text'] = self.t[x['start']:x['value']] + box.render()

    def remove(self, i):
        if i == 0 and len(self.items) > 1: self.items[1]['sep'] = self.items[0]['sep']
        del self.items[i]
        if not self.items: self.tail = ''

    def add(self, text_for, parent_base, unit, key=None):
        """Append an item whose text text_for(indentation) gives, separated like the items before it."""
        if self.items:
            lead = self.items[-1]['sep'].split(',', 1)[-1]
            base, sep = (lead.rsplit('\n', 1)[1] if '\n' in lead else None), ',' + (lead or ' ')
        elif unit is not None and parent_base is not None:
            base, sep, self.tail = parent_base + unit, '\n' + parent_base + unit, '\n' + parent_base
        else: base, sep = None, ''
        self.items.append({'sep': sep, 'text': text_for(base), 'key': key})

    def render(self):
        o, c = ('{', '}') if self.obj else ('[', ']')
        return o + ''.join(x['sep'] + x['text'] for x in self.items) + self.tail + c


def dump(value, base, unit):
    if base is None or unit is None: return json.dumps(value, ensure_ascii=False)
    return json.dumps(value, indent=unit, ensure_ascii=False).replace('\n', '\n' + base)


def plan(text, host, install, changes):
    """The settings text with exactly one Axis group per event (install) or none (uninstall), listing each change in
    changes; ValueError refuses. Only Axis's own entries are ever named, so no other setting is printed."""
    want = entries(host)
    adds = [f'add to hooks.{e}: {json.dumps(g)}' for e, g in want.items()]
    if text is None or not text.strip():
        if install: changes += ['create the file'] + adds
        return json.dumps({'hooks': {e: [g] for e, g in want.items()}}, indent=2) + '\n' if install else text
    data = json.loads(text)
    if not isinstance(data, dict): raise ValueError('the file is not a JSON object')
    top = Box(text, skip(text, 0))
    first = top.items[0]['sep'] if top.items else '\n  '
    unit = first.rsplit('\n', 1)[1] if '\n' in first else None
    found = top.keys('hooks')
    if len(found) > 1: raise ValueError('it has two "hooks" keys')
    if not found:
        if not install: return text
        top.add(lambda b: '"hooks": ' + dump({e: [g] for e, g in want.items()}, b, unit), '', unit, 'hooks')
        changes += adds
        return text[:top.start] + top.render() + text[top.end:]
    if not isinstance(data['hooks'], dict): raise ValueError('"hooks" is not an object')
    h, changed = found[0], False
    hooks, hooks_base = top.child(h), top.base(h)
    for event, group in want.items():
        found = hooks.keys(event)
        if len(found) > 1: raise ValueError(f'it has two "{event}" keys')
        if not found:
            if install:
                hooks.add(lambda b: json.dumps(event) + ': ' + dump([group], b, unit), hooks_base, unit, event)
                changed = True; changes.append(f'add to hooks.{event}: {json.dumps(group)}')
            continue
        k = found[0]
        groups = data['hooks'][event]
        if not isinstance(groups, list): raise ValueError(f'"{event}" is not a list')
        kinds = [axis_group(g) for g in groups]
        if None in kinds: raise ValueError(f'an Axis handler shares a {event} group with other handlers; edit it by hand')
        mine = [i for i, kind in enumerate(kinds) if kind]
        if (install and len(mine) == 1 and groups[mine[0]] == group) or (not install and not mine): continue
        array, changed = hooks.child(k), True
        for i in reversed(mine[1:] if install else mine):
            array.remove(i); changes.append(f'remove from hooks.{event}: {json.dumps(groups[i])}')
        if install and mine:
            array.items[mine[0]]['text'] = dump(group, array.base(mine[0]), unit)
            changes.append(f'replace in hooks.{event}: {json.dumps(groups[mine[0]])} with {json.dumps(group)}')
        elif install:
            array.add(lambda b: dump(group, b, unit), hooks.base(k), unit); changes.append(f'add to hooks.{event}: {json.dumps(group)}')
        if array.items: hooks.put(k, array)
        else:
            hooks.remove(k); changes.append(f'remove the now empty hooks.{event} list')
    if not changed: return text
    if hooks.items: top.put(h, hooks)
    else:
        top.remove(h); changes.append('remove the now empty "hooks" object')
    return text[:top.start] + top.render() + text[top.end:]


def normal(data):
    """The settings without Axis's hook groups and the empty lists and "hooks" object they leave."""
    data = json.loads(json.dumps(data))
    hooks = data.get('hooks') if isinstance(data, dict) else None
    if isinstance(hooks, dict):
        for event in list(hooks):
            if isinstance(hooks[event], list):
                hooks[event] = [g for g in hooks[event] if not axis_group(g)]
                if not hooks[event]: del hooks[event]
        if not hooks: del data['hooks']
    return data


def check(old, new, host, install):
    """Refuse a text unless it holds exactly one current Axis group per event (none after uninstall) and nothing else changed."""
    try: data = json.loads(new) if new is not None and new.strip() else {}
    except ValueError: raise ValueError('the result is not valid JSON') from None
    hooks = data.get('hooks') if isinstance(data, dict) else None
    for event, group in entries(host).items():
        groups = hooks.get(event) if isinstance(hooks, dict) else None
        mine = [g for g in groups if axis_group(g)] if isinstance(groups, list) else []
        if mine != ([group] if install else []):
            raise ValueError(f'the result does not hold exactly {"one current" if install else "no"} Axis {event} entry')
    if normal(json.loads(old) if old is not None and old.strip() else {}) != normal(data):
        raise ValueError('the result changes more than the Axis entries')


def read_settings(path):
    """The settings text, or None when the file is absent; ValueError for a link or a file that is not UTF-8 text."""
    if os.path.lexists(path.parent) and not plain_dir(path.parent): raise ValueError(f'{path.parent.name}/ is a link or not a folder')
    if not os.path.lexists(path): return None
    text = small(path, 1 << 20)
    if text is None: raise ValueError('it is a link, not a regular file, or not UTF-8 text')
    return text


def write_settings(path, text, mode):
    """Replace the file atomically with text (None removes it), never through a link."""
    if text is None:
        os.unlink(path); return
    if not os.path.lexists(path.parent): os.mkdir(path.parent)
    if not plain_dir(path.parent): raise ValueError(f'{path.parent.name}/ is a link or not a folder')
    temp = path.parent / f'.{path.name}.{os.getpid()}.axis-tmp'
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o600)
    try:
        data = text.encode('utf-8')
        while data: data = data[os.write(fd, data):]
        os.fsync(fd)
    finally: os.close(fd)
    try:
        os.chmod(temp, mode); os.replace(temp, path)
    except OSError:
        os.unlink(temp); raise


def install_main(action, argv):
    parser = argparse.ArgumentParser(prog=f'host-context.py {action}', description=f'{action} the Axis context hooks for one host')
    parser.add_argument('--host', required=True, choices=sorted(TARGET))
    parser.add_argument('--dry-run', action='store_true', help='print the exact change and write nothing')
    o = parser.parse_args(argv)
    install, rel = action == 'install', TARGET[o.host]
    path = ROOT / rel
    print(f'{"Install" if install else "Uninstall"} Axis context hooks for {TITLE[o.host]} in {rel}.')
    try:
        old, changes = read_settings(path), []
        try: new = plan(old, o.host, install, changes)
        except json.JSONDecodeError as error: raise ValueError(f'it is not valid JSON ({error.msg}, line {error.lineno})') from None
        check(old, new, o.host, install)
    except ValueError as error:
        print(f'REFUSED: {rel}: {error}. Nothing was changed.'); return 2
    if new == old:
        print('No change: ' + ('exactly one current Axis entry per event is already there.' if install else 'no Axis entry is there.')); return 0
    for change in changes: print(change)
    print('Every other setting and hook stays byte for byte.')
    if o.dry_run:
        print('Dry run: nothing was written.'); return 0
    written = False
    try:
        if read_settings(path) != old: raise ValueError('it changed while the change was prepared; run the command again')
        mode = stat.S_IMODE(os.lstat(path).st_mode) if old is not None else 0o644
        write_settings(path, new, mode)
        written = True
        back = read_settings(path)
        if back != new: raise ValueError('the file read back differs from the change')
        check(old, back, o.host, install)
    except (OSError, ValueError) as error:
        reason = str(error) if isinstance(error, ValueError) else 'the file could not be written'
        if not written:
            print(f'REFUSED: {rel}: {reason}. Nothing was changed.'); return 2
        try:
            write_settings(path, old, mode)
            print(f'REFUSED: {rel}: {reason}. The previous file was restored.')
        except (OSError, ValueError):
            print(f'REFUSED: {rel}: {reason}. Check the file by hand: the previous version could not be restored.')
        return 2
    print(f'Written and read back: {"exactly one Axis entry" if install else "no Axis entry"} for {" and ".join(entries(o.host))}; every other setting and hook unchanged.')
    return 0


def whoami(root, host=None, environ=None):
    """The Axis Session ID and (role name, title) bound to this host session, or (None, reason)."""
    environ = os.environ if environ is None else environ
    values = [v for v in (environ.get(var, '').strip() for key, var in HOST_SESSION.items() if host in (None, key)) if v]
    if len(values) != 1: return None, 'two host session variables; name --host' if values else 'no host session variable'
    session = bound(root, values[0])
    if session is None: return None, 'no binding for this host session'
    found = identity(root, session)
    if found is None: return None, 'the bound Session ID has no live Marker'
    return (session, found), None


def whoami_main(argv):
    parser = argparse.ArgumentParser(prog='host-context.py whoami', description='print the Axis Session ID bound to this host session')
    parser.add_argument('--host', choices=sorted(HOST_SESSION), help='which host session variable to read')
    o = parser.parse_args(argv)
    try: found, reason = whoami(ROOT, o.host)
    except Exception: found, reason = None, 'binding unreadable'
    if found is None:
        print(f'UNBOUND: {reason}. Your identity is not recovered: make no writes and follow _Axis/Resources/Continue-Session.md.')
        return 4
    session, (name, title) = found
    print(f'SESSION {session}; role {title} (_Axis/Roles/{name}.md); bound to this host session. Use it word for word: run turn.py --session {session}.')
    return 0


def bind_main(argv):
    parser = argparse.ArgumentParser(prog='host-context.py bind', description='map this host session to its Axis Session ID')
    parser.add_argument('--session', required=True)
    parser.add_argument('--host', choices=sorted(HOST_SESSION), help='which host session variable to read')
    o = parser.parse_args(argv)
    try: result = bind(ROOT, o.session, o.host)
    except Exception: result = {'status': 'refused', 'reason': 'binding not written'}
    print(json.dumps(result, sort_keys=True))
    return 0


def main(argv):
    if argv[:1] == ['bind']: return bind_main(argv[1:])
    if argv[:1] == ['whoami']: return whoami_main(argv[1:])
    if argv[:1] in (['install'], ['uninstall']): return install_main(argv[0], argv[1:])
    try:
        host = argv[argv.index('--host') + 1] if '--host' in argv[:-1] else 'unknown'
        out = hook(ROOT, host if HOST.fullmatch(host) else 'unknown', sys.stdin.buffer.read(1 << 20))
        if out:
            sys.stdout.buffer.write((out + '\n').encode('utf-8')); sys.stdout.flush()
    except BaseException:
        try: os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except (OSError, ValueError, AttributeError): pass
    return 0


if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
