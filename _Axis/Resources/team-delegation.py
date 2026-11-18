#!/usr/bin/env python3
"""Sponsor-controlled nested Teams inside one Main-accepted Team grant. Standard library only.

coordination.py loads this file on first need: a charter `delegation` grant, a delegated record or a sponsor
call. A sponsor is the session currently bound to a slot that its Team's accepted grant names. It writes as
itself, and every record it writes carries `delegated_control`: its parent Team, slot, session, epoch and head,
the grant digest, the live placement and its depth. That is local acceptance. It is never Main acceptance or
project integration, and like every snapshot here it is provenance, not authentication.

A change to a grant or to a sponsoring seat is complete only once it is fenced: every Team beneath the change
has passed its own control lock once since the change was published. Until then nothing new starts beneath
it; stopping, reconciling and accounting stay available.

No provider is called and no process is started here. No lock is held across model work.
"""
import contextlib
import copy
import os
import time

C = None  # live view of the coordination module that loaded this file

# Controls that only stop, reconcile or account. They stay available after a grant is revoked or frozen.
SAFE = frozenset({'cancel', 'pause', 'boundary', 'checkpoint', 'expire', 'reconcile', 'charge', 'budget_hold', 'route_boundary'})
# What Main or an ancestor sponsor may do to a descendant it does not directly sponsor: supervise, never accept.
SUPERVISORY = {'Teams': frozenset({'pause', 'resume', 'cancel', 'fail', 'checkpoint', 'budget_hold'}),
               'Jobs': frozenset({'pause', 'resume', 'cancel', 'fail', 'expire', 'boundary', 'reconcile', 'checkpoint',
                                  'charge', 'budget_hold', 'uncertain', 'attempt_failed'})}
RESERVED_SLOTS = frozenset({'main', 'owner', 'sponsor', 'team'})
MEMBER_SUBJECT = None  # set by bind() from the coordination role table's spawned-helper subject
GRANT_KEYS = {'version', 'depth', 'sponsors', 'actions', 'scope', 'purpose'}
FENCE_KEYS = {'team', 'through', 'changes', 'drained', 'expired_holders'}
DRAIN_WAIT = 2            # seconds to wait for one Team's lock when a change is fenced in the same call
FENCE_WAIT_CEILING = 15   # bounded wait per Team; elapsed time never proves that its writer stopped
LEASE_RENEW_AFTER = 1800  # seconds; the same threshold checked member tools use


class _Core:
    def __init__(self, namespace): object.__setattr__(self, '_namespace', namespace)

    def __getattr__(self, name):
        try: return self._namespace[name]
        except KeyError: raise AttributeError(name) from None


class Duplicate(Exception):
    """The same sponsor operation already created this child Team."""
    def __init__(self, record):
        super().__init__(record['id']); self.record = record


def bind(namespace):
    global C, MEMBER_SUBJECT
    C = _Core(namespace)
    MEMBER_SUBJECT = next(r['subject'] for r in C.ROLE_TABLE if r['created_by'] == 'spawner' and r['match'] == 'prefix') + 'Delegated Team member'


def inside(path, bases):
    return any(path == base or path.startswith(base + '/') for base in bases)


def permits(view, slot, levels=1):
    """The grant a Team holds now (or held at a cited head) names this slot and reaches this many levels down."""
    C.need('delegation' in view, 'delegation-not-granted')
    held = view['delegation']
    C.need(held is not None, 'delegation-revoked')
    C.need(slot in held['sponsors'], 'delegation-slot-not-named')
    C.need(held['depth'] >= levels, 'delegation-depth')
    return held


# ---------------------------------------------------------------------------------------------------------
# Grants


def grant(value, charter):
    """Shape of one Team's delegation grant, checked against the charter that carries it."""
    C.need(isinstance(value, dict) and set(value) == GRANT_KEYS and type(value['version']) is int and value['version'] == 1, 'delegation-grant-shape')
    C._integer(value['depth'], 'delegation-depth', 1, C.DELEGATION_DEPTH_CEILING)
    slots = [m.get('slot') for m in charter.get('members', []) if isinstance(m, dict)]
    sponsors = value['sponsors']
    C.need(isinstance(sponsors, list) and sponsors and len(set(sponsors)) == len(sponsors)
           and all(isinstance(s, str) and s in slots for s in sponsors), 'delegation-sponsors')
    actions = value['actions']
    C.need(isinstance(actions, list) and actions and all(isinstance(a, str) for a in actions) and len(set(actions)) == len(actions)
           and set(actions) <= set(charter.get('actions', [])), 'delegation-actions')
    C.need(isinstance(value['scope'], list) and value['scope'] and all(isinstance(p, str) for p in value['scope']), 'delegation-scope')
    for path in value['scope']:
        C.relative(path); C.need(inside(path, charter.get('scope', [])), 'delegation-scope')
    C.need(isinstance(value['purpose'], str) and value['purpose'].strip() and len(value['purpose'].encode()) <= 1024, 'delegation-purpose')
    # A grant lets sponsors carve this Team's own allocation; without one there is nothing to carve.
    C.need(C._native(charter) and isinstance(charter.get('resource_allocation'), dict), 'delegation-requires-team-grant')
    return value


def admission(store, value):
    """Complete a grant on a charter being admitted. Depth defaults to one level; nothing defaults to unlimited."""
    supplied = value['delegation']
    C.need(isinstance(supplied, dict), 'delegation-grant-shape')
    filled = copy.deepcopy(supplied)
    filled.setdefault('version', 1); filled.setdefault('depth', 1)
    filled.setdefault('actions', list(value['actions'])); filled.setdefault('scope', list(value['scope']))
    return grant(filled, value)


def narrower(new, old):
    return (new['depth'] <= old['depth'] and set(new['sponsors']) <= set(old['sponsors']) and set(new['actions']) <= set(old['actions'])
            and all(inside(p, old['scope']) for p in new['scope']) and new['purpose'] == old['purpose'])


def amended(record, state, new):
    """An accepted amendment narrows or revokes a grant. It never creates one and never widens one."""
    old = state.get('delegation')
    if new is None: return None
    C.need(old is not None, 'delegation-not-granted')
    value = grant(new, dict(record, members=list(state['members'].values())))
    C.need(narrower(value, old), 'delegation-widened')
    return copy.deepcopy(value)


# ---------------------------------------------------------------------------------------------------------
# Parent chains


def chain(store, team):
    """Charters from the Main-accepted root down to this Team. Refuses cycles, gaps and over-deep lineage."""
    path = [team]; seen = {team['id']}
    while path[0].get('delegated_only'):
        control = path[0]['delegated_control']
        C.need(len(path) <= C.DELEGATION_DEPTH_CEILING and control['parent'] not in seen, 'delegation-depth')
        parent = store.read('Teams', control['parent']); seen.add(parent['id']); path.insert(0, parent)
    root = path[0]
    C._accepted(root)
    for depth in range(1, len(path)):
        control = path[depth]['delegated_control']; share = path[depth].get('resource_allocation') or {}
        C.need(control['depth'] == depth and control['root'] == root['id'] and control['parent'] == path[depth - 1]['id'], 'delegation-lineage')
        C.need(share.get('schema') == 2 and share.get('parent') == control['parent'] and share.get('root') == root['id']
               and share.get('depth') == depth and share.get('pool') == path[depth - 1]['limits']['budget'], 'delegation-resource-lineage')
    return path


def _memo(store):
    cache = getattr(store, '_operation_records', None)
    return None if cache is None else cache.setdefault(('delegation', 'memo'), {})


def _listing(store, ident):
    try:
        with os.scandir(store.root / '_Axis/Messages/Teams' / ident) as entries:
            return tuple(sorted(e.name for e in entries if e.name.endswith('.md')))
    except FileNotFoundError:
        return ()


