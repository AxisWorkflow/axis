#!/usr/bin/env python3
"""Read-only check of one OpenClaw configuration file for Axis group and direct-message admission.

  group-check.py [--json] CONFIG

Reads CONFIG alone (JSON, comments and trailing commas allowed; at most 1 MB). It never runs OpenClaw, signs in,
restarts, sends, or reads a session, memory or pairing store. It prints no identifier, number, prompt text or path:
known OpenClaw channels are named, any other channel key is "another channel", accounts and groups go by position.

Only WhatsApp is checked. Every other enabled channel is reported Unverified (`channel_not_checked`), never ready or
refused: its account inheritance and group allowlist keys differ, so check it by hand. `channels.defaults` and
`channels.modelByChannel` are shared settings, not channels; `channels.defaults.groupPolicy` fills a WhatsApp group
policy left unset (`disabled` there is checked as `allowlist`, the documented default it may not override).

For each WhatsApp bot account (a key takes the account's own value, else `accounts.default`, else the channel's; the
group sender list falls back to `allowFrom` when unset or empty) it refuses, exit 1:
- an admitted group entry whose prompt has no valid declaration line while anyone besides the owner can write in
  groups (a sender list inside the entry counts), any malformed declaration line, or two declarations; valid is exactly
  `Axis role: {Role}; surface: {name}` with Role Auxiliary, Assistant, Group Agent or Observer and an optional
  `; promote: ...` ignored, or `Axis role: Auxiliary` alone (the channel form Axis serves until each chat is asked its
  role); a pre-3.15 role word is refused, so the line is rewritten in the current form;
- an empty or missing group map, or a `*` entry, while any group sender is allowed: on OpenClaw 2026.10.2 an empty
  map admits every group;
- group policy `open` or a `*` group sender;
- direct messages `open`, or allowing `*` or any sender not on `commands.ownerAllowFrom`.
It reports Unverified, exit 2 when nothing is refused: an unreadable, oversized, too deeply nested or non-JSON file, an
`$include`, an unexpected shape, an unset or unknown policy, direct messages under pairing or allowlist, whose paired
senders are kept outside this file and admitted too, a channel it does not check, or an internal error (`internal_error`; the check never ends in a traceback).
Exit 0: nothing refused or unverified.
"""
import argparse
import json
import os
import re
import stat
import sys

MAX_BYTES = 1000000
MAX_DEPTH = 64
ROLES = ('Auxiliary', 'Assistant', 'Group Agent', 'Observer')
DECLARATION = re.compile(r'Axis role: (%s); surface: [A-Za-z0-9][A-Za-z0-9._-]{0,63}(?:; promote: [A-Za-z-]{1,32})?' % '|'.join(ROLES))
CHANNEL_FORM = re.compile(r'Axis role: (Auxiliary)(?:; promote: [A-Za-z-]{1,32})?')
CANDIDATE = re.compile(r'\W*axis\W*role\b', re.I)
# OpenClaw channel ids from the installed documentation's channel catalog; any other key may be a name, so it is never printed.
KNOWN_CHANNELS = ('a2a', 'bluebubbles', 'buzz', 'clickclack', 'discord', 'feishu', 'googlechat', 'imessage', 'irc', 'line', 'matrix', 'mattermost',
                  'msteams', 'nextcloud-talk', 'nostr', 'openclaw-weixin', 'openclaw-zaloclawbot', 'qqbot', 'raft', 'reef', 'signal', 'slack', 'sms',
                  'synology-chat', 'telegram', 'tlon', 'twitch', 'webchat', 'wecom', 'whatsapp', 'yuanbao', 'zalo', 'zalouser')
SHARED_KEYS = ('defaults', 'modelByChannel')
CHECKED = 'whatsapp'
ENTRY_SENDERS = ('allowFrom', 'groupAllowFrom', 'users')
POLICIES = ('open', 'allowlist', 'disabled')


class Report:
    def __init__(self):
        self.findings = []

    def add(self, level, code, where, text):
        self.findings.append({'level': level, 'code': code, 'where': where, 'text': text})

    def verdict(self):
        levels = {f['level'] for f in self.findings}
        return 'refused' if 'refused' in levels else 'unverified' if 'unverified' in levels else 'ready'


