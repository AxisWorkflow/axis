/** Pure offline proposal. Every host fact below is a caller-supplied assumption.
 * No SDK integration, authentication, timers, filesystem access, process execution,
 * Main claim, submission or mutating-effect capability is implemented here. */
import { createHash } from 'node:crypto';

export type Role = 'Main' | 'Assistant' | 'Auxiliary' | 'GroupAgent' | 'Observer';
export type Principal = 'owner' | 'participant';
export type Refusal =
  | 'invalid-policy' | 'missing-key' | 'invalid-identity' | 'undeclared-route'
  | 'workspace' | 'native-chat' | 'native-sender' | 'alias' | 'sender'
  | 'owner-direct' | 'provenance' | 'origin-unverified' | 'origin-contradiction'
  | 'session-unproven' | 'session-poisoned' | 'session-ended' | 'capacity'
  | 'run-poisoned' | 'run-revoked' | 'run-contradiction' | 'stale-generation'
  | 'hook-inactive' | 'guidance' | 'budget' | 'assembly-unverified' | 'not-prepared' | 'not-admitted'
  | 'final-prompt' | 'policy-changed' | 'requester' | 'owner' | 'aborted'
  | 'event-run' | 'operation' | 'stale-event' | 'invalid-epoch';
export type Result<T> = Readonly<{ ok: true; value: T }> | Readonly<{ ok: false; reason: Refusal }>;
export interface Transition<T> { readonly state: IdentityState; readonly result: Result<T> }

export interface BindingInput {
  readonly projectId: string; readonly instanceId: string; readonly agentId: string;
  readonly channel: string; readonly accountId: string; readonly chatId: string;
  readonly kind: 'direct' | 'group'; readonly ownerSenderId: string;
  readonly participantSenderIds: readonly string[];
}
export interface Route extends BindingInput {
  readonly workspaceDir: string; readonly surface: string; readonly role: Role;
  readonly readScope: 'project' | readonly string[]; readonly revision: string;
  readonly binding: string; readonly rowPolicyDigest: string; readonly runtimePolicyDigest: string;
  /** Exact route-specific alias values; no universal alias normalization. */
  readonly messageProvider?: string; readonly channelId?: string;
}
export interface StrictPolicy {
  readonly instanceId: string;
  /** This namespace must be independently qualified against actual storage. */
  readonly physicalKey: 'instance-agent-session';
  readonly routes: readonly Route[];
}
export interface RunKey {
  readonly agentId: string; readonly sessionKey: string; readonly sessionId: string; readonly runId: string;
}
export interface PromptIdentity extends RunKey {
  readonly workspaceDir: string; readonly channel: string; readonly accountId: string;
  readonly chatId: string; readonly senderId: string; readonly nativeChatId: string;
  readonly nativeSenderId?: string; readonly messageProvider?: string; readonly channelId?: string;
  /** Current qualified peer identity, required for owner-only roles. */
  readonly directPeerId?: string;
}
export interface ExternalUserProvenance {
  readonly kind: 'external_user'; readonly originSessionId?: string;
  readonly sourceSessionKey?: string; readonly sourceChannel?: string; readonly sourceTool?: string;
}
export interface OriginalAudience {
  readonly agentId: string; readonly sessionId: string; readonly sessionKey: string;
  readonly incarnation: string; readonly workspaceDir: string; readonly channel: string;
  readonly accountId: string; readonly chatId: string; readonly surface: string;
  readonly binding: string; readonly role: Role;
}
export interface OriginEvidence {
  readonly epoch: string; readonly kind: 'creation' | 'original-audience';
  readonly physicalIdentityVerified: true; readonly originalAudienceVerified: true;
  readonly original: OriginalAudience;
}
export interface SessionTicket {
  readonly epoch: string; readonly agentId: string; readonly sessionId: string; readonly incarnation: string;
}
export interface PreparationTicket { readonly epoch: string; readonly key: RunKey; readonly generation: number }
export interface BudgetWitness {
  /** The actual host estimator must measure this exact complete contribution. */
  readonly measuredText: string; readonly estimatedTokens: number;
  readonly contextTokenBudget?: number; readonly contextWindow?: number;
}
export interface PrepareInput {
  readonly identity: PromptIdentity; readonly provenance: ExternalUserProvenance;
  readonly roleText: string; readonly budget: BudgetWitness; readonly hookActive: boolean;
  /** Hypothetical qualified host assembly input, NOT a documented SDK field.
   * The host must establish that this slot is trusted, unquoted system guidance.
   * Missing capability refuses the route; a model-controlled assertion is invalid. */
  readonly assembly: Readonly<{ verified: true; placement: 'unquoted-system'; before: string; after: string }>;
}
export interface ModelInput {
  readonly identity: PromptIdentity; readonly systemPrompt: string; readonly hookActive: boolean;
}
export interface Requester {
  readonly channel: string; readonly accountId: string; readonly senderId: string;
  readonly senderIsOwner?: boolean;
}
export interface ToolInput {
  /** Captured by this plugin incarnation, never taken from model arguments. */
  readonly epoch: string;
  readonly key: RunKey; readonly requester: Requester; readonly operation: 'read' | 'status';
  readonly invocationCurrent: boolean; readonly aborted: boolean;
  readonly eventRunId?: string; readonly channelId?: string;
}
export interface IdentityMatch {
  /** This is a comparison result, never permission for a file/tool/effect. */
  readonly kind: 'identity-match-only'; readonly role: Role; readonly principal: Principal;
  readonly surface: string; readonly binding: string; readonly rowPolicyDigest: string; readonly runtimePolicyDigest: string;
}
export interface Prepared extends IdentityMatch {
  readonly ticket: PreparationTicket; readonly contribution: string; readonly contributionDigest: string;
}
function preparedView(frozen: FrozenPreparation): Prepared {
  return { ...match(frozen), ticket: frozen.ticket, contribution: frozen.contribution, contributionDigest: frozen.contributionDigest };
}
interface FrozenPreparation extends Prepared {
  readonly identity: PromptIdentity; readonly provenance: ExternalUserProvenance;
  readonly policy: Route; readonly roleText: string; readonly budget: BudgetWitness;
  readonly frameDigest: string; readonly expectedSystemPromptDigest: string;
}
interface PhysicalSession {
  readonly original: OriginalAudience; readonly status: 'active' | 'poisoned' | 'ended';
}
interface Run {
  readonly key: RunKey; readonly generation: number;
  readonly status: 'building' | 'prepared' | 'admitted' | 'poisoned' | 'revoked' | 'ended';
  readonly frozen?: FrozenPreparation;
}
export interface IdentityState {
  readonly epoch: string; readonly policy: StrictPolicy; readonly policyValid: boolean;
  readonly nextGeneration: number; readonly sessions: readonly PhysicalSession[]; readonly runs: readonly Run[];
}

