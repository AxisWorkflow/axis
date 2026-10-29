#!/usr/bin/env python3
"""Launch-time credentials. No credential values are returned as metadata or persisted."""
import json
import os
from pathlib import Path
import re
import stat
import subprocess

MODES = {'subscription', 'api-key', 'either'}
PROVIDERS = {'claude': ('anthropic-api-key', 'ANTHROPIC_API_KEY'),
             'codex': ('openai-api-key', 'OPENAI_API_KEY')}
SELECTORS = {'OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN',
             'CLAUDE_CODE_OAUTH_TOKEN', 'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX',
             'CLAUDE_CODE_USE_FOUNDRY', 'OPENAI_BASE_URL', 'ANTHROPIC_BASE_URL',
             'ANTHROPIC_PROFILE', 'ANTHROPIC_CONFIG_FILE', 'ANTHROPIC_BEARER_TOKEN',
             'ANTHROPIC_DEFAULT_MODEL', 'CODEX_ACCESS_TOKEN'}


def setting(root, provider):
    try:text = (Path(root) / '_Axis/SETTINGS.md').read_text()
    except FileNotFoundError:text = ''
    def value(name):
        match = re.search(r'^### ' + re.escape(name) + r'\n(.*?)(?=^### |\Z)', text, re.M | re.S)
        if not match: return None
        found = re.search(r'^\*\*Value:\*\*\s*(\S+)', match[1], re.M)
        return found[1].strip('`') if found else None
    mode = value('Model Access ' + provider.title()) or value('Model Access') or 'subscription'
    if mode not in MODES: raise ValueError('invalid Model Access setting')
    return mode


def secret(root, filename, optional=False):
    """Descriptor-relative traversal refuses links, hardlinks and permissive key files."""
    root = Path(root)
    if root.is_symlink() or root.resolve() != root.absolute(): raise ValueError('unsafe credential root')
    fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for component in ('_Axis', 'Secrets'):
            try: child = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            except FileNotFoundError:
                if optional:return None
                raise ValueError('selected provider credential unavailable') from None
            os.close(fd); fd = child
        try: keyfd = os.open(filename, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=fd)
        except FileNotFoundError:
            if optional: return None
            raise ValueError('selected provider credential unavailable') from None
        try:
            info = os.fstat(keyfd)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_mode & 0o077 or info.st_size > 16384:
                raise ValueError('provider credential requires one private regular file')
            raw = os.read(keyfd, 16385)
            key = raw.decode().strip()
            if not key or any(c.isspace() or ord(c) < 32 for c in key): raise ValueError('invalid provider credential')
            return key
        finally: os.close(keyfd)
    finally: os.close(fd)


def selected(root, provider, observed=None, mode=None):
    if provider not in PROVIDERS: raise ValueError('unsupported credential provider')
    mode = mode or setting(root, provider)
    if mode not in MODES: raise ValueError('invalid Model Access selection')
    if mode == 'either':
        # No trial call or paid fallback: a trusted fresh route observation decides.
        return 'subscription' if not observed or observed.get('included') is True else 'api-key'
    return mode