def strip_jsonc(text):
    """Drop // and /* */ comments outside strings and commas before a closing bracket."""
    out, i, n, quote = [], 0, len(text), None
    while i < n:
        c = text[i]
        if quote:
            out.append(c)
            if c == '\\' and i + 1 < n:
                out.append(text[i + 1]); i += 2; continue
            if c == quote:
                quote = None
            i += 1; continue
        if c == '"':
            quote = c; out.append(c); i += 1; continue
        if text.startswith('//', i):
            j = text.find('\n', i); i = n if j < 0 else j; continue
        if text.startswith('/*', i):
            j = text.find('*/', i + 2); i = n if j < 0 else j + 2; continue
        out.append(c); i += 1
    return re.sub(r',(\s*[}\]])', r'\1', ''.join(out))


def too_deep(text):
    """True when brackets outside strings nest deeper than MAX_DEPTH; counted without recursion."""
    depth, quote, i, n = 0, False, 0, len(text)
    while i < n:
        c = text[i]
        if quote:
            if c == '\\':
                i += 2; continue
            if c == '"':
                quote = False
        elif c == '"':
            quote = True
        elif c in '[{':
            depth += 1
            if depth > MAX_DEPTH:
                return True
        elif c in ']}':
            depth -= 1
        i += 1
    return False


def load(path, report):
    try:
        info = os.stat(path)
    except (OSError, ValueError):
        report.add('unverified', 'unreadable', 'file', 'the configuration file cannot be read'); return None
    if not stat.S_ISREG(info.st_mode):
        report.add('unverified', 'unreadable', 'file', 'the configuration path is not a regular file'); return None
    if info.st_size > MAX_BYTES:
        report.add('unverified', 'too_large', 'file', 'the configuration file is over 1 MB; check it by hand'); return None
    try:
        with open(path, 'rb') as handle:
            raw = handle.read(MAX_BYTES + 1)
        text = raw.decode('utf-8-sig')
    except (OSError, UnicodeDecodeError):
        report.add('unverified', 'unreadable', 'file', 'the configuration file cannot be read as UTF-8 text'); return None
    if too_deep(text):
        report.add('unverified', 'too_deep', 'file', 'the configuration nests deeper than %d levels, which this check does not read; check it by hand' % MAX_DEPTH); return None
    for attempt in (text, strip_jsonc(text)):
        try:
            data = json.loads(attempt)
            break
        except ValueError:
            data = None
    if not isinstance(data, dict):
        report.add('unverified', 'not_json', 'file', 'the configuration is not a JSON object this check can read; check it by hand'); return None
    return data


def has_include(node):
    if isinstance(node, dict):
        return any(str(k).startswith('$include') or has_include(v) for k, v in node.items())
    if isinstance(node, list):
        return any(has_include(v) for v in node)
    return False


def norm(value, channel):
    if not isinstance(value, str):
        return None
    s = value.strip().lower()
    if s.startswith(channel + ':'):
        s = s[len(channel) + 1:]
    if s == '*':
        return '*'
    s = s.split('@', 1)[0]
    s = re.sub(r'[\s().+-]', '', s)
    return s or None


def as_list(value, report, where, key):
    if value is None:
        return None
    if isinstance(value, list):
        return value
    report.add('unverified', 'shape', where, key + ' is not a list')
    return []


def owners(config, channel, report):
    found = set()
    commands = config.get('commands')
    entries = as_list(commands.get('ownerAllowFrom') if isinstance(commands, dict) else None, report, 'file', 'the owner list')
    for entry in entries or []:
        if isinstance(entry, str) and (':' not in entry or entry.strip().lower().startswith(channel + ':')):
            key = norm(entry, channel)
            if key and key != '*':
                found.add(key)
    return found


def declarations(entry):
    prompt = entry.get('systemPrompt') if isinstance(entry, dict) else None
    lines = prompt.splitlines() if isinstance(prompt, str) else []
    valid, invalid, channel_form = [], 0, 0
    for line in lines:
        s = line.strip()
        if not CANDIDATE.match(s):
            continue
        full = DECLARATION.fullmatch(s)
        short = None if full else CHANNEL_FORM.fullmatch(s)
        if full or short:
            valid.append((full or short).group(1))
            channel_form += 1 if short else 0
        else:
            invalid += 1
    return valid, invalid, channel_form


def entry_senders(entry, channel, own):
    """True when a sender list inside a group entry names anyone besides the owner."""
    if not isinstance(entry, dict):
        return False
    for key in ENTRY_SENDERS:
        value = entry.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            return True
        if any(norm(s, channel) in (None, '*') or norm(s, channel) not in own for s in value):
            return True
    return False


