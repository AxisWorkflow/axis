#!/usr/bin/env python3
"""Stage and check a copied OpenClaw profile stanza with a schema-2 surface table (strict chat gate, H3 staging).

This script never activates anything. The operator stops the OpenClaw profile, copies the `axis-guardrails` plugin
stanza (the JSON object that holds `chatPolicy`) and the project's schema-2 surface table into ordinary files, and
copies what each will replace (the preimages; `absent` when there was none). `stage` checks that every strict chat
in the stanza matches its table row (binding and policy digests through `surfaces.py`) and that no host-bound row
lacks a chat, then writes all four copies and a manifest as a new numbered generation below a stage root. A
generation exists only once its folder is renamed into place after every file was written, synced and read back;
an interrupted run leaves an `.incomplete-` folder that is reported and never used. Earlier generations are kept
unchanged and are verified on every run. `check` reads a stage root back, writes nothing, and confirms the newest
generation: digests equal to the manifest, the chain of earlier generations intact, the parser unchanged and the
pairing recomputed equal; with --stanza or --table it also confirms those copies equal the staged ones, and with
--manifest-sha256 that the newest manifest is the one `stage` reported (both print manifest_sha256).

  profile-staging.py stage --stanza FILE --table FILE --stanza-preimage FILE|absent --table-preimage FILE|absent
                           --stage-root DIR
  profile-staging.py check --stage-root DIR [--stanza FILE] [--table FILE] [--manifest-sha256 HEX]

Isolation. On a host that has the operating system sandbox (macOS, /usr/bin/sandbox-exec), every run takes place
inside the operating system sandbox. Two sandboxed passes first find the real path of each live folder (the
OPENCLAW_* folders; then the homes, their state folders and .config/openclaw, with those real paths already denied);
the checker then re-executes itself under a generated profile that denies every file read, metadata read and write
under each live folder by its given spellings and its real path, under every .openclaw*, .clawdbot*, .moltbot* and
.config/openclaw* folder anywhere, of every openclaw.json*, clawdbot.json* and moltbot.json* file, and of .git,
.claude, .codex and .gemini folders; it allows writes only below the stage root (stage) and nowhere for check. The
path checks below still run inside it. If the host has the sandbox but it cannot be applied (for example when the
checker already runs inside another sandbox), the run refuses (sandbox_unavailable); a run told it is the sandboxed
child whose sandbox canary is readable refuses (sandbox_not_applied). Where no sandbox is available (Linux and other
hosts, and a Mac without an executable /usr/bin/sandbox-exec), the path checks below run alone, with the limits stated
under Limits. Every output names its isolation (sandbox or path-checks). The only programs the checker starts are
/usr/bin/sandbox-exec, itself and, under sandbox-exec, /usr/bin/true (to check that the generated profile applies
before the run).

Live paths are refused, by spelling and by identity, before they are touched. As text, before any filesystem call
and again after each folder symlink: a path with a component starting with `.openclaw`, `.clawdbot` or `.moltbot`
(the default and every named profile, and the legacy state folders; the installed build still falls back to
~/.clawdbot), a `.config/openclaw*` folder (the host's gateway.env), a `.git`, `.claude`, `.codex`, `.gemini` or
`_Axis` component, a file named `openclaw.json*`, `clawdbot.json*` or `moltbot.json*`, or a path at or below the
value of any `OPENCLAW*` environment variable (and the folder of one ending in _PATH, _FILE or _CONFIG or their
plurals), trimmed as the host trims it, `~` expanded with HOME, the value and each of its entries split on `:`,
`;` and `,` (the host's list form), all compared without case or Unicode normalization, without a leading
/System/Volumes/Data and with /private/tmp, /private/var and /private/etc equal to /tmp, /var and /etc. By
identity: first the device and inode of every .openclaw*, .clawdbot* and .moltbot* entry and of .config/openclaw
in HOME, USERPROFILE and OPENCLAW_HOME, of every OPENCLAW_* folder and of the target of each one that is a symlink
are read from a listing of its parent, so a live folder is never opened; then every path is walked folder by
folder, each folder's identity read the same way before it is entered, and refused on a match. A live folder that
does not exist yet is refused by its physical spelling (every folder symlink on the way resolved), so staging never
creates it under another name. A name that matches
an entry only without case or Unicode normalization is refused (path_invalid) unless it is a live folder, which is
refused as live_path. An OPENCLAW_* path value (a name ending in DIR, _PATH, _FILE, _HOME, _ROOT, _CONFIG, _LOG or
their plurals) that is relative, a value of any OPENCLAW_* name starting with ~user, ./ or ../, or a HOME that is
unset or relative, refuses the run (environment_unresolved): the host would place it from a working folder or
account this script cannot know. CLAWDBOT_* and MOLTBOT_* variables are ignored by the installed build and are not
read. An input must be a regular file with one link, opened without following a symlink. A folder on the way to an
input or the stage root whose listing holds a file named openclaw.json*, clawdbot.json* or moltbot.json* is refused
(live_name) before anything in it is opened or created. Every entry listed inside the stage root is checked by
identity and by spelling before it is touched, and the temporary and new generation folders by spelling before
either is created: a live folder named like a generation, an incomplete generation or a preimage folder is never
entered, and a live folder named as the next generation is never created, nor a live path below the temporary or
new generation folder (such as its preimage folder or a file name in it). A home (HOME, USERPROFILE or
OPENCLAW_HOME) that lies inside a live folder by its spelling, or by a folder symlink on its way, refuses the run
(live_path) before the home is listed. So does a home that is itself a symlink into one, or that is
equal to a live folder (an OPENCLAW_* folder other than OPENCLAW_HOME, in any spelling). A commit rename that the
system refuses
is reported as io_error, not generation_conflict. Nothing here starts, stops or asks a host, opens a host or account
configuration file, or grants authority.

Limits. The checker cannot know about a live profile it is never told about: a profile in a folder of another
name, named by no OPENCLAW_* variable in this shell and not linked from HOME, USERPROFILE or OPENCLAW_HOME, is not
recognized, so run it in the shell that runs the host. A folder swapped for a symlink
between the walk and the open is not detected; inputs are read again by bytes before commit. Where no sandbox is
available, when two live locations
nest under different spellings, or a home (HOME, USERPROFILE or OPENCLAW_HOME) lies inside an OPENCLAW_* folder
under a different spelling, recording the inner one may list the outer one's names and the names in each folder
below it on the way to the inner one (for a home, the home and its .config folder too), and read a folder symlink
there, but never opens a file, before the outer identity is known; the run then refuses. One variable is enough:
OPENCLAW_STATE_DIR spelled through a folder symlink with ~/.openclaw (or another HOME state folder)
linked to a folder inside it, or with HOME inside it. Inside the sandbox the homes and their links are resolved only
once the OPENCLAW_* folders' real paths are denied, so those forms refuse before anything inside the outer folder is
listed; the OPENCLAW_* folders themselves are resolved shortest spelling first, so an inner one spelled with fewer
folders than the outer one it lies in may still have the names on its way listed before the run refuses. Inside the
sandbox OPENCLAW_HOME, which is also a home, may still be listed, with its .config folder, and its state-folder links
read (names and links only); an OPENCLAW_* folder below a .git, .claude, .codex or .gemini folder makes the run refuse
(io_error), since the sandbox denies reading those folders. Inside the sandbox a live folder that lies inside an
OPENCLAW_* folder under any spelling (an inner OPENCLAW_* folder, or the target of a home's state-folder link) also
refuses the run (live_path); with the path checks alone such a folder spelled inside the outer one is accepted.
Each home's .config folder is listed (names only, never a file) to find a symlinked .config/openclaw and refuse its
target: looking the entry up by name would touch it. When a file-valued OPENCLAW_* variable (such as
OPENCLAW_CONFIG_PATH) is a symlink, the folder of the real file is recognized only by a configuration file name in
it (the rule above), never by its link: reading the link would touch the live folder of the value; inside the
sandbox that file is unreadable by its name, but its folder's names may be listed and a real file of another name
there is not recognized. A parser
(surfaces.py) update makes stage and check refuse parser_changed
on an existing stage root, so a parser update needs a new stage root. `check` alone confirms that the newest
generation is consistent, not where it came from; give it the copies or --manifest-sha256 to pin it.

These limits hold in both isolations unless they name one. Two link layouts are a known limit, in which names may be
listed but no file is opened. When a home's state-folder entry (.openclaw*, .clawdbot*, .moltbot* or
.config/openclaw*) is a symlink to a folder of another name: (1) inside the sandbox, an OPENCLAW_* folder that lies
inside that folder may have the names on its way listed by the first pass before the run refuses (live_path); with
the path checks alone nothing in that folder is listed and the OPENCLAW_* folder is accepted; (2) a home (HOME,
USERPROFILE or OPENCLAW_HOME) spelled inside that folder has the names in that folder, in each folder on the way and
in the home listed before the run refuses, in both isolations, and the metadata of those folders may also be read. Inside the sandbox, a
double quote in the spelling or real path of a live folder makes every run refuse (sandbox_unavailable), since the
profile cannot express it. The sandbox is path based: a hard link to a live file, placed outside every live folder,
is not denied by it; the one-link rule refuses such an input after reading its metadata, never its contents. The
sandbox profile holds the live folders as the two sandboxed passes found them: a state-folder link made after them is
refused by the path checks only. XDG_CONFIG_HOME is not read: an openclaw folder in it counts as live only when its
path is spelled .config/openclaw* (as in the default ~/.config) or an OPENCLAW_* variable names it; otherwise it is a
profile the checker is not told about.

Activation is an operator step outside this script, and it needs a qualified outer latch: a host mechanism that
keeps the profile's service closed across boot, reload, malformed configuration and plugin absence unless the guard
is loaded with exactly the staged stanza (H3). No installed OpenClaw build has one (the host capability record
denies H3 on every carrier), so no generation may be activated and in-place migration of a live profile is
unavailable. Once a latch is qualified, the operator, with the profile still stopped, runs `check`, applies the
staged stanza and table together through the host's validated writers, reads both back against the manifest
digests, confirms the plugin is ready, and on any mismatch restores the retained preimages byte for byte and keeps
new sessions stopped. The manifest cannot express an active state.

Exit status: 0 staged (stage) or a valid staged generation (check); 1 refused; 2 usage. Output is one JSON object,
except when the sandbox applies to the profile check but fails to apply to the final run: the run then ends with
sandbox-exec's own exit status and no output.
"""
from __future__ import annotations

