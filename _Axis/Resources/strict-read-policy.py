"""Inert, pure M1 proposal. Compare explicit read/status inputs, never authorize I/O.

No filesystem, environment, current directory, shell, transport or live helper is
consulted. A match leaves physical evidence unresolved. The host adapter must
meet every ADAPTER_OBLIGATIONS item before reading or disclosing anything.
"""
from dataclasses import dataclass
import re

SCHEMA = 'axis.strict-read/v1'
ROLES = ('Main', 'Assistant', 'Auxiliary', 'GroupAgent', 'Observer')
OWNER_ONLY = ('Main', 'Assistant', 'Auxiliary')
TOOLS = {'read_file': ('read', ('file',)),
         'search_files': ('read', ('search_root', 'file')),
         'path_status': ('status', ('path',))}
# Strict shared-role workflow guidance excludes private surface tables and
# mutable/recovery state directories. Legacy guards and role prose need reconciliation.
WORKFLOW_FILES = frozenset((
    '_Axis/RULES.md', '_Axis/PRACTICES.md', '_Axis/PRINCIPLES.md',
    '_Axis/GLOSSARY.md', '_Axis/MANIFEST.md', '_Axis/CHANGELOG.md',
    '_Axis/SETTINGS.md', 'AGENTS.md', 'CLAUDE.md', 'GEMINI.md', 'README.md'))
WORKFLOW_DIRS = frozenset((
    '_Axis/Rules', '_Axis/Practices', '_Axis/Roles', '_Axis/Commands',
    '_Axis/Resources'))
ADAPTER_OBLIGATIONS = (
    'Authenticate current identity, canonical role, principal, scope and root from the frozen route; recheck policy and invocation at use.',
    'Parse the actual supported host tool schema; include every input, search root, expanded leaf and indirect content source; refuse aliases or unrecognized fields.',
    'Establish the project root object and canonical names on the actual filesystem; reject unresolved paths, aliases, devices, streams, reparse points and forbidden objects.',
    'Bind checks to the actual open objects under a confined root; prevent symlink/TOCTOU escapes and hard-link aliases to protected or out-of-scope data.',
    'Enumerate searches without following excluded paths; apply these checks to every returned/read object and suppress forbidden metadata, content and diagnostics.',
    'Enforce the same limits independently on every host tool, connector, shell, process, transcript, memory and reply attachment path; otherwise strict service is unavailable.',
    'Keep this comparison separate from execution and lifecycle authority; refuse errors and strict failures without legacy fallback.',
)

# Frozen Unicode 16 Cc/Cf/Cs and White_Space profile from the named parser proposal.
# These are format checks, not filesystem normalization or confusable detection.
_FORBIDDEN = ((0x0,0x1f),(0x7f,0x9f),(0xad,0xad),(0x600,0x605),(0x61c,0x61c),
 (0x6dd,0x6dd),(0x70f,0x70f),(0x890,0x891),(0x8e2,0x8e2),(0x180e,0x180e),
 (0x200b,0x200f),(0x202a,0x202e),(0x2060,0x2064),(0x2066,0x206f),
 (0xd800,0xdfff),(0xfeff,0xfeff),(0xfff9,0xfffb),(0x110bd,0x110bd),
 (0x110cd,0x110cd),(0x13430,0x1343f),(0x1bca0,0x1bca3),(0x1d173,0x1d17a),
 (0xe0001,0xe0001),(0xe0020,0xe007f))
_WHITE = ((0x9,0xd),(0x20,0x20),(0x85,0x85),(0xa0,0xa0),(0x1680,0x1680),
 (0x2000,0x200a),(0x2028,0x2028),(0x2029,0x2029),(0x202f,0x202f),
 (0x205f,0x205f),(0x3000,0x3000))
_FOLDER = re.compile(r'[A-Za-z0-9][A-Za-z0-9 ._-]{0,127}\Z')
_RESERVED = frozenset(('CON','PRN','AUX','NUL') + tuple(f'{p}{n}' for p in ('COM','LPT') for n in range(1,10)))

@dataclass(frozen=True)
class ReadComparison:
    lexical_match: bool
    reason: str
    kind: str = 'read-status-comparison-only'
    execution_authority: bool = False
    physical_evidence: str = 'unresolved'
    adapter_obligations: tuple[str, ...] = ADAPTER_OBLIGATIONS

    def __bool__(self):
        raise TypeError('ReadComparison is not an execution authorization; inspect lexical_match explicitly')


def _in_ranges(char, ranges):
    return any(lo <= ord(char) <= hi for lo, hi in ranges)


def _safe(value):
    return (type(value) is str and 0 < len(value) <= 4096
            and not any(_in_ranges(c, _FORBIDDEN) for c in value)
            and len(value.encode('utf-8')) <= 4096
            and not _in_ranges(value[0], _WHITE) and not _in_ranges(value[-1], _WHITE))


def _components(parts, windows=False):
    for part in parts:
        if not _safe(part) or part in ('.','..') or any(c in '*?[]{}<>:"|$`' for c in part):
            return False
        if part.startswith('~'):
            return False
        if windows and (part.endswith('.') or '~' in part or part.split('.')[0].upper() in _RESERVED):
            return False
    return True