def current(store, team, local=None):
    """Current projection of one Team. Inside an owned operation the read cache applies until that Team's
    Message folder changes, so a revocation published a moment ago is seen before the next write."""
    ident = team['id']; memo = _memo(store)
    if memo is None:
        if local is None: return store._project(team, store.records('Messages', team=ident))
        if ('view', ident) not in local: local[('view', ident)] = (None, store._project(team, store.records('Messages', team=ident)))
        return local[('view', ident)][1]
    token = _listing(store, ident); hit = memo.get(('view', ident))
    if hit is None or hit[0] != token:
        cache = store._operation_records
        for key in [k for k in cache if len(k) == 3 and k[0] == 'Messages' and k[1] in (ident, None)]: del cache[key]
        for key in [k for k in memo if k[1] == ident]: del memo[key]
        hit = memo[('view', ident)] = (token, store._project(team, store.records('Messages', team=ident)))
    return hit[1]


def at_head(store, team, head, local):
    """One Team's accepted chain as it stood at a cited head."""
    view = current(store, team, local); memo = _memo(store); space = local if memo is None else memo
    C.need(not view['held'], 'delegation-parent-held')
    key = ('head', team['id'], head)
    if key not in space:
        history = [team['id']] + view['history']
        C.need(head in history, 'delegation-parent-head')
        if head == view['head']: space[key] = view
        else:
            allowed = set(history[:history.index(head) + 1])
            space[key] = store._project(team, [m for m in store.records('Messages', team=team['id']) if m['id'] in allowed])
    return space[key]


def budget_lineage(child, parent):
    """A child grant keeps its pool's clock, routes, owner and basis; it may only be smaller."""
    C.need(all(child.get(k) == parent.get(k) for k in ('version', 'clock_start', 'accounting_owner', 'scope', 'routes')), 'delegation-resource-lineage')
    C.need(('money' in child) == ('money' in parent) and ('runtime_seconds' in child) == ('runtime_seconds' in parent), 'delegation-resource-lineage')
    if 'money' in parent:
        C.need(child['money']['currency'] == parent['money']['currency'] and child['money']['cost_basis'] == parent['money']['cost_basis'], 'delegation-resource-lineage')
    if 'runtime_seconds' in parent: C.need(child['runtime_seconds'] <= parent['runtime_seconds'], 'delegation-resource-lineage')


class Lineage:
    """Causal verifier for one projection of a delegated Team or Job.

    Each founding record on the path is checked against its own parent as that parent stood at the cited head:
    the sponsor was bound to the named slot at that epoch, the grant named that slot, and the child stays inside
    the grant. Each later control is checked the same way and ranked by the seat that issued it.
    """
    def __init__(self, store, founding):
        self.store = store; self.local = {}; self.family = founding['family']
        team = founding if self.family == 'Teams' else store.read('Teams', C.identity(founding.get('team')))
        C.need(team.get('delegated_only') is True, 'team-classification')
        self.path = chain(store, team); self.depth = len(self.path) - 1
        for level in range(1, self.depth + 1): self.founded(level)
        if self.family == 'Jobs':
            # Only the Team's own sponsoring seat admits its Jobs; a supervisor never does.
            C.need(self.seat(founding, True) == self.depth, 'delegated-controller')
            C.need(founding.get('authority') == team['authority'] and not any(k in founding for k in ('schedule', 'occurrence', 'budget_amendment')), 'delegated-job-scope')

    def bound(self, record, parent, live):
        control = record['delegated_control']; view = at_head(self.store, parent, control['parent_head'], self.local)
        C.need(record['issuer'] == {'role': 'worker', 'session': control['sponsor']}, 'delegated-sponsor')
        C.need(view['epoch'] == control['parent_epoch'] and view['members'].get(control['slot'], {}).get('session') == control['sponsor'], 'delegation-sponsor-binding')
        held = view.get('delegation')
        C.need(C.digest(held) == control['grant_sha256'], 'delegation-grant-binding')
        if live: permits(view, control['slot'])
        return held

    def founded(self, level):
        team = self.path[level]; parent = self.path[level - 1]; control = team['delegated_control']
        held = self.bound(team, parent, True)
        C.need(set(team['actions']) <= set(held['actions']) and all(inside(p, held['scope']) for p in team['scope']), 'delegation-exceeds-grant')
        C.need(team['authority'] == parent['authority'], 'delegation-authority')
        C.need(C.timestamp(team['limits']['deadline']) <= C.timestamp(parent['limits']['deadline']), 'delegation-deadline')
        C.need(C._native(team), 'delegated-native-budget-required')
        budget_lineage(team['limits']['budget'], parent['limits']['budget'])
        C.need(team.get('acceptance_owner') == control['sponsor'], 'acceptance-owner')
        members = team.get('members', [])
        C.need(all(isinstance(m, dict) and m.get('session') is None for m in members)
               and not RESERVED_SLOTS.intersection(m.get('slot') for m in members), 'delegated-team-members')
        if 'delegation' in team:
            lower = grant(team['delegation'], team)
            C.need(lower['depth'] < held['depth'] and set(lower['actions']) <= set(held['actions'])
                   and all(inside(p, held['scope']) for p in lower['scope']) and lower['purpose'] == held['purpose'], 'delegation-widened')

    def seat(self, record, live):
        """Level of the Team whose sponsoring seat issued this record; nearest first."""
        control = record['delegated_control']
        for level in range(self.depth, 0, -1):
            own = self.path[level]['delegated_control']
            if (control['parent'], control['slot']) == (own['parent'], own['slot']): break
        else:
            raise C.CoordinationError('delegated-controller')
        C.need(control['depth'] == level and control['root'] == self.path[0]['id'], 'delegation-lineage')
        self.bound(record, self.path[level - 1], live)
        return level

    def rank(self, message, event):
        """0 for Main, else the issuing seat's level. Anyone above the direct sponsor may only supervise."""
        if message.get('delegated_only'): level = self.seat(message, event.get('action') not in SAFE)
        else:
            C._accepted(message); level = 0
        if level < self.depth: C.need(event.get('action') in SUPERVISORY[self.family], 'delegated-supervisory-scope')
        return level

    def supervised(self, state, event):
        """A pause placed from above is lifted only from the same level or higher."""
        hold = state.get('supervisor_hold')
        if event['action'] == 'resume':
            C.need(hold is None or event['rank'] <= hold['rank'], 'supervisor-hold')
            state.pop('supervisor_hold', None)
        elif event['action'] == 'pause' and event['rank'] < self.depth:
            state['supervisor_hold'] = {'rank': event['rank'], 'event': event['id']}


def allocation_rank(store, team, message):
    """Authority behind one allocation Message of a nested Team: a controller seat on that Team's path.

    Structural on every read. The cited-head binding is checked when the record is written and by `audit`.
    """
    C._controlled(message)
    path = chain(store, team); control = message['delegated_control']
    for level in range(len(path) - 1, 0, -1):
        own = path[level]['delegated_control']
        if (control['parent'], control['slot']) == (own['parent'], own['slot']):
            C.need(control['depth'] == level and control['root'] == path[0]['id'], 'delegation-lineage')
            return level
    raise C.CoordinationError('delegated-controller')


def audit(store, message):
    """Full chain verification of one sponsor-issued Message, for `check`."""
    C._controlled(message)
    C.need(message.get('team') is not None, 'delegated-message-scope')
    team = store.read('Teams', message['team'])
    line = Lineage(store, team); event = message.get('event')
    if isinstance(event, dict):
        level = line.seat(message, event.get('action') not in SAFE)
        if level < line.depth: C.need(event.get('action') in SUPERVISORY.get(event.get('family'), ()), 'delegated-supervisory-scope')
    else: level = line.seat(message, False)
    return level