import argparse
import errno
import hashlib
import importlib.util
import json
import os
import re
import secrets
import stat
import sys
import unicodedata

SCHEMA = 'axis.openclaw-profile-staging/v1'
ACTIVATION = {'by': 'operator', 'requires': 'qualified outer latch (H3)', 'latch_qualified': False}
ABSENT = 'absent'
MANIFEST = 'manifest.json'
FILES = ('stanza.json', 'SURFACES.md', 'preimage/stanza.json', 'preimage/SURFACES.md')
MANIFEST_KEYS = {'schema', 'generation', 'previous', 'state', 'active', 'activation', 'parser_sha256', 'files',
                 'pairs', 'pairs_sha256'}
MAX_MANIFEST = 524288
MAX_HOPS = 40
GENERATION = re.compile(r'g[0-9]{4}\Z')
INCOMPLETE = re.compile(r'\.incomplete-g[0-9]{4}-[0-9a-f]{16}\Z')
HEX64 = re.compile(r'[0-9a-f]{64}\Z')
PROTECTED = frozenset(('.git', '.claude', '.codex', '.gemini', '_axis'))
STATE_FOLDERS = ('.openclaw', '.clawdbot', '.moltbot')
LEGACY_FOLDERS = ('.clawdbot', '.moltbot')
LEGACY_NAMES = ('clawdbot.json', 'moltbot.json')
CONFIG_NAMES = ('openclaw.json',) + LEGACY_NAMES  # a folder listing one of these (folded prefix) is refused as live
PATH_KEYS = ('DIR', 'DIRS', '_PATH', '_PATHS', '_FILE', '_FILES', '_HOME', '_ROOT', '_ROOTS', '_CONFIG', '_LOG', '_LOGS')
FILE_KEYS = ('_PATH', '_PATHS', '_FILE', '_FILES', '_CONFIG')
UNPLACED = ('~', './', '../')  # a value of any OPENCLAW_* name that starts so (other than ~ and ~/) cannot be placed
LIST_SPLIT = re.compile('[:;,]')
PRIVATE = ('etc', 'tmp', 'var')  # /private/<name> is /<name> on macOS
JS_SPACE = ('\x09\x0a\x0b\x0c\x0d \xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a'
            '\u2028\u2029\u202f\u205f\u3000\ufeff')  # what JavaScript's String.prototype.trim removes
PARSER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'surfaces.py')
O_CLOEXEC = getattr(os, 'O_CLOEXEC', 0)
SANDBOX_EXEC = '/usr/bin/sandbox-exec'  # the macOS sandbox; on a host without it the path checks run alone
CANARY = '/usr/bin/sandbox-exec'  # denied inside the checker's own sandbox, readable anywhere else
SANDBOX_MARK = 'AXIS_PROFILE_STAGING_SANDBOX'  # set only for the checker's own sandboxed children
SANDBOX_LIVE = 'AXIS_PROFILE_STAGING_LIVE'  # the real paths found by the first child, for the second
_RUNNER = None  # the command that runs this checker in a child (None: this interpreter on this file)


class Refusal(Exception):
    def __init__(self, code, field='', reason='', detail=''):
        super().__init__(code)
        self.code, self.field, self.reason, self.detail = code, field, reason, detail

    def output(self):
        out = {'result': 'refused', 'code': self.code, 'field': self.field, 'active': False,
               'activation': dict(ACTIVATION)}
        if self.reason:
            out['reason'] = self.reason
        if self.detail:
            out['detail'] = self.detail
        return out


def _boundary(name, where=None):
    """A named staging or readback boundary. It does nothing; the interruption tests replace it."""
    return None


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'), sort_keys=True).encode('utf-8')


# Paths: textual rules first, then folder-by-folder resolution that never touches a refused path.

class Roots(list):
    """Live roots as text (compared folded), the homes whose state folders are recorded, and the recorded live
    folder identities: (st_dev of the parent folder, inode from its listing) -> refusal reason. While the roots are
    recorded, `walked` collects every folder identity a recording walk entered and `state` the identities recorded
    as live (all but OPENCLAW_HOME itself), so a recording that entered a live folder refuses the run."""

    def __init__(self):
        super().__init__()
        self.homes, self.ids, self.home_roots = [], {}, set()
        self.walked, self.state, self.recording = set(), set(), False
        self.spelled = {}  # folded physical spelling of a live folder that does not exist yet -> refusal reason
        self.live_keys = set()  # folded spellings some variable other than OPENCLAW_HOME gives (a home is never one)


def _unplaced(key, value):
    """True when the host would place `value` from a working folder or an account this script cannot know."""
    return bool(value) and (key.upper().endswith(PATH_KEYS) or value.startswith(UNPLACED) or value in ('.', '..'))


def _entries_of(key, raw, home):
    """The absolute entries of a list-valued OPENCLAW_* value (split on : ; , as the host splits lists); none when the
    value holds no separator. An entry the host could not place refuses the run."""
    if not LIST_SPLIT.search(raw):
        return []
    out = []
    for part in LIST_SPLIT.split(raw):
        part = part.strip(JS_SPACE)
        if part == '~' or part.startswith('~/'):
            part = home + part[1:]
        if part.startswith('/') and '\0' not in part:
            out.append(_normal(part))
        elif _unplaced(key, part):
            raise Refusal('environment_unresolved', key)
    return out