def prepare(root, provider, argv, *, mode=None, observed=None, paid_authorized=False, environ=None, native_cli=True):
    """Caller is the trusted Main/User launcher; never callable by a worker tool."""
    mode = selected(root, provider, observed, mode)
    if mode == 'api-key' and paid_authorized is not True:
        raise ValueError('paid API use requires explicit spending authority before credential access')
    env = dict(os.environ if environ is None else environ)
    for name in SELECTORS: env.pop(name, None)
    args = list(argv)
    if mode == 'api-key':
        filename, variable = PROVIDERS[provider]
        # Prefer an explicitly supplied host environment credential; it is never logged.
        inherited = (os.environ if environ is None else environ).get(variable)
        key = inherited or secret(root, filename)
        if not key or any(c.isspace() or ord(c)<32 for c in key):raise ValueError('invalid provider credential')
        env[variable] = key
        if provider == 'codex' and native_cli:
            # Dedicated provider avoids writing auth.json or replacing the user's login.
            args[1:1] = ['-c', 'model_provider="axis_openai"', '-c', 'model_providers.axis_openai.name="OpenAI API"',
                         '-c', 'model_providers.axis_openai.base_url="https://api.openai.com/v1"',
                         '-c', 'model_providers.axis_openai.env_key="OPENAI_API_KEY"',
                         '-c', 'model_providers.axis_openai.wire_api="responses"',
                         '-c', 'model_providers.axis_openai.requires_openai_auth=false']
        elif provider == 'claude' and native_cli:
            args[1:1] = ['--settings', '{"apiKeyHelper":"","env":{}}']
    else:
        if provider == 'codex' and native_cli: args[1:1] = ['-c', 'model_provider="openai"', '-c', 'forced_login_method="chatgpt"']
        elif provider == 'claude':
            if native_cli:args[1:1] = ['--settings', '{"forceLoginMethod":"claudeai","apiKeyHelper":"","env":{}}']
            token = (os.environ if environ is None else environ).get('CLAUDE_CODE_OAUTH_TOKEN')
            if not token: token = secret(root, 'claude-subscription-token', optional=True)
            if token: env['CLAUDE_CODE_OAUTH_TOKEN'] = token
    env['AXIS_MODEL_ACCESS'] = mode
    return args, env, {'provider': provider, 'mode': mode, 'credential': 'launch-environment-only'}


def observed_mode():
    # Presence only; no account, path or credential value enters a Flag.
    selected_mode = os.environ.get('AXIS_MODEL_ACCESS')
    if selected_mode in {'subscription', 'api-key', 'unverified'}: return selected_mode
    if any(os.environ.get(k) for k in ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY')): return 'api-key'
    return 'unverified'


def verify_cli(provider, argv, env, cwd, *, allow_interactive_choice=False):
    """Read-only native auth metadata; never expose account details or raw output.

    Claude settings can inject provider variables after process launch. Confirm
    the effective selection before permitting a model request. Custom checked
    transports must perform their own trusted verify_access observation.
    """
    if provider!='claude' or Path(argv[0]).stem!='claude':return
    if argv[1:2]!=['--settings']:raise ValueError('missing native authentication selector')
    try:
        result=subprocess.run([*argv[:3],'auth','status'],cwd=cwd,env=env,capture_output=True,timeout=20)
        value=json.loads(result.stdout)
    except (OSError,ValueError,subprocess.SubprocessError):
        raise ValueError('native authentication verification unavailable') from None
    mode=env.get('AXIS_MODEL_ACCESS')
    methods={'subscription':{'claude.ai','oauth_token'},'api-key':{'api_key'}}
    valid = value.get('authMethod') in methods.get(mode,set())
    # auth status describes the interactive login on some CLI versions. The
    # documented print-mode precedence always selects the environment API key.
    if mode == 'api-key' and any(x in argv[3:] for x in ('--print', '-p')):
        valid = (value.get('apiProvider') == 'firstParty' and
                 value.get('apiKeySource') == 'ANTHROPIC_API_KEY' and
                 bool(env.get('ANTHROPIC_API_KEY')))
    if (not result.returncode and not valid and allow_interactive_choice and mode == 'api-key'
            and not any(x in argv[3:] for x in ('--print', '-p'))
            and value.get('authMethod') in {'claude.ai', 'oauth_token'}
            and value.get('apiProvider') == 'firstParty'
            and value.get('apiKeySource') == 'ANTHROPIC_API_KEY'
            and env.get('ANTHROPIC_API_KEY')):
        # The interactive CLI owns its explicit first-use key approval prompt.
        # Do not claim that the eventual choice is already verified.
        return 'interactive-approval-required'
    if result.returncode or not valid:
        raise ValueError('effective native authentication differs from selected Model Access')
    return 'verified'