# ---------------------------------------------------------------------------------------------------------
# Fences: when a change to a grant or to a sponsoring seat is complete


def changes(store, team, view):
    """Accepted events on one Team that change who may sponsor beneath it, in that Team's own history order:
    a delegation amendment, or a new session on a seat its founding grant names. A first binding moves nothing."""
    founding = team.get('delegation')
    if not isinstance(founding, dict): return []
    named = set(founding.get('sponsors') or ())
    seats = {m.get('slot'): m.get('session') for m in team.get('members', []) if isinstance(m, dict)}
    order = {ident: index for index, ident in enumerate(view.get('history', ()))}
    found = []
    for message in sorted((m for m in store.records('Messages', team=team['id']) if m.get('id') in order), key=lambda m: order[m['id']]):
        event = message.get('event') or {}; data = event.get('data') or {}; action = event.get('action')
        if action == 'amend' and 'delegation' in data:
            found.append({'event': message['id'], 'kind': 'grant'})
        elif action in ('bind_member', 'replace_leader'):
            slot = 'leader' if action == 'replace_leader' else data.get('slot')
            previous = seats.get(slot); seats[slot] = data.get('session')
            if slot in named and previous is not None and previous != data.get('session'):
                found.append({'event': message['id'], 'kind': 'seat', 'slot': slot, 'previous': previous, 'session': data.get('session')})
    return found


def fence_author(store, team, message):
    """Main, or a controller seat on this Team's own path, may declare its fence complete. Structural on every
    read, like an allocation Message; the cited-head binding is checked when written and by `audit`."""
    if not message.get('delegated_only') or not team.get('delegated_only'):
        C._accepted(message); return 0
    return allocation_rank(store, team, message)


def waiting(store, team, view):
    """Changes on one Team that no authorized completion covers yet, oldest first. Computed from records alone."""
    found = changes(store, team, view)
    if not found: return []
    order = {ident: index for index, ident in enumerate([team['id']] + list(view.get('history', ())))}
    covered = -1
    for message in store.records('Messages', team=team['id']):
        value = message.get('data', {}).get('delegation_fence') if isinstance(message.get('data'), dict) else None
        if not isinstance(value, dict) or 'event' in message or message.get('team') != team['id']: continue
        try:
            C.need(set(value) == FENCE_KEYS and value['team'] == team['id'] and value['through'] in order and message.get('kind') == 'control', 'delegation-fence-shape')
            fence_author(store, team, message)
        except (C.CoordinationError, KeyError, TypeError, ValueError):
            continue  # An unauthorized or malformed completion completes nothing; `check` reports it.
        covered = max(covered, order[value['through']])
    return [item for item in found if order[item['event']] > covered]


def pending(store, team, view):
    """`waiting`, shared within one owned operation and refreshed with the Team's view."""
    if not isinstance(team.get('delegation'), dict): return []
    memo = _memo(store); key = ('fence', team['id'], view.get('head'))
    if memo is None: return waiting(store, team, view)
    if key not in memo: memo[key] = waiting(store, team, view)
    return memo[key]


# ---------------------------------------------------------------------------------------------------------
# Live checks, run at every effect


def holder(store, session):
    """A sponsoring seat counts for new work only while the session on it holds a live lease of its own."""
    try: store._worker_session(session)
    except C.CoordinationError as error: raise C.CoordinationError('delegation-sponsor-lost') from error


def edges(store, path, slots, live, caller=None):
    """Current authority along one chain of Teams, root first. `path[-1]` is the subject Team, or None for a
    child not founded yet; `slots[n]` is the seat in `path[n]` that sponsors `path[n + 1]`.

    Every edge is judged as it stands now, never as it stood at founding. The seat is bound. For new work the
    Team above is also active, unfrozen and unexpired, is not waiting on a fence, still grants this seat enough
    depth, has a live session on the seat, and still covers the Team below it. Stopping, reconciling and
    accounting need only the bound seats. Sponsor effects and member participation share this one calculation.
    Returns the view of each granting Team, root first.
    """
    allocation = C.allocation_module() if live else None
    count = len(path) - 1; views = [None] * count
    for level in range(count - 1, -1, -1):
        upper = path[level]; lower = path[level + 1]; slot = slots[level]; view = current(store, upper)
        C.need(not view['held'], 'delegation-ancestor-held')
        seated = view['members'].get(slot, {}).get('session')
        C.need(seated is not None and (level != caller or seated == store.session), 'delegation-sponsor-changed')
        if live:
            held = permits(view, slot, count - level)
            C.need(view['state'] in {'ready', 'running'}, 'delegation-ancestor-inactive')
            C.need(allocation.settled(store, upper) is None and allocation.effective(store, upper)['freeze'] is None, 'delegation-ancestor-frozen')
            store.validate_authority(upper['authority'])
            # A published change to this grant or to a sponsoring seat is not complete until it is fenced.
            C.need(not pending(store, upper, view), 'delegation-fence-pending')
            if level != caller: holder(store, seated)
            # A grant narrowed after the Team below was founded no longer covers a wider Team, at any depth.
            if lower is not None:
                C.need(set(lower['actions']) <= set(held['actions']) and all(inside(p, held['scope']) for p in lower['scope']), 'delegation-exceeds-grant')
        views[level] = view
    return views


def guard(store):
    """The caller's own seat and every Team between the root and its subject, as they stand now. Returns the
    facts a new record must carry."""
    control = store._delegated_control
    C.need(isinstance(control, dict), 'delegated-context-required')
    store.guard()
    C.need(not store.io.lease[2], 'delegate-required')
    C.need(store.storage_profile() == 'atomic', 'direct-storage-unavailable')
    placement = store._read_placement()
    C.Store(store.root, placement['session']).require_placement(expected=placement['activation'])
    live = control.get('live', True)
    path = chain(store, store.read('Teams', C.identity(control['parent'])))
    root = path[0]
    # The grant was accepted by one Main session under one placement; neither is a credential to reuse.
    if live: C.need(root['acceptance_owner'] == placement['session'], 'delegation-main-changed')
    subject = path + [None]; direct = None
    if control.get('team'):
        target = store.read('Teams', C.identity(control['team']))
        C.need(target.get('delegated_only') is True, 'delegated-controller')
        target_path = chain(store, target); level = None
        for index in range(len(target_path) - 1, 0, -1):
            own = target_path[index]['delegated_control']
            if (own['parent'], own['slot']) == (control['parent'], control['slot']):
                level = index; break
        C.need(level == len(path), 'delegated-controller')
        direct = level == len(target_path) - 1; subject = target_path
    slots = [team['delegated_control']['slot'] for team in subject[1:] if team is not None]
    if subject[-1] is None: slots.append(control['slot'])
    views = edges(store, subject, slots, live, caller=len(path) - 1)
    if live: store._delegated_live = True
    return {'session': store.session, 'placement': placement, 'root': root['id'], 'rank': len(path),
            'parent': path[-1], 'parent_view': views[len(path) - 1], 'direct': direct}


def snapshot(store):
    info = guard(store); control = store._delegated_control; view = info['parent_view']
    return {'version': 1, 'root': info['root'], 'parent': control['parent'], 'parent_head': view['head'],
            'parent_epoch': view['epoch'], 'slot': control['slot'], 'sponsor': store.session,
            'marker_sha256': C.digest(store.io.marker_body()), 'grant_sha256': C.digest(view.get('delegation')),
            'depth': info['rank'], 'main': info['placement']['session'], 'placement_activation': info['placement']['activation']}


def stamp(store, family, payload):
    """Scope one record to the caller's delegated context, then return its provenance."""
    control = store._delegated_control
    if family == 'Teams':
        C.need(control.get('team') is None and payload.get('acceptance_owner') == store.session, 'delegated-team-context')
    elif family == 'Jobs':
        C.need(control.get('team') is not None and payload.get('team') == control['team'] and payload.get('acceptance_owner') == store.session
               and not any(k in payload for k in ('schedule', 'occurrence', 'budget_amendment')), 'delegated-job-scope')
    else:
        C.need(control.get('team') is not None and payload.get('team') == control['team'], 'delegated-message-scope')
    return snapshot(store)