def _environment_roots():
    roots = _environment_text()
    _record(roots)
    return roots


def _environment_text():
    """The homes and live roots the environment names, as text; nothing on the filesystem is touched."""
    roots = Roots()
    home = os.environ.get('HOME', '').strip(JS_SPACE)
    if not home.startswith('/') or '\0' in home:
        raise Refusal('environment_unresolved', 'HOME')
    roots.homes.append(_normal(home))
    other = os.environ.get('USERPROFILE', '').strip(JS_SPACE)
    if other.startswith('/') and '\0' not in other:
        roots.homes.append(_normal(other))
    for key in sorted(os.environ):
        if not key.upper().startswith('OPENCLAW'):
            continue
        value = os.environ[key].strip(JS_SPACE)
        if value == '~' or value.startswith('~/'):
            if not home.startswith('/'):
                continue
            value = home + value[1:]
        for entry in _entries_of(key, os.environ[key], home):
            roots.append(entry)
            if key.upper().endswith(FILE_KEYS):
                roots.append(os.path.dirname(entry))
        if not value.startswith('/') or '\0' in value:
            if _unplaced(key, value):
                raise Refusal('environment_unresolved', key)
            continue
        root = _normal(value)
        roots.append(root)
        if key.upper().endswith(('_PATH', '_FILE', '_CONFIG')):
            roots.append(os.path.dirname(root))
        if key.upper().endswith(('_PATHS', '_FILES')):
            roots.append(os.path.dirname(root))
        if key.upper() == 'OPENCLAW_HOME':
            roots.homes.append(root)
            roots.home_roots.add(_key(root))
    return roots


def _normal(path):
    path = os.path.normpath(path)
    return '/' + path.lstrip('/') if path.startswith('//') else path


def _fold(text):
    """Without case or Unicode normalization, as APFS compares names."""
    return unicodedata.normalize('NFD', unicodedata.normalize('NFD', text).casefold())


def _key(path):
    """A path as compared with a live root: folded, and without a leading /System/Volumes/Data (the macOS firmlink
    that also presents the data volume under /)."""
    parts = _fold(path).split('/')
    if parts[:4] == ['', 'system', 'volumes', 'data']:
        parts = [''] + parts[4:]
    if len(parts) > 2 and parts[1] == 'private' and parts[2] in PRIVATE:
        parts = [''] + parts[2:]
    return '/'.join(parts) or '/'


def _live_reason(path, roots, protected=None):
    """The refusal reason for `path` as text, or None. Protected parts are skipped while live folders are recorded
    (listing a folder there reads names only; it never makes an input of it)."""
    if protected is None:
        protected = not getattr(roots, 'recording', False)
    parts = [unicodedata.normalize('NFD', part) for part in path.split('/') if part]
    before = ''
    for part in parts:
        folded = part.casefold()
        if folded.startswith('.openclaw'):
            return 'openclaw_folder'
        if folded.startswith(LEGACY_FOLDERS):
            return 'openclaw_folder'
        if before == '.config' and folded.startswith('openclaw'):
            return 'openclaw_folder'
        if folded in PROTECTED and protected:
            return 'protected_part'
        before = folded
    key = _key(path)
    for root in roots:
        base = _key(root)
        if base == '/' or key == base or key.startswith(base + '/'):
            return 'environment_root'
    for base, why in getattr(roots, 'spelled', {}).items():
        if key == base or key.startswith(base + '/'):
            return why
    if parts and parts[-1].casefold().startswith('openclaw.json'):
        return 'live_name'
    if parts and parts[-1].casefold().startswith(LEGACY_NAMES):
        return 'live_name'
    return None


def _textual(text, field, roots):
    if type(text) is not str or not text or '\0' in text:
        raise Refusal('path_invalid', field)
    path = _normal(os.path.abspath(text))
    reason = _live_reason(path, roots)
    if reason:
        raise Refusal('live_path', field, reason)
    return path


def _entry(folder, name, field, roots):
    """(identity, name, kind) of `name` in `folder` from a listing of `folder`, or None when it has no such entry.
    The identity is (st_dev of the folder, inode of the entry); the entry itself is touched, for its kind, only once
    that identity is known not to be a live folder. An exact name is preferred, else the one entry equal to it
    without case or normalization (APFS resolves such a name to it); two such entries refuse. Outside recording,
    such an inexact match refuses (path_invalid) once its identity is known not to be live: the path names an
    entry by another spelling, and on a case-sensitive volume it would be another folder."""
    dev = os.stat(folder).st_dev
    with os.scandir(folder) as listing:
        entries = list(listing)
    if not roots.recording and any(_fold(entry.name).startswith(CONFIG_NAMES) for entry in entries):
        raise Refusal('live_path', field, 'live_name')  # e.g. the folder of the real file behind a symlinked config path
    found = [entry for entry in entries if entry.name == name]
    exact = bool(found)
    if not found:
        want = _fold(name)
        found = [entry for entry in entries if _fold(entry.name) == want]
    if not found:
        return None
    if len(found) > 1:
        raise Refusal('path_invalid', field)
    entry = found[0]
    identity = (dev, entry.inode())
    if identity in roots.ids:
        raise Refusal('live_path', field, roots.ids[identity])
    if not exact and not roots.recording:
        raise Refusal('path_invalid', field)
    kind = 'link' if entry.is_symlink() else 'dir' if entry.is_dir(follow_symlinks=False) else 'other'
    return identity, entry.name, kind


def _resolve(path, field, roots, missing, seen=None):
    """Walk an already textual-checked absolute path from / with _entry, so every component is refused by identity
    before it is entered; folder symlinks are followed and the new path checked as text again. The last component is
    never followed; `seen['last']` receives its entry (None when absent). Returns the walked path."""
    parts = [part for part in path.split('/') if part]
    if not parts:
        raise Refusal('path_invalid', field)
    done, index, hops = '', 0, 0
    while True:
        entry = _entry(done or '/', parts[index], field, roots)
        if index == len(parts) - 1:
            break
        if entry is None:
            if seen is not None:
                seen['partial'] = done + '/' + '/'.join(parts[index:])
            raise Refusal(missing, field)
        current = done + '/' + entry[1]
        if entry[2] == 'link':
            hops += 1
            if hops > MAX_HOPS:
                raise Refusal('path_invalid', field)
            target = os.readlink(current)
            joined = target if target.startswith('/') else (done or '/') + '/' + target
            path = _normal(joined + '/' + '/'.join(parts[index + 1:]))
            reason = _live_reason(path, roots)
            if reason:
                raise Refusal('live_path', field, reason)
            parts, done, index = [part for part in path.split('/') if part], '', 0
            continue
        if entry[2] != 'dir':
            raise Refusal(missing, field)
        if roots.recording:
            roots.walked.add(entry[0])
        done, index = current, index + 1
    if seen is not None:
        seen['last'] = entry
    return done + '/' + (parts[-1] if entry is None else entry[1])


def _join(folder, target):
    return _normal(target if target.startswith('/') else folder + '/' + target)


def _folder(path, roots):
    """The walked path of folder `path`, followed when it is itself a symlink; None when missing, refused or not a
    folder."""
    for _ in range(MAX_HOPS):
        seen = {}
        try:
            path = _resolve(path, 'environment', roots, 'absent', seen)
        except Refusal as error:
            if error.code == 'live_path':  # a home inside a live folder: its state folders cannot be listed
                raise Refusal('live_path', 'environment', error.reason) from None
            return None
        last = seen.get('last')
        if last is None or last[2] not in ('dir', 'link'):
            return None
        if last[2] == 'dir':
            roots.walked.add(last[0])
            return path
        path = _join(os.path.dirname(path), os.readlink(path))
        reason = _live_reason(path, [root for root in roots if _key(root) in roots.live_keys], protected=False)
        if reason:  # a home that is a symlink into a live folder: its target is never walked
            raise Refusal('live_path', 'environment', reason)
    return None


