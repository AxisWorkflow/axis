#!/usr/bin/env python3
"""Optional host hook: mark a context compaction, and give a resumed or compacted session its Axis identity back.

`^install context hooks` makes this the one hook command on each host: Claude Code SessionStart (startup|resume|compact)
and PreCompact; Codex SessionStart and PostCompact; Gemini CLI PreCompress; Copilot CLI and Cursor
preCompact; Devin PostCompaction; OpenCode `session.compacted` through a small plugin. It reads the host's hook JSON on
stdin (the event from `hook_event_name`, else from `--event`; the host session from `session_id`, `sessionId` or
`conversation_id`).
- A compaction event (PreCompact, PostCompact, SessionStart `compact`, or another host's compaction event) appends
  `{UTC identifier timestamp} {host} {12 hex of sha256(host session ID) or -}` to `_Temp/Context/compactions.log`.
  Cursor and Copilot CLI also run the project's Claude Code hooks; there the host's own entry stays silent while Axis's
  Claude Code PreCompact entry is in `.claude/settings.json` or `.claude/settings.local.json` and CLAUDE_PROJECT_DIR names
  this project, so each compaction is marked once. Hosts other than Claude Code and Codex get the mark only: none of
  them adds a compaction hook's output to the model's context.
- SessionStart `resume` or `compact` prints the Card (the bound Axis Session ID, its role, and the instruction to run
  turn.py and reload before answering), then that role's guidance from `_Axis/Roles/{Role}.md`, when both fit the
  host's cap: on Claude Code one string of at most 9,500 characters, on Codex the 10,000-token additionalContextLimit
  its entry sets. Over the cap it prints the Card only, never cut text.
- Without a binding it prints one role-neutral line. A Codex `compact` always gets that line, never role text, because
  a spawned agent's hook carries its parent's session ID; a Claude Code call from a spawned agent (agent_id) gets nothing.
- On a Codex compaction, with the entry installed by 3.18 or later (`--core`), the role-neutral line is followed by
  the compiled startup core `_Axis/Resources/Starting-Context.md`, verbatim, when the core is whole (ends with its end
  marker), current (no loader or source in the loader's table is newer) and the whole output fits the limit; otherwise
  the line alone. A resume never gets the core.
- Claude Code UserPromptSubmit prints one line naming `turn.py --session {bound ID}` whenever this host session is
  bound, also after a kill or takeover (turn.py then reports it); nothing otherwise, and nothing for a spawned agent.
  3.18 does not install this entry: in its live check, sessions with it followed fewer planted rules before compaction.
- `startup` prints nothing. Every call exits 0, blocks nothing, never prints Secrets or absolute paths, and, apart from
  the per-turn line, stays silent on a missing Marker, a kill tombstone, an unknown role or malformed input.

Subcommands:
  bind --session {Session ID} [--host claude|codex]
      Map this host session (CLAUDE_CODE_SESSION_ID or CODEX_THREAD_ID) to its Axis Session ID in
      `_Temp/Context/bindings/`; writes nothing unless exactly one such variable is set. Prints one JSON line; exit 0.
  whoami [--host claude|codex]
      Print the Axis Session ID and role bound to this host session when its Marker is live (exit 0); otherwise UNBOUND
      (exit 4). This binding is the verified native-session binding Continue-Session.md accepts.
  install|uninstall --host claude|codex|gemini|copilot|cursor|devin|opencode [--dry-run]
      Print the exact change to the host's file (TARGET below); without --dry-run, apply it (exactly one Axis entry per
      event, every other byte kept; for OpenCode, Axis's own plugin file, never another file of that name) and read it
      back. Exit 0 done or unchanged, 2 refused. `_Axis/Resources/Host-Channels.md` records each host's channels.
  audit [--host claude|codex|gemini|copilot|cursor|devin|opencode]
      Read only the known project hook paths. Report matching payload releases, not an inferred installing release;
      correlate the file hash with the installation Log to identify the release that wrote it. Never print settings.
Without hooks, the entry file's after-compaction rule and turn.py recover on every host. Standard library only."""
import argparse, datetime as dt, hashlib, json, os, re, stat, sys
from pathlib import Path