@contextlib.contextmanager
def context(store, parent, slot, *, team=None, lock=None, live=True):
    C.need(store._delegated_control is None and store._proposal_control is None and store._lock is None, 'nested-delegated-control')
    store._delegated_control = {'parent': parent, 'slot': slot, 'team': team, 'lock': lock or team or parent, 'live': live}
    try:
        guard(store)
        yield
    finally:
        store._delegated_control = None


def own_slot(store, parent):
    view = current(store, parent)
    slots = [s for s, m in view['members'].items() if m.get('session') == store.session]
    C.need(not view['held'] and len(slots) == 1, 'delegation-sponsor-changed')
    return slots[0]


def seat(store, team):
    """Nearest controller seat on this Team's path that the caller holds now: (parent Team, slot)."""
    C.need(team.get('delegated_only') is True, 'delegated-controller')
    path = chain(store, team)
    for level in range(len(path) - 1, 0, -1):
        own = path[level]['delegated_control']; view = current(store, path[level - 1])
        if not view['held'] and view['members'].get(own['slot'], {}).get('session') == store.session:
            return own['parent'], own['slot']
    raise C.CoordinationError('delegated-controller')


def direct_seat(store, team):
    own = team.get('delegated_control') or {}; found = seat(store, team)
    C.need(found == (own['parent'], own['slot']), 'delegated-controller')
    return found


def sponsor(store, charter):
    """Session bound now to the seat that sponsors this Team."""
    control = charter['delegated_control']
    view = current(store, store.read('Teams', control['parent']))
    C.need(not view['held'], 'delegation-ancestor-held')
    session = view['members'].get(control['slot'], {}).get('session')
    C.need(session is not None, 'delegation-sponsor-changed')
    return session


def seat_view(store, charter):
    """Who founded a child Team and who holds its sponsoring seat now. After a fenced seat transfer the two
    differ: the founding session stays as provenance, the current session is the local acceptance owner."""
    control = charter['delegated_control']
    view = current(store, store.read('Teams', control['parent']))
    return {'parent': control['parent'], 'slot': control['slot'], 'founding_session': control['sponsor'],
            'current_session': None if view['held'] else view['members'].get(control['slot'], {}).get('session')}


def participation_floor(store, team):
    """Slots a sponsoring Team keeps for its own members: what its admitted plan needs at once, at least one."""
    view = current(store, team); plan = None if view['held'] else view.get('collaboration_plan')
    if not plan: return 1
    bound = C._bound_plan(dict(team, members=[dict(item, slot=slot) for slot, item in view['members'].items()], collaboration_plan=plan), verify=False)
    return max(1, bound['summary']['required_capacity'])


def member_origin(store, session, team, slot):
    """A child Team's member is a Marker its sponsor minted for exactly this Team and slot."""
    worker = store._worker_session(session); lines = worker.marker_body().splitlines()
    C.need(lines[:1] == [MEMBER_SUBJECT], 'delegated-member-origin')
    for label, value in (('delegated-team', team), ('delegated-slot', slot)):
        C.need([line for line in lines if line.startswith(label + ':')] == [label + ': ' + str(value)], 'delegated-member-origin')
    return worker


def participation(store, charter, founding, placement):
    """A member works only while every sponsoring seat above its Team is held by a live session and every edge
    of the chain still grants what the Team below it holds. Checked inside the member's own Team lock."""
    C.need(founding.get('delegated_only') is True and founding.get('team') == charter['id'], 'delegated-controller')
    path = chain(store, charter)
    C.need(path[0]['acceptance_owner'] == placement['session'], 'delegation-main-changed')
    edges(store, path, [team['delegated_control']['slot'] for team in path[1:]], True)
    member_origin(store, store.session, charter['id'], next((s for s, m in store.project('Teams', charter['id'])['members'].items() if m.get('session') == store.session), None))


def event_guard(store, family, ident, founding, action, data):
    """Checks that only a sponsor's own write path needs; the projection re-verifies the result."""
    control = store._delegated_control
    team = ident if family == 'Teams' else founding.get('team')
    C.need(founding.get('delegated_only') is True and control.get('team') == team, 'delegated-controller')
    # Automatic process and provider routes stay with Main.
    C.need(action != 'route_boundary', 'delegated-control-scope')
    if action in {'bind_member', 'replace_leader'}:
        member_origin(store, data.get('session'), team, 'leader' if action == 'replace_leader' else data.get('slot'))
    if action == 'dispatch':
        C.need('route_request_sha256' not in data, 'delegated-native-carried-route')
        member_origin(store, data.get('session'), team, C.workspace_token(data.get('slot')))


# ---------------------------------------------------------------------------------------------------------
# Sponsor operations


def status(store, team):
    """Read-only place of one Team in its chain: grant, sponsor seat, share, liabilities and children. Grants nothing."""
    store.guard(); charter = store.read('Teams', C.identity(team)); allocation = C.allocation_module()
    path = chain(store, charter) if charter.get('delegated_only') else [charter]
    view = store.project('Teams', team)
    result = {'team': team, 'acceptance_class': view.get('acceptance_class'), 'state': view['state'], 'held': view['held'],
              'holds': view.get('holds', []), 'depth': len(path) - 1, 'root': path[0]['id'], 'chain': [t['id'] for t in path],
              'grant': view.get('delegation'), 'sponsor': None, 'allocation': None, 'budget': None, 'children': [],
              'integration': 'Main only; local acceptance never integrates into the shared project'}
    if charter.get('delegated_only'):
        control = charter['delegated_control']
        seated = current(store, path[-2])['members'].get(control['slot'], {}).get('session')
        result['sponsor'] = {'parent': control['parent'], 'slot': control['slot'], 'founding_session': control['sponsor'], 'current_session': seated}
    if not view['held']:
        result['members'] = {slot: item.get('session') for slot, item in view['members'].items()}
        if isinstance(charter.get('delegation'), dict):
            # A change that is published but not yet fenced stops new work beneath this Team; `fence` completes it.
            open_changes = waiting(store, charter, view)
            result['fence'] = {'status': 'pending' if open_changes else 'complete', 'changes': open_changes}
    if charter.get('resource_allocation'):
        closed = allocation.settled(store, charter)
        result['allocation'] = {'settled': closed, 'effective': None if closed else allocation.effective(store, charter)}
        budget = store.native_budget_state(charter['limits']['budget']['key'])
        result['budget'] = {k: budget[k] for k in ('key', 'known_minor', 'reserved_minor', 'uncertain_minor', 'liability_minor',
                            'base_liability_minor', 'allocated_minor', 'remaining_minor', 'remaining_seconds', 'unpriced_attempts', 'reasons', 'status')}
    for other in store.records('Teams'):
        if (other.get('resource_allocation') or {}).get('parent') != team: continue
        closed = allocation.settled(store, other); share = None if closed else allocation.effective(store, other)
        result['children'].append({'team': other['id'], 'slot': other['delegated_control']['slot'], 'settled': closed is not None,
                                   'money_minor': closed['known_minor'] if closed else share['money_minor'], 'slots': 0 if closed else share['slots']})
    return result


