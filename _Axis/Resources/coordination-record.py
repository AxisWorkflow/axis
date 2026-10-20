"""Subject-first Markdown with a checked readable view and trailing JSON payload.

The JSON object is parsed, then the entire readable representation is regenerated
and compared before use. SHA-256 detects accidental edits, not author identity.
UTF-8 and LF are canonical; CRLF is normalized only for this document checksum.
Exact-byte evidence hashes remain a separate responsibility of the caller.
"""
import hashlib
import json
import re

PAYLOAD = '\n## Machine payload\n\n```json\n'
FOOTER = 'checksum-sha256: '
MAX_DEPTH = 32


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError('duplicate payload key')
        value[key] = item
    return value


def _plain(value):
    # Escape Markdown syntax so untrusted scalar data cannot create links/images
    # or imitate structural headings. Preserve multiline text as a blockquote.
    return re.sub(r'([\\`*_{}\[\]()<>#!|])', r'\\\1', str(value))


def _label(key):
    return _plain(key.replace('_', ' ').replace('-', ' ').capitalize())


def _mapped_lines(value, indent=0, path=()):
    if indent > MAX_DEPTH:
        raise ValueError('payload nesting limit')
    prefix = '  '*indent
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ValueError('payload keys must be strings')
        if not value:
            return [(prefix+'- None', path)]
        result = []
        for key in sorted(value):
            item = value[key]
            child = path+(key,)
            if isinstance(item, (dict, list)):
                result.append((prefix+'- **'+_label(key)+':**', child))
                result.extend(_mapped_lines(item, indent+1, child))
            else:
                result.extend((line, child) for line in _scalar(item, prefix+'- **'+_label(key)+':** ', prefix+'  '))
        return result
    if isinstance(value, list):
        if not value:
            return [(prefix+'- None', path)]
        result = []
        for index, item in enumerate(value):
            child = path+(index,)
            if isinstance(item, (dict, list)):
                result.append((prefix+'- Item:', child))
                result.extend(_mapped_lines(item, indent+1, child))
            else:
                result.extend((line, child) for line in _scalar(item, prefix+'- ', prefix+'  '))
        return result
    return [(line, path) for line in _scalar(value, prefix+'- ', prefix+'  ')]


def _lines(value, indent=0):
    return [line for line, path in _mapped_lines(value, indent)]


def reference_metadata_lines(text):
    """Non-reference rows in a validated coordination detail, indexed from one.

    The checked readable view covers every payload value. Scan its local links
    once; the identical trailing payload is data, not a second set of links.
    Foreign provenance and time/session values are not local record identities.
    """
    subject, payload = decode(text)
    if payload.get('schema') != 'axis.coordination/v1':
        return set()
    lines = text.replace('\r\n', '\n').splitlines()
    first = lines.index('## Details')+3
    ignored = set(range(lines.index('## Machine payload')+1, len(lines)+1))
    time_fields = {'created', 'updated', 'expires', 'deadline', 'authority_expires',
                   'session', 'issuer_session', 'at', 'cursor', 'last_observed',
                   'next_due', 'last_tick'}
    transport = isinstance(payload.get('data', {}).get('transport'), dict)
    legacy = isinstance(payload.get('data', {}).get('legacy'), dict)
    imported = transport or legacy
    for offset, (line, path) in enumerate(_mapped_lines(payload)):
        foreign = path[:2] == ('data', 'transport') and len(path)>2 and (str(path[2]).startswith('source_') or path[2] == 'origin_message')
        foreign = foreign or (legacy and path[:2] == ('data', 'legacy') and len(path)>2 and path[2] in {'from', 'directive'})
        if (path and path[-1] in time_fields) or foreign or (imported and path in {('body',), ('subject',)}):
            ignored.add(first+offset)
    if imported:
        ignored.add(1)
        ignored.update(range(5, lines.index('## Details')+1))
    return ignored


def _scalar(value, first, continuation):
    if value is None:
        value = 'None'
    elif value is True:
        value = 'Yes'
    elif value is False:
        value = 'No'
    elif value == '':
        value = '(empty)'
    lines = _plain(value).split('\n')
    if len(lines) == 1:
        return [first+lines[0]]
    return [first.rstrip()] + [continuation+'> '+line for line in lines]


def render(subject, payload):
    if not isinstance(subject, str) or not 0 < len(subject) <= 80 or subject != subject.strip() or any(c in subject for c in '\r\n'):
        raise ValueError('invalid Subject')
    if not isinstance(payload, dict):
        raise ValueError('payload object required')
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)
    parts = [subject, '', '## Content', '']
    # Put the communication itself ahead of its metadata. The complete payload
    # is still rendered below, including nested source records and authority.
    content = payload.get('body', payload.get('objective'))
    if content is None and isinstance(payload.get('record'), dict):
        content = payload['record'].get('body', payload['record'].get('objective'))
    if isinstance(content, str):
        parts.extend('> '+_plain(line) for line in content.split('\n'))
    else:
        parts.append('See the details below.')
    parts.extend(['', '## Details', ''])
    parts.extend(_lines(payload))
    prefix = '\n'.join(parts)+'\n'+PAYLOAD+encoded+'\n```\n\n'
    return prefix+FOOTER+hashlib.sha256(prefix.encode('utf-8')).hexdigest()+'\n'


def decode(text, limit=131072):
    if not isinstance(text, str) or len(text.encode('utf-8')) > limit:
        raise ValueError('record size')
    text = text.replace('\r\n', '\n')
    if '\r' in text:
        raise ValueError('unsupported line endings')
    match = re.search(r'\nchecksum-sha256: ([0-9a-f]{64})\n\Z', text)
    if not match:
        raise ValueError('checksum missing')
    prefix = text[:match.start()+1]
    if hashlib.sha256(prefix.encode('utf-8')).hexdigest() != match[1]:
        raise ValueError('checksum mismatch; preserve for review')
    if PAYLOAD not in prefix or not prefix.endswith('\n```\n\n'):
        raise ValueError('record shape')
    encoded = prefix.rsplit(PAYLOAD, 1)[1][:-6]
    try:
        payload = json.loads(encoded, object_pairs_hook=_pairs, parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    except (ValueError, TypeError, RecursionError):
        raise ValueError('invalid payload') from None
    subject = text.split('\n', 1)[0]
    if render(subject, payload) != text:
        raise ValueError('readable content and payload disagree; preserve for review')
    return subject, payload