def _identity(path, roots, reason, depth=0, state=True):
    """Record the identity of `path`, and of its target when it is a symlink, from a listing of its parent. A path
    inside a folder already refused by spelling or identity is covered and never listed. `state` is False only for
    OPENCLAW_HOME, a home that is listed for its state folders."""
    if depth > MAX_HOPS or _live_reason(os.path.dirname(path), roots):
        return
    seen = {}
    try:
        path = _resolve(path, 'environment', roots, 'absent', seen)
    except Refusal as error:
        if error.code == 'absent' and seen.get('partial'):
            roots.spelled.setdefault(_key(_normal(seen['partial'])), reason)  # its part from the first missing folder on
        return
    last = seen.get('last')
    if last is None:
        roots.spelled.setdefault(_key(path), reason)  # not there yet: refused by its physical spelling
        return
    roots.ids.setdefault(last[0], reason)
    if state:
        roots.state.add(last[0])
    if last[2] == 'link':
        _identity(_join(os.path.dirname(path), os.readlink(path)), roots, reason, depth + 1, state)


def _record(roots):
    """Fill roots.ids before any input is touched: the state-folder entries and .config/openclaw of each home, their
    symlink targets, then every OPENCLAW_* folder (shortest spelling first). A recording walk that entered a folder
    then recorded as live (two roots nested under different spellings) refuses the run."""
    roots.recording = True
    try:
        targets = []
        keys = [_key(root) for root in roots]
        roots.live_keys = {key for key in keys if keys.count(key) > (key in roots.home_roots)}
        for home in dict.fromkeys(roots.homes):
            others = [root for root in roots if _key(root) in roots.live_keys]
            inside = _live_reason(home, others, protected=False)
            if inside:  # its state-folder entries cannot be recorded without listing inside a live folder
                raise Refusal('live_path', 'environment', inside)
            folder = _folder(home, roots)
            if folder is None:
                continue
            dev = os.stat(folder).st_dev
            with os.scandir(folder) as listing:
                entries = list(listing)
            for entry in entries:
                if _fold(entry.name).startswith(STATE_FOLDERS):
                    roots.ids.setdefault((dev, entry.inode()), 'openclaw_folder')
                    roots.state.add((dev, entry.inode()))
                    if entry.is_symlink():
                        targets.append(_join(folder, os.readlink(folder + '/' + entry.name)))
            targets.append(folder + '/.config/openclaw')
        for target in targets:
            _identity(target, roots, 'openclaw_folder')
        for root in sorted(set(roots), key=_key):
            _identity(root, roots, 'environment_root', state=_key(root) in roots.live_keys)
    finally:
        roots.recording = False
    if roots.walked & roots.state:
        raise Refusal('live_path', 'environment', 'environment_root')


def _read_file(path, field, limit, missing='input_missing', oversize='input_size', other='not_regular_file'):
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        raise Refusal(missing, field) from None
    if stat.S_ISLNK(info.st_mode):
        raise Refusal('symlink', field)
    if not stat.S_ISREG(info.st_mode):
        raise Refusal(other, field)
    if info.st_nlink != 1:
        raise Refusal('hardlink', field)
    if info.st_size > limit:
        raise Refusal(oversize, field)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | O_CLOEXEC)
    try:
        now = os.fstat(fd)
        if (now.st_dev, now.st_ino) != (info.st_dev, info.st_ino) or not stat.S_ISREG(now.st_mode) or now.st_nlink != 1:
            raise Refusal('input_changed', field)
        chunks, size = [], 0
        while size <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - size))
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
    finally:
        os.close(fd)
    data = b''.join(chunks)
    if len(data) > limit:
        raise Refusal(oversize, field)
    return data


def _input(path, field, limit, roots):
    seen = {}
    walked = _resolve(path, field, roots, 'input_missing', seen)
    if seen.get('last') is None:
        raise Refusal('input_missing', field)  # a name its folder does not list is never looked up
    return _read_file(walked, field, limit)


# The parser: surfaces.py beside this folder, executed from the same bytes that are hashed.

def _load_parser():
    data = _read_file(PARSER, 'parser', 1048576, missing='parser_missing', oversize='parser_missing',
                      other='parser_missing')
    name = 'axis_profile_staging_surfaces'
    spec = importlib.util.spec_from_loader(name, loader=None)
    module = importlib.util.module_from_spec(spec)
    module.__file__ = PARSER
    sys.modules[name] = module
    exec(compile(data, PARSER, 'exec'), module.__dict__)
    return module, _sha(data)


def _pair(surfaces, stanza, table):
    """[surface, binding, policy digest] for every strict chat; every host-bound row must have its chat."""
    try:
        policy = surfaces.parse_plugin_config(stanza)
        if policy is None:
            raise Refusal('strict_stanza_required', 'stanza')
        try:
            text = table.decode('utf-8')
        except UnicodeDecodeError:
            raise Refusal('table_encoding', 'table') from None
        parsed = surfaces.parse_surface_table(text)
        if parsed.schema != 2:
            raise Refusal('strict_table_required', 'table')
        if len({agent.project_id for agent in policy.agents}) != 1:
            raise Refusal('stanza_project_count', 'stanza')
        pairs = []
        for agent in policy.agents:
            for chat in agent.chats:
                row = surfaces.check_declaration(chat, parsed)
                pairs.append([chat.surface, chat.binding, surfaces.policy_digest(row)])
        paired = {pair[0] for pair in pairs}
        for row in parsed.rows:
            if row.host_binding not in (None, 'manual') and row.surface not in paired:
                raise Refusal('orphan_binding_row', 'table')
    except surfaces.SurfaceError as error:
        raise Refusal(error.code, error.field or 'stanza') from None
    return sorted(pairs)


# Stage root and generations.

def _listed(folder, roots, field):
    """The names in `folder` (inside the stage root), each refused by its identity from the listing and by its
    spelling before anything touches it: a live folder there is never stat'ed, listed, read or entered."""
    dev = os.stat(folder).st_dev
    with os.scandir(folder) as listing:
        entries = list(listing)
    for entry in entries:
        why = roots.ids.get((dev, entry.inode())) or _live_reason(folder + '/' + entry.name, roots)
        if why:
            raise Refusal('live_path', field, why)
    return {entry.name for entry in entries}


def _load_manifest(raw, name):
    def pairs_hook(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError('duplicate key')
            out[key] = value
        return out
    try:
        manifest = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs_hook)
    except (UnicodeDecodeError, ValueError):
        raise Refusal('manifest_invalid', name) from None
    ok = (type(manifest) is dict and set(manifest) == MANIFEST_KEYS and manifest['schema'] == SCHEMA
          and manifest['generation'] == name and manifest['state'] == 'staged'
          and manifest['active'] is False
          and manifest['activation'] == ACTIVATION and type(manifest['activation']['latch_qualified']) is bool
          and type(manifest['parser_sha256']) is str and HEX64.match(manifest['parser_sha256'])
          and type(manifest['pairs_sha256']) is str and HEX64.match(manifest['pairs_sha256'])
          and type(manifest['files']) is dict and set(manifest['files']) == set(FILES))
    if ok:
        previous = manifest['previous']
        ok = previous is None or (type(previous) is dict and set(previous) == {'generation', 'manifest_sha256'}
                                  and type(previous['generation']) is str and GENERATION.match(previous['generation'])
                                  and type(previous['manifest_sha256']) is str and HEX64.match(previous['manifest_sha256']))
    if ok:
        for rel in FILES:
            meta = manifest['files'][rel]
            if meta is None and rel.startswith('preimage/'):
                continue
            ok = ok and (type(meta) is dict and set(meta) == {'sha256', 'bytes'} and type(meta['sha256']) is str
                         and HEX64.match(meta['sha256']) and type(meta['bytes']) is int and meta['bytes'] >= 0)
    if ok:
        ok = type(manifest['pairs']) is list and all(
            type(pair) is list and len(pair) == 3 and all(type(item) is str for item in pair) for pair in manifest['pairs'])
    if not ok:
        raise Refusal('manifest_invalid', name)
    return manifest