ROOT = Path(os.path.abspath(__file__)).parents[2]
SCRIPT = '_Axis/Resources/host-context.py'
SESSION = re.compile(r'\d{4}(\.\d{2}){5}\.\d{3}Z')
HOST = re.compile(r'[a-z][a-z0-9-]{0,31}')
HOST_SESSION = {'claude': 'CLAUDE_CODE_SESSION_ID', 'codex': 'CODEX_THREAD_ID'}
CLAUDE_CAP = 9500     # characters (UTF-16 units) in the one printed string; Claude Code's own cap is 10,000
CODEX_TOKENS = 10000  # the additionalContextLimit the Codex entry sets; printed text is counted at 3 bytes per token
COMPACTION = ('precompact', 'postcompact', 'precompress', 'postcompaction', 'session.compacted')
EVENT = re.compile(r'[A-Za-z][A-Za-z0-9._-]{0,63}')
SHARES_CLAUDE = ('cursor', 'copilot')  # hosts that also run the project's Claude Code PreCompact hooks
ROLE_ROW = re.compile(r'^```axis-role\n(.*?)^```$', re.M | re.S)
NOFOLLOW, NONBLOCK = getattr(os, 'O_NOFOLLOW', 0), getattr(os, 'O_NONBLOCK', 0)
NEUTRAL = 'if you serve this project under an Axis Session ID, run turn.py with it before answering; if you no longer know it, follow _Axis/Resources/Continue-Session.md; a delegated helper follows its envelope instead.'
TURN = 'Axis: run `python3 _Axis/Resources/turn.py --session {}` first.'
CORE, LOADER, CORE_END = '_Axis/Resources/Starting-Context.md', '_Axis/Resources/Load-Starting-Context.md', '<!-- axis:starting-context:end -->'


def card(session, title, name, compacted):
    lead = 'Axis: context was compacted. Your' if compacted else 'Axis: your'
    return (f'{lead} Axis Session ID is {session} and your role is {title} (_Axis/Roles/{name}.md); run turn.py and reload '
            f'before answering: python3 _Axis/Resources/turn.py --session {session}, then re-read in full every file it lists.')


def neutral(compacted):
    return ('Axis: context was compacted; ' if compacted else 'Axis: ') + NEUTRAL


def fits(host, text):
    if host == 'claude': return len(text.encode('utf-16-le')) // 2 <= CLAUDE_CAP
    return (len(text.encode('utf-8')) + 2) // 3 <= CODEX_TOKENS


def core(root):
    """The compiled startup core as written, when it ends with its end marker and neither its loader nor a source in the
    loader's table is newer (Load-Starting-Context.md's own freshness test); '' otherwise."""
    text, loader = small(root / CORE), small(root / LOADER)
    if not text or not loader or text.rstrip('\n').rsplit('\n', 1)[-1] != CORE_END: return ''
    sources = re.findall(r'^\| `([^`]+)` \|', loader, re.M)
    try:
        made = os.lstat(root / CORE).st_mtime
        if not sources or any(os.lstat(root / rel).st_mtime > made for rel in [LOADER] + sources): return ''
    except OSError: return ''
    return text[:-1] if text.endswith('\n') else text


def with_core(root, line):
    """Codex: the role-neutral line, then the startup core when the whole fits the entry's limit; the line alone otherwise."""
    text = core(root)
    full = f'{line}\n{text}'
    return full if text and fits('codex', full + '\n') else line


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


