#!/usr/bin/env python3
"""Optional, read-only provider probes and typed session-operation contracts.

Help verifies syntax, not authentication, allowance, runtime identity or authority.
The baseline prepares exact invocations. Explicit execution requires source authority,
verified included access and finite launch/time/output bounds. No daemon or shell input.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass, field
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import time
import uuid

SID = re.compile(r'\d{4}(?:\.\d{2}){5}\.\d{3}Z\Z')
OPS = ('inspect', 'start', 'attach', 'notify', 'pause', 'stop', 'resume')
ANCHORS = ('AGENTS.md', 'CLAUDE.md', 'GEMINI.md', '_Axis/MANIFEST.md',
           '_Axis/PROJECT.md', '_Axis/PRACTICES.md', '_Axis/RULES.md')
MANUAL = 'Open the exact project root in a separate agent session and follow its entry file; retain results in Axis records.'


def load_core():
    path = Path(__file__).with_name('coordination.py')
    if not path.is_file() or path.is_symlink():
        raise ValueError('coordination foundation unavailable; use the manual workflow')
    spec = importlib.util.spec_from_file_location('axis_coordination_adapters', path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def load_record_format():
    path = Path(__file__).with_name('coordination-record.py')
    if not path.is_file() or path.is_symlink():
        raise ValueError('readable record format unavailable')
    spec = importlib.util.spec_from_file_location('axis_adapter_record', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def exact_root(value):
    path = Path(value)
    if not path.is_absolute() or str(path) != str(path.resolve(strict=True)):
        raise ValueError('root must be an absolute canonical path without symlinks')
    if not path.is_dir():
        raise ValueError('project root is not a directory')
    return path


def recognized(root):
    try:
        root = exact_root(root)
        for name in ANCHORS:
            p = root / name
            if not p.is_file() or p.is_symlink():
                return False
        return (root / '_Axis').is_dir() and not (root / '_Axis').is_symlink() and (root / '_Temp').is_dir() and not (root / '_Temp').is_symlink()
    except (OSError, ValueError):
        return False


def file_digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(data)
    return h.hexdigest()


@dataclass(frozen=True)
class ProjectRef:
    project: str
    root: str

    def validate(self):
        if str(uuid.UUID(self.project)) != self.project:
            raise ValueError('noncanonical project UUID')
        root = exact_root(self.root)
        if not recognized(root):
            raise ValueError('incomplete project anchors')
        store = load_core().Store(root)
        if store.project_id() != self.project:
            raise ValueError('project UUID mismatch')
        return store


@dataclass(frozen=True)
class SessionBinding:
    project: str
    root: str
    axis_session: str
    native_handle: str
    generation: str
    adapter: str
    adapter_version: str
    executable: str
    executable_sha256: str
    verified_at: float
    residency: str = 'on-demand'
    observed_runtime: str = 'unknown'

    def validate_shape(self):
        if not SID.fullmatch(self.axis_session):
            raise ValueError('invalid Axis session')
        if not self.native_handle or not self.generation or len(self.native_handle) > 256 or len(self.generation) > 256:
            raise ValueError('native handle and generation are required')
        if self.residency not in ('on-demand', 'warm', 'managed'):
            raise ValueError('unknown residency')
        if not re.fullmatch('[a-f0-9]{64}', self.executable_sha256):
            raise ValueError('missing executable digest')
        if not isinstance(self.verified_at, (int, float)) or not 0 < self.verified_at <= time.time() + 5:
            raise ValueError('invalid verification time')


@dataclass(frozen=True)
class CapabilityResult:
    operation: str
    status: str
    reason: str
    details: dict = field(default_factory=dict)
    manual: str = MANUAL

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class Probe:
    adapter: str
    executable: str | None
    executable_sha256: str | None
    version: str | None
    help_sha256: dict
    syntax: tuple
    status: str
    reason: str
    probed_at: float
    auth_mode: str = 'unverified'
    allowance: str = 'unverified'
    cancellation: str = 'unverified for existing sessions; bounded starts own one process group'
    file_identity: tuple | None = None


def _help(executable, args, timeout):
    # Exact read-only probes only. Never accept a command or shell string.
    if args not in (('--version',), ('--help',), ('exec', '--help'), ('exec', 'resume', '--help')):
        raise ValueError('probe is not allowlisted')
    result = _bounded_process([executable, *args], None, '', timeout, 256 * 1024, lambda: None)
    if result['returncode'] != 0 or result['reason']:
        raise ValueError('provider help failed or exceeded output/deadline limit')
    return result['stdout'].decode('utf-8', 'strict')


def executable_identity(path):
    value = Path(path).stat()
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns)


def _native_executable(adapter, path):
    # The npm Codex entrypoint is a JS selector, not the model runtime binary.
    # Resolve its documented installation layout without executing wrapper code.
    if adapter != 'codex' or path.suffix != '.js':
        return path
    import platform
    package = path.parent.parent
    if path.name != 'codex.js' or path.parent.name != 'bin' or json.loads((package / 'package.json').read_text()).get('name') != '@openai/codex':
        raise ValueError('unverified executable wrapper; select an exact native executable')
    arch = {'arm64': 'arm64', 'aarch64': 'arm64', 'x86_64': 'x64', 'AMD64': 'x64'}.get(platform.machine())
    system = {'darwin': 'darwin', 'linux': 'linux'}.get(sys.platform)
    if not arch or not system:
        raise ValueError('native Codex wrapper resolution unavailable on this platform')
    target = ('aarch64' if arch == 'arm64' else 'x86_64') + ('-apple-darwin' if system == 'darwin' else '-unknown-linux-musl')
    package_name = 'codex-' + system + '-' + arch
    candidates = [package / 'node_modules/@openai' / package_name / 'vendor' / target / 'bin/codex',
                  package.parent / package_name / 'vendor' / target / 'bin/codex',
                  package / 'vendor' / target / 'bin/codex']
    candidates = [p.resolve(strict=True) for p in candidates if p.is_file()]
    if len(set(candidates)) != 1:
        raise ValueError('native Codex executable missing or ambiguous; use manual dispatch')
    return candidates[0]


def probe(adapter, executable=None, timeout=5):
    now = time.time()
    if adapter not in ('codex', 'claude'):
        return Probe(adapter, None, None, None, {}, (), 'unavailable',
                     'OpenClaw is explicitly unavailable' if adapter == 'openclaw' else 'manual provider route', now)
    resolved = shutil.which(executable or adapter)
    if not resolved:
        return Probe(adapter, None, None, None, {}, (), 'unavailable', 'executable missing', now)
    try:
        path = _native_executable(adapter, Path(resolved).resolve(strict=True))
        if not path.is_file() or not os.access(path, os.X_OK):
            raise ValueError('executable is not a regular executable file')
        identity = executable_identity(path)
        before = file_digest(path)
        version = _help(str(path), ('--version',), timeout).strip()
        if not version or len(version) > 512:
            raise ValueError('invalid version response')
        commands = [('exec', '--help'), ('exec', 'resume', '--help')] if adapter == 'codex' else [('--help',)]
        outputs = {' '.join(c): _help(str(path), c, timeout) for c in commands}
        if executable_identity(path) != identity or file_digest(path) != before:
            raise ValueError('executable changed during probe')
        if adapter == 'codex':
            start = outputs['exec --help']
            resume = outputs['exec resume --help']
            syntax = tuple(op for op, okay in (
                ('start', all(s in start for s in ('--json', '--model', '--sandbox', '--cd', '[PROMPT]', 'workspace-write'))),
                ('resume', all(s in resume for s in ('[SESSION_ID]', '--json', '--model')))) if okay)
        else:
            help_text = outputs['--help']
            syntax = tuple(op for op, okay in (
                ('start', all(s in help_text for s in ('--print', '--output-format', '--model', '--session-id', '--permission-mode', 'manual', 'json'))),
                ('resume', all(s in help_text for s in ('--resume', '--print', '--output-format', '--model')))) if okay)
        return Probe(adapter, str(path), before, version,
                     {k: hashlib.sha256(v.encode()).hexdigest() for k, v in outputs.items()},
                     syntax, 'verified-syntax', 'help/version only; no model call', now, file_identity=identity)
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError) as exc:
        return Probe(adapter, str(resolved), None, None, {}, (), 'unverified', str(exc), now)


def lease_state(project, session):
    """Read only: never renew, synthesize or repair a lease."""
    try:
        if not SID.fullmatch(session):
            return 'unknown'
        store = project.validate()
        marker = store.path('_Axis/Agents/' + session + '.md')
        killed = store.root / '_Axis/Agents' / (session + '.kill')
        if killed.exists() or killed.is_symlink():
            return 'fenced'
        lines = marker.read_text().splitlines()
        if len(lines) != 4 or lines[:3] != ['Main: session', '', 'session: ' + session] or not lines[3].startswith('host: ') or not lines[3][6:].strip():
            return 'unknown'
        age = time.time() - marker.stat().st_mtime
        if age < -5:
            return 'unknown'
        if age >= 3600:
            return 'expired'
        owner = store.path('_Axis/Flags/session-id').read_text().splitlines()
        if not owner or owner[0].strip() != session:
            return 'fenced'
        for other in (store.root / '_Axis/Agents').glob('*.md'):
            if other == marker:
                continue
            if other.is_symlink():
                return 'unknown'
            if other.read_text().splitlines()[:1] == ['Main: session'] and time.time() - other.stat().st_mtime < 3600 and not other.with_suffix('.kill').exists():
                return 'contested'
        return 'valid'
    except (OSError, ValueError, RuntimeError):
        return 'unknown'


class Adapter:
    """Syntax-preparing adapter; verifier is trusted runtime evidence, never document data.

    execute_start executes a separately reviewed startup plan. A deployment may
    supply a verifier for exact native runtime identity; CLI help cannot prove it.
    """
    def __init__(self, probe_result, verifier=None):
        self.probe = probe_result
        self.verifier = verifier

    def _same_executable(self, force=True):
        p = self.probe
        return (p.executable and p.executable_sha256 and Path(p.executable).is_file() and
                executable_identity(p.executable) == p.file_identity and
                (not force or file_digest(p.executable) == p.executable_sha256))

    def inspect(self, binding):
        try:
            binding.validate_shape()
            project = ProjectRef(binding.project, binding.root)
            project.validate()
            p = self.probe
            if (binding.adapter, binding.adapter_version, binding.executable, binding.executable_sha256) != (p.adapter, p.version, p.executable, p.executable_sha256) or not self._same_executable():
                raise ValueError('adapter executable or version changed')
            lease = lease_state(project, binding.axis_session)
            if lease != 'valid':
                return CapabilityResult('inspect', 'denied', 'Axis lease is ' + lease, {'lease': lease, 'runtime': 'unverified'})
            if self.verifier is None:
                return CapabilityResult('inspect', 'unverified', 'native identity/generation cannot be established by CLI help', {'lease': lease, 'runtime': 'unverified'})
            observation = self.verifier(binding)
            expected = asdict(binding)
            if not isinstance(observation, dict) or any(observation.get(k) != expected[k] for k in ('project', 'root', 'axis_session', 'native_handle', 'generation', 'adapter', 'adapter_version', 'executable', 'executable_sha256')):
                raise ValueError('runtime identity or generation mismatch')
            if observation.get('runtime') not in ('ready', 'busy', 'absent', 'starting', 'stopping', 'failed', 'unreachable'):
                raise ValueError('runtime state not verified')
            return CapabilityResult('inspect', 'verified', 'exact binding and current lease verified', {'lease': lease, 'runtime': observation['runtime'], 'binding': expected})
        except Exception as exc:
            return CapabilityResult('inspect', 'denied', str(exc))

    def start(self, project, model, *, store=None, authority=None, explicit=False, residency='on-demand', opted_in=False):
        try:
            target = project.validate()
            if not explicit or store is None or authority is None:
                raise ValueError('explicit action and source Main authority are required')
            store.require_main()
            placement = store.require_placement()
            store.guard()
            if lease_state(ProjectRef(store.project_id(), str(store.root)), store.session) != 'valid':
                raise ValueError('source Main lease is not valid')
            checked = store.validate_authority(authority)
            if authority.get('action') != 'session.start' or authority.get('target_project') != project.project or authority.get('target_root') != project.root:
                raise ValueError('authority does not name this exact startup action and project')
            if residency not in ('on-demand', 'warm', 'managed') or (residency != 'on-demand' and not opted_in):
                raise ValueError('warm/managed residency requires explicit opt-in')
            if residency != 'on-demand':
                return CapabilityResult('start', 'unsupported', 'persistent residency has no verified runtime integration; use on-demand')
            if store.project_id() == project.project:
                raise ValueError('source and target share a project UUID; copied placement is not activation')
            if target.root in store.root.parents:
                raise ValueError('a child cannot start its ancestor')
            if store.root in target.root.parents:
                nearest = next((p for p in target.root.parents if recognized(p)), None)
                if nearest != store.root:
                    raise ValueError('only a direct child may be started across a project boundary')
            if not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}', model):
                raise ValueError('an exact model name is required')
            if 'start' not in self.probe.syntax or not self._same_executable():
                return CapabilityResult('start', 'unavailable', 'installed CLI start syntax is unverified')
            # Never quietly create a second session when a Main may already exist.
            agents = target.root / '_Axis/Agents'
            for marker in agents.glob('*.md'):
                if marker.is_symlink():
                    raise ValueError('unsafe session marker')
                if marker.read_text().splitlines()[:1] == ['Main: session'] and time.time() - marker.stat().st_mtime < 3600 and not marker.with_suffix('.kill').exists():
                    raise ValueError('target has a live Main; inspect its exact binding')
            prompt = 'Read and follow AGENTS.md in this exact project root. Perform normal Axis session startup. Stop after the Ready greeting; do not execute queued work.'
            if self.probe.adapter == 'codex':
                argv = [self.probe.executable, 'exec', '--json', '--model', model, '--sandbox', 'workspace-write', '--cd', project.root, '-']
            else:
                argv = [self.probe.executable, '--print', '--output-format', 'json', '--model', model, '--permission-mode', 'manual', '--session-id', str(uuid.uuid4())]
            store.guard()
            return CapabilityResult('start', 'unverified', 'startup plan prepared; auth, included allowance and runtime handoff require verification before execution',
                                    {'model': model, 'argv': argv, 'stdin': prompt, 'cwd': project.root, 'project': project.project, 'authority': checked, 'residency': residency,
                                     'executed': False, 'normal_startup_required': True, 'syntax_verified': True, 'placement_activation': placement['activation']})
        except Exception as exc:
            return CapabilityResult('start', 'denied', str(exc))

    def _bound_operation(self, operation, binding):
        inspected = self.inspect(binding)
        if inspected.status != 'verified':
            return CapabilityResult(operation, inspected.status, inspected.reason, inspected.details)
        return CapabilityResult(operation, 'unsupported', 'no verified native ' + operation + ' transport; keep the immutable record queued', inspected.details)

    def attach(self, binding):
        return self._bound_operation('attach', binding)

    def notify(self, binding, message_id):
        if not SID.fullmatch(message_id):
            return CapabilityResult('notify', 'denied', 'notification must reference one exact immutable Message ID')
        return self._bound_operation('notify', binding)

    def pause(self, binding):
        return self._bound_operation('pause', binding)

    def stop(self, binding):
        return self._bound_operation('stop', binding)

    def resume(self, binding):
        return self._bound_operation('resume', binding)


def _message_rows(store):
    for item in store.records('Messages'):
        record = item.get('record', item) if isinstance(item, dict) else store.read('Messages', Path(item).stem)
        if record.get('data', {}).get('protocol') == 'axis.session/v1':
            load_core().validate_acceptance(record)
            if record['data'].get('stage') not in ('dispatch-intent', 'dispatch-result', 'dispatch-reconciled'):
                raise ValueError('unknown session control event')
        yield record


def _native_identity(adapter, raw, argv):
    text = raw.decode('utf-8', 'strict')
    if adapter == 'codex':
        events = [json.loads(line) for line in text.splitlines() if line.strip()]
        handles = [e.get('thread_id') for e in events if e.get('type') == 'thread.started']
        if len(handles) != 1 or not any(e.get('type') == 'turn.completed' for e in events) or any(e.get('type') in ('error', 'turn.failed') for e in events):
            raise ValueError('missing or ambiguous completed Codex thread identity')
        native = handles[0]
    else:
        event = json.loads(text)
        if not isinstance(event, dict) or event.get('is_error') is not False or event.get('type') != 'result':
            raise ValueError('invalid Claude result')
        native = event.get('session_id')
        if native != argv[argv.index('--session-id') + 1]:
            raise ValueError('Claude session identity differs from the requested UUID')
    if not isinstance(native, str) or str(uuid.UUID(native)) != native:
        raise ValueError('native identity is not an exact canonical UUID')
    return native


def _bounded_process(argv, cwd, prompt, seconds, max_output, check, *, launch_state=None, truncate_output=False, output_sink=None, on_launch=None):
    """Own one fresh process group; keep post-spawn failures as bounded evidence.

    PID and cleanup observations are diagnostics, never authority to signal a
    saved process. Only this invocation owns Popen and may signal its unreaped
    group. An exited, already-reaped leader grants no later signaling authority.
    External child reapers are unsupported; this invocation must own wait/poll.
    """
    import selectors
    import signal
    if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
        raise ValueError('cleanup requires default SIGCHLD disposition and sole child reaping ownership')
    check()
    streams = [bytearray(), bytearray()]
    output_truncated = False
    input_error = None
    reason = None
    sel = None
    cleanup_errors = []
    signals = []
    started = time.monotonic()
    if launch_state is not None:
        launch_state.update(attempted=True, spawned=False)
    proc = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, shell=False, start_new_session=True)
    if launch_state is not None:
        launch_state.update(spawned=True, pid=proc.pid, leader_reaped=False, diagnostic_only=True)
    try:
        if on_launch is not None:
            on_launch({'pid': proc.pid, 'launched': True, 'diagnostic_only': True})
        # All fallible setup after successful Popen belongs inside this boundary.
        sel = selectors.DefaultSelector()
        if seconds is None:
            # Native total-budget checks must also run while a child ignores input.
            pending_input = memoryview(prompt.encode('utf-8'))
            os.set_blocking(proc.stdin.fileno(), False)
            if pending_input:
                sel.register(proc.stdin, selectors.EVENT_WRITE, 2)
            else:
                proc.stdin.close()
        else:
            proc.stdin.write(prompt.encode('utf-8'))
            proc.stdin.close()
        for index, stream in enumerate((proc.stdout, proc.stderr)):
            os.set_blocking(stream.fileno(), False)
            sel.register(stream, selectors.EVENT_READ, index)
        while sel.get_map() or proc.poll() is None:
            try:
                check()
            except Exception as exc:
                reason = getattr(exc, 'process_reason', 'authority-or-lease-lost')
                break
            if seconds is not None and time.monotonic() - started >= seconds:
                reason = 'deadline-exceeded'
                break
            if not sel.get_map():
                time.sleep(.05 if seconds is None else min(.05, max(.001, seconds - (time.monotonic() - started))))
            for key, _ in sel.select(.1 if seconds is None else min(.1, max(.001, seconds - (time.monotonic() - started)))):
                if key.data == 2:
                    try:
                        sent = os.write(key.fileobj.fileno(), pending_input[:65536])
                    except BrokenPipeError:
                        # A rejected input stream must not discard available diagnostics.
                        sel.unregister(key.fileobj); proc.stdin.close()
                        pending_input = memoryview(b''); input_error = 'input-closed'
                        continue
                    pending_input = pending_input[sent:]
                    if not pending_input:
                        sel.unregister(key.fileobj)
                        proc.stdin.close()
                    continue
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    sel.unregister(key.fileobj)
                    continue
                room = max_output - sum(map(len, streams))
                captured = chunk[:max(0, room)]
                streams[key.data].extend(captured)
                if captured and output_sink is not None:
                    output_sink(('stdout', 'stderr')[key.data], captured)
                if len(chunk) > room:
                    output_truncated = True
                    if not truncate_output:
                        reason = 'output-limit-exceeded'
                        break
            if reason:
                break
        if reason is None:
            remaining = None if seconds is None else seconds - (time.monotonic() - started)
            try:
                proc.wait(timeout=None if remaining is None else max(.001, remaining))
                try: check()
                except Exception: reason = 'authority-or-lease-lost'
            except subprocess.TimeoutExpired:
                reason = 'deadline-exceeded'
        if reason is None and input_error is not None:
            reason = input_error
    except Exception as exc:
        reason = 'process-error:' + type(exc).__name__
    finally:
        cleanup_deadline = time.monotonic() + 2.0
        def failure(stage, exc):
            cleanup_errors.append({'stage': stage, 'type': type(exc).__name__,
                                   'errno': getattr(exc, 'errno', None)})
        # Do not poll here: poll could reap an exited leader while descendants
        # still hold its pipes. With sole Popen ownership, returncode=None keeps
        # the leader unreaped and its PID unavailable for reuse until we wait.
        if proc.returncode is None:
            for sig in (signal.SIGTERM, signal.SIGKILL):
                try:
                    os.killpg(proc.pid, sig)
                    signals.append({'signal': sig.name, 'outcome': 'sent'})
                except ProcessLookupError:
                    signals.append({'signal': sig.name, 'outcome': 'group-absent'})
                except Exception as exc:
                    failure(sig.name, exc)
                    signals.append({'signal': sig.name, 'outcome': 'error'})
                if sig == signal.SIGTERM:
                    # A bounded grace without poll/wait preserves group ownership
                    # even when the leader exits before a TERM-resistant child.
                    try: time.sleep(min(.1, max(0, cleanup_deadline - time.monotonic())))
                    except Exception as exc: failure('grace', exc)
            try:
                proc.wait(timeout=max(.001, cleanup_deadline - time.monotonic()))
            except Exception as exc:
                failure('wait', exc)
            # No group signals follow this observation/reap attempt.
            if proc.returncode is None:
                try: proc.poll()
                except Exception as exc: failure('poll', exc)
        if sel is not None:
            try: sel.close()
            except Exception as exc: failure('selector-close', exc)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            if stream is not None:
                try: stream.close()
                except Exception as exc: failure('stream-close', exc)
    reaped = proc.returncode is not None
    if not reaped:
        reason = reason or 'cleanup-unconfirmed'
    elif cleanup_errors:
        reason = reason or 'process-cleanup-error'
    process = {'pid': proc.pid, 'launched': True, 'leader_reaped': reaped,
               'group_stop_confirmed': False, 'signals': signals,
               'cleanup_errors': cleanup_errors, 'diagnostic_only': True}
    if launch_state is not None:
        launch_state.update(leader_reaped=reaped, process=process)
    return {'returncode': proc.returncode, 'reason': reason, 'stdout': bytes(streams[0]),
            'stderr': bytes(streams[1]), 'elapsed_seconds': time.monotonic() - started,
            'pid': proc.pid, 'process': process, 'output_truncated': output_truncated}


def execute_start(adapter, plan, *, store, authority, access, operation, explicit=False):
    """Execute one separately authorized startup plan; never retry an uncertain launch.

    `access` is a caller-verified, pinned observation of the included subscription,
    not a new authentication claim made by this helper. All budgets are conservative
    local launch/time/output bounds; subscription/currency enforcement remains external.
    """
    from contextlib import contextmanager
    intent = None
    local_result = None
    launch_state = {}
    lock = None
    owner = None
    try:
        if not explicit or not isinstance(plan, CapabilityResult) or plan.operation != 'start' or not plan.details.get('syntax_verified'):
            raise ValueError('an explicit reviewed startup plan is required')
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', operation):
            raise ValueError('invalid operation key')
        activation = plan.details.get('placement_activation')
        if not isinstance(activation, str) or not re.fullmatch(r'[0-9a-f]{32}', activation):
            raise ValueError('startup plan lacks exact placement activation')
        store.require_placement(expected=activation)
        store.require_history()
        p = adapter.probe
        model = plan.details['model']
        project = ProjectRef(plan.details['project'], plan.details['cwd'])
        if authority.get('adapter') != p.adapter or authority.get('model') != model:
            raise ValueError('authority must bind this exact adapter and model')
        limits = authority.get('limits', {})
        launches, seconds, output = limits.get('launches'), limits.get('seconds'), limits.get('output_bytes')
        if type(launches) is not int or not 1 <= launches <= 12 or not isinstance(seconds, (int, float)) or not 0 < seconds <= 3600 or type(output) is not int or not 1024 <= output <= 4 * 1024 * 1024:
            raise ValueError('missing or invalid launch/time/output budgets')
        budget = authority.get('budget')
        if not isinstance(budget, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:-]{0,127}', budget):
            raise ValueError('a shared authority budget key is required')
        if access.get('adapter') != p.adapter or access.get('model') != model or access.get('executable_sha256') != p.executable_sha256 or access.get('mode') != 'included-subscription' or access.get('auth_verified') is not True:
            raise ValueError('exact included-subscription access has not been verified')
        when, remaining, reserve = access.get('verified_at'), access.get('remaining_fraction'), access.get('reserve_fraction')
        if not isinstance(when, (int, float)) or not 0 <= time.time() - when <= 900 or not isinstance(remaining, (int, float)) or not isinstance(reserve, (int, float)) or not .2 <= reserve < remaining <= 1:
            raise ValueError('fresh allowance evidence above the minimum 20% reserve is required')
        store.validate_authority(access.get('authority', {}))
        # No credential values are inspected, copied or logged. Refuse API/cloud
        # auth selectors instead of silently falling back from an included account.
        forbidden = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'ANTHROPIC_API_KEY', 'ANTHROPIC_AUTH_TOKEN',
                     'CLAUDE_CODE_USE_BEDROCK', 'CLAUDE_CODE_USE_VERTEX', 'CLAUDE_CODE_USE_FOUNDRY')
        if any(key in os.environ for key in forbidden):
            raise ValueError('API/cloud authentication selectors present; no substitution allowed')
        fresh = adapter.start(project, model, store=store, authority=authority, explicit=True)
        if not fresh.details.get('syntax_verified'):
            raise ValueError(fresh.reason)
        # Rebuild fixed arguments, not user-edited argv. Claude's reserved UUID is
        # the only generated value carried across the review boundary.
        expected = list(fresh.details['argv'])
        if p.adapter == 'claude':
            ix = expected.index('--session-id') + 1
            native = plan.details['argv'][ix]
            if str(uuid.UUID(native)) != native:
                raise ValueError('invalid reserved Claude session')
            expected[ix] = native
        if plan.details['argv'] != expected or plan.details['stdin'] != fresh.details['stdin']:
            raise ValueError('startup plan changed')
        target = project.validate()
        original_markers = {f.name for f in (target.root / '_Axis/Agents').glob('*.md')}
        store.require_main()
        store.guard()
        if store.storage_profile() != 'atomic':
            raise ValueError('automatic launch storage is unqualified; use manual startup')
        lock = store.root / '_Axis/Flags/session-adapter-dispatch.lock'
        if lock.is_symlink():
            raise ValueError('unsafe adapter lock')
        lock.mkdir()
        owner = {'session': str(getattr(store, 'session', '')), 'nonce': uuid.uuid4().hex}
        with (lock / 'OWNER').open('x') as f:
            json.dump(owner, f)
        rows = [r for r in _message_rows(store) if r.get('data', {}).get('protocol') == 'axis.session/v1']
        intents = [r for r in rows if r['data'].get('stage') == 'dispatch-intent']
        if any(r['data'].get('operation') == operation for r in intents):
            raise ValueError('operation already dispatched or uncertain; reconcile retained records')
        if sum(r['data'].get('budget') == budget for r in intents) >= launches:
            raise ValueError('shared launch budget exhausted')
        outcomes = {}
        for row in rows:
            data = row['data']
            if data.get('stage') in ('dispatch-result', 'dispatch-reconciled'):
                origin = next((r for r in intents if r['id'] == data.get('intent')), None)
                if origin is None or data.get('operation') != origin['data']['operation']:
                    raise ValueError('session outcome does not match a dispatch intent')
                key = (data['intent'], data['stage'])
                if key in outcomes:
                    raise ValueError('divergent session outcome records')
                outcomes[key] = data
        completed = {ident for (ident, stage), data in outcomes.items()
                     if (stage == 'dispatch-result' and data.get('status') == 'completed') or
                     (stage == 'dispatch-reconciled' and data.get('outcome') in ('not-started', 'completed', 'stopped') and data.get('evidence'))}
        if any(r['id'] not in completed for r in intents):
            raise ValueError('another launch is active or uncertain; concurrency is one')
        record = store.message('control', 'Main', 'Authorized normal session startup intent; no queued work is authorized.', correlation=operation,
                               data={'protocol': 'axis.session/v1', 'stage': 'dispatch-intent', 'operation': operation, 'budget': budget,
                                     'adapter': p.adapter, 'model': model, 'project': project.project, 'root': project.root,
                                     'executable': p.executable, 'executable_sha256': p.executable_sha256, 'generation': owner['nonce'],
                                     'authority': store.validate_authority(authority), 'limits': limits})
        intent = record.get('record', record)
        # Release short admission lock before the long subprocess. The immutable
        # intent reserves the sole concurrent slot, including after a crash.
        (lock / 'OWNER').unlink()
        lock.rmdir()
        lock = None
        def check():
            store.require_placement(expected=activation)
            store.require_main()
            store.guard()
            store.validate_authority(authority)
            store.validate_authority(access['authority'])
            if lease_state(ProjectRef(store.project_id(), str(store.root)), store.session) != 'valid':
                raise ValueError('source Main lease expired or changed')
            project.validate()
            if not adapter._same_executable(force=False):
                raise ValueError('executable changed')
        # Repeat startup preconditions at the dispatch boundary after intent commit.
        gate = adapter.start(project, model, store=store, authority=authority, explicit=True)
        if not gate.details.get('syntax_verified'):
            raise ValueError(gate.reason)
        check()
        outputs = store.path('_Axis/Messages/' + intent['id'], missing=True, kind='directory')
        if outputs.is_symlink() or outputs.parent.is_symlink():
            raise ValueError('unsafe output directory')
        outputs.mkdir(exist_ok=True)
        local_result = _bounded_process(expected, project.root, plan.details['stdin'], seconds, output, check, launch_state=launch_state)
        paths = {}
        for name in ('stdout', 'stderr'):
            path = outputs / (name + '.txt')
            with path.open('xb') as f:
                f.write(local_result[name])
                f.flush()
                os.fsync(f.fileno())
            paths[name] = {'path': str(path.relative_to(store.root)), 'sha256': hashlib.sha256(local_result[name]).hexdigest(), 'size': len(local_result[name])}
        status = 'needs-reconciliation'
        binding = None
        reason = local_result['reason'] or ('provider-exit-' + str(local_result['returncode']))
        if local_result['reason'] is None and local_result['returncode'] == 0:
            try:
                native = _native_identity(p.adapter, local_result['stdout'], expected)
                owner_session = target.path('_Axis/Flags/session-id').read_text().splitlines()[0].strip()
                if owner_session + '.md' in original_markers or lease_state(project, owner_session) != 'valid':
                    raise ValueError('normal startup did not create one new valid Axis Main lease')
                binding = SessionBinding(project.project, project.root, owner_session, native, intent['data']['generation'],
                                         p.adapter, p.version, p.executable, p.executable_sha256, time.time(), observed_runtime='absent')
                binding.validate_shape()
                status, reason = 'completed', 'startup completed; provider process exited, exact native context retained'
            except Exception as exc:
                reason = str(exc)
        result_data = {'protocol': 'axis.session/v1', 'stage': 'dispatch-result', 'operation': operation, 'intent': intent['id'],
                       'status': status, 'reason': reason, 'returncode': local_result['returncode'], 'outputs': paths,
                       'elapsed_seconds': local_result['elapsed_seconds'], 'binding': asdict(binding) if binding else None,
                       'process': local_result['process'],
                       'currency_enforcement': 'unverified; caller retains included-allowance responsibility'}
        # Save a local recovery receipt first. If source authority was lost, retain
        # bounded evidence without claiming an authoritative accepted result.
        recovery = outputs / 'result.md'
        with recovery.open('x') as f:
            f.write(load_record_format().render('Session dispatch recovery', result_data))
            f.flush()
            os.fsync(f.fileno())
        check()
        store.message('result', 'Main', 'Session startup result; inspect retained evidence before further work.', correlation=operation, data=result_data)
        return CapabilityResult('start', status, reason, result_data)
    except Exception as exc:
        error_details = {'intent': intent['id'] if intent else None, 'executed': local_result is not None or launch_state.get('spawned', False),
                         'manual_reconciliation_required': intent is not None,
                         'process': dict(launch_state)}
        if intent:
            try:
                outputs = store.path('_Axis/Messages/' + intent['id'], missing=True, kind='directory')
                if outputs.is_symlink() or outputs.parent.is_symlink():
                    raise ValueError('unsafe local recovery path')
                outputs.mkdir(exist_ok=True)
                path = outputs / 'error.md'
                with path.open('x') as stream:
                    stream.write(load_record_format().render('Session dispatch needs reconciliation', {'status': 'needs-reconciliation', 'reason': str(exc), **error_details}))
                    stream.flush()
                    os.fsync(stream.fileno())
                error_details['local_error'] = str(path.relative_to(store.root))
            except Exception:
                error_details['error_retention'] = 'unavailable; immutable intent remains unresolved'
        return CapabilityResult('start', 'needs-reconciliation' if intent else 'denied', str(exc), error_details)
    finally:
        if lock is not None and owner is not None:
            try:
                if not lock.is_symlink() and json.loads((lock / 'OWNER').read_text()) == owner:
                    (lock / 'OWNER').unlink()
                    lock.rmdir()
            except (OSError, ValueError):
                pass


def reconcile_start(store, intent_id, *, outcome, evidence, explicit=False):
    """Record a Main-validated external outcome; this never repeats provider work."""
    if not explicit or outcome not in ('not-started', 'completed', 'stopped'):
        raise ValueError('explicit observed startup outcome required')
    store.require_main(); store.guard()
    original = store.read('Messages', intent_id)
    load_core().validate_acceptance(original)
    data = original.get('data', {})
    if data.get('protocol') != 'axis.session/v1' or data.get('stage') != 'dispatch-intent':
        raise ValueError('not a startup dispatch intent')
    pin = store.validate_authority(evidence)
    previous = [r for r in _message_rows(store) if r.get('data', {}).get('stage') == 'dispatch-reconciled' and r['data'].get('intent') == intent_id]
    expected = {'protocol': 'axis.session/v1', 'stage': 'dispatch-reconciled', 'intent': intent_id,
                'operation': data['operation'], 'outcome': outcome, 'evidence': pin}
    if previous:
        if len(previous) != 1 or previous[0]['data'] != expected:
            raise ValueError('conflicting startup reconciliation')
        return previous[0]
    result = store.message('validation', 'Main', 'Main verified the startup outcome; no action replayed.', correlation=data['operation'], data=expected)
    return result.get('record', result)


def inventory(roots):
    rows = []
    core = load_core()
    seen = {}
    for value in roots:
        try:
            root = exact_root(value)
            if not recognized(root):
                raise ValueError('incomplete project anchors')
            store = core.Store(root)
            project = store.project_id()
            if project in seen and seen[project] != str(root):
                raise ValueError('copied project UUID also exists at ' + seen[project])
            seen[project] = str(root)
            sessions = []
            for marker in sorted((root / '_Axis/Agents').glob('*.md')):
                if SID.fullmatch(marker.stem):
                    sessions.append({'session': marker.stem, 'lease': lease_state(ProjectRef(project, str(root)), marker.stem)})
            rows.append({'root': str(root), 'project': project, 'sessions': sessions, 'runtime': 'unverified'})
        except Exception as exc:
            rows.append({'root': str(value), 'status': 'held', 'reason': str(exc)})
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description='Optional Axis inventory and explicit bounded normal startup')
    parser.add_argument('command', choices=('ls', 'projects', 'status', 'probe', 'start'))
    parser.add_argument('roots', nargs='*', help='exact absolute canonical project paths; no aliases or discovery')
    parser.add_argument('--adapter', choices=('codex', 'claude', 'openclaw'), default='codex')
    parser.add_argument('--model')
    parser.add_argument('--source-root')
    parser.add_argument('--session')
    parser.add_argument('--authority', help='source-project relative JSON containing an explicitly scoped authority pin')
    parser.add_argument('--explicit-start', action='store_true')
    parser.add_argument('--execute', action='store_true', help='execute the explicit startup after all verification gates')
    parser.add_argument('--access-evidence', help='source-relative pinned JSON access/allowance observation')
    parser.add_argument('--operation', dest='operation_key', help='unique startup operation key')
    args = parser.parse_args(argv)
    try:
        if args.execute and (args.command != 'start' or not args.operation_key or not args.access_evidence):
            raise ValueError('execution requires start, pinned access evidence and a unique operation key')
        if args.command == 'probe':
            result = asdict(probe(args.adapter))
        elif args.command in ('ls', 'projects', 'status'):
            result = inventory(args.roots or [str(Path.cwd().resolve())])
        else:
            if len(args.roots) != 1 or not args.source_root or not args.session or not args.authority:
                raise ValueError('start requires one exact target path, source root/session and authority; no model will be launched')
            core = load_core()
            source = core.Store(exact_root(args.source_root), session=args.session)
            authority = json.loads(source.path(args.authority).read_text())
            root = exact_root(args.roots[0])
            project = ProjectRef(core.Store(root).project_id(), str(root))
            adapter = Adapter(probe(args.adapter))
            plan = adapter.start(project, args.model, store=source, authority=authority, explicit=args.explicit_start)
            if args.execute:
                if not args.access_evidence or not args.operation_key:
                    raise ValueError('execution requires pinned access evidence and a unique operation key')
                access = json.loads(source.path(args.access_evidence).read_text())
                result = execute_start(adapter, plan, store=source, authority=authority, access=access, operation=args.operation_key, explicit=args.explicit_start).to_dict()
            else:
                result = plan.to_dict()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        print(json.dumps({'status': 'held', 'reason': str(exc), 'manual': MANUAL}, sort_keys=True))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