def team(store, parent, charter, operation_key):
    """Commission a child Team inside the caller's own Team grant, with a carved-out share of its resources.

    The child inherits the parent's authority, clock, routes and accounting owner. Its actions and paths stay
    inside the grant. Repeating the same operation returns the first Team; it never reserves twice.
    """
    C.identity(parent)
    C.need(isinstance(charter, dict) and isinstance(operation_key, str), 'delegated-charter')
    C._attempt_token(operation_key)
    C.need(not {'resource_allocation', 'resource_pool', 'guidance', 'delegated_operation', 'acceptance_owner'}.intersection(charter), 'reserved-fields')
    value = copy.deepcopy(charter); request = C.digest(charter)
    source = store.read('Teams', parent); slot = own_slot(store, source)
    with context(store, parent, slot, lock=parent):
        held = guard(store)['parent_view']['delegation']
        if 'authority' in value:
            C.need(isinstance(value['authority'], dict) and set(value['authority']) <= {'ref', 'expires', 'digest'}
                   and all(value['authority'][k] == source['authority'][k] for k in value['authority']), 'delegation-authority')
        value['authority'] = copy.deepcopy(source['authority'])
        value.setdefault('actions', list(held['actions'])); value.setdefault('scope', list(held['scope']))
        C.need(isinstance(value['actions'], list) and value['actions'] and set(value['actions']) <= set(held['actions']), 'delegation-exceeds-grant')
        C.need(isinstance(value['scope'], list) and value['scope'] and all(isinstance(p, str) and inside(p, held['scope']) for p in value['scope']), 'delegation-exceeds-grant')
        members = value.get('members')
        C.need(isinstance(members, list) and members and all(isinstance(m, dict) and set(m) <= {'slot', 'scope'} and isinstance(m.get('slot'), str) for m in members), 'delegated-team-members')
        C.need(not RESERVED_SLOTS.intersection(m['slot'] for m in members), 'delegated-team-members')
        limits = value.get('limits')
        C.need(isinstance(limits, dict) and isinstance(limits.get('budget'), dict), 'delegated-native-budget-required')
        base = source['limits']['budget']; budget = limits['budget']
        for key in ('version', 'key', 'clock_start', 'accounting_owner', 'scope', 'routes'): budget.setdefault(key, copy.deepcopy(base[key]))
        if 'runtime_seconds' in base: budget.setdefault('runtime_seconds', base['runtime_seconds'])
        if 'money' in base:
            # The sponsor states the child's money share. Zero is a real share; silence is not.
            money = budget.get('money')
            C.need(isinstance(money, dict) and 'ceiling_minor' in money, 'delegated-money-required')
            money.setdefault('currency', base['money']['currency']); money.setdefault('cost_basis', base['money']['cost_basis'])
        if 'delegation' in value:
            lower = value['delegation']
            C.need(isinstance(lower, dict), 'delegation-grant-shape')
            lower.setdefault('purpose', held['purpose']); lower.setdefault('depth', 1)
            C.need(type(lower['depth']) is int and lower['depth'] < held['depth'], 'delegation-depth')
            # The purpose Main granted travels down unchanged; a child states its own aim in its objective.
            C.need(lower['purpose'] == held['purpose'], 'delegation-widened')
        value['delegated_operation'] = {'key': operation_key, 'slot': slot, 'request_sha256': request}
        try:
            return store.create_team(value)
        except Duplicate as found:
            # An interrupted first call may have published the charter without its workspaces.
            with store.locked(): store._init_workspaces(found.record['id'])
            return {'status': 'duplicate', 'id': found.record['id'], 'path': '_Axis/Teams/' + found.record['id'] + '.md', 'record': found.record}


def _census(store, team=None):
    """Live Markers in the project, oldest first, and every member Marker this lane minted for one child Team."""
    live = []; minted = {}
    directory = store.path('_Axis/Agents', kind='directory')
    with os.scandir(directory) as entries:
        names = sorted(entry.name for entry in entries if entry.name.endswith('.md'))
    for name in names:
        marker = directory / name
        C.identity(marker.stem)
        try:
            checked = store.path('_Axis/Agents/' + marker.name)
            try: checked.with_suffix('.kill').lstat()
            except FileNotFoundError: killed = False
            else: killed = True
            fresh = time.time() - checked.stat().st_mtime < 3600
            lines = (store.io.read('_Axis/Agents/' + marker.name, optional=True) or '').splitlines() if team is not None else []
        except FileNotFoundError:
            continue  # retired between the listing and this read
        except (C.CoordinationError, C._START.Fault) as error:
            if error.code == 'missing_path' and error.path == '_Axis/Agents/' + marker.name:
                continue
            raise
        if not killed and fresh: live.append(marker.stem)
        if lines[:1] != [MEMBER_SUBJECT] or [line for line in lines if line.startswith('delegated-team:')] != ['delegated-team: ' + team]: continue
        slots = [line[16:] for line in lines if line.startswith('delegated-slot: ')]
        keys = [line[11:] for line in lines if line.startswith('admission: ')]
        request = [line[len('admission-request: '):] for line in lines if line.startswith('admission-request: ')]
        C.need(len(request) <= 1, 'delegated-operation-conflict')
        minted[marker.stem] = {'request': request[0] if request else None, 'slot': slots[0] if len(slots) == 1 else None, 'admission': keys[0] if len(keys) == 1 else None,
                               'killed': killed, 'fresh': fresh}
    return live, minted


def _tombstone(store, session, reason):
    """Stop one lease with an exclusive kill tombstone, inside the caller's Team lock. The Marker stays as the
    record of who minted it."""
    path = store.path('_Axis/Agents/' + session + '.kill', missing=True)
    if path.exists(): return False
    body = 'killed-by: ' + store.session + '\n' + time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()) + '\n' + reason + '\n'
    store._check_lock()
    try: fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644)
    except FileExistsError: return False
    try:
        C._START.write_fd(fd, body.encode()); os.fsync(fd)
    finally: os.close(fd)
    return True


def _minted_for(store, session, team, slot):
    """True when this lane minted the session's Marker for exactly this Team and slot; None when no Marker is left."""
    text = store.io.read('_Axis/Agents/' + session + '.md', optional=True)
    if text is None: return None
    lines = text.splitlines()
    return (lines[:1] == [MEMBER_SUBJECT] and [line for line in lines if line.startswith('delegated-team:')] == ['delegated-team: ' + team]
            and [line for line in lines if line.startswith('delegated-slot:')] == ['delegated-slot: ' + slot])


def _admission(store, session, team, slot):
    """The operation key under which a bound member was admitted to this Team and slot, if it carries one."""
    if not _minted_for(store, session, team, slot): return None
    keys = [line[11:] for line in store.io.read('_Axis/Agents/' + session + '.md').splitlines() if line.startswith('admission: ')]
    return keys[0] if len(keys) == 1 else None


def _admission_pin(operation, checkpoint=None):
    return C.digest({'operation': operation, 'checkpoint': checkpoint})


def _admission_result(store, team, slot, operation_key, view, request):
    """Replay accepted slot transitions in causal order. A retry reports the old holder's
    remaining work even when its Marker was retired or another replacement has since run."""
    if operation_key is None: return None
    accepted = {m['id']: m for m in store.records('Messages', team=team) if 'event' in m}
    previous = None  # delegated charters start with every slot unbound
    matches = []
    for ident in view['history']:
        event = accepted[ident]['event']
        action, data = event['action'], event['data']
        if action not in {'bind_member', 'replace_leader'}: continue
        if ('leader' if action == 'replace_leader' else data.get('slot')) != slot: continue
        session = data['session']
        key = data.get('admission_operation')
        if key is None: key = _admission(store, session, team, slot)
        if key == operation_key:
            kind = 'replace' if previous is not None else 'member'
            pin = _admission_pin(kind, data.get('checkpoint') if kind == 'replace' and slot == 'leader' else None)
            # The member operation also looks up an already accepted binding by key.
            # This read-only lookup is supported for a completed replacement.
            C.need(request == _admission_pin('member') or pin == request, 'delegated-operation-conflict')
            matches.append((session, previous, ident))
        previous = session
    if not matches: return None
    C.need(len(matches) == 1, 'delegated-operation-conflict')
    session, replaced, binding = matches[0]
    current = view['members'][slot].get('session')
    if session == current and session in _census(store)[0]:
        result = _admitted(store, team, slot, session, 'duplicate', binding, operation_key)
    else:
        result = {'status': 'superseded' if session != current else 'retired', 'session': None,
                  'previous_session': session, 'current_session': current, 'team': team, 'slot': slot,
                  'sponsor': store.session, 'operation_key': operation_key,
                  'note': 'this operation already completed; a new replacement requires a new operation key'}
    if replaced is not None:
        result.update(replaced=replaced, outstanding_attempts=_outstanding(store, team, replaced))
    return result