def claude_marks(root):
    """True when this host also runs Axis's Claude Code PreCompact entry: a project Claude settings file holds it and
    CLAUDE_PROJECT_DIR, which its command needs, names this project."""
    folder = os.environ.get('CLAUDE_PROJECT_DIR', '')
    try:
        if not folder or os.path.realpath(folder) != os.path.realpath(root): return False
        for rel in ('.claude/settings.json', '.claude/settings.local.json'):
            data = json.loads(read_settings(root / rel, root) or '{}')
            hooks = data.get('hooks') if isinstance(data, dict) else None
            groups = hooks.get('PreCompact') if isinstance(hooks, dict) else None
            if isinstance(groups, list) and any(axis_group(g) is not False for g in groups): return True
    except (OSError, ValueError): return False
    return False


def hook(root, host, raw, fallback=None, with_startup=False):
    """What to print for one hook call ('' for nothing); a compaction event also appends its mark. with_startup: the Codex
    entry was installed with --core (3.18 or later), so a compaction also gets the startup core."""
    try: event = json.loads(raw)
    except ValueError: return ''
    name = event.get('hook_event_name', fallback) if isinstance(event, dict) else None
    if not isinstance(name, str) or not (plain_dir(root / '_Axis') and plain_dir(root / '_Axis/Agents')): return ''
    source = event.get('source') if name == 'SessionStart' else None
    compacted = name.lower() in COMPACTION or source == 'compact'
    host_session = next((v for v in map(event.get, ('session_id', 'sessionId', 'conversation_id')) if isinstance(v, str) and v.strip()), None)
    spawned = host == 'claude' and bool(event.get('agent_id'))
    if name == 'UserPromptSubmit':  # Claude Code: the per-turn step before each prompt of a bound session
        session = bound(root, host_session) if host == 'claude' and host_session and not spawned else None
        return TURN.format(session) if session else ''  # also when killed or replaced: turn.py then says so
    if compacted and host in SHARES_CLAUDE and claude_marks(root): return ''  # Axis's Claude Code entry marks it there
    if compacted and not spawned:  # a spawned agent's compaction is not its parent's
        try: mark(root, host, host_session)
        except OSError: pass
    if source not in ('resume', 'compact') or host not in HOST_SESSION: return ''
    if spawned: return ''
    if host == 'codex' and compacted: return with_core(root, neutral(True)) if with_startup else neutral(True)
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
TARGET = {'claude': '.claude/settings.json', 'codex': '.codex/hooks.json', 'gemini': '.gemini/settings.json',
          'copilot': '.github/hooks/axis.json', 'cursor': '.cursor/hooks.json', 'devin': '.devin/config.json',
          'opencode': '.opencode/plugins/axis-context.js'}
TITLE = {'claude': 'Claude Code', 'codex': 'Codex', 'gemini': 'Gemini CLI', 'copilot': 'Copilot CLI', 'cursor': 'Cursor',
         'devin': 'Devin', 'opencode': 'OpenCode'}
FLAT = ('copilot', 'cursor')  # each event lists handlers, not groups; a new file starts with "version": 1
# '|| true': a missing or broken script must never block the host; Claude Code reads exit 2 on PreCompact as "block".
CLAUDE_COMMAND = 'python3 "$CLAUDE_PROJECT_DIR/_Axis/Resources/host-context.py" --host claude || true'
CODEX_COMMAND = 'python3 _Axis/Resources/host-context.py --host codex --core || true'  # --core: an install from 3.17 (4,000 tokens) never gets the core
COMMAND = {'gemini': 'python3 "$GEMINI_PROJECT_DIR/_Axis/Resources/host-context.py" --host gemini || true',
           'copilot': 'python3 _Axis/Resources/host-context.py --host copilot --event preCompact || true',
           'cursor': 'python3 "$CURSOR_PROJECT_DIR/_Axis/Resources/host-context.py" --host cursor || true',
           'devin': 'python3 "$DEVIN_PROJECT_DIR/_Axis/Resources/host-context.py" --host devin || true'}
