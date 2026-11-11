"""Conditional checked-session completion primitives; not a save-policy engine.

Imported only for an explicitly granted completion operation. Main still performs
ordinary save assessment, semantic review, checkpoint and send duties. No shell,
arbitrary path, overwrite-record, lease restoration or policy mutation operation.
"""
import datetime as dt
import hashlib
import os
from pathlib import Path
import re
import secrets
import time

# BEGIN GENERATED: role-table
# Compiled from _Axis/Roles/ at release; edit the role files, never this region.
ROLE_TABLE=(
    {'name': 'Main', 'cls': 'session', 'subject': 'Main: session', 'match': 'exact', 'shape': 'exact4', 'created_by': 'claim', 'exclusive': True, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': None, 'survey_key': None, 'notice': None, 'issuer': 'main', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Main', 'log_by': 'Main Agent', 'title': 'Main Agent', 'plural': 'Main Agents', 'article': 'the', 'serves': 'User', 'families': 'all', 'recovery': ('@core', '@role', '_Axis/INSTRUCTIONS.md', '_Axis/MINDSET.md', '_Axis/DIRECTIVES.md', '@overlay', '@state')},
    {'name': 'Auxiliary', 'cls': 'session', 'subject': 'Auxiliary: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'helper', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_auxiliary', 'notice': 'An Auxiliary Agent is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': True, 'proposal_issuer': 'auxiliary', 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'externalAgents', 'flag': '--external', 'block_spawn': True, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'Auxiliary', 'log_by': 'Auxiliary Agent', 'title': 'Auxiliary Agent', 'plural': 'Auxiliary Agents', 'article': 'an', 'serves': 'User', 'families': ('Ideas', 'Logs', 'Notes'), 'recovery': ('@core', '@role', '_Axis/Practices/Agents.md > Auxiliary Agent', '@state')},
    {'name': 'Assistant', 'cls': 'session', 'subject': 'Assistant: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'helper', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_assistant', 'notice': 'An Assistant is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'assistantAgents', 'flag': None, 'block_spawn': False, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'Assistant', 'log_by': 'Assistant', 'title': 'Assistant', 'plural': 'Assistants', 'article': 'an', 'serves': 'User', 'families': ('Ideas', 'Logs', 'Notes'), 'recovery': ('@core', '@role', '@state')},
    {'name': 'GroupAgent', 'cls': 'session', 'subject': 'Group Agent: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'helper', 'exclusive': False, 'version_bound': True, 'reply_frame': True, 'blocks_save': False, 'survey': 'list', 'survey_key': 'fresh_groupagent', 'notice': 'A Group Agent is serving this project ({id}).', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': 'axis.external-submission/v1', 'guard': {'config_key': 'groupAgents', 'flag': None, 'block_spawn': True, 'new_files': ('subfolders', '_Axis/Submissions/', '_Temp/')}, 'reference_word': 'GroupAgent', 'log_by': 'Group Agent', 'title': 'Group Agent', 'plural': 'Group Agents', 'article': 'a', 'serves': 'User and named participants', 'families': ('Ideas', 'Logs', 'Notes'), 'recovery': ('@core', '@role', '@state')},
    {'name': 'Observer', 'cls': 'session', 'subject': 'Observer: ', 'match': 'prefix', 'shape': 'single-session-line', 'created_by': 'none', 'exclusive': False, 'version_bound': False, 'reply_frame': True, 'blocks_save': False, 'survey': None, 'survey_key': None, 'notice': None, 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': {'config_key': 'observerAgents', 'flag': None, 'block_spawn': True, 'new_files': ()}, 'reference_word': 'Observer', 'log_by': None, 'title': 'Observer', 'plural': 'Observers', 'article': 'an', 'serves': 'anyone on the surface', 'families': (), 'recovery': ('@core', '@role')},
    {'name': 'Subagent', 'cls': 'session', 'subject': 'Subagent: ', 'match': 'prefix', 'shape': 'free', 'created_by': 'spawner', 'exclusive': False, 'version_bound': False, 'reply_frame': False, 'blocks_save': True, 'survey': 'count', 'survey_key': 'orphan_subagents', 'notice': '{count} orphaned Subagent record(s) from a crashed spawn; ^refresh can clear them', 'issuer': 'worker', 'proposal_owner': False, 'proposal_issuer': None, 'submit_schema': None, 'guard': None, 'reference_word': 'Subagent', 'log_by': None, 'title': 'Subagent', 'plural': 'Subagents', 'article': 'a', 'serves': 'spawner', 'families': 'delegated', 'recovery': None},
    {'name': 'CX', 'cls': 'delegated', 'token': 'CX', 'carries_blocks': True, 'agent_type': 'axis-cx', 'write_scope': (('_Axis/CX/', True), ('_Temp/', False)), 'deny': None},
    {'name': 'Wiki', 'cls': 'delegated', 'token': 'WIKI', 'carries_blocks': True, 'agent_type': 'axis-wiki', 'write_scope': (('_Wiki/', False), ('_Axis/Wiki/', False), ('_Temp/', False)), 'deny': None},
    {'name': 'Local', 'cls': 'delegated', 'token': 'LOCAL', 'carries_blocks': False, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'General', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': 'axis-general', 'write_scope': None, 'deny': ('_Axis/Agents/', '_Axis/Flags/', '_Axis/Secrets/', '_Axis/Submissions/', '_Axis/Messages/', '_Axis/Teams/', '_Axis/Jobs/', '_Axis/Schedules/', '_Axis/Updates/', '.git/', '.claude/', '.codex/', '.gemini/')},
    {'name': 'Lookup', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': 'axis-lookup', 'write_scope': (), 'deny': None},
    {'name': 'Worker', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'TeamMember', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': None, 'write_scope': None, 'deny': None},
    {'name': 'TeamLeader', 'cls': 'delegated', 'token': 'GENERAL', 'carries_blocks': True, 'agent_type': None, 'write_scope': None, 'deny': None},
)
ROLE_LEDGER={'issuers': ('auxiliary', 'external', 'main', 'worker'), 'submission_schemas': ('axis.external-submission/v1',), 'proposal_member_subject': 'Subagent: External proposal Team', 'survey_keys': ('fresh_assistant', 'fresh_auxiliary', 'fresh_external', 'fresh_groupagent', 'orphan_subagents'), 'proposal_owners': (('External:', 'external'), ('Auxiliary:', 'auxiliary'))}
# END GENERATED: role-table
# Fresh Markers of these roles hold an ordinary save until they return.
SAVE_BLOCKING = tuple(r['subject'].rstrip() for r in ROLE_TABLE if r['cls'] == 'session' and r['blocks_save'])

HEADER = '---------------------------\n A X I S   W O R K F L O W\n---------------------------'
INDEX = '_Axis/SNAPSHOTS.md'


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


class Lifecycle:
    def __init__(self, broker, require):
        self.b, self.io, self.need = broker, broker.io, require
        self.reviewed = {}
        self.save_started = False

    def atomic_storage(self):
        self.need(self.io.setting('Storage Policy') == 'auto', 'storage-policy')
        for name, value in (('host-storage', 'atomic'), ('host-cloud-sync', 'no')):
            rows = self.io.read('_Axis/Flags/' + name).splitlines()
            self.need(len(rows) == 2 and rows[0] == value, 'storage-profile')
            when = self.b.start.parse_stamp(rows[1])
            self.need(self.b.start.parse_stamp(self.io.sid) <= when <= dt.datetime.now(dt.timezone.utc), 'storage-profile')

    def acquire(self, relative):
        self.atomic_storage()
        self.b.guard()
        path = self.io.path(relative, missing=True, kind='directory')
        os.mkdir(path)  # Contention refuses; never reclaim or move another lock.
        identity = self.b.start.identity(path.stat())
        token = secrets.token_hex(16) + '\n' + self.io.sid + '\n'
        fd = os.open(self.io.path(relative + '/OWNER', missing=True), os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        try:
            self.b.start.write_fd(fd, token.encode())
            os.fsync(fd)
            self.need(self.b.start.read_fd(fd, 'lock-owner').decode() == token, 'lock-owner')
        finally:
            os.close(fd)
        lease = (relative, identity, token, time.monotonic())
        self.owned(lease)
        return lease

    def owned(self, lease):
        relative, identity, token, started = lease
        self.need(time.monotonic() - started < 10, 'lock-expired')
        self.need(self.b.start.identity(self.io.path(relative, kind='directory').stat()) == identity, 'lock-replaced')
        self.need(self.io.read(relative + '/OWNER') == token, 'lock-owner')

    def release(self, lease):
        self.owned(lease)
        relative = lease[0]
        os.unlink(self.io.path(relative + '/OWNER'))
        os.rmdir(self.io.path(relative, kind='directory'))

    def read_created_record(self, id):
        self.need(isinstance(id, str) and id in self.b.created, 'record-scope')
        record = self.b.created[id]
        text = self.io.read(record['path'])
        self.need(digest(text) == record['sha256'], 'record-changed')
        self.b.guard()
        return {'id': id, 'path': record['path'], 'content': text, 'sha256': digest(text)}

    def save_tracking(self, kind, text):
        self.need(self.save_started and kind in ('STATUS', 'DONE'), 'save-tracking')
        self.need(isinstance(text, str) and text.strip() and len(text.encode()) <= 4096 and all(ord(c) >= 32 for c in text), 'save-tracking')
        if self.io.setting('Tracking') == 'off':
            return {'status': 'disabled-by-setting'}
        self.io.track(kind, '^save', text)
        return {'status': 'appended', 'kind': kind, 'scope': '^save'}

    def begin_save(self, during_shutdown):
        self.need(type(during_shutdown) is bool, 'shutdown-mode')
        self.need(not during_shutdown or self.b.allow_shutdown, 'shutdown-scope')
        self.b.local_history()
        agents = list(self.io.path('_Axis/Agents', kind='directory').glob('*.md'))
        self.need(len(agents) <= 1000, 'agent-bound')
        running = 0
        for path in agents:
            name = path.relative_to(self.io.root).as_posix()
            text = self.io.read(name)
            if text.startswith(SAVE_BLOCKING) and not self.io.exists(name[:-3] + '.kill') and time.time() - path.stat().st_mtime < 3600:
                running += 1
        self.need(during_shutdown or not running, 'running-subagents')
        # The ordinary save refresh may not replace somebody else's identity.
        name = '_Axis/Flags/session-id'
        previous = self.io.read(name)
        rows = previous.splitlines()
        self.need(len(rows) == 2 and rows[0] == self.io.sid, 'identity-owner')
        previous_time = self.b.start.parse_stamp(rows[1])
        self.need(self.b.start.parse_stamp(self.io.sid) <= previous_time <= dt.datetime.now(dt.timezone.utc), 'identity-time')
        versions = re.findall(r'^current-version: (\S+)$', self.metadata('_Axis/CHANGELOG.md', limit=4194304), re.M)
        version = versions[0] if len(versions) == 1 else 'Unknown'
        fence = self.acquire('_Axis/Flags/starting.lock')
        try:
            self.b.guard()
            self.need(self.io.read(name) == previous, 'identity-changed')
            if self.io.setting('Tracking') != 'off':
                self.io.track('INTENT', '^save', 'Begin ordinary save through checked operations; assessment and checkpoint remain required.')
            self.save_started = True
            self.io.renew(self.io.marker_name, self.io.marker_body())
            stamp = self.b.start.stamp()
            self.owned(fence)
            self.need(self.io.read(name) == previous, 'identity-changed')
            self.io.write_flag('session-id', self.io.sid + '\n' + stamp + '\n')
            self.need(self.io.read(name) == self.io.sid + '\n' + stamp + '\n', 'identity-readback')
        finally:
            self.release(fence)
        return {'status': 'save-step1-complete', 'session': self.io.sid, 'refreshed_at': stamp,
                'folder': self.folder(), 'axis_version': version, 'running_subagents': running,
                'save_complete': False, 'remaining': 'Perform every other applicable save assessment, Snapshot, index, checkpoint and reporting step.'}

    def own_snapshot(self, id):
        self.need(isinstance(id, str) and id in self.b.created, 'snapshot-scope')
        record = self.b.created[id]
        self.need(record['family'] == 'Snapshots', 'snapshot-scope')
        text = self.io.read(record['path'])
        self.need(digest(text) == record['sha256'], 'snapshot-changed')
        return text

    def review_snapshot(self, id):
        text = self.own_snapshot(id)
        index = self.io.read(INDEX)
        self.b.guard()
        hashes = (digest(text), digest(index))
        self.reviewed[id] = hashes
        return {'id': id, 'content': text, 'sha256': hashes[0], 'index_sha256': hashes[1],
                'review_required': 'Main must check content, Continuity, exact queues and all ordinary save duties before indexing.'}

    def index_snapshot(self, id, record_sha256, index_sha256, summary):
        self.need(id in self.reviewed and self.reviewed[id] == (record_sha256, index_sha256), 'review-required')
        self.need(isinstance(summary, str) and summary == summary.strip() and 0 < len(summary.split()) < 200
                  and len(summary.encode()) <= 4096 and not any(ord(c) < 32 for c in summary), 'summary')
        self.need(not re.search(r'(^#|\]\(|<|>)', summary), 'summary-markup')
        self.own_snapshot(id)
        original = self.io.read(INDEX)
        self.need(digest(original) == index_sha256, 'index-changed')
        self.need(not re.search(r'^##\s+' + re.escape(id) + r'\s*$', original, re.M), 'already-indexed')
        for flag in ('update-pending', 'starting'):
            value = self.io.read('_Axis/Flags/' + flag, optional=True)
            self.need(value is None or value.splitlines()[:1] in ([], ['cleared']), 'lifecycle-pending')
        separator = '' if original.endswith('\n\n') else ('\n' if original.endswith('\n') else '\n\n')
        updated = original + separator + '## ' + id + '\n\n' + summary + '\n\n[Details...](Snapshots/' + id + '.md)\n'
        self.need(len(updated.encode()) <= 65536, 'index-size')
        lease = self.acquire(INDEX + '.lock')
        try:
            self.own_snapshot(id)
            self.need(self.io.read(INDEX) == original, 'index-changed')
            temporary = INDEX + '.' + secrets.token_hex(12) + '.tmp'
            path = self.io.path(temporary, missing=True)
            fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
            try:
                self.b.start.write_fd(fd, updated.encode())
                os.fsync(fd)
                self.need(self.b.start.read_fd(fd, 'index-staging').decode() == updated, 'index-readback')
            finally:
                os.close(fd)
            self.owned(lease)
            self.b.guard()
            self.own_snapshot(id)
            self.need(self.io.read(INDEX) == original, 'index-changed')
            self.b.start.replace_shared(path, self.io.path(INDEX))
            self.need(self.io.read(INDEX) == updated, 'index-readback')
            self.b.guard()
        finally:
            self.release(lease)  # Replaced or expired ownership is deliberately retained.
        return {'status': 'indexed', 'id': id, 'index_sha256': digest(updated),
                'save_complete': False, 'remaining': 'Ordinary save assessment, checkpoint and reporting duties still apply.'}

    def folder(self):
        home = Path.home()
        root = self.io.root
        return '~/' + str(root.relative_to(home)) if root != home and root.is_relative_to(home) else ('~' if root == home else str(root))

    def format_response(self, body, background_tasks_running):
        self.need(isinstance(body, str) and 0 < len(body.encode()) <= 48000 and body == body.strip(), 'response-body')
        self.need(type(background_tasks_running) is bool, 'background-status')
        self.need(not re.search(r'(?m)^\s*>?\s*READY\b', body) and HEADER not in body, 'duplicate-frame')
        self.need(not any(ord(c) < 32 and c not in '\n\t' for c in body), 'response-body')
        self.b.guard()
        suffix = ' (background tasks running)' if background_tasks_running else ''
        return {'text': HEADER + '\n\n' + body + '\n\n> READY ' + self.folder() + suffix + ':',
                'relay': 'Return text verbatim as the final application response; no additional frame.'}

    def metadata(self, name, limit=65536):
        try:
            return self.io.read(name, limit=limit)
        except (OSError, UnicodeError, self.b.start.Fault):
            return ''  # Missing/unsafe display metadata never grants access or blocks own retirement.

    def stopped_presentation(self):
        match = re.match(r'# Project: (.+)', self.metadata('_Axis/PROJECT.md'))
        title = match.group(1).strip() if match else 'Not set'
        title = title if title and '{{' not in title and all(ord(c) >= 32 for c in title) else 'Not set'
        versions = re.findall(r'^current-version: (\S+)$', self.metadata('_Axis/CHANGELOG.md', limit=4194304), re.M)
        version = versions[0] if len(versions) == 1 else 'Unavailable'
        context = 'Two-pass' if self.io.setting('Context Management') == 'Two-Pass' else 'Default'
        return HEADER + '\n\n' + '\n'.join(('  Project:  ' + title, '  Folder:   ' + self.folder(), '  Session:  ' + self.io.sid,
                '  Version:  ' + version, '  Context:  ' + context, '  Status:   Stopped', '  Agent:    Main')) + '\n---------------------------\n\nThis session has stopped. Start a new session to continue.'

    def retire_session(self):
        # A distinct fixed launcher grant represents explicit shutdown authority.
        # Hold the existing admission directory through identity handback so a new
        # startup cannot be admitted between our Marker deletion and flag update.
        presentation = self.stopped_presentation()
        self.b.local_history()
        fence = self.acquire('_Axis/Flags/starting.lock')
        stopped = False
        shutdown_log = None
        try:
            self.b.guard()
            if self.io.setting('Tracking') != 'off':
                self.io.track('INTENT', 'shutdown', 'Complete explicitly authorized own-session retirement.')
            _, shutdown_log = self.io.record('Logs', lambda _: 'Shutdown by User\n\nby: Main Agent\nsession: ' + self.io.sid + '\n\nExplicit checked shutdown grant; ordinary save outcome is recorded separately.\n')
            if self.io.setting('Tracking') != 'off':
                self.io.track('DONE', 'shutdown', 'shutdown - stopping')
            self.owned(fence)
            self.b.guard()
            marker = self.io.path(self.io.marker_name)
            self.need(self.b.start.identity(marker.stat()) == self.io.lease[1], 'marker-changed')
            os.unlink(marker)
            stopped = True
            # The only project-state write permitted after retirement is identity
            # handback; ownership-fence cleanup is part of that same operation.
            name = '_Axis/Flags/session-id'
            prior = self.io.read(name, optional=True)
            if prior is not None and prior.splitlines()[:1] == [self.io.sid]:
                foreign = self.io.foreign_mains()
                target = foreign[0]['session'] if foreign else 'cleared'
                value = target + '\n' + self.b.start.stamp() + '\n'
                temporary = name + '.' + secrets.token_hex(12) + '.tmp'
                fd = os.open(self.io.path(temporary, missing=True), os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
                try:
                    self.b.start.write_fd(fd, value.encode())
                    os.fsync(fd)
                finally:
                    os.close(fd)
                self.owned(fence)
                self.need(self.io.read(name, optional=True) == prior, 'identity-changed')
                self.b.start.replace_shared(self.io.path(temporary), self.io.path(name))
                self.need(self.io.read(name) == value, 'identity-readback')
            self.release(fence)
            return {'status': 'stopped', 'shutdown_log': shutdown_log, 'identity_handback': 'verified', 'presentation': presentation,
                    'next': 'No further ordinary work or file writes in this conversation. Point User to a new session.'}
        except Exception:
            if stopped:
                # Never imply an already-deleted Marker is live or retry by making
                # ordinary records. Keep uncertain state/fence for explicit recovery.
                return {'status': 'stopped', 'shutdown_log': shutdown_log, 'identity_handback': 'unverified', 'presentation': presentation,
                        'next': 'Session stopped; identity cleanup requires quiescent recovery. No ordinary writes.'}
            self.release(fence)
            raise