def _admit(store, team, slot, operation_key, request):
    """One member Marker for one slot, inside the child Team's lock. A Marker that an interrupted call minted
    was never returned to anyone: it is adopted, or retired when it cannot be. Never two live ones for a slot."""
    live, minted = _census(store, team)
    bound = {item.get('session') for item in store.project('Teams', team)['members'].values()}
    spare = sorted(s for s, m in minted.items() if m['slot'] == slot and not m['killed'] and s not in bound)
    matching = [m for m in minted.values() if m['slot'] == slot and m['admission'] == operation_key]
    for record in matching:
        # Legacy initial admissions have no variable checkpoint. A pending old leader
        # replacement needs manual reconciliation if its request cannot be established.
        if record['request'] is None:
            C.need(slot != 'leader' or request == _admission_pin('member'), 'delegated-request-unverified')
        else:
            C.need(record['request'] == request, 'delegated-operation-conflict')
    usable = [s for s in spare if minted[s]['fresh'] and minted[s]['admission'] == operation_key]
    keep = usable[0] if usable else None
    for session in spare:
        if session != keep: _tombstone(store, session, 'unbound member Marker retired by its sponsor; never launched')
    if keep is not None: return keep, '_Axis/Agents/' + keep + '.md', 'adopted'
    configured = store.io.setting('Max Concurrent Sessions')
    cap = int(configured) if isinstance(configured, str) and configured.isascii() and configured.isdigit() and 1 <= int(configured) <= 100 else 10
    C.need(len([s for s in live if s not in spare]) < cap, 'project-concurrency')

    def body(session):
        return (MEMBER_SUBJECT + '\n\nsponsor: ' + store.session + '\ndelegated-team: ' + team + '\ndelegated-slot: ' + slot
                + ('' if operation_key is None else '\nadmission: ' + operation_key)
                + '\nadmission-request: ' + request + '\nstarted: ' + session + '\nreturn: sponsor; Main alone accepts project integration.\n')
    session, path = store.io.record('Agents', body, renew_lease=False)
    # Sponsors of other Teams mint under other locks. The cap therefore holds at the admission itself: each
    # admission counts again after minting and withdraws its own Marker, before it is bound, if the count is
    # over. The last admission to count sees every Marker that stays, so the Markers that stay fit the cap.
    if len(_census(store)[0]) > cap:
        _tombstone(store, session, 'member Marker withdrawn at admission; project concurrency cap reached')
        raise C.CoordinationError('project-concurrency')
    return session, path, 'created'


def _admitted(store, team, slot, session, status, binding, operation_key):
    return {'status': status, 'session': session, 'path': '_Axis/Agents/' + session + '.md', 'team': team, 'slot': slot,
            'sponsor': store.session, 'binding': binding, 'operation_key': operation_key,
            'launch': 'not launched; the host or the User starts this member with a TeamMember envelope'}


def _bind(store, team, slot, session, status, operation_key, action='bind_member', data=None, expected=None, request=None):
    """Record the binding. A binding the Team's budget holds is reported as held, never as an admitted member;
    the Marker stays unbound and the same call adopts it once the hold clears."""
    payload = copy.deepcopy(data) if data is not None else {'slot': slot, 'session': session}
    if operation_key is not None: payload['admission_operation'] = operation_key
    try:
        bound = store.event('Teams', team, action, payload, expected=expected)
    except C.CoordinationError as error:
        if error.code != 'stale-predecessor': raise
        # Admission and binding use separate lock scopes. A concurrent same-key call may have
        # completed the binding; recover it instead of advancing the epoch a second time.
        with store.locked(team=team):
            view = store.project('Teams', team)
            C.need(not view['held'] and slot in view['members'], 'delegated-member-bound')
            prior = _admission_result(store, team, slot, operation_key, view, request)
            if prior is not None: return prior
        # A different change won the gap. Preserve the unbound Marker for an explicit same-key retry.
        raise
    if bound.get('status') == 'created': return _admitted(store, team, slot, session, status, bound['id'], operation_key)
    return dict(bound, team=team, slot=slot, session=None, unbound_marker=session, operation_key=operation_key,
                note='not admitted: the binding is held; repeat the same call after the hold clears')


def _outstanding(store, team, session):
    """Attempts of one session that still hold capacity or an unknown outcome in this Team."""
    found = []
    for job in store.records('Jobs'):
        if job.get('team') != team: continue
        state = store.project('Jobs', job['id'])
        if state['held']:
            found.append({'job': job['id'], 'attempt': None, 'status': 'held'}); continue
        for name, item in state['attempts'].items():
            if item.get('session') == session and (name in state['active'] or name in state['stop_unconfirmed'] or item.get('route_pending')):
                found.append({'job': job['id'], 'attempt': name, 'status': item.get('status')})
    return found


def member(store, team, slot, operation_key=None):
    """Admit one member to an unbound slot of the caller's own child Team: one Marker, bound once. This starts
    no host process. Repeating the call after an interruption adopts the Marker the first call minted; with
    the same `operation_key` it also returns the member that call already bound, instead of refusing."""
    C.workspace_token(slot)
    if operation_key is not None: C._attempt_token(operation_key)
    request = _admission_pin('member')
    charter = store.read('Teams', C.identity(team)); parent, seat_slot = direct_seat(store, charter)
    with context(store, parent, seat_slot, team=team):
        with store.locked(team=team):
            view = store.project('Teams', team)
            C.need(not view['held'] and view['state'] in {'ready', 'running'} and slot in view['members'], 'delegated-member-bound')
            prior = _admission_result(store, team, slot, operation_key, view, request)
            if prior is not None: return prior
            C.need(view['members'][slot].get('session') is None, 'delegated-member-bound')
            session, path, status = _admit(store, team, slot, operation_key, request)
        return _bind(store, team, slot, session, status, operation_key, expected=view['head'], request=request)