NOTE = {h: f'{TITLE[h]} also runs the project\'s Claude Code hooks: while Axis\'s Claude Code PreCompact entry is in .claude/settings.json '
           'and CLAUDE_PROJECT_DIR names this project, this entry stays silent, so each compaction is marked once.' for h in SHARES_CLAUDE}


def codex_note(root):
    """The Codex preview's statement of its SessionStart limit and what the startup core costs per request."""
    head = f'Codex SessionStart additionalContextLimit: {CODEX_TOKENS:,} tokens. '
    text = with_core(root, neutral(True))
    if text == neutral(True): return head + f'{CORE} is missing, stale or over that limit here, so a compaction gets the role-neutral line alone.'
    tokens = (len((text + '\n').encode('utf-8')) + 2) // 3
    return head + (f'After each compaction the role-neutral line and {CORE} (about {tokens:,} tokens at 3 bytes per token) join the '
                   f'context, so every later model request carries about {tokens:,} more input tokens until the next compaction.')


OPENCODE_PLUGIN ='''// Axis context hook for OpenCode, written by `python3 _Axis/Resources/host-context.py install --host opencode`.
// After each compaction it runs that script, which appends one line to _Temp/Context/compactions.log. It prints
// nothing, blocks nothing and ignores every error. Remove it with the same command's `uninstall`.
import { spawnSync } from "node:child_process"
import { fileURLToPath } from "node:url"

const root = fileURLToPath(new URL("../../", import.meta.url))

export const AxisContext = async () => ({
  event: async ({ event }) => {
    if (event?.type !== "session.compacted") return
    try {
      const id = event.properties?.sessionID
      spawnSync("python3", ["_Axis/Resources/host-context.py", "--host", "opencode"], {
        cwd: root,
        input: JSON.stringify({ hook_event_name: "session.compacted", session_id: typeof id === "string" ? id : "" }),
        stdio: ["pipe", "ignore", "ignore"],
        timeout: 10000,
      })
    } catch {}
  },
})
'''
# Exact published payloads at exact published paths. A header or script-name match is not plugin ownership.
# 3.18 freeze a3e10a875e3635894efafbe83193429b92304d6b; 3.17 shipped no OpenCode plugin.
PLUGIN_RELEASES = {'.opencode/plugins/axis-context.js': {
    '9d1360b412b5bffe71526f7561cee5e5106e578138cf04ced87c38138a73b955': ('3.18',),
}}
ENTRY_RELEASES = {'claude': {'PreCompact': {'f27dad92cd99b07a4c075ecdc41f606ba66c6f1b994ee824c47fde45b634ccaf': ['3.17',
                                                                                                '3.18']},
            'SessionStart': {'73e74935356413dac94d0bd06574cd4a180c1435b6d9fe6a545277db8f9cc4a0': ['3.17',
                                                                                                  '3.18']}},
 'codex': {'PostCompact': {'72b8f84800b4693b785eb3e1137de6014c2dd0a70c60f451e8d492e6d6fd7abd': ['3.17'],
                           '9964ced3c6b75153d1a241a40fea7dff6bb0009c62eaa39de5142d60d69f1f55': ['3.18']},
           'SessionStart': {'1e7dda4002e2aeb5c7122009baab7a56a4407d58c51520786cda90fa7c230910': ['3.18'],
                            '879186a038324aac003e521f9bd5c0d51db74434b0cd5ca22f35b8425b59638e': ['3.17']}},
 'copilot': {'preCompact': {'50e1651548fcaa207d5df07128a4f6eda79ac32ee98372326c85e9fd64d93427': ['3.18']}},
 'cursor': {'preCompact': {'d89e601fa30d51d5656163129a637f4d9d619db53ba425bf86cfb65dbe986708': ['3.18']}},
 'devin': {'PostCompaction': {'df80e480182e0b0c9fb30a20f5c3d83d6144e767c8d320f9f83dd96093a6e9f6': ['3.18']}},
 'gemini': {'PreCompress': {'b3e2690693e1313122d0753b000829b51a1a099f973d6a2ff8b83e44cdf5a4a7': ['3.18']}}}