def group_policy(get, shared, where, report):
    policy = get('groupPolicy')
    if policy is not None or shared is None:
        return policy
    if shared == 'open':
        return 'open'
    if shared in ('allowlist', 'disabled'):
        report.add('note', 'group_policy_from_defaults', where, 'group policy is unset here, so the shared default applies; it is checked as allowlist')
        return 'allowlist'
    report.add('unverified', 'group_policy_unknown', where, 'the shared default group policy has a value this check does not know')
    return 'unknown'


def check_account(channel, where, get, own, shared, report):
    policy = group_policy(get, shared, where, report)
    groups = get('groups')
    allow = as_list(get('allowFrom'), report, where, 'the direct-message sender list') or []
    senders = as_list(get('groupAllowFrom'), report, where, 'the group sender list')
    if not senders:
        # Documented: an unset group sender list falls back to allowFrom. Not documented for an empty one; it is
        # checked as unset, the stricter reading (an empty group map admitted every group on OpenClaw 2026.10.2).
        if senders == [] and allow:
            report.add('note', 'group_senders_empty_fallback', where, 'the group sender list is empty; it is checked as unset, so the direct-message sender list applies to groups')
        senders = allow
    keys = [norm(s, channel) for s in senders]
    if policy == 'disabled':
        report.add('note', 'groups_disabled', where, 'groups are disabled')
    else:
        if policy == 'open':
            report.add('refused', 'group_policy_open', where, 'group policy is open, or unset with an open shared default, so any sender in an admitted group reaches the agent; set it to allowlist')
        elif policy is None:
            report.add('unverified', 'group_policy_unset', where, 'group policy is not set, so the release default decides; set allowlist or disabled')
        elif policy not in POLICIES and policy != 'unknown':
            report.add('unverified', 'group_policy_unknown', where, 'group policy has a value this check does not know')
        if '*' in keys:
            report.add('refused', 'group_sender_wildcard', where, 'the group sender list holds *, which admits every sender; list each person')
        reachable = policy != 'allowlist' or bool(senders)
        anyone = policy != 'allowlist' or any(k != '*' and k not in own for k in keys) or '*' in keys or any(k is None for k in keys)
        if not reachable:
            report.add('note', 'groups_no_sender', where, 'no group sender is allowed, so no group message is admitted')
        elif groups is None or groups == {}:
            report.add('refused', 'group_map_empty', where, 'the group map is empty or missing while group senders are allowed; on OpenClaw 2026.10.2 that admits every group')
        elif not isinstance(groups, dict):
            report.add('unverified', 'shape', where, 'the group map is not an object')
        else:
            if '*' in groups:
                report.add('refused', 'group_map_wildcard', where, 'the group map holds *, which admits every group; declare each group in its own entry')
            for index, (key, entry) in enumerate(groups.items(), 1):
                if key == '*':
                    continue
                label = 'group entry %d' % index
                valid, invalid, channel_form = declarations(entry)
                if invalid:
                    report.add('refused', 'declaration_invalid', where, label + ' has an Axis role line that is not a valid declaration (`Axis role: {Role}; surface: {name}`, Role Auxiliary, Assistant, Group Agent or Observer)')
                elif len(set(valid)) > 1 or len(valid) > 1:
                    report.add('refused', 'declaration_conflict', where, label + ' carries more than one declaration; keep exactly one')
                elif not valid:
                    if anyone or entry_senders(entry, channel, own):
                        report.add('refused', 'declaration_missing', where, label + ' has no Axis role declaration while someone besides the owner can write in groups, so its first message can start Main')
                    else:
                        report.add('note', 'undeclared_owner_only', where, label + ' has no declaration: it runs Main by the ordinary rule, which is allowed only while the owner is the only allowed group sender')
                elif channel_form:
                    report.add('note', 'declaration_channel_form', where, label + ' declares Auxiliary without a surface, which Axis serves on a chat until each chat is asked its role; add `; surface: {name}` and a surface-table row')
    dm = get('dmPolicy')
    dkeys = [norm(s, channel) for s in allow]
    if dm == 'disabled':
        return
    if dm == 'open':
        report.add('refused', 'dm_open', where, 'direct messages are open to anyone; allow only the owner or disable them')
        return
    if dm not in (None, 'pairing', 'allowlist'):
        report.add('unverified', 'dm_policy_unknown', where, 'the direct-message policy has a value this check does not know')
        return
    if '*' in dkeys:
        report.add('refused', 'dm_sender_wildcard', where, 'the direct-message sender list holds *, which admits everyone')
    others = sum(1 for k in dkeys if k != '*' and k not in own)
    if others:
        report.add('refused', 'dm_sender_not_owner', where, 'direct messages allow %d sender(s) not on the owner list' % others)
    if dm in (None, 'pairing'):
        report.add('unverified', 'dm_pairing', where, 'direct messages use pairing, whose approvals are kept outside this file; confirm by hand that only the owner is approved')
    else:
        report.add('unverified', 'dm_allow_store', where, 'paired senders in the allow store are admitted beside the sender list; confirm by hand that only the owner is approved')