def _limit(surfaces, rel):
    return surfaces.TABLE_BYTES if rel.endswith('SURFACES.md') else surfaces.CONFIG_BYTES


def _verify_generation(root, name, previous, parser_sha, newest, surfaces, roots):
    folder = root + '/' + name
    info = os.lstat(folder)
    if stat.S_ISLNK(info.st_mode):
        raise Refusal('symlink', name)
    if not stat.S_ISDIR(info.st_mode):
        raise Refusal('generation_unexpected_entry', name)
    entries = _listed(folder, roots, name)
    if MANIFEST not in entries:
        raise Refusal('manifest_missing', name)
    raw = _read_file(folder + '/' + MANIFEST, name, MAX_MANIFEST, missing='manifest_missing',
                     oversize='manifest_invalid', other='generation_unexpected_entry')
    manifest = _load_manifest(raw, name)
    if entries != {MANIFEST, 'stanza.json', 'SURFACES.md', 'preimage'}:
        raise Refusal('generation_unexpected_entry', name)
    pre_info = os.lstat(folder + '/preimage')
    if stat.S_ISLNK(pre_info.st_mode):
        raise Refusal('symlink', name)
    if not stat.S_ISDIR(pre_info.st_mode):
        raise Refusal('generation_unexpected_entry', name)
    present = {rel.split('/', 1)[1] for rel in FILES if rel.startswith('preimage/') and manifest['files'][rel] is not None}
    if _listed(folder + '/preimage', roots, name) != present:
        raise Refusal('generation_unexpected_entry', name)
    staged = {}
    for rel in FILES:
        meta = manifest['files'][rel]
        if meta is None:
            continue
        data = _read_file(folder + '/' + rel, name, _limit(surfaces, rel), missing='generation_unexpected_entry',
                          oversize='digest_mismatch', other='generation_unexpected_entry')
        if _sha(data) != meta['sha256'] or len(data) != meta['bytes']:
            raise Refusal('digest_mismatch', name)
        staged[rel] = data
    expected_previous = None if previous is None else {'generation': previous[0], 'manifest_sha256': previous[1]}
    if manifest['previous'] != expected_previous:
        raise Refusal('chain_mismatch', name)
    if newest:
        if manifest['parser_sha256'] != parser_sha:
            raise Refusal('parser_changed', name)
        pairs = _pair(surfaces, staged['stanza.json'], staged['SURFACES.md'])
        if pairs != manifest['pairs'] or _sha(_compact(pairs)) != manifest['pairs_sha256']:
            raise Refusal('pairs_mismatch', name)
    _boundary('readback:' + name, folder)
    return _sha(raw), manifest


def _verify_root(root, parser_sha, surfaces, roots):
    """Return (generations, incomplete, newest manifest or None); refuses on any unexpected or changed entry, and on a
    live folder before it is touched."""
    names = _listed(root, roots, 'stage-root')
    generations = sorted(name for name in names if GENERATION.match(name))
    incomplete = sorted(name for name in names if INCOMPLETE.match(name))
    if names - set(generations) - set(incomplete):
        raise Refusal('stage_unexpected_entry', 'stage-root')
    for name in incomplete:
        if not stat.S_ISDIR(os.lstat(root + '/' + name).st_mode):
            raise Refusal('stage_unexpected_entry', 'stage-root')
    previous, manifest = None, None
    for index, name in enumerate(generations):
        newest = index == len(generations) - 1
        try:
            digest, manifest = _verify_generation(root, name, previous, parser_sha, newest, surfaces, roots)
        except Refusal as error:
            if newest or error.code == 'live_path':
                raise
            raise Refusal('retained_generation_changed', name, detail=error.code) from None
        previous = (name, digest)
    return generations, incomplete, manifest, previous