export const MAX_CONTRIBUTION_CHARS = 8000;
const MAX_SESSIONS = 256;
const MAX_RUNS = 512;
const MAX_PARTICIPANTS = 256;
const MAX_READ_FOLDERS = 64;
const MAX_AGENTS = 64;
const ID_SCALARS = 256;
const ID_BYTES = 1024;
const WORKSPACE_BYTES = 4096;
// Runtime-only keys have no portable parser counterpart. Preserve their prior
// 4096 UTF-16-unit bound; the scalar and UTF-8 bounds below are explicit ceilings.
const MAX_RUNTIME_UNITS = 4096;
const MAX_RUNTIME_BYTES = 16384;
// Retained string values in UTF-16 units, not JSON bytes or heap size.
// Common IDs: 256 scalars => at most 512 units; workspace <=4096 bytes;
// surface <=64 ASCII units; folders <=128 ASCII units; runtime IDs <=4096.
// Maximum uses group kind (5) and canonical GroupAgent role (10), because a
// direct route cannot retain participants. Root plus <=256 route payloads.
const MAX_POLICY_STRING_UNITS = 512 + 22 + MAX_SESSIONS *
  ((7 + MAX_PARTICIPANTS) * 512 + WORKSPACE_BYTES + 64 + 3 * MAX_RUNTIME_UNITS +
   MAX_READ_FOLDERS * 128 + 76 + 64 + 64 + 5 + 10);
const OPEN = '<axis-strict-context ';
const roles: readonly Role[] = ['Main', 'Assistant', 'Auxiliary', 'GroupAgent', 'Observer'];
const keyFields = ['agentId', 'sessionKey', 'sessionId', 'runId'] as const;
const identityFields = [...keyFields, 'workspaceDir', 'channel', 'accountId', 'chatId', 'senderId', 'nativeChatId'] as const;
const ownerOnly = (role: Role): boolean => ['Main', 'Assistant', 'Auxiliary'].includes(role);
const stable = (value: unknown): string | undefined => JSON.stringify(value, (_key, item: unknown) =>
  record(item) ? Object.fromEntries(Object.keys(item).sort().map(key => [key, item[key]])) : item);
const equal = (a: unknown, b: unknown): boolean => stable(a) === stable(b);
const hash = (text: string): string => createHash('sha256').update(text, 'utf8').digest('hex');
const yes = <T>(value: T): Result<T> => ({ ok: true, value });
const no = <T>(reason: Refusal): Result<T> => ({ ok: false, reason });
const record = (value: unknown): value is Record<string, unknown> =>
  typeof value === 'object' && value !== null && !Array.isArray(value);
const unicodeText = (value: unknown): value is string => typeof value === 'string' &&
  !/[\uD800-\uDBFF](?![\uDC00-\uDFFF])|(?<![\uD800-\uDBFF])[\uDC00-\uDFFF]/u.test(value);
// Frozen Unicode16 Cc/Cf/Cs and White_Space. No ambient Unicode tables,
// trim(), normalization or case folding participate in identifier validation.
const forbiddenRanges: readonly (readonly [number, number])[] = [
  [0x0, 0x1F],
  [0x7F, 0x9F],
  [0xAD, 0xAD],
  [0x600, 0x605],
  [0x61C, 0x61C],
  [0x6DD, 0x6DD],
  [0x70F, 0x70F],
  [0x890, 0x891],
  [0x8E2, 0x8E2],
  [0x180E, 0x180E],
  [0x200B, 0x200F],
  [0x202A, 0x202E],
  [0x2060, 0x2064],
  [0x2066, 0x206F],
  [0xD800, 0xDFFF],
  [0xFEFF, 0xFEFF],
  [0xFFF9, 0xFFFB],
  [0x110BD, 0x110BD],
  [0x110CD, 0x110CD],
  [0x13430, 0x1343F],
  [0x1BCA0, 0x1BCA3],
  [0x1D173, 0x1D17A],
  [0xE0001, 0xE0001],
  [0xE0020, 0xE007F],
];
const edgeWhiteSpaceRanges: readonly (readonly [number, number])[] = [
  [0x9, 0xD],
  [0x20, 0x20],
  [0x85, 0x85],
  [0xA0, 0xA0],
  [0x1680, 0x1680],
  [0x2000, 0x200A],
  [0x2028, 0x2028],
  [0x2029, 0x2029],
  [0x202F, 0x202F],
  [0x205F, 0x205F],
  [0x3000, 0x3000],
];
const inRanges = (cp: number, ranges: readonly (readonly [number, number])[]): boolean =>
  ranges.some(([low, high]) => cp >= low && cp <= high);