def check(config, report):
    if has_include(config):
        report.add('unverified', 'include', 'file', 'the file includes other files, which this check does not read; check them by hand')
    channels = config.get('channels')
    if channels is None:
        report.add('note', 'no_channels', 'file', 'no channel is configured'); return
    if not isinstance(channels, dict):
        report.add('unverified', 'shape', 'file', 'channels is not an object'); return
    defaults = channels.get('defaults')
    shared = defaults.get('groupPolicy') if isinstance(defaults, dict) else None
    for name, channel in channels.items():
        if name in SHARED_KEYS:
            continue
        cname = name if name in KNOWN_CHANNELS else 'another channel'
        if name != CHECKED:
            if isinstance(channel, dict) and channel.get('enabled') is False:
                report.add('note', 'channel_disabled', cname, 'the channel is disabled')
            elif isinstance(channel, dict):
                report.add('unverified', 'channel_not_checked', cname, 'group and direct-message admission on this channel is not checked here; check it by hand')
            continue
        if not isinstance(channel, dict):
            report.add('unverified', 'shape', cname, 'the channel is not an object'); continue
        if channel.get('enabled') is False:
            report.add('note', 'channel_disabled', cname, 'the channel is disabled'); continue
        own = owners(config, name, report)
        accounts = channel.get('accounts')
        if accounts is not None and not isinstance(accounts, dict):
            report.add('unverified', 'shape', cname, 'accounts is not an object'); accounts = None
        scopes = []
        if accounts:
            default = accounts.get('default') if isinstance(accounts.get('default'), dict) else {}
            for index, (aname, account) in enumerate(accounts.items(), 1):
                where = cname + (', the default account' if aname == 'default' else ', account %d' % index)
                if not isinstance(account, dict):
                    report.add('unverified', 'shape', where, 'the account is not an object'); continue
                if account.get('enabled') is False:
                    report.add('note', 'account_disabled', where, 'the account is disabled'); continue
                chain = [account] + ([default] if aname != 'default' else []) + [channel]
                scopes.append((where, chain))
            if 'default' not in accounts:
                scopes.append((cname + ', the channel settings', [channel]))
        else:
            scopes.append((cname, [channel]))
        for where, chain in scopes:
            def get(key, chain=chain):
                for layer in chain:
                    if key in layer:
                        return layer[key]
                return None
            check_account(name, where, get, own, shared, report)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only Axis check of one OpenClaw configuration file; prints no identifier or path.')
    parser.add_argument('--json', action='store_true', help='print one JSON report')
    parser.add_argument('config')
    args = parser.parse_args(argv)
    report = Report()
    try:
        config = load(args.config, report)
        if config is not None:
            check(config, report)
    except Exception:
        # An unexpected file: no traceback (it could quote the file); the error itself is Unverified, never a refusal.
        report.add('unverified', 'internal_error', 'file', 'the check stopped on an unexpected error; check the file by hand')
    verdict = report.verdict()
    counts = {level: sum(1 for f in report.findings if f['level'] == level) for level in ('refused', 'unverified', 'note')}
    if args.json:
        print(json.dumps({'schema': 'axis.openclaw-group-check/v1', 'verdict': verdict, 'counts': counts, 'findings': report.findings}, indent=1, sort_keys=True))
    else:
        print('OpenClaw group check: %s (%d refused, %d unverified)' % (verdict.upper(), counts['refused'], counts['unverified']))
        for f in report.findings:
            print('%s %s: %s [%s]' % (f['level'].upper(), f['where'], f['text'], f['code']))
    return {'ready': 0, 'refused': 1, 'unverified': 2}[verdict]


if __name__ == '__main__':
    sys.exit(main())