def replace(store, team, slot, operation_key, checkpoint=None):
    """Fence one member that the caller's own child Team admitted, and bind a fresh one to the same slot.

    Only a Marker this lane minted for exactly this Team and slot is ever stopped. The Team epoch advances, so
    attempts dispatched before it stop being current; they and their charges stay recorded. A tombstone is not
    proof that a process exited: stop or reconcile each outstanding attempt separately. Safe to repeat with the
    same `operation_key`."""
    C.workspace_token(slot); C._attempt_token(operation_key)
    request = _admission_pin('replace', checkpoint if slot == 'leader' else None)
    C.need(slot != 'leader' or (isinstance(checkpoint, str) and checkpoint.strip()), 'leader-checkpoint')
    charter = store.read('Teams', C.identity(team)); parent, seat_slot = direct_seat(store, charter)
    with context(store, parent, seat_slot, team=team):
        with store.locked(team=team):
            view = store.project('Teams', team)
            C.need(not view['held'] and view['state'] in {'ready', 'running'} and slot in view['members'], 'delegated-member-bound')
            previous = view['members'][slot].get('session')
            C.need(previous is not None, 'delegated-member-unbound')
            prior = _admission_result(store, team, slot, operation_key, view, request)
            if prior is not None: return prior
            origin = _minted_for(store, previous, team, slot)
            C.need(origin is not False, 'delegated-member-origin')
            if origin:
                reason = 'member replaced by its sponsor; Team ' + team + ' slot ' + slot + ' operation ' + operation_key
                tombstone = store.io.read('_Axis/Agents/' + previous + '.kill', optional=True)
                if tombstone is not None and reason in tombstone.splitlines():
                    pins = [line for line in tombstone.splitlines() if line.startswith('admission-request: ')]
                    C.need(pins == ['admission-request: ' + request] or (not pins and slot != 'leader'), 'delegated-operation-conflict')
                _tombstone(store, previous, reason + '\nadmission-request: ' + request)
            session, path, status = _admit(store, team, slot, operation_key, request)
        if slot == 'leader': result = _bind(store, team, slot, session, status, operation_key, 'replace_leader', {'session': session, 'previous': previous, 'checkpoint': checkpoint}, expected=view['head'], request=request)
        else: result = _bind(store, team, slot, session, status, operation_key, expected=view['head'], request=request)
        result.update(replaced=previous, outstanding_attempts=_outstanding(store, team, previous))
        if result.get('session'): result['note'] = 'a tombstone is not proof of process exit; record a boundary or reconcile each outstanding attempt'
        return result


def retire(store, team, session):
    """Stop one member Marker that the caller's own child Team admitted. Cleanup: available after revocation.
    The binding and every recorded attempt and charge stay as they are."""
    charter = store.read('Teams', C.identity(team)); parent, seat_slot = direct_seat(store, charter); C.identity(session)
    with context(store, parent, seat_slot, team=team, live=False):
        with store.locked(team=team):
            minted = _census(store, team)[1]
            C.need(session in minted, 'delegated-member-origin')
            done = _tombstone(store, session, 'member Marker retired by its sponsor; Team ' + team)
        return {'status': 'retired' if done else 'already-retired', 'session': session, 'team': team, 'slot': minted[session]['slot'],
                'outstanding_attempts': _outstanding(store, team, session),
                'note': 'a tombstone is not proof of process exit; record a boundary or reconcile each outstanding attempt'}


def renew(store, team):
    """Keep the caller's own lease alive while its authority over this child Team is live. The Marker keeps its
    identity and no authority deadline moves."""
    charter = store.read('Teams', C.identity(team)); parent, slot = direct_seat(store, charter)
    with context(store, parent, slot, team=team):
        try: store.io.renew(store.io.marker_name, store.io.marker_body())
        except C._START.Fault as error: raise C.CoordinationError(error.code, error.path) from None
        return {'status': 'renewed', 'session': store.session, 'team': team, 'authority_expires': charter['authority']['expires']}


def _keep_lease(store):
    """Activity under live authority renews only the caller's own existing, validated lease."""
    try:
        if time.time() - store.io.path(store.io.marker_name).stat().st_mtime >= LEASE_RENEW_AFTER:
            store.io.renew(store.io.marker_name, store.io.marker_body())
    except (C._START.Fault, OSError):
        pass  # The operation already completed; a lease that cannot be renewed is refused at its next use.


def job(store, mandate, operation_key):
    C.need(isinstance(mandate, dict) and isinstance(operation_key, str) and operation_key.strip(), 'delegated-mandate')
    value = copy.deepcopy(mandate); ident = C.identity(value.get('team'))
    C.need(not any(k in value for k in ('schedule', 'occurrence', 'budget_amendment')), 'delegated-job-scope')
    charter = store.read('Teams', ident); parent, slot = direct_seat(store, charter)
    with context(store, parent, slot, team=ident):
        if 'authority' in value:
            C.need(isinstance(value['authority'], dict) and set(value['authority']) <= {'ref', 'expires', 'digest'}
                   and all(value['authority'][k] == charter['authority'][k] for k in value['authority']), 'delegation-authority')
        value['authority'] = copy.deepcopy(charter['authority'])
        value.setdefault('scope', list(charter['scope'])); value.setdefault('actions', list(charter['actions']))
        limits = value.setdefault('limits', {})
        C.need(isinstance(limits, dict), 'limits')
        limits.setdefault('budget', copy.deepcopy(charter['limits']['budget']))
        limits.setdefault('concurrency', charter['limits']['concurrency'])
        return store.admit_job(value, 'delegated:' + ident + ':' + operation_key)


def event(store, family, ident, action, data=None, expected=None, epoch=None):
    """One transition on a child Team or its Job. The direct sponsor runs the work and accepts it locally;
    an ancestor sponsor may only supervise. Every call rechecks the whole chain first."""
    C.need(family in {'Teams', 'Jobs'}, 'projection-family')
    C.need(data is None or isinstance(data, dict), 'event-data')
    record = store.read(family, C.identity(ident))
    C.need(record.get('delegated_only') is True, 'delegated-controller')
    charter = record if family == 'Teams' else store.read('Teams', C.identity(record.get('team')))
    parent, slot = seat(store, charter)
    with context(store, parent, slot, team=charter['id'], live=action not in SAFE):
        return store.event(family, ident, action, copy.deepcopy(data or {}), expected, epoch)


def message(store, team, recipient, body, kind='question', attachments=None, reply_to=None):
    C.need(kind in C.PROPOSALS and isinstance(body, str) and isinstance(recipient, str), 'delegated-message-kind')
    charter = store.read('Teams', C.identity(team)); parent, slot = direct_seat(store, charter)
    with context(store, parent, slot, team=team):
        prefix = '_Axis/Teams/' + team + '/members/'
        C.need(isinstance(attachments or [], list) and all(isinstance(a, dict) and str(a.get('path', '')).startswith(prefix) for a in (attachments or [])), 'delegated-attachment-scope')
        checked = store.validate_attachments(attachments or [])
        data = {}; correlation = team
        if reply_to is not None:
            original = store.read('Messages', C.identity(reply_to))
            C.need(original.get('team') == team, 'reply-scope')
            data['reply_to'] = reply_to; correlation = original['correlation']
        with store.locked(team=team):
            delivery = store._route(team, recipient)
            C.need(all(t['slot'] != 'sponsor' for t in delivery['recipients']), 'delegated-sponsor-loop')
            delivery['sender_slot'] = 'sponsor'
            return store._record('Messages', {'subject': 'Sponsor ' + kind, 'kind': kind, 'recipient': recipient, 'body': body,
                'team': team, 'job': None, 'epoch': store.project('Teams', team)['epoch'], 'expires': charter['authority']['expires'],
                'correlation': correlation, 'authority': None, 'data': data, 'delivery': delivery, 'attachments': checked})


def _attending(store):
    """A sponsor that reads its child Team under authority that is still live is attending to it, and that keeps
    its own lease. Reading stays possible after revocation; it then renews nothing."""
    control = store._delegated_control; control['live'] = True
    try: guard(store)
    except C.CoordinationError: pass
    finally: control['live'] = False


def inbox(store, team, after=None):
    charter = store.read('Teams', C.identity(team)); parent, slot = seat(store, charter)
    if after is not None: C.identity(after)
    with context(store, parent, slot, team=team, live=False):
        _attending(store)
        names = {'sponsor', 'owner', charter['acceptance_owner'], store.session}
        rows = [m for m in store.records('Messages', team=team) if m.get('team') == team and (after is None or m['id'] > after)
                and (any(isinstance(t, dict) and t.get('slot') == 'sponsor' for t in (m.get('delivery') or {}).get('recipients', []))
                     or ('delivery' not in m and m.get('recipient') in names))]
        return {'team': team, 'sponsor': store.session, 'acceptance_class': 'delegated', 'messages': rows,
                'next': rows[-1]['id'] if rows else after}