function scalarText(value: unknown, maxScalars: number, maxBytes: number): value is string {
  // Cheap length preflight precedes the scalar walk and UTF-8 accounting.
  if (typeof value !== 'string' || !value.length || value.length > maxScalars * 2 || value.length > maxBytes) return false;
  let scalars = 0, bytes = 0, first = -1, last = -1;
  for (const char of value) {
    const cp = char.codePointAt(0)!;
    if (inRanges(cp, forbiddenRanges)) return false;
    if (++scalars > maxScalars) return false;
    bytes += cp <= 0x7f ? 1 : cp <= 0x7ff ? 2 : cp <= 0xffff ? 3 : 4;
    if (bytes > maxBytes) return false;
    if (first < 0) first = cp;
    last = cp;
  }
  return !inRanges(first, edgeWhiteSpaceRanges) && !inRanges(last, edgeWhiteSpaceRanges);
}
const id = (value: unknown): value is string => scalarText(value, ID_SCALARS, ID_BYTES) && !/[*?\[\]{}]/u.test(value);
const runtimeId = (value: unknown): value is string => typeof value === 'string' && value.length <= MAX_RUNTIME_UNITS &&
  scalarText(value, MAX_RUNTIME_UNITS, MAX_RUNTIME_BYTES) && !value.includes('*');
const surfaceName = (value: unknown): value is string => typeof value === 'string' &&
  value.length <= 64 && /^[A-Za-z0-9]/.test(value) && !/[^A-Za-z0-9._-]/.test(value);
const folderName = (value: unknown): value is string => typeof value === 'string' &&
  value.length <= 128 && /^[A-Za-z0-9]/.test(value) && !/[^A-Za-z0-9 ._-]/.test(value) && !value.endsWith(' ');
const bindingText = (value: unknown): value is string => typeof value === 'string' &&
  value.length === 76 && /^openclaw:v1:[0-9a-f]{64}$/.test(value);
const digestText = (value: unknown): value is string => typeof value === 'string' &&
  value.length === 64 && /^[0-9a-f]{64}$/.test(value);
function workspace(value: unknown): value is string {
  if (!scalarText(value, WORKSPACE_BYTES, WORKSPACE_BYTES) || /[*?\[\]{}]/u.test(value)) return false;
  let parts: string[];
  if (value.startsWith('/') && !value.startsWith('//')) {
    if (value.includes('\\')) return false;
    parts = value.slice(1).split('/');
  } else if (/^[A-Za-z]:\\/.test(value)) {
    if (value.includes('/')) return false;
    parts = value.slice(3).split('\\');
  } else if (value.startsWith('\\\\')) {
    if (value.includes('/')) return false;
    parts = value.slice(2).split('\\');
    if (parts.length < 2) return false;
  } else return false;
  return parts.every(part => part !== '.' && part !== '..' && scalarText(part, WORKSPACE_BYTES, WORKSPACE_BYTES));
}
const keyFieldValid = (field: typeof keyFields[number], value: unknown): boolean => field === 'agentId' ? id(value) : runtimeId(value);
const identityFieldValid = (field: typeof identityFields[number], value: unknown): boolean =>
  field === 'workspaceDir' ? workspace(value) : keyFields.includes(field as typeof keyFields[number])
    ? keyFieldValid(field as typeof keyFields[number], value) : id(value);
const originalFieldValid = (field: string, value: unknown): boolean => {
  if (field === 'workspaceDir') return workspace(value);
  if (field === 'surface') return surfaceName(value);
  if (field === 'binding') return bindingText(value);
  if (['sessionId', 'sessionKey', 'incarnation'].includes(field)) return runtimeId(value);
  return id(value);
};
const keysOnly = (value: Record<string, unknown>, allowed: readonly string[]): boolean =>
  Reflect.ownKeys(value).every(key => typeof key === 'string' && allowed.includes(key));
const immutable = <T>(value: T): T => {
  if (typeof value === 'object' && value !== null && !Object.isFrozen(value)) {
    for (const child of Object.values(value)) immutable(child);
    Object.freeze(value);
  }
  return value;
};
const transition = <T>(state: IdentityState, result: Result<T>): Transition<T> => immutable({ state, result });
const copyKey = (key: RunKey): RunKey => ({ agentId: key.agentId, sessionKey: key.sessionKey, sessionId: key.sessionId, runId: key.runId });
const validKey = (key: unknown): key is RunKey => record(key) && keyFields.every(field => keyFieldValid(field, key[field]));
const runIndex = (state: IdentityState, key: RunKey): number => state.runs.findIndex(run => equal(run.key, copyKey(key)));
const sessionIndex = (state: IdentityState, key: Pick<RunKey, 'agentId' | 'sessionId'>): number =>
  state.sessions.findIndex(session => session.original.agentId === key.agentId && session.original.sessionId === key.sessionId);
/** Present fields here must be independent authenticated host observations.
 * Missing/invalid fields cannot invent a contradiction. A live ticket may only
 * affect its own physical transcript; epoch/generation/liveness checks precede
 * this call. Full identity validation still follows and refuses incomplete data. */