DECODER = json.JSONDecoder()


def entries(host):
    if host == 'claude':
        handler = {'type': 'command', 'command': CLAUDE_COMMAND, 'timeout': 10}
        # No UserPromptSubmit entry: with it, Claude Code sessions missed L4 (pre-compaction compliance) in the 3.18 live check.
        return {'SessionStart': {'matcher': 'startup|resume|compact', 'hooks': [handler]}, 'PreCompact': {'hooks': [handler]}}
    if host == 'gemini': return {'PreCompress': {'hooks': [{'name': 'axis-context', 'type': 'command', 'command': COMMAND[host], 'timeout': 10000}]}}
    if host == 'copilot': return {'preCompact': {'type': 'command', 'bash': COMMAND[host], 'cwd': '.', 'timeoutSec': 10}}
    if host == 'cursor': return {'preCompact': {'type': 'command', 'command': COMMAND[host], 'timeout': 10}}
    if host == 'devin': return {'PostCompaction': {'matcher': '', 'hooks': [{'type': 'command', 'command': COMMAND[host], 'timeout': 10}]}}
    handler = {'type': 'command', 'command': CODEX_COMMAND}
    return {'SessionStart': {'matcher': 'startup|resume|compact', 'hooks': [dict(handler, additionalContextLimit=CODEX_TOKENS)]},
            'PostCompact': {'hooks': [handler]}}


def axis_group(group, flat=False):
    """True when every handler in this hook group (on a flat host, this one handler) runs this script, None when only
    some do, False otherwise."""
    handlers = [group] if flat else (group.get('hooks') if isinstance(group, dict) else None)
    keys = ('command', 'bash', 'powershell') if flat else ('command',)
    ours = [isinstance(h, dict) and any(isinstance(h.get(k), str) and SCRIPT in h[k] for k in keys) for h in handlers] if isinstance(handlers, list) else []
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
        return json.dumps(dict(fresh(host), hooks={e: [g] for e, g in want.items()}), indent=2) + '\n' if install else text
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
        kinds = [axis_group(g, host in FLAT) for g in groups]
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


def fresh(host):
    """What a new file holds besides Axis's entries."""
    return {'version': 1} if host in FLAT else {}


def normal(data, flat=False):
    """The settings without Axis's hook groups and the empty lists and "hooks" object they leave."""
    data = json.loads(json.dumps(data))
    hooks = data.get('hooks') if isinstance(data, dict) else None
    if isinstance(hooks, dict):
        for event in list(hooks):
            if isinstance(hooks[event], list):
                hooks[event] = [g for g in hooks[event] if not axis_group(g, flat)]
                if not hooks[event]: del hooks[event]
        if not hooks: del data['hooks']
    return data


def check(old, new, host, install):
    """Refuse a text unless it holds exactly one current Axis group per event (none after uninstall) and nothing else changed."""
    try: data = json.loads(new) if new is not None and new.strip() else {}
    except ValueError: raise ValueError('the result is not valid JSON') from None
    hooks, flat = data.get('hooks') if isinstance(data, dict) else None, host in FLAT
    for event, group in entries(host).items():
        groups = hooks.get(event) if isinstance(hooks, dict) else None
        mine = [g for g in groups if axis_group(g, flat)] if isinstance(groups, list) else []
        if mine != ([group] if install else []):
            raise ValueError(f'the result does not hold exactly {"one current" if install else "no"} Axis {event} entry')
    if normal(json.loads(old) if old is not None and old.strip() else fresh(host), flat) != normal(data, flat):
        raise ValueError('the result changes more than the Axis entries')


def folders(path, root):
    """Each folder from the project root down to the file's own, outermost first, with its project-relative name."""
    parts = path.parent.relative_to(root).parts
    return [(root.joinpath(*parts[:i]), '/'.join(parts[:i])) for i in range(1, len(parts) + 1)]