def checkpoint(store, team):
    charter = store.read('Teams', C.identity(team)); parent, slot = seat(store, charter)
    with context(store, parent, slot, team=team, live=False):
        _attending(store)
        return store.team_checkpoint(team)


def artifact_check(store, team, slot, revision):
    charter = store.read('Teams', C.identity(team)); parent, seat_slot = seat(store, charter)
    with context(store, parent, seat_slot, team=team, live=False):
        view = store.project('Teams', team)
        C.need(not view['held'], 'team-held')
        return store.artifact_check(team, slot, revision, _view=view)


def freeze(store, team, operation):
    charter = store.read('Teams', C.identity(team)); parent, slot = seat(store, charter)
    with context(store, parent, slot, team=team, live=False):
        with store.locked(team=team):
            return C.allocation_module().freeze(store, team, operation)


def revise(store, team, predecessor, money_minor, slots, operation, source_release=None):
    """Grow or shrink a child's share. The pool is the parent Team's grant, so the parent's lock serializes it."""
    charter = store.read('Teams', C.identity(team)); parent, slot = seat(store, charter); allocation = C.allocation_module()
    share = charter.get('resource_allocation') or {}
    C.need(share.get('parent'), 'allocation-required')
    now = allocation.effective(store, charter)
    grows = type(money_minor) is int and type(slots) is int and (money_minor > now['money_minor'] or slots > now['slots'])
    with context(store, parent, slot, team=team, lock=share['parent'], live=grows):
        with store.locked(team=share['parent']):
            peer = C.Store(store.root, store.session, clock=store.clock)
            peer._delegated_control = dict(store._delegated_control, lock=team)
            with peer.locked(team=team):
                peer._check_lock(); store._peer_lock = peer
                try: return allocation.revise(store, team, predecessor, money_minor, slots, operation, source_release)
                finally: store._peer_lock = None


def settle(store, team):
    """Return a finished child's proven unused share to its parent Team. This is not project integration."""
    charter = store.read('Teams', C.identity(team)); parent, slot = seat(store, charter)
    with context(store, parent, slot, team=team, live=False):
        with store.locked(team=team):
            return C.allocation_module().settlement(store, team)


def _descendants(store, ident):
    """Child Teams carved from one Team, read fresh: a cached list could miss a Team founded a moment ago."""
    return sorted(t['id'] for t in store._read_records('Teams') if (t.get('resource_allocation') or {}).get('parent') == ident)


def drain(store, ident, wait):
    """Pass one Team's control lock once. Whoever held it has released it, and whoever takes it next rechecks
    the whole chain under it. An unchanged or expired lock does not prove that its writer stopped."""
    try: os.lstat(store.root / '_Axis/Teams' / ident)
    except FileNotFoundError: return 'drained'  # no Team folder has been created
    until = time.monotonic() + wait
    while True:
        try:
            with store.locked(team=ident): pass
            return 'drained'
        except C.CoordinationError as error:
            if error.code != 'locked': raise
        if time.monotonic() >= until: return 'blocked'
        time.sleep(0.02)


def _fence(store, charter, wait):
    """Drain every Team beneath one Team, top down, then record completion in that Team's own folder."""
    ident = charter['id']; view = store.project('Teams', ident)
    C.need(not view['held'], 'team-held')
    open_changes = waiting(store, charter, view)
    if not open_changes: return {'status': 'complete', 'team': ident, 'changes': [], 'note': 'no delegation change awaits a fence'}
    through = view['head']; queue = _descendants(store, ident); drained = []; expired = []; blocked = []
    while queue:
        team = queue.pop(0); outcome = drain(store, team, wait)
        if outcome == 'blocked':
            blocked.append(team); continue
        drained.append(team)
        # A child is founded under its parent's lock, so this list is final once that lock has been passed.
        queue.extend(_descendants(store, team))
    report = {'team': ident, 'through': through, 'changes': [item['event'] for item in open_changes], 'drained': drained, 'expired_holders': expired}
    if blocked: return dict(report, status='pending', blocked=blocked)
    with contextlib.ExitStack() as stack:
        until = time.monotonic() + wait
        while True:
            try:
                stack.enter_context(store.locked(team=ident)); break
            except C.CoordinationError as error:
                if error.code != 'locked' or time.monotonic() >= until: raise
                time.sleep(0.02)
        if not waiting(store, charter, store.project('Teams', ident)): return dict(report, status='complete', completion=None)
        record = store._record('Messages', {
            'subject': 'Delegation fence completed: ' + ident, 'kind': 'control', 'recipient': 'main' if store._delegated_control is None else 'sponsor',
            'body': 'Every Team beneath this change has passed its control lock since the change was published. An effect that cited the earlier grant or seat can no longer be written.',
            'team': ident, 'job': None, 'correlation': 'delegation-fence:' + ident, 'epoch': 0,
            'data': {'delegation_fence': {'team': ident, 'through': through, 'changes': report['changes'], 'drained': drained, 'expired_holders': expired}},
            'authority': charter['authority'], 'expires': charter['authority']['expires'], 'attachments': []})
    later = waiting(store, charter, store.project('Teams', ident))
    # A change published after this run began is covered by the next run, never by this one.
    return dict(report, status='pending' if later else 'complete', completion=record['id'], later=[item['event'] for item in later])


def fence(store, team, wait_seconds=None):
    """Complete the fence for every delegation change on one Team that still waits for it. Safe to repeat, by
    Main for any Team or by a sponsor seated above that Team; it grants nothing."""
    wait = DRAIN_WAIT if wait_seconds is None else wait_seconds
    C.need(type(wait) in (int, float) and 0 <= wait <= FENCE_WAIT_CEILING, 'delegation-fence-wait')
    charter = store.read('Teams', C.identity(team))
    C.need(isinstance(charter.get('delegation'), dict), 'delegation-not-granted')
    store.guard()
    if store.io.lease[2]:
        store.require_placement()
        return _fence(store, charter, wait)
    parent, slot = seat(store, charter)
    with context(store, parent, slot, team=team, live=False):
        return _fence(store, charter, wait)


def changed(store, team, result):
    """After an accepted change to a grant or to a sponsoring seat: fence it in the same call when every Team
    beneath it yields its lock promptly. Otherwise the published change is itself the durable intent; nothing
    new starts beneath it until `fence` completes, and the result says so."""
    try:
        charter = store.read('Teams', team); view = store.project('Teams', team)
        if view['held'] or not waiting(store, charter, view): return
        outcome = _fence(store, charter, DRAIN_WAIT)
    except (C.CoordinationError, C._START.Fault, OSError) as error:
        outcome = {'status': 'pending', 'team': team, 'reason': getattr(error, 'code', 'io')}
    result['delegation_fence'] = outcome


OPERATIONS = {'status': status, 'team': team, 'member': member, 'replace': replace, 'retire': retire, 'renew': renew, 'job': job,
              'event': event, 'message': message, 'inbox': inbox, 'checkpoint': checkpoint, 'artifact-check': artifact_check,
              'freeze': freeze, 'revise': revise, 'settle': settle, 'fence': fence}


def call(store, operation, arguments):
    C.need(operation in OPERATIONS and isinstance(arguments, dict), 'delegated-operation')
    store._delegated_live = False
    try:
        # Checks made before a lock is taken share one read of each ancestor; every lock starts a fresh one.
        with store.cached_reads():
            result = OPERATIONS[operation](store, **arguments)
    except FileNotFoundError as error:
        # Minting a record identity walks every Team folder. Another writer's lock directory can be released
        # under that walk. Earlier steps of this compound call may already exist; keep the same operation key
        # and recover from their records. This status never means the whole call made no change.
        if '/control.lock' not in str(error.filename or ''): raise
        raise C.CoordinationError('locked', 'record identity scan met a released Team lock; reconcile partial effects and repeat the same operation key') from error
    if store._delegated_live: _keep_lease(store)
    return result