function physicalContradiction(state: IdentityState, identity: PromptIdentity, key: RunKey): number {
  if (!record(identity) || !id(identity.agentId) || !runtimeId(identity.sessionId) ||
      identity.agentId !== key.agentId || identity.sessionId !== key.sessionId) return -1;
  const index = sessionIndex(state, identity); if (index < 0) return -1;
  const original = state.sessions[index].original;
  const fields = ['sessionKey', 'workspaceDir', 'channel', 'accountId', 'chatId'] as const;
  return fields.some(field => identityFieldValid(field, identity[field]) && original[field] !== identity[field]) ||
    (id(identity.nativeChatId) && original.chatId !== identity.nativeChatId) ? index : -1;
}
const replaceRun = (state: IdentityState, index: number, run: Run): IdentityState => immutable({ ...state,
  runs: index < 0 ? [...state.runs, run] : state.runs.map((item, i) => i === index ? run : item) });
const revoke = (state: IdentityState, index: number, reason: Refusal, poison = false): Transition<never> =>
  transition(index < 0 ? state : replaceRun(state, index, { ...state.runs[index], status: poison ? 'poisoned' : 'revoked' }), no(reason));
const poisonPhysical = (state: IdentityState, index: number): IdentityState => {
  const original = state.sessions[index].original;
  return immutable({ ...state,
    sessions: state.sessions.map((session, i) => i === index ? { ...session, status: 'poisoned' as const } : session),
    runs: state.runs.map(run => run.key.agentId === original.agentId && run.key.sessionId === original.sessionId
      ? { ...run, status: 'poisoned' as const } : run) });
};
const codePointOrder = (left: string, right: string): number => {
  const a = Array.from(left, ch => ch.codePointAt(0)!); const b = Array.from(right, ch => ch.codePointAt(0)!);
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] - b[i];
  return a.length - b.length;
};
export function bindingFor(route: BindingInput): string {
  return 'openclaw:v1:' + hash(JSON.stringify(['axis.openclaw-chat-binding/v1', route.projectId, route.instanceId,
    route.agentId, route.channel, route.accountId, route.chatId, route.kind, route.ownerSenderId,
    [...route.participantSenderIds].sort(codePointOrder)]));
}
/** Selected portable parser encoding, supplied by Main. Never substitute the runtime digest. */
export function rowPolicyDigestFor(route: Pick<Route, 'binding' | 'surface' | 'role' | 'readScope'>): string {
  return hash(JSON.stringify(['axis.openclaw-chat-policy/v1', route.binding, route.surface, route.role, route.readScope]));
}
/** Adapter-local consistency digest; this wider state is not the portable surface row. */
export function runtimePolicyDigestFor(route: Omit<Route, 'runtimePolicyDigest'>): string {
  return hash(JSON.stringify(['axis.strict-runtime-identity-policy/v1', route.rowPolicyDigest, route.workspaceDir,
    route.revision, route.messageProvider ?? null, route.channelId ?? null]));
}
const denseArray = (value: unknown, maximum: number, minimum = 0): value is readonly unknown[] => {
  if (!Array.isArray(value) || value.length < minimum || value.length > maximum) return false;
  for (let index = 0; index < value.length; index++) if (!Object.hasOwn(value, index)) return false;
  return true;
};
const denseIds = (value: unknown, maximum: number, minimum = 0): value is readonly string[] => {
  if (!denseArray(value, maximum, minimum)) return false;
  for (let index = 0; index < value.length; index++) if (!id(value[index])) return false;
  return true;
};
const validReadScope = (scope: Route['readScope']): boolean => scope === 'project' ||
  (denseArray(scope, MAX_READ_FOLDERS, 1) && scope.every(folderName));