def read_settings(path, root=None):
    """The settings text, or None when the file is absent; ValueError for a link or a file that is not UTF-8 text."""
    for folder, name in folders(path, ROOT if root is None else root):
        if os.path.lexists(folder) and not plain_dir(folder): raise ValueError(f'{name}/ is a link or not a folder')
    if not os.path.lexists(path): return None
    text = small(path, 1 << 20)
    if text is None: raise ValueError('it is a link, not a regular file, or not UTF-8 text')
    return text


def write_settings(path, text, mode):
    """Replace the file atomically with text (None removes it), never through a link."""
    if text is None:
        os.unlink(path); return
    for folder, name in folders(path, ROOT):
        if not os.path.lexists(folder): os.mkdir(folder)
        if not plain_dir(folder): raise ValueError(f'{name}/ is a link or not a folder')
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


def text_hash(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest() if text is not None else None


def plugin_releases(text, rel):
    return PLUGIN_RELEASES.get(rel, {}).get(text_hash(text), ())


def plugin_plan(old, install, changes, rel):
    """OpenCode: accept current or exact known shipped bytes at the canonical path; preserve everything else."""
    if rel != TARGET['opencode']: raise ValueError('the path is not an approved Axis plugin path')
    if not plugin_releases(old, rel):
        if old is not None and old != OPENCODE_PLUGIN: raise ValueError('a different file of that name is there; Axis neither replaces nor removes it')
    if install and old is None: changes.append(f'create {rel} ({len(OPENCODE_PLUGIN.encode())} bytes):\n' + OPENCODE_PLUGIN.rstrip('\n'))
    if install and old is not None and old != OPENCODE_PLUGIN:
        changes.append(f'replace {rel}, matching release {", ".join(plugin_releases(old, rel))}, with ({len(OPENCODE_PLUGIN.encode())} bytes):\n' + OPENCODE_PLUGIN.rstrip('\n'))
    if not install and old is not None: changes.append(f'remove {rel}, which holds exactly a known Axis plugin')
    return OPENCODE_PLUGIN if install else None


def retain_plugin(root, old):
    """Keep and verify the known plugin preimage outside the host's loader; never overwrite a retained copy."""
    if old is None: return None
    folder = context_dir(root, 'hook-rollback', create=True)
    if folder is None: raise ValueError('the plugin rollback folder is not a plain directory')
    path = folder / (text_hash(old) + '.plugin')
    if not os.path.lexists(path):
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o600)
        try:
            data = old.encode('utf-8')
            while data: data = data[os.write(fd, data):]
            os.fsync(fd)
        finally: os.close(fd)
    if small(path) != old: raise ValueError('the retained plugin rollback copy does not match; the host file is unchanged')
    return path.relative_to(root).as_posix()


def retain_plugin_operation(root, rel, old, new, mode):
    """Persist recovery identity before mutation, including absence and the original permissions."""
    backup = retain_plugin(root, old)
    folder = context_dir(root, 'hook-rollback', create=True)
    if folder is None: raise ValueError('the plugin rollback folder is not a plain directory')
    record = {'schema': 1, 'host': 'opencode', 'path': rel,
              'before': {'sha256': text_hash(old), 'mode': mode, 'backup': backup} if old is not None else None,
              'after': {'sha256': text_hash(new), 'mode': mode} if new is not None else None}
    text = json.dumps(record, sort_keys=True, separators=(',', ':')) + '\n'
    path = folder / ('operation-' + os.urandom(16).hex() + '.json')
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | NOFOLLOW, 0o600)
    try:
        data = text.encode('utf-8')
        while data: data = data[os.write(fd, data):]
        os.fsync(fd)
    finally: os.close(fd)
    if small(path) != text: raise ValueError('the retained plugin operation does not match; the host file is unchanged')
    fd = os.open(folder, os.O_RDONLY | NOFOLLOW)
    try: os.fsync(fd)
    finally: os.close(fd)
    return path.relative_to(root).as_posix()