def _root_state(path):
    """'missing', or 'folder'; anything else at the stage root path refuses."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return 'missing'
    if stat.S_ISLNK(info.st_mode):
        raise Refusal('symlink', 'stage-root')
    if not stat.S_ISDIR(info.st_mode):
        raise Refusal('stage_root_invalid', 'stage-root')
    return 'folder'


def _write_all(fd, data):
    view = memoryview(data)
    while view:
        view = view[os.write(fd, view):]


def _write_new(path, data, rel):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | O_CLOEXEC, 0o600)
    try:
        half = len(data) // 2
        _write_all(fd, data[:half])
        _boundary('partial:' + rel, path)
        _write_all(fd, data[half:])
        os.fsync(fd)
    finally:
        os.close(fd)
    _boundary('wrote:' + rel, path)


def _sync_folder(path):
    fd = os.open(path, os.O_RDONLY | O_CLOEXEC)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _summary(result, root, generations, incomplete, manifest, digest=None):
    return {'result': result, 'stage_root': root, 'generation': generations[-1] if generations else None,
            'manifest_sha256': digest,
            'generations': generations, 'incomplete': incomplete, 'active': False, 'activation': dict(ACTIVATION),
            'files': manifest['files'] if manifest else None,
            'pairs_sha256': manifest['pairs_sha256'] if manifest else None,
            'parser_sha256': manifest['parser_sha256'] if manifest else None}


def stage(args):
    roots = _environment_roots()
    named = [('stanza', args.stanza), ('table', args.table), ('stanza-preimage', args.stanza_preimage),
             ('table-preimage', args.table_preimage), ('stage-root', args.stage_root)]
    paths = {field: None if field.endswith('preimage') and text == ABSENT else _textual(text, field, roots)
             for field, text in named}
    surfaces, parser_sha = _load_parser()
    limits = {'stanza': surfaces.CONFIG_BYTES, 'table': surfaces.TABLE_BYTES,
              'stanza-preimage': surfaces.CONFIG_BYTES, 'table-preimage': surfaces.TABLE_BYTES}
    data = {field: None if paths[field] is None else _input(paths[field], field, limits[field], roots)
            for field in limits}
    _boundary('inputs-read')
    pairs = _pair(surfaces, data['stanza'], data['table'])
    _boundary('validated')
    seen = {}
    root = _resolve(paths['stage-root'], 'stage-root', roots, 'stage_root_invalid', seen)
    state = 'missing' if seen.get('last') is None else _root_state(root)
    generations, incomplete, previous = [], [], None
    if state == 'folder':
        generations, incomplete, _, previous = _verify_root(root, parser_sha, surfaces, roots)
    number = int(generations[-1][1:]) + 1 if generations else 1
    if number > 9999:
        raise Refusal('generation_limit', 'stage-root')
    name = 'g%04d' % number
    temp = root + '/.incomplete-' + name + '-' + secrets.token_hex(8)
    target = root + '/' + name
    for path in (temp, target):  # roots.spelled covers a live folder that does not exist yet
        reason = _live_reason(path, roots)
        inside = _key(path) + '/'
        for base, why in [(_key(root), 'environment_root') for root in roots] + list(roots.spelled.items()):
            if base.startswith(inside):  # a live path below a folder this run creates would be created with it
                reason = reason or why
        if reason:
            raise Refusal('live_path', 'stage-root', reason)
    content = {'stanza.json': data['stanza'], 'SURFACES.md': data['table'],
               'preimage/stanza.json': data['stanza-preimage'], 'preimage/SURFACES.md': data['table-preimage']}
    manifest = {'schema': SCHEMA, 'generation': name, 'state': 'staged', 'active': False,
                'activation': dict(ACTIVATION), 'parser_sha256': parser_sha,
                'previous': None if previous is None else {'generation': previous[0], 'manifest_sha256': previous[1]},
                'files': {rel: None if blob is None else {'sha256': _sha(blob), 'bytes': len(blob)}
                          for rel, blob in content.items()},
                'pairs': pairs, 'pairs_sha256': _sha(_compact(pairs))}
    manifest_bytes = json.dumps(manifest, indent=1, sort_keys=True).encode('utf-8') + b'\n'
    if state == 'missing':
        os.mkdir(root, 0o700)
    os.mkdir(temp, 0o700)
    os.mkdir(temp + '/preimage', 0o700)
    _boundary('temp-created', temp)
    written = [(rel, blob) for rel, blob in content.items() if blob is not None]
    for rel, blob in written:
        _write_new(temp + '/' + rel, blob, rel)
    _write_new(temp + '/' + MANIFEST, manifest_bytes, MANIFEST)
    _sync_folder(temp + '/preimage')
    _sync_folder(temp)
    _boundary('synced', temp)
    for rel, blob in written + [(MANIFEST, manifest_bytes)]:
        back = _read_file(temp + '/' + rel, rel, len(blob), missing='readback_mismatch', oversize='readback_mismatch',
                          other='readback_mismatch')
        if back != blob:
            raise Refusal('readback_mismatch', rel)
    _boundary('readback-temp', temp)
    for field in limits:
        if paths[field] is None:
            continue
        try:
            again = _input(paths[field], field, limits[field], roots)
        except Refusal:
            raise Refusal('input_changed', field) from None
        if again != data[field]:
            raise Refusal('input_changed', field)
    _boundary('inputs-rechecked', temp)
    try:
        os.lstat(target)
        raise Refusal('generation_conflict', name)
    except FileNotFoundError:
        pass
    try:
        os.rename(temp, target)
    except OSError as error:
        if not isinstance(error, FileExistsError) and error.errno not in (errno.EEXIST, errno.ENOTEMPTY):
            raise  # refused by the system for another reason: main reports io_error
        raise Refusal('generation_conflict', name) from None
    _sync_folder(root)
    _boundary('committed', target)
    try:
        generations, incomplete, final, newest = _verify_root(root, parser_sha, surfaces, roots)
    except Refusal as error:
        raise Refusal('readback_mismatch', error.field, detail=error.code) from None
    if generations[-1] != name or final['pairs_sha256'] != manifest['pairs_sha256']:
        raise Refusal('readback_mismatch', name)
    _boundary('readback-final', target)
    return _summary('staged', root, generations, incomplete, final, newest[1])


def check(args):
    roots = _environment_roots()
    root = _textual(args.stage_root, 'stage-root', roots)
    sources = {field: _textual(text, field, roots) for field, text in (('stanza', args.stanza), ('table', args.table))
               if text is not None}
    surfaces, parser_sha = _load_parser()
    seen = {}
    root = _resolve(root, 'stage-root', roots, 'stage_root_invalid', seen)
    if seen.get('last') is None or _root_state(root) != 'folder':
        raise Refusal('stage_root_invalid', 'stage-root')
    generations, incomplete, manifest, newest = _verify_root(root, parser_sha, surfaces, roots)
    _boundary('readback-done', root)
    if not generations:
        error = Refusal('nothing_staged', 'stage-root')
        error.incomplete = incomplete
        raise error
    if args.manifest_sha256 is not None and args.manifest_sha256 != newest[1]:
        raise Refusal('manifest_digest_mismatch', 'manifest-sha256')
    for field, path in sources.items():
        rel = 'stanza.json' if field == 'stanza' else 'SURFACES.md'
        if _sha(_input(path, field, _limit(surfaces, rel), roots)) != manifest['files'][rel]['sha256']:
            raise Refusal('source_digest_mismatch', field)
    return _summary('staged', root, generations, incomplete, manifest, newest[1])


# Operating-system sandbox (macOS sandbox-exec): the run is re-executed inside a profile that denies every read,
# metadata read and write under each live folder by its given spellings and its real path; the path checks run inside.

def _sandbox_host():
    """True when the host advertises its sandbox: macOS with an executable /usr/bin/sandbox-exec."""
    return (sys.platform == 'darwin' and bool(SANDBOX_EXEC) and os.path.isfile(SANDBOX_EXEC)
            and os.access(SANDBOX_EXEC, os.X_OK))


def _canary():
    """Inside the checker's own sandbox the canary's metadata is denied; anywhere else the run refuses."""
    try:
        os.lstat(CANARY)
    except PermissionError:
        return
    except OSError:
        pass
    raise Refusal('sandbox_not_applied')


def _named(path):
    """The sandbox's own name rules (independent of the path checks): a live state, legacy or .config/openclaw folder
    in the path, or a configuration file name at its end."""
    before = ''
    parts = [_fold(part) for part in path.split('/') if part]
    for part in parts:
        if part.startswith(STATE_FOLDERS) or (before == '.config' and part.startswith('openclaw')):
            return 'openclaw_folder'
        before = part
    if parts and parts[-1].startswith(CONFIG_NAMES):
        return 'live_name'
    return None


def _within(path, bases, below=False):
    """True when `path` is at (unless `below`) or below one of `bases` (keys, compared folded as _key)."""
    key = _key(path)
    return any((key == base and not below) or key.startswith(base.rstrip('/') + '/') for base in bases)


def _sb_walk(path, stop, walked, field='environment'):
    """(physical spelling, kind) of absolute `path`: each folder from / is listed (names only) and its entry found
    there, folder symlinks followed. `stop(folder)` is asked before a folder is listed and after every symlink, and a
    reason it returns ends the walk: ('stop', reason, path); `stop(path, True)` is asked of the new spelling after each
    symlink. kind: dir, other, link (the last part is a symlink, not followed) or missing (the physical spelling is then
    the first missing folder)."""
    parts = [part for part in path.split('/') if part]
    done, index, hops = '', 0, 0
    while index < len(parts):
        folder = done or '/'
        why = stop(folder, False)
        if why:
            return 'stop', why, folder
        walked.add(_key(folder))
        with os.scandir(folder) as listing:
            entries = list(listing)
        found = [entry for entry in entries if entry.name == parts[index]]
        if not found:
            found = [entry for entry in entries if _fold(entry.name) == _fold(parts[index])]
        if len(found) > 1:
            raise Refusal('path_invalid', field)
        if not found:
            return 'missing', None, _normal(done + '/' + parts[index])
        entry = found[0]
        current = done + '/' + entry.name
        last = index == len(parts) - 1
        if entry.is_symlink():
            if last:
                return 'link', None, current
            hops += 1
            if hops > MAX_HOPS:
                raise Refusal('path_invalid', field)
            target = os.readlink(current)
            path = _normal((target if target.startswith('/') else folder + '/' + target) + '/' + '/'.join(parts[index + 1:]))
            why = stop(path, True)
            if why:
                return 'stop', why, path
            parts, done, index = [part for part in path.split('/') if part], '', 0
            continue
        if last:
            return ('dir' if entry.is_dir(follow_symlinks=False) else 'other'), None, current
        if not entry.is_dir(follow_symlinks=False):
            return 'missing', None, _normal(current + '/' + parts[index + 1])
        done, index = current, index + 1
    return 'dir', None, '/'


def _sb_follow(path, stop, walked, field='environment'):
    """_sb_walk, following a last-part symlink too (at most MAX_HOPS times); every link spelling is returned."""
    links = []
    for _ in range(MAX_HOPS):
        kind, why, where = _sb_walk(path, stop, walked, field)
        if kind != 'link':
            return kind, why, where, links
        links.append(where)
        path = _join(os.path.dirname(where), os.readlink(where))
        why = stop(path, True)
        if why:
            return 'stop', why, path, links
    raise Refusal('path_invalid', field)


def _located(found, where, kind, links):
    for link in links:
        found['links'].append(link)
    if kind == 'missing':
        found['futures'].append(where)
    elif kind in ('dir', 'other'):
        found['live'].append(where)


def _locate(args, phase):
    """Run inside the sandbox (phase roots, then homes): the real paths of the live folders, for the profile. Refuses
    as the path checks refuse when two live locations nest under different spellings or a home lies in a live folder,
    before anything inside a known live folder is listed."""
    roots = _environment_text()
    keys = [_key(root) for root in roots]
    live_keys = {key for key in keys if keys.count(key) > (key in roots.home_roots)}
    found = {'result': 'located', 'phase': phase, 'live': [], 'futures': [], 'links': [], 'homes': [], 'stage_root': None}
    walked = set()
    if phase == 'roots':
        spelled = sorted(set(roots), key=lambda root: (len([p for p in root.split('/') if p]), _key(root)))
        for root in spelled:
            others = [_key(other) for other in spelled if _key(other) != _key(root)]
            physical = [_key(p) for p in found['live'] + found['futures']]

            def stop(folder, last, others=others, physical=physical):
                if _within(folder, physical, last):
                    return 'environment_root'
                if _named(folder) or _within(folder, others):
                    return 'covered'
                return None
            if _named(os.path.dirname(root)) or _within(os.path.dirname(root), others):
                continue  # covered by the spelling of a live folder above it
            kind, why, where, links = _sb_follow(root, stop, walked)
            if why == 'environment_root':
                raise Refusal('live_path', 'environment', 'environment_root')
            _located(found, where, kind, links)
            if kind in ('dir', 'other', 'missing') and _key(root) in roots.home_roots and _key(root) not in live_keys:
                found['homes'].append(where)
        found['walked'] = sorted(walked)  # the second pass checks them against the homes' live folders
        state = [_key(p) for p in found['live'] + found['futures'] if p not in found['homes']]
        if any(_within(folder, state) for folder in walked):
            raise Refusal('live_path', 'environment', 'environment_root')
        return found
    earlier = json.loads(os.environ.get(SANDBOX_LIVE, '{}'))
    homes_physical = [_key(p) for p in earlier.get('homes', [])]
    live_physical = [_key(p) for p in earlier.get('live', []) + earlier.get('futures', []) if _key(p) not in homes_physical]
    others = [_key(root) for root in roots if _key(root) in live_keys]

    def home_stop(folder, last=False):
        reason = _named(folder)
        if reason:
            return 'openclaw_folder'
        if _within(folder, others) or _within(folder, live_physical):
            return 'environment_root'
        return None

    def target_stop(folder, last):
        if _within(folder, live_physical, last):
            return 'environment_root'
        if _named(folder) or _within(folder, others):
            return 'covered'
        return None
    for home in dict.fromkeys(roots.homes):
        why = home_stop(home)
        if why:
            raise Refusal('live_path', 'environment', why)
        kind, why, where, _ = _sb_follow(home, home_stop, walked)
        if why:
            raise Refusal('live_path', 'environment', why)
        if kind != 'dir':
            continue
        with os.scandir(where) as listing:
            entries = list(listing)
        for entry in entries:
            name = _fold(entry.name)
            if name.startswith(STATE_FOLDERS) or name == '.config':
                path = where + '/' + entry.name
                if not entry.is_symlink():
                    if name != '.config':
                        found['live'].append(path)
                        continue
                    if not entry.is_dir(follow_symlinks=False):
                        continue
                    folder = path
                else:
                    target = _join(where, os.readlink(path))
                    if name != '.config':
                        found['links'].append(path)
                    kind, why, folder, links = _sb_follow(target, target_stop, walked)
                    if why == 'environment_root':
                        raise Refusal('live_path', 'environment', why)
                    if name != '.config':
                        if why != 'covered':
                            _located(found, folder, kind, links)
                        continue
                    if kind != 'dir' or why:
                        continue
                if name == '.config':
                    with os.scandir(folder) as listing:
                        inner = list(listing)
                    for item in inner:
                        if not _fold(item.name).startswith('openclaw'):
                            continue
                        spot = folder + '/' + item.name
                        if not item.is_symlink():
                            found['live'].append(spot)
                            continue
                        found['links'].append(spot)
                        kind, why, deep, links = _sb_follow(_join(folder, os.readlink(spot)), target_stop, walked)
                        if why == 'environment_root':
                            raise Refusal('live_path', 'environment', why)
                        if why != 'covered':
                            _located(found, deep, kind, links)
    homes_live = [_key(p) for p in found['live'] + found['futures']]
    if any(_within(folder, homes_live) for folder in earlier.get('walked', [])):  # the first pass listed inside one
        raise Refusal('live_path', 'environment', 'environment_root')
    if args.command == 'stage':
        text = args.stage_root
        if type(text) is str and text and '\0' not in text:
            path = _normal(os.path.abspath(text))
            known = [_key(p) for p in found['live'] + found['futures']] + live_physical

            def root_stop(folder, last=False):
                protected = any(_fold(part) in PROTECTED for part in folder.split('/'))
                return 'live' if (protected or _named(folder) or _within(folder, others + known)) else None
            if not root_stop(path):
                try:
                    kind, why, where = _sb_walk(path, root_stop, set(), 'stage-root')
                except (OSError, Refusal):
                    kind, why, where = 'missing', 'unresolved', None  # the run's own checks refuse it; no write allowed
                if not why and kind in ('dir', 'missing') and not root_stop(where):
                    found['stage_root'] = where
    return found


def _sb_quote(text):
    if '\0' in text or '\n' in text:
        raise Refusal('path_invalid', 'environment')
    return '"' + text.replace('\\', '\\\\').replace('"', '\\"') + '"'


def _sb_regex(text):
    """`text` as a sandbox regular expression, every letter in both cases."""
    out = []
    for ch in text:
        if ch.isalpha() and len(ch.upper()) == 1 and len(ch.lower()) == 1 and ch.upper() != ch.lower():
            out.append(('[%s%s]' if ch.isascii() else '(%s|%s)') % (ch.upper(), ch.lower()))  # bytes: no UTF-8 class
        elif ch in '.^$*+?()[]{}|\\#"/':
            out.append('\\' + ch if ch != '/' else '/')
        else:
            out.append(ch)
    return ''.join(out)


def _sb_spellings(path):
    """Every spelling of `path` the kernel may report: NFC and NFD, with and without /System/Volumes/Data, and
    /private/tmp, /private/var and /private/etc for /tmp, /var and /etc."""
    out = set()
    for form in ('NFC', 'NFD'):
        p = unicodedata.normalize(form, _normal(path))
        parts = p.split('/')
        if parts[:4] == ['', 'System', 'Volumes', 'Data']:
            p = '/' + '/'.join(parts[4:])
        variants = {p}
        bits = p.split('/')
        if len(bits) > 1 and bits[1] in PRIVATE:
            variants.add('/private' + p)
        if len(bits) > 2 and bits[1] == 'private' and bits[2] in PRIVATE:
            variants.add('/' + '/'.join(bits[2:]))
        for v in list(variants):
            variants.add('/System/Volumes/Data' + v)
        out |= variants
    return sorted(out)


def _sb_rules(kind, path):
    """Deny rules (read, metadata read and write) for one location, in every spelling. tree: the folder and
    everything below it. below: everything below it, and the entry itself unless it is a symlink (a link's own entry
    may be read; its target is denied by its real path). home (OPENCLAW_HOME): everything below it except its .config
    folder entry and its state-folder symlink entries, which the path checks read as names; no write to it."""
    lines, ops = [], 'file-read* file-write*'
    state = '|'.join(_sb_regex(name[1:]) for name in STATE_FOLDERS)
    for p in _sb_spellings(path):
        r = _sb_regex(p)
        if kind == 'tree':
            lines.append('(deny %s (subpath %s))' % (ops, _sb_quote(p)))
            lines.append('(deny %s (regex #"^%s(/|$)"))' % (ops, r))
        elif kind == 'below':
            lines.append('(deny %s (regex #"^%s/"))' % (ops, r))
            lines.append('(deny %s (require-all (regex #"^%s$") (require-not (vnode-type SYMLINK))))' % (ops, r))
        else:
            lines.append('(deny %s (require-all (regex #"^%s/") (require-not (regex #"^%s/\\.%s$")) '
                         '(require-not (require-all (regex #"^%s/\\.(%s)[^/]*$") (vnode-type SYMLINK)))))'
                         % (ops, r, r, _sb_regex('config'), r, state))
            lines.append('(deny file-write* (regex #"^%s$"))' % r)
    return lines


NAME_RULES = (
    # a .openclaw*, .clawdbot* or .moltbot* folder anywhere, and .config/openclaw*: everything below it, and the entry
    # itself unless it is a symlink (its target is denied by its real path); a configuration file name anywhere
    '(deny file-read* file-write* (regex #"/\\.(%s)[^/]*/"))',
    '(deny file-read* file-write* (require-all (regex #"/\\.(%s)[^/]*$") (require-not (vnode-type SYMLINK))))',
)


def _profile(roots, found, stage_root=None):
    """The sandbox profile: writes nowhere but below the stage root (stage only); then, overriding any allow, every
    live location denied for read, metadata read and write; the canary denied last."""
    state = '|'.join(_sb_regex(name[1:]) for name in STATE_FOLDERS)
    config = _sb_regex('config') + '/' + _sb_regex('openclaw')
    names = '|'.join(_sb_regex(name) for name in CONFIG_NAMES)
    lines = ['(version 1)', '(allow default)', '(deny file-write*)']
    if stage_root:
        for p in _sb_spellings(stage_root):
            lines.append('(allow file-write* (subpath %s))' % _sb_quote(p))
    lines += [NAME_RULES[0] % state, NAME_RULES[1] % state,
              '(deny file-read* file-write* (regex #"/\\.%s[^/]*/"))' % config,
              '(deny file-read* file-write* (require-all (regex #"/\\.%s[^/]*$") (require-not (vnode-type SYMLINK))))' % config,
              '(deny file-read* file-write* (regex #"/(%s)[^/]*$"))' % names,
              '(deny file-read* file-write* (regex #"/(\\.%s|\\.%s|\\.%s|\\.%s)(/|$)"))' % tuple(
                  _sb_regex(name[1:]) for name in ('.git', '.claude', '.codex', '.gemini')),
              '(deny file-write* (regex #"/%s(/|$)"))' % _sb_regex('_axis'),
              '(deny file-read* file-write* (regex #"/%s/%s(/|$)"))' % (_sb_regex('_axis'), _sb_regex('secrets'))]
    homes = {_key(p) for p in found.get('homes', [])}
    keys = [_key(root) for root in roots]
    for root in sorted(set(roots), key=_key):
        key = _key(root)
        lines += _sb_rules('home' if key in roots.home_roots and keys.count(key) == 1 else 'below', root)
    for link in sorted(set(found.get('links', []))):
        lines += _sb_rules('below', link)
    for path in sorted(set(found.get('live', []) + found.get('futures', []))):
        lines += _sb_rules('home' if _key(path) in homes else 'tree', path)
    lines.append('(deny file-read* file-write* (literal %s))' % _sb_quote(CANARY))
    return '\n'.join(lines) + '\n'


def _runner():
    """The command that runs this checker in a child: this interpreter with its own isolation flags, on this file."""
    if _RUNNER:
        return list(_RUNNER)
    flags = ['-B']
    for flag, on in (('-E', sys.flags.ignore_environment), ('-s', sys.flags.no_user_site), ('-S', sys.flags.no_site),
                     ('-I', getattr(sys.flags, 'isolated', 0))):
        if on:
            flags.append(flag)
    return [sys.executable] + flags + [os.path.abspath(__file__)]


def _spawn(command, env):
    """Run `command` with its output read back; returns (exit status, output text)."""
    read, write = os.pipe()
    try:
        pid = os.posix_spawn(command[0], command, env,
                             file_actions=[(os.POSIX_SPAWN_DUP2, write, 1), (os.POSIX_SPAWN_CLOSE, read)])
    except OSError:
        os.close(read)
        os.close(write)
        raise Refusal('sandbox_unavailable', detail='spawn') from None
    os.close(write)
    chunks = []
    while True:
        chunk = os.read(read, 65536)
        if not chunk:
            break
        chunks.append(chunk)
    os.close(read)
    _, status = os.waitpid(pid, 0)
    code = os.waitstatus_to_exitcode(status) if hasattr(os, 'waitstatus_to_exitcode') else (status >> 8)
    return code, b''.join(chunks).decode('utf-8', 'replace')


def _child(phase, argv, profile, extra=None):
    env = dict(os.environ)
    env.pop(SANDBOX_LIVE, None)
    env.update(extra or {})
    env[SANDBOX_MARK] = phase
    code, text = _spawn([SANDBOX_EXEC, '-p', profile] + _runner() + list(argv), env)
    try:
        out = json.loads(text.strip().splitlines()[-1])
    except (ValueError, IndexError):
        out = None
    if type(out) is dict and out.get('result') == 'located' and code == 0:
        return out
    if type(out) is dict and out.get('result') == 'refused' and code == 1 and type(out.get('code')) is str:
        raise Refusal(out['code'], out.get('field', ''), out.get('reason', ''), out.get('detail', ''))
    raise Refusal('sandbox_unavailable', detail='exit %s' % code)


def _sandboxed(args, argv):
    """Locate the live folders inside the sandbox (roots, then homes with the roots' real paths denied), then replace
    this process with the run itself inside the full profile. Returns only by refusing."""
    roots = _environment_text()
    first = _child('roots', argv, _profile(roots, {}))
    second = _child('homes', argv, _profile(roots, first), {SANDBOX_LIVE: json.dumps(first)})
    found = {key: first[key] + second[key] for key in ('live', 'futures', 'links', 'homes')}
    profile = _profile(roots, found, second.get('stage_root') if args.command == 'stage' else None)
    code, _ = _spawn([SANDBOX_EXEC, '-p', profile, '/usr/bin/true'], dict(os.environ))
    if code != 0:
        raise Refusal('sandbox_unavailable', detail='profile')
    env = dict(os.environ)
    env.pop(SANDBOX_LIVE, None)
    env[SANDBOX_MARK] = 'run'
    sys.stdout.flush()
    try:
        os.execve(SANDBOX_EXEC, [SANDBOX_EXEC, '-p', profile] + _runner() + list(argv), env)
    except OSError:
        raise Refusal('sandbox_unavailable', detail='exec') from None


def main(argv=None):
    parser = argparse.ArgumentParser(prog='profile-staging.py', description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command', required=True)
    put = sub.add_parser('stage', help='stage copies as a new generation; never activates')
    put.add_argument('--stanza', required=True)
    put.add_argument('--table', required=True)
    put.add_argument('--stanza-preimage', required=True)
    put.add_argument('--table-preimage', required=True)
    put.add_argument('--stage-root', required=True)
    get = sub.add_parser('check', help='read a stage root back; writes nothing')
    get.add_argument('--stage-root', required=True)
    get.add_argument('--stanza')
    get.add_argument('--table')
    get.add_argument('--manifest-sha256')
    args = parser.parse_args(argv)
    argv = list(sys.argv[1:] if argv is None else argv)
    mark = os.environ.get(SANDBOX_MARK)
    isolation = 'sandbox' if mark is not None or _sandbox_host() else 'path-checks'
    try:
        if not hasattr(os, 'O_NOFOLLOW'):
            raise Refusal('platform_unsupported')
        if mark is not None:
            _canary()
            if mark in ('roots', 'homes'):
                out = _locate(args, mark)
            elif mark == 'run':
                out = stage(args) if args.command == 'stage' else check(args)
            else:
                raise Refusal('sandbox_not_applied')
        elif isolation == 'sandbox':
            _sandboxed(args, argv)
            raise Refusal('sandbox_unavailable')
        else:
            out = stage(args) if args.command == 'stage' else check(args)
        status = 0
    except Refusal as error:
        out, status = error.output(), 1
        if hasattr(error, 'incomplete'):
            out['incomplete'] = error.incomplete
    except OSError as error:
        out, status = Refusal('io_error', detail=type(error).__name__).output(), 1
    out['isolation'] = isolation
    print(json.dumps(out, sort_keys=True))
    return status


if __name__ == '__main__':
    sys.exit(main())