function validPolicy(policy: StrictPolicy): boolean {
  if (!record(policy) || !id(policy.instanceId) || policy.physicalKey !== 'instance-agent-session' ||
      !denseArray(policy.routes, MAX_SESSIONS) ||
      !keysOnly(policy, ['instanceId', 'physicalKey', 'routes'])) return false;
  const routeIds = ['projectId', 'instanceId', 'agentId', 'channel', 'accountId', 'chatId',
    'ownerSenderId'] as const;
  const seenRoutes = new Set<string>(); const seenSurfaces = new Set<string>();
  const agentProjects = new Map<string, string>(); const projectRoots = new Map<string, string>(); const rootProjects = new Map<string, string>();
  let stringUnits = policy.instanceId.length + policy.physicalKey.length;
  // Validate the entire bounded input shape before sorting, hashing or cloning
  // any route, so an invalid later route cannot trigger earlier digest work.
  for (let routeIndex = 0; routeIndex < policy.routes.length; routeIndex++) {
    const route = policy.routes[routeIndex];
    if (!record(route) || !keysOnly(route, ['projectId', 'instanceId', 'agentId', 'channel', 'accountId', 'chatId', 'kind',
      'ownerSenderId', 'participantSenderIds', 'workspaceDir', 'surface', 'role', 'readScope', 'revision', 'binding',
      'rowPolicyDigest', 'runtimePolicyDigest', 'messageProvider', 'channelId'])) return false;
    if (!routeIds.every(field => id(route[field])) || route.instanceId !== policy.instanceId ||
      !workspace(route.workspaceDir) || !surfaceName(route.surface) || !runtimeId(route.revision) ||
      !roles.includes(route.role) || !['direct', 'group'].includes(route.kind) ||
      (ownerOnly(route.role) && route.kind !== 'direct') ||
      !denseIds(route.participantSenderIds, MAX_PARTICIPANTS) ||
      route.participantSenderIds.includes(route.ownerSenderId) || (route.kind === 'direct' && route.participantSenderIds.length !== 0) ||
      !validReadScope(route.readScope) ||
      (['GroupAgent', 'Observer'].includes(route.role) && route.readScope === 'project') ||
      (route.messageProvider !== undefined && !runtimeId(route.messageProvider)) ||
      (route.channelId !== undefined && !runtimeId(route.channelId)) ||
      !bindingText(route.binding) || !digestText(route.rowPolicyDigest) || !digestText(route.runtimePolicyDigest)) return false;
    for (const field of routeIds) stringUnits += route[field].length;
    stringUnits += route.workspaceDir.length + route.surface.length + route.revision.length + (route.messageProvider?.length ?? 0) + (route.channelId?.length ?? 0) +
      route.binding.length + route.rowPolicyDigest.length + route.runtimePolicyDigest.length + route.kind.length + route.role.length;
    for (let index = 0; index < route.participantSenderIds.length; index++) stringUnits += route.participantSenderIds[index].length;
    if (route.readScope === 'project') stringUnits += route.readScope.length;
    else for (let index = 0; index < route.readScope.length; index++) stringUnits += route.readScope[index].length;
    if (stringUnits > MAX_POLICY_STRING_UNITS) return false;
    const tuple = JSON.stringify([route.agentId, route.channel, route.accountId, route.chatId]);
    const surfaceKey = JSON.stringify([route.projectId, route.surface]);
    if (seenRoutes.has(tuple) || seenSurfaces.has(surfaceKey) ||
        (agentProjects.has(route.agentId) && agentProjects.get(route.agentId) !== route.projectId) ||
        (projectRoots.has(route.projectId) && projectRoots.get(route.projectId) !== route.workspaceDir) ||
        (rootProjects.has(route.workspaceDir) && rootProjects.get(route.workspaceDir) !== route.projectId)) return false;
    agentProjects.set(route.agentId, route.projectId);
    if (agentProjects.size > MAX_AGENTS) return false;
    seenRoutes.add(tuple); seenSurfaces.add(surfaceKey);
    projectRoots.set(route.projectId, route.workspaceDir); rootProjects.set(route.workspaceDir, route.projectId);
  }
  for (let routeIndex = 0; routeIndex < policy.routes.length; routeIndex++) {
    const route = policy.routes[routeIndex];
    if (new Set(route.participantSenderIds).size !== route.participantSenderIds.length ||
      (route.readScope !== 'project' && new Set(route.readScope).size !== route.readScope.length) ||
      route.binding !== bindingFor(route) || route.rowPolicyDigest !== rowPolicyDigestFor(route) ||
      route.runtimePolicyDigest !== runtimePolicyDigestFor(route)) return false;

  }
  return true;
}
const clonePolicy = (policy: StrictPolicy): StrictPolicy => ({ ...policy,
  routes: policy.routes.map(route => ({ ...route, participantSenderIds: [...route.participantSenderIds],
    readScope: route.readScope === 'project' ? 'project' : [...route.readScope] })) });