def _absolute(value):
    """Return exact anchor/components. No case folding, normpath, realpath or I/O."""
    if not _safe(value):
        return None
    if value.startswith('/') and not value.startswith('//') and '\\' not in value:
        anchor, parts = ('posix',), tuple(value[1:].split('/'))
    elif re.match(r'[A-Za-z]:\\', value) and '/' not in value:
        anchor, parts = ('drive',value[:2]), tuple(value[3:].split('\\'))
    elif value.startswith('\\\\') and '/' not in value:
        all_parts = tuple(value[2:].split('\\'))
        if len(all_parts) < 3 or not _components(all_parts[:2], True):
            return None
        anchor, parts = ('unc',*all_parts[:2]), all_parts[2:]
    else:
        return None
    if not _components(parts, anchor[0] != 'posix'):
        return None
    return anchor, parts


def _relative(root, value):
    if not _safe(value):
        return None, 'path_invalid'
    if value.startswith(('/', '\\')) or re.match(r'[A-Za-z]:', value):
        parsed = _absolute(value)
        if parsed is None:
            return None, 'path_invalid'
        anchor, parts = parsed
        if anchor != root[0] or parts[:len(root[1])] != root[1]:
            return None, 'path_escape'
        relative = parts[len(root[1]):]
    else:
        relative = tuple(value.split('/'))
        if '\\' in value or not _components(relative, root[0][0] != 'posix'):
            return None, 'path_invalid'
    if not relative:
        return None, 'root_operand'
    return relative, None


def _excluded(part):
    # Protect suffix-only names and excluded stems before any extension, including
    # versioned names. Exact case is preserved; physical aliases are adapter work.
    return any(prefix.endswith('_X') for prefix in part.split('.'))


def _secret_path(parts):
    return any(a.lower() == '_axis' and b.lower() == 'secrets' for a,b in zip(parts,parts[1:]))


def _protected(parts):
    if any(part.startswith('.') or _excluded(part) for part in parts):
        return True
    return _secret_path(parts)


def _scope_valid(scope, role):
    if type(scope) is str:
        return scope == 'project' and role in OWNER_ONLY
    return (type(scope) in (list,tuple) and 1 <= len(scope) <= 64
            and all(type(f) is str and _safe(f) and _FOLDER.fullmatch(f) and not _excluded(f) for f in scope)
            and len(set(scope)) == len(scope))


def _within_scope(parts, scope):
    if scope == 'project':
        return True
    rel = '/'.join(parts)
    return (rel in WORKFLOW_FILES or any(rel == d or rel.startswith(d+'/') for d in WORKFLOW_DIRS)
            or parts[0] in scope)


def compare_read(project_root, role, principal, read_scope, request):
    """Compare trusted explicit context to a typed, complete operand declaration.

    Inputs are data, never authentication. A true lexical_match MUST NOT dispatch
    any tool: physical_evidence remains unresolved and execution_authority false.
    Only plain JSON-shaped dictionaries/lists and optional immutable scope tuples
    are supported. Malformed and unsupported values return fixed refusal codes.
    """
    no = lambda reason: ReadComparison(False, reason)
    root = _absolute(project_root)
    if root is None:
        return no('root_invalid')
    root_names = root[0][1:] + root[1]
    if any(_excluded(part) for part in root_names) or _secret_path(root_names):
        return no('root_invalid')
    if type(role) is not str or role not in ROLES:
        return no('role_invalid')
    if type(principal) is not str or principal not in ('owner','participant'):
        return no('principal_invalid')
    if role in OWNER_ONLY and principal != 'owner':
        return no('principal_ceiling')
    if not _scope_valid(read_scope, role):
        return no('scope_invalid')
    if (type(request) is not dict or set(request) != {'schema','operation','tool','complete','operands'}
            or type(request['schema']) is not str or request['schema'] != SCHEMA):
        return no('request_invalid')
    operation, tool = request['operation'], request['tool']
    if type(operation) is not str or operation not in ('read','status'):
        return no('operation_unsupported')
    if type(tool) is not str or tool not in TOOLS:
        return no('tool_unsupported')
    if operation != TOOLS[tool][0]:
        return no('tool_operation')
    if request['complete'] is not True:
        return no('operands_incomplete')
    operands = request['operands']
    if type(operands) is not list or not 1 <= len(operands) <= 256:
        return no('operands_invalid')
    paths, seen = [], set()
    for operand in operands:
        if (type(operand) is not dict or set(operand) != {'kind','path'}
                or type(operand['kind']) is not str or operand['kind'] not in TOOLS[tool][1]):
            return no('operands_invalid')
        parts, error = _relative(root, operand['path'])
        if error:
            return no(error)
        signature = (operand['kind'], parts)
        if signature in seen:
            return no('operands_invalid')
        seen.add(signature)
        if _protected(parts):
            return no('protected_path')
        if not _within_scope(parts, read_scope):
            return no('out_of_scope')
        paths.append(signature)
    if tool == 'search_files':
        roots = [parts for kind,parts in paths if kind == 'search_root']
        if not roots:
            return no('search_roots_required')
        if any('/'.join(parts) in WORKFLOW_FILES for parts in roots):
            return no('search_root_not_directory')
        for kind,parts in paths:
            if kind == 'file' and not any(len(parts) > len(r) and parts[:len(r)] == r for r in roots):
                return no('search_leaf_outside_roots')
    return ReadComparison(True, 'match')