def installer_release(root):
    matches = re.findall(r'^current-version: ([0-9]+\.[0-9]+)$', small(root / '_Axis/CHANGELOG.md', 1 << 20) or '', re.M)
    return matches[0] if len(matches) == 1 else 'unknown'


def audit_main(argv):
    parser = argparse.ArgumentParser(prog='host-context.py audit', description='read-only inventory of known project context-hook paths')
    parser.add_argument('--host', choices=sorted(TARGET))
    o = parser.parse_args(argv)
    def unique_object(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj: raise ValueError('duplicate setting key')
            obj[key] = value
        return obj
    for host in ([o.host] if o.host else sorted(TARGET)):
        rel = TARGET[host]
        row = {'host': host, 'path': rel, 'installer_release': 'unknown; correlate an installation Log by this file hash'}
        try:
            old = read_settings(ROOT / rel)
            row['sha256'] = text_hash(old)
            if old is None: row['state'] = 'absent'
            elif host == 'opencode':
                row['payload_releases'] = list(plugin_releases(old, rel))
                row['state'] = 'current payload' if old == OPENCODE_PLUGIN else 'known earlier payload' if row['payload_releases'] else 'unknown or modified; preserved'
            else:
                data = json.loads(old, object_pairs_hook=unique_object)
                if not isinstance(data, dict): raise ValueError('settings is not an object')
                hooks = data.get('hooks')
                if hooks is not None and not isinstance(hooks, dict): raise ValueError('hooks is not an object')
                row['entries'] = []
                for event, groups in (hooks or {}).items():
                    if not isinstance(groups, list): raise ValueError('a hook event is not a list')
                    for group in groups:
                        kind = axis_group(group, host in FLAT)
                        if kind is False: continue
                        current = entries(host).get(event)
                        signature = hashlib.sha256(json.dumps(group, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
                        releases = ENTRY_RELEASES.get(host, {}).get(event, {}).get(signature, [])
                        # Never echo a user-controlled event name, handler, command or setting.
                        row['entries'].append({'event': event if event in COMPACTION or event in entries(host) or event == 'UserPromptSubmit' else 'other',
                                               'state': 'current entry' if group == current else 'known earlier entry' if releases else 'unrecognized reference; review by hand',
                                               'payload_releases': releases})
                row['state'] = 'entries found' if row['entries'] else 'no Axis references found'
        except (OSError, ValueError):
            row['state'] = 'unreadable or malformed; preserved'
        print(json.dumps(row, sort_keys=True))
    return 0


def install_main(action, argv):
    parser = argparse.ArgumentParser(prog=f'host-context.py {action}', description=f'{action} the Axis context hooks for one host')
    parser.add_argument('--host', required=True, choices=sorted(TARGET))
    parser.add_argument('--dry-run', action='store_true', help='print the exact change and write nothing')
    o = parser.parse_args(argv)
    install, rel, plugin = action == 'install', TARGET[o.host], o.host == 'opencode'
    path = ROOT / rel
    print(f'{"Install" if install else "Uninstall"} Axis context hooks for {TITLE[o.host]} in {rel}.')
    try:
        old, changes = read_settings(path), []
        if plugin: new = plugin_plan(old, install, changes, rel)
        else:
            try: new = plan(old, o.host, install, changes)
            except json.JSONDecodeError as error: raise ValueError(f'it is not valid JSON ({error.msg}, line {error.lineno})') from None
            check(old, new, o.host, install)
    except ValueError as error:
        print(f'REFUSED: {rel}: {error}. Nothing was changed.'); return 2
    if new == old:
        if plugin: print('No change: ' + ("Axis's plugin file is already there." if install else 'no Axis plugin file is there.')); return 0
        print('No change: ' + ('exactly one current Axis entry per event is already there.' if install else 'no Axis entry is there.')); return 0
    for change in changes: print(change)
    if install and o.host in NOTE: print(NOTE[o.host])
    if install and o.host == 'codex': print(codex_note(ROOT))
    print('No other host file changes.' if plugin else 'Every other setting and hook stays byte for byte.')
    if plugin:
        if old is None: print('Rollback: the prior plugin was absent; remove only the exact newly installed bytes.')
        else: print(f'Rollback copy: _Temp/Context/hook-rollback/{text_hash(old)}.plugin; retained and verified before changing the host file.')
    if o.dry_run:
        print('Dry run: nothing was written.'); return 0
    written = False
    try:
        if read_settings(path) != old: raise ValueError('it changed while the change was prepared; run the command again')
        mode = stat.S_IMODE(os.lstat(path).st_mode) if old is not None else 0o644
        if plugin:
            operation = retain_plugin_operation(ROOT, rel, old, new, mode)
            print(f'Recovery operation: {operation}; retained and verified before mutation.', flush=True)
        if read_settings(path) != old or (plugin and old is not None and stat.S_IMODE(os.lstat(path).st_mode) != mode):
            raise ValueError('it changed while rollback was prepared; run the command again')
        write_settings(path, new, mode)
        written = True
        back = read_settings(path)
        if back != new: raise ValueError('the file read back differs from the change')
        if not plugin: check(old, back, o.host, install)
    except (OSError, ValueError) as error:
        reason = str(error) if isinstance(error, ValueError) else 'the file could not be written'
        if not written:
            print(f'REFUSED: {rel}: {reason}. The host file is unchanged; any rollback copy is retained.'); return 2
        try:
            if read_settings(path) != new: raise ValueError('the file changed again; preserve it for manual recovery')
            write_settings(path, old, mode)
            if read_settings(path) != old or (old is not None and stat.S_IMODE(os.lstat(path).st_mode) != mode):
                raise ValueError('rollback readback differs')
            print(f'REFUSED: {rel}: {reason}. The previous file was restored and read back.')
        except (OSError, ValueError):
            print(f'REFUSED: {rel}: {reason}. Check the file by hand: the previous version could not be restored.')
        return 2
    if plugin:
        print('Written and read back: ' + ("Axis's plugin file is in place" if install else "Axis's plugin file is removed") + '; no other host file changed.')
        print(f'Installation Log: declared release {installer_release(ROOT)}; helper {text_hash(small(ROOT / SCRIPT, 1 << 20)) or "unknown"}; host {o.host}; path {rel}; before {text_hash(old) or "absent"}; after {text_hash(new) or "absent"}; prior mode {mode:o}.')
        return 0
    print(f'Written and read back: {"exactly one Axis entry" if install else "no Axis entry"} for {" and ".join(entries(o.host))}; every other setting and hook unchanged.')
    print(f'Installation Log: declared release {installer_release(ROOT)}; helper {text_hash(small(ROOT / SCRIPT, 1 << 20)) or "unknown"}; host {o.host}; path {rel}; before {text_hash(old) or "absent"}; after {text_hash(new) or "absent"}; prior mode {mode:o}.')
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
    if argv[:1] == ['audit']: return audit_main(argv[1:])
    if argv[:1] in (['install'], ['uninstall']): return install_main(argv[0], argv[1:])
    try:
        host = argv[argv.index('--host') + 1] if '--host' in argv[:-1] else 'unknown'
        event = argv[argv.index('--event') + 1] if '--event' in argv[:-1] else None
        out = hook(ROOT, host if HOST.fullmatch(host) else 'unknown', sys.stdin.buffer.read(1 << 20), event if event and EVENT.fullmatch(event) else None,
                   '--core' in argv)
        if out:
            sys.stdout.buffer.write((out + '\n').encode('utf-8')); sys.stdout.flush()
    except BaseException:
        try: os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        except (OSError, ValueError, AttributeError): pass
    return 0


if __name__ == '__main__': sys.exit(main(sys.argv[1:]))