export function createIdentityState(policy: StrictPolicy, epoch: string): Result<IdentityState> {
  if (!runtimeId(epoch)) return no('invalid-epoch');
  if (!validPolicy(policy)) return no('invalid-policy');
  return yes(immutable({ epoch, policy: clonePolicy(policy), policyValid: true, nextGeneration: 1, sessions: [], runs: [] }));
}
export function replacePolicy(state: IdentityState, policy: StrictPolicy): Transition<null> {
  const valid = validPolicy(policy) && policy.instanceId === state.policy.instanceId;
  const next = immutable({ ...state, policy: valid ? clonePolicy(policy) : state.policy, policyValid: valid,
    runs: state.runs.map(run => ({ ...run, status: 'revoked' as const })) });
  return transition(next, valid ? yes(null) : no('invalid-policy'));
}
function routeFor(state: IdentityState, identity: Pick<PromptIdentity, 'agentId' | 'channel' | 'accountId' | 'chatId'>): Result<Route> {
  if (!state.policyValid) return no('invalid-policy');
  const routes = state.policy.routes.filter(route => route.agentId === identity.agentId && route.channel === identity.channel &&
    route.accountId === identity.accountId && route.chatId === identity.chatId);
  return routes.length === 1 ? yes(routes[0]) : no('undeclared-route');
}
function validOriginal(original: OriginalAudience): boolean {
  return record(original) && ['agentId', 'sessionId', 'sessionKey', 'incarnation', 'workspaceDir', 'channel',
    'accountId', 'chatId', 'surface', 'binding'].every(field => originalFieldValid(field, original[field])) && roles.includes(original.role) &&
    keysOnly(original, ['agentId', 'sessionId', 'sessionKey', 'incarnation', 'workspaceDir', 'channel',
      'accountId', 'chatId', 'surface', 'binding', 'role']);
}
export function observeSession(state: IdentityState, evidence: OriginEvidence): Transition<SessionTicket> {
  if (!record(evidence) || evidence.epoch !== state.epoch || evidence.physicalIdentityVerified !== true ||
      evidence.originalAudienceVerified !== true || !['creation', 'original-audience'].includes(evidence.kind))
    return transition(state, no('origin-unverified'));
  // Current, independently authenticated evidence can contradict ownership even
  // when another field is absent. Incomplete evidence never creates ownership.
  if (record(evidence.original) && id(evidence.original.agentId) && runtimeId(evidence.original.sessionId)) {
    const known = sessionIndex(state, evidence.original);
    if (known >= 0) {
      const prior = state.sessions[known].original;
      const fields = ['sessionKey', 'incarnation', 'workspaceDir', 'channel', 'accountId', 'chatId', 'surface', 'binding'] as const;
      if (fields.some(field => originalFieldValid(field, evidence.original[field]) && evidence.original[field] !== prior[field]) ||
          (roles.includes(evidence.original.role) && evidence.original.role !== prior.role))
        return transition(poisonPhysical(state, known), no('origin-contradiction'));
    }
  }
  if (!validOriginal(evidence.original)) return transition(state, no('origin-unverified'));
  const original = evidence.original; const index = sessionIndex(state, original);
  if (index >= 0) {
    if (!equal(state.sessions[index].original, original)) return transition(poisonPhysical(state, index), no('origin-contradiction'));
    if (state.sessions[index].status !== 'active') return transition(state, no(state.sessions[index].status === 'poisoned' ? 'session-poisoned' : 'session-ended'));
  }
  const found = routeFor(state, original);
  if (!found.ok) return transition(state, found);
  const route = found.value;
  if (route.binding !== original.binding || route.role !== original.role || route.surface !== original.surface ||
      route.workspaceDir !== original.workspaceDir) return transition(state, no('origin-contradiction'));
  if (index < 0 && state.sessions.length >= MAX_SESSIONS) return transition(state, no('capacity'));
  const next = index < 0 ? immutable({ ...state, sessions: [...state.sessions, { original: { ...original }, status: 'active' as const }] }) : state;
  return transition(next, yes({ epoch: state.epoch, agentId: original.agentId, sessionId: original.sessionId, incarnation: original.incarnation }));
}
export function beginPreparation(state: IdentityState, key: RunKey): Transition<PreparationTicket> {
  if (!validKey(key)) return transition(state, no('missing-key'));
  if (!state.policyValid) return transition(state, no('invalid-policy'));
  const index = runIndex(state, key); const existing = state.runs[index];
  if (existing?.status === 'poisoned') return transition(state, no('run-poisoned'));
  if (existing && ['revoked', 'ended'].includes(existing.status)) return transition(state, no('run-revoked'));
  if (index < 0 && state.runs.length >= MAX_RUNS) return transition(state, no('capacity'));
  const generation = state.nextGeneration;
  const next = replaceRun({ ...state, nextGeneration: generation + 1 }, index,
    { key: copyKey(key), generation, status: 'building', ...(existing?.frozen ? { frozen: existing.frozen } : {}) });
  return transition(next, yes({ epoch: state.epoch, key: copyKey(key), generation }));
}
function ticketIndex(state: IdentityState, ticket: PreparationTicket): number {
  if (!record(ticket) || ticket.epoch !== state.epoch || !validKey(ticket.key) || !Number.isSafeInteger(ticket.generation)) return -1;
  const index = runIndex(state, ticket.key);
  return index >= 0 && state.runs[index].generation === ticket.generation ? index : -1;
}
function identityCheck(state: IdentityState, identity: PromptIdentity): Result<{ route: Route; principal: Principal; identity: PromptIdentity }> {
  if (!record(identity) || !identityFields.every(field => identityFieldValid(field, identity[field])) ||
      !['nativeSenderId', 'directPeerId'].every(field => identity[field] === undefined || id(identity[field])) ||
      !['messageProvider', 'channelId'].every(field => identity[field] === undefined || runtimeId(identity[field])) ||
      !keysOnly(identity, [...identityFields, 'nativeSenderId', 'messageProvider', 'channelId', 'directPeerId'])) return no('invalid-identity');
  const found = routeFor(state, identity); if (!found.ok) return found;
  const route = found.value;
  if (identity.workspaceDir !== route.workspaceDir) return no('workspace');
  if (identity.nativeChatId !== identity.chatId) return no('native-chat');
  if (identity.nativeSenderId !== undefined && identity.nativeSenderId !== identity.senderId) return no('native-sender');
  if ((identity.messageProvider !== undefined && identity.messageProvider !== route.messageProvider) ||
      (identity.channelId !== undefined && identity.channelId !== route.channelId)) return no('alias');
  const owner = identity.senderId === route.ownerSenderId;
  if (!owner && !route.participantSenderIds.includes(identity.senderId)) return no('sender');
  if (ownerOnly(route.role) && (!owner || route.kind !== 'direct' || identity.directPeerId !== route.ownerSenderId)) return no('owner-direct');
  const clean: PromptIdentity = { ...copyKey(identity), workspaceDir: identity.workspaceDir, channel: identity.channel,
    accountId: identity.accountId, chatId: identity.chatId, senderId: identity.senderId, nativeChatId: identity.nativeChatId,
    ...(identity.nativeSenderId === undefined ? {} : { nativeSenderId: identity.nativeSenderId }),
    ...(identity.messageProvider === undefined ? {} : { messageProvider: identity.messageProvider }),
    ...(identity.channelId === undefined ? {} : { channelId: identity.channelId }),
    ...(identity.directPeerId === undefined ? {} : { directPeerId: identity.directPeerId }) };
  return yes({ route, principal: owner ? 'owner' : 'participant', identity: clean });
}
function provenanceCheck(provenance: ExternalUserProvenance): boolean {
  const optional = ['originSessionId', 'sourceSessionKey', 'sourceChannel', 'sourceTool'];
  return record(provenance) && provenance.kind === 'external_user' && keysOnly(provenance, ['kind', ...optional]) &&
    optional.every(field => provenance[field] === undefined || (field === 'sourceChannel' ? id(provenance[field]) : runtimeId(provenance[field])));
}
function sessionCheck(state: IdentityState, identity: PromptIdentity, route: Route): Result<number> {
  const index = sessionIndex(state, identity); if (index < 0) return no('session-unproven');
  const session = state.sessions[index];
  if (session.status === 'poisoned') return no('session-poisoned');
  if (session.status === 'ended') return no('session-ended');
  const original = session.original;
  if (original.sessionKey !== identity.sessionKey || original.binding !== route.binding || original.role !== route.role ||
      original.surface !== route.surface || original.workspaceDir !== identity.workspaceDir || original.channel !== identity.channel ||
      original.accountId !== identity.accountId || original.chatId !== identity.chatId) return no('origin-contradiction');
  return yes(index);
}
/** Preview for the host's real token estimator; this creates no prepared state. */
export function previewContribution(state: IdentityState, ticket: PreparationTicket, identity: PromptIdentity, roleText: string): Result<string> {
  if (ticketIndex(state, ticket) < 0) return no('stale-generation');
  const check = identityCheck(state, identity); if (!check.ok) return check;
  if (!unicodeText(roleText) || !roleText.trim() || roleText.includes(OPEN) || roleText.includes('</axis-strict-context>')) return no('guidance');
  const route = check.value.route;
  const notice = JSON.stringify({ surface: route.surface, role: route.role, principal: check.value.principal,
    binding: route.binding, rowPolicyDigest: route.rowPolicyDigest, runtimePolicyDigest: route.runtimePolicyDigest });
  const contribution = `${OPEN}epoch=${JSON.stringify(state.epoch)} generation=${ticket.generation}>\n${roleText}\nTrusted surface: ${notice}\n</axis-strict-context>`;
  return contribution.length <= MAX_CONTRIBUTION_CHARS ? yes(contribution) : no('guidance');
}
function budgetCheck(witness: BudgetWitness, contribution: string): boolean {
  if (!record(witness) || !keysOnly(witness, ['measuredText', 'estimatedTokens', 'contextTokenBudget', 'contextWindow']) ||
      witness.measuredText !== contribution || !Number.isSafeInteger(witness.estimatedTokens) || witness.estimatedTokens <= 0) return false;
  const bounds = [witness.contextTokenBudget, witness.contextWindow].filter(value => value !== undefined);
  return bounds.length > 0 && bounds.every(value => typeof value === 'number' && Number.isSafeInteger(value) && value > 0) &&
    witness.estimatedTokens <= Math.min(...bounds as number[]);
}
function assemblyCheck(assembly: PrepareInput['assembly']): boolean {
  return record(assembly) && keysOnly(assembly, ['verified', 'placement', 'before', 'after']) &&
    assembly.verified === true && assembly.placement === 'unquoted-system' &&
    unicodeText(assembly.before) && unicodeText(assembly.after) &&
    assembly.before.length + assembly.after.length <= 1_000_000 &&
    !assembly.before.includes(OPEN) && !assembly.after.includes(OPEN);
}
export function completePreparation(state: IdentityState, ticket: PreparationTicket, input: PrepareInput): Transition<Prepared> {
  const index = ticketIndex(state, ticket); if (index < 0) return transition(state, no('stale-generation'));
  const run = state.runs[index];
  if (!['building', 'prepared'].includes(run.status)) return transition(state, no(run.status === 'poisoned' ? 'run-poisoned' : 'run-revoked'));
  if (!record(input) || input.hookActive !== true) return revoke(state, index, 'hook-inactive');
  const conflict = physicalContradiction(state, input.identity, ticket.key);
  if (conflict >= 0) return transition(poisonPhysical(state, conflict), no('origin-contradiction'));
  const check = identityCheck(state, input.identity); if (!check.ok) return revoke(state, index, check.reason);
  if (!equal(copyKey(input.identity), ticket.key)) return revoke(state, index, 'run-contradiction', true);
  const { route, principal, identity } = check.value;
  const physical = sessionCheck(state, identity, route);
  if (!physical.ok) {
    const si = sessionIndex(state, identity);
    return physical.reason === 'origin-contradiction' && si >= 0
      ? transition(poisonPhysical(state, si), physical) : revoke(state, index, physical.reason);
  }
  if (!provenanceCheck(input.provenance)) return revoke(state, index, 'provenance');
  if (!assemblyCheck(input.assembly)) return revoke(state, index, 'assembly-unverified');
  const frameDigest = hash(JSON.stringify([input.assembly.before, input.assembly.after, input.assembly.placement]));
  if (run.frozen && (!equal(run.frozen.identity, identity) || !equal(run.frozen.provenance, input.provenance) ||
      !equal(run.frozen.policy, route) || run.frozen.roleText !== input.roleText || run.frozen.frameDigest !== frameDigest)) return revoke(state, index, 'run-contradiction', true);
  const preview = previewContribution(state, ticket, identity, input.roleText); if (!preview.ok) return revoke(state, index, preview.reason);
  if (!budgetCheck(input.budget, preview.value)) return revoke(state, index, 'budget');
  const frozen: FrozenPreparation = immutable({ kind: 'identity-match-only', role: route.role, principal,
    surface: route.surface, binding: route.binding, rowPolicyDigest: route.rowPolicyDigest, runtimePolicyDigest: route.runtimePolicyDigest,
    ticket: { epoch: ticket.epoch, key: copyKey(ticket.key), generation: ticket.generation },
    contribution: preview.value, contributionDigest: hash(preview.value), identity, provenance: { ...input.provenance },
    policy: route, roleText: input.roleText,
    budget: { measuredText: input.budget.measuredText, estimatedTokens: input.budget.estimatedTokens,
      ...(input.budget.contextTokenBudget === undefined ? {} : { contextTokenBudget: input.budget.contextTokenBudget }),
      ...(input.budget.contextWindow === undefined ? {} : { contextWindow: input.budget.contextWindow }) }, frameDigest,
    expectedSystemPromptDigest: hash(input.assembly.before + preview.value + input.assembly.after) });
  if (run.status === 'prepared') return equal(run.frozen, frozen) ? transition(state, yes(preparedView(frozen))) : revoke(state, index, 'run-contradiction', true);
  return transition(replaceRun(state, index, { ...run, frozen, status: 'prepared' }), yes(preparedView(frozen)));
}
export function modelGate(state: IdentityState, ticket: PreparationTicket, input: ModelInput): Transition<IdentityMatch> {
  const index = ticketIndex(state, ticket); if (index < 0) return transition(state, no('not-prepared'));
  const run = state.runs[index]; const frozen = run.frozen;
  if (!frozen || !['prepared', 'admitted'].includes(run.status)) return transition(state, no('not-prepared'));
  if (!record(input) || input.hookActive !== true) return revoke(state, index, 'hook-inactive');
  const conflict = physicalContradiction(state, input.identity, ticket.key);
  if (conflict >= 0) return transition(poisonPhysical(state, conflict), no('origin-contradiction'));
  const current = identityCheck(state, input.identity); if (!current.ok) return revoke(state, index, current.reason);
  if (!equal(copyKey(current.value.identity), ticket.key)) return revoke(state, index, 'run-contradiction', true);
  const physical = sessionCheck(state, current.value.identity, current.value.route);
  if (!physical.ok) {
    const si = sessionIndex(state, current.value.identity);
    return physical.reason === 'origin-contradiction' && si >= 0
      ? transition(poisonPhysical(state, si), physical) : revoke(state, index, physical.reason);
  }
  if (!equal(frozen.policy, current.value.route)) return revoke(state, index, 'policy-changed');
  if (!equal(frozen.identity, current.value.identity)) return revoke(state, index, 'run-contradiction', true);
  // Compare complete bytes and a precommitted full-frame digest. The caller's
  // verified unquoted assembly is still an assumption, not authentication here.
  if (!unicodeText(input.systemPrompt) || !input.systemPrompt.includes(frozen.contribution) ||
      hash(input.systemPrompt) !== frozen.expectedSystemPromptDigest ||
      input.systemPrompt.split(OPEN).length !== 2) return revoke(state, index, 'final-prompt');
  return transition(replaceRun(state, index, { ...run, status: 'admitted' }), yes(match(frozen)));
}
function match(frozen: FrozenPreparation): IdentityMatch {
  return { kind: 'identity-match-only', role: frozen.role, principal: frozen.principal,
    surface: frozen.surface, binding: frozen.binding, rowPolicyDigest: frozen.rowPolicyDigest, runtimePolicyDigest: frozen.runtimePolicyDigest };
}
export function checkToolIdentity(state: IdentityState, input: ToolInput): Result<IdentityMatch> {
  if (!record(input) || input.epoch !== state.epoch) return no('stale-event');
  if (!record(input) || !validKey(input.key)) return no('missing-key');
  const index = runIndex(state, input.key); const run = state.runs[index]; const frozen = run?.frozen;
  if (!run || run.status !== 'admitted' || !frozen) return no('not-admitted');
  if (input.aborted !== false || input.invocationCurrent !== true) return no('aborted');
  if (input.eventRunId !== undefined && input.eventRunId !== input.key.runId) return no('event-run');
  const found = routeFor(state, frozen.identity); if (!found.ok) return found;
  if (!equal(found.value, frozen.policy)) return no('policy-changed');
  const physical = sessionCheck(state, frozen.identity, found.value); if (!physical.ok) return physical;
  const requester = input.requester;
  if (!record(requester) || ['channel', 'accountId', 'senderId'].some(field =>
      requester[field] !== frozen.identity[field as 'channel' | 'accountId' | 'senderId'])) return no('requester');
  if (requester.senderIsOwner !== undefined && typeof requester.senderIsOwner !== 'boolean') return no('owner');
  const owner = requester.senderId === frozen.policy.ownerSenderId && requester.senderIsOwner === true;
  if (ownerOnly(frozen.role) && !owner) return no('owner');
  if (input.channelId !== undefined && input.channelId !== frozen.policy.channelId) return no('alias');
  if (!['read', 'status'].includes(input.operation)) return no('operation');
  return immutable(yes(match(frozen)));
}
export function expirePreparation(state: IdentityState, ticket: PreparationTicket): Transition<null> {
  const index = ticketIndex(state, ticket); if (index < 0) return transition(state, no('stale-event'));
  return transition(replaceRun(state, index, { ...state.runs[index], status: 'revoked' }), yes(null));
}
export function endRun(state: IdentityState, ticket: PreparationTicket): Transition<null> {
  const index = ticketIndex(state, ticket); if (index < 0) return transition(state, no('stale-event'));
  return transition(replaceRun(state, index, { ...state.runs[index], status: 'ended' }), yes(null));
}
export function endSession(state: IdentityState, ticket: SessionTicket): Transition<null> {
  if (!record(ticket) || ticket.epoch !== state.epoch) return transition(state, no('stale-event'));
  const index = sessionIndex(state, ticket);
  if (index < 0 || state.sessions[index].original.incarnation !== ticket.incarnation) return transition(state, no('stale-event'));
  const next = immutable({ ...state,
    sessions: state.sessions.map((session, i) => i === index && session.status === 'active' ? { ...session, status: 'ended' as const } : session),
    runs: state.runs.map(run => run.key.agentId === ticket.agentId && run.key.sessionId === ticket.sessionId ? { ...run, status: 'ended' as const } : run) });
  return transition(next, yes(null));
}
/** Reload forgets grants and ownership; re-entry still needs independent original-audience evidence. */
export function reload(state: IdentityState, epoch: string): Transition<null> {
  if (!runtimeId(epoch) || epoch === state.epoch) return transition(state, no('invalid-epoch'));
  return transition(immutable({ ...state, epoch, nextGeneration: 1, runs: [], sessions: [] }), yes(null));
}
/** Eviction denies the run; its tombstone prevents reusing a finished key in this epoch. */
export const evictRun = expirePreparation;
