// Axis strict chat gate for OpenClaw: the optional `chatPolicy` branch of axis-guardrails. Inert on every installed
// build: it never admits a chat. With no `chatPolicy` key in the plugin configuration nothing here runs and the plugin
// keeps its legacy behaviour. With the key present, the agents it manages get no service from these hooks:
// before_agent_run blocks the model run on the carriers that call it (the P3 record shows paths that skip it),
// before_tool_call blocks every tool on the carriers that call it, and before_prompt_build adds nothing. A hook without
// an agent ID is refused too, because it cannot prove it is outside that domain. An invalid `chatPolicy` refuses every
// agent of this plugin instance, legacy-listed or not; it never falls back to the legacy branch. The reasons come from
// the host capability record beside this file (host-capabilities.json), which names no build or carrier able to serve a
// strict chat.
// Refusal texts carry codes only, never an agent, account, chat, sender, workspace, project or instance identifier.
// The prompt and tool mappers below turn the pinned host hook shapes into identity-state.ts inputs for a later,
// separately qualified host; no handler here calls them or the reducer's run state.
import { readFileSync } from "node:fs";
import { bindingFor, createIdentityState, rowPolicyDigestFor, runtimePolicyDigestFor } from "./identity-state.ts";
import type { BindingInput, Route } from "./identity-state.ts";

export const CHAT_POLICY_SCHEMA = "axis.openclaw-chats/v1";
const RECORD_SCHEMA = "axis.openclaw-host-capabilities/v1";
const PREDICATES = ["H1", "H2", "H3", "H4", "H5", "tool-requester"] as const;
const TAIL = ["build-unverified", "final-effect-revocation:not-runnable", "live-qualification-absent", "strict-runtime-not-implemented"];
const TOP_KEYS = ["schema", "instanceId", "agents"];
const AGENT_KEYS = ["agentId", "projectId", "workspaceDir", "chats"];
const CHAT_KEYS = ["surface", "channel", "accountId", "chatId", "kind", "ownerSenderId", "participantSenderIds"];
const PREFIX = "Axis strict chat gate: ";
const CHECK = "axis-chat-policy-check";

export type Availability = Readonly<{ strict_admission: "unavailable"; host_pass: false; execution_authority: false; reasons: readonly string[] }>;
export type StrictSetup = Readonly<{ valid: boolean; reason: string; managed: ReadonlySet<string>; availability: Availability }>;
type Plain = Record<string, unknown>;

const plain = (value: unknown): value is Plain => typeof value === "object" && value !== null && !Array.isArray(value);
const exactKeys = (value: Plain, keys: readonly string[]): boolean =>
  Reflect.ownKeys(value).length === keys.length && keys.every((key) => Object.hasOwn(value, key));
const strings = (value: unknown): value is string[] => Array.isArray(value) && value.every((item) => typeof item === "string");
const text = (value: unknown): string | undefined => (typeof value === "string" ? value : undefined);

// The host capability answer. Every value of the record, and a missing or unreadable record, gives unavailable.
export function availability(recordText: string | null): Availability {
  const reasons: string[] = [];
  try {
    const record: unknown = JSON.parse(String(recordText));
    if (!plain(record) || record.schema !== RECORD_SCHEMA || !Array.isArray(record.builds) || record.builds.length === 0) throw new Error("shape");
    const seen = new Map<string, Set<string>>(PREDICATES.map((p) => [p, new Set<string>()]));
    for (const build of record.builds) {
      if (!plain(build) || typeof build.version !== "string" || !plain(build.carriers) || Object.keys(build.carriers).length === 0) throw new Error("build");
      for (const carrier of Object.values(build.carriers)) {
        if (!plain(carrier) || !plain(carrier.predicates)) throw new Error("carrier");
        for (const p of PREDICATES) {
          const entry = carrier.predicates[p];
          if (!plain(entry) || typeof entry.status !== "string") throw new Error("predicate");
          seen.get(p)!.add(entry.status);
        }
      }
    }
    for (const p of PREDICATES) reasons.push(`${p}:${[...seen.get(p)!].sort().join("|")}`);
  } catch {
    reasons.splice(0, reasons.length, "record-invalid");
  }
  return Object.freeze({ strict_admission: "unavailable", host_pass: false, execution_authority: false, reasons: Object.freeze([...reasons, ...TAIL]) });
}

function readRecord(): string | null {
  try { return readFileSync(new URL("./host-capabilities.json", import.meta.url), "utf8"); } catch { return null; }
}

// Validate a chatPolicy. Host-side identifiers go through the selected reducer's own policy validation (exact opaque
// strings, no wildcard, control or edge-space characters, unique routes and surfaces, one workspace per project, owner
// never a participant, a direct chat without participants), with a placeholder row role and scope that the reducer
// accepts for either kind; role and read scope belong to the surface table, never to host configuration. An agent
// with no chats is managed (none of its chats is served); a placeholder route lets the reducer check its identifiers.
function checkRoute(host: BindingInput, workspaceDir: string, surface: string): Route {
  const binding = bindingFor(host);
  const row = { ...host, workspaceDir, surface, role: "Observer" as const, readScope: ["Placeholder"], revision: CHECK, binding,
    rowPolicyDigest: rowPolicyDigestFor({ binding, surface, role: "Observer", readScope: ["Placeholder"] }) };
  return { ...row, runtimePolicyDigest: runtimePolicyDigestFor(row) };
}

export function parseChatPolicy(policy: unknown, legacyAgents: ReadonlySet<string>): { ok: true; managed: Set<string> } | { ok: false; reason: string } {
  if (!plain(policy)) return { ok: false, reason: "not-an-object" };
  if (!exactKeys(policy, TOP_KEYS)) return { ok: false, reason: "keys" };
  if (policy.schema !== CHAT_POLICY_SCHEMA) return { ok: false, reason: "schema" };
  if (typeof policy.instanceId !== "string" || !Array.isArray(policy.agents) || policy.agents.length === 0) return { ok: false, reason: "shape" };
  const managed = new Set<string>(); const routes: Route[] = [];
  for (const agent of policy.agents) {
    if (!plain(agent) || !exactKeys(agent, AGENT_KEYS)) return { ok: false, reason: "agent-keys" };
    const { agentId, projectId, workspaceDir, chats } = agent;
    if (typeof agentId !== "string" || typeof projectId !== "string" || typeof workspaceDir !== "string" || !Array.isArray(chats))
      return { ok: false, reason: "agent-shape" };
    if (managed.has(agentId)) return { ok: false, reason: "agent-duplicate" };
    if (legacyAgents.has(agentId)) return { ok: false, reason: "legacy-overlap" };
    managed.add(agentId);
    if (chats.length === 0) routes.push(checkRoute({ projectId, instanceId: policy.instanceId, agentId, channel: CHECK, accountId: CHECK, chatId: CHECK,
      kind: "direct", ownerSenderId: CHECK, participantSenderIds: [] }, workspaceDir, `${CHECK}-${managed.size}`));
    for (const chat of chats) {
      if (!plain(chat) || !exactKeys(chat, CHAT_KEYS)) return { ok: false, reason: "chat-keys" };
      const { surface, channel, accountId, chatId, kind, ownerSenderId, participantSenderIds } = chat;
      if (![surface, channel, accountId, chatId, ownerSenderId].every((v) => typeof v === "string") || (kind !== "direct" && kind !== "group") ||
          !strings(participantSenderIds)) return { ok: false, reason: "chat-shape" };
      const host = { projectId, instanceId: policy.instanceId, agentId, channel: channel as string, accountId: accountId as string,
        chatId: chatId as string, kind: kind as "direct" | "group", ownerSenderId: ownerSenderId as string, participantSenderIds: [...participantSenderIds] };
      routes.push(checkRoute(host, workspaceDir, surface as string));
    }
  }
  const checked = createIdentityState({ instanceId: policy.instanceId, physicalKey: "instance-agent-session", routes }, CHECK);
  return checked.ok ? { ok: true, managed } : { ok: false, reason: "identifiers" };
}

// Beside a chatPolicy, every other configuration key must be a legacy list of strings, and no agent ID may repeat.
function legacyLists(config: Plain): string | null {
  const ids: string[] = [];
  for (const [key, value] of Object.entries(config)) {
    if (key === "chatPolicy") continue;
    if (!strings(value)) return "legacy-shape";
    ids.push(...value);
  }
  return new Set(ids).size === ids.length ? null : "legacy-duplicate";
}

// The strict branch for one plugin registration, or null when the configuration has no chatPolicy key.
export function strictSetup(config: unknown, legacyAgents: ReadonlySet<string>): StrictSetup | null {
  if (!plain(config) || !Object.hasOwn(config, "chatPolicy")) return null;
  let parsed: ReturnType<typeof parseChatPolicy>;
  try {
    const legacy = legacyLists(config);
    parsed = legacy ? { ok: false, reason: legacy } : parseChatPolicy(config.chatPolicy, legacyAgents);
  } catch { parsed = { ok: false, reason: "unreadable" }; }
  return Object.freeze({ valid: parsed.ok, reason: parsed.ok ? "valid" : parsed.reason, managed: parsed.ok ? parsed.managed : new Set<string>(),
    availability: availability(readRecord()) });
}

// The handlers index.ts uses once it has loaded this module: the strict decision first, the legacy branch outside the domain.
export function strictBranch(config: unknown, legacyAgents: ReadonlySet<string>) {
  const setup: StrictSetup = strictSetup(config, legacyAgents) ??
    Object.freeze({ valid: false, reason: "no-chat-policy", managed: new Set<string>(), availability: availability(null) });
  return {
    tool: (event: any, ctx: any, legacy: () => unknown): unknown => strictTool(setup, event, ctx) ?? legacy(),
    prompt: <T extends object>(ctx: any, legacy: () => T): T | Record<string, never> => (strictPrompt(setup, ctx) ? {} : legacy()),
    run: (event: any, ctx: any) => strictRun(setup, event, ctx),
  };
}

// Whether a hook belongs to the strict domain: everything under an invalid policy, a managed agent, or no agent ID.
function inDomain(setup: StrictSetup, ctx: any): boolean {
  if (!setup.valid) return true;
  const agentId = ctx?.agentId;
  return typeof agentId !== "string" || !agentId || setup.managed.has(agentId);
}

function why(setup: StrictSetup, ctx: any, what: string): string {
  if (!setup.valid) return `${PREFIX}chatPolicy is invalid (${setup.reason}), so every agent of this plugin instance is refused until it is corrected. ${what}`;
  if (typeof ctx?.agentId !== "string" || !ctx.agentId) return `${PREFIX}a call without an agent ID is refused while chatPolicy is configured. ${what}`;
  return `${PREFIX}strict chat service is ${setup.availability.strict_admission} on this host (${setup.availability.reasons.join(", ")}). ${what}`;
}

// before_tool_call: a block for every tool call in the domain, null to leave the call to the legacy branch.
export function strictTool(setup: StrictSetup, event: any, ctx: any): { block: true; blockReason: string } | null {
  try {
    if (!inDomain(setup, ctx)) return null;
    return { block: true, blockReason: why(setup, ctx, "This tool call is refused.") };
  } catch {
    return { block: true, blockReason: `${PREFIX}the strict check failed; the call is refused.` };
  }
}

// before_agent_run: the host's block decision ({outcome: "block", reason}) in the domain; undefined allows.
export function strictRun(setup: StrictSetup, event: any, ctx: any): { outcome: "block"; reason: string } | undefined {
  try {
    if (!inDomain(setup, ctx)) return undefined;
    return { outcome: "block", reason: why(setup, ctx, "This model run is refused.") };
  } catch {
    return { outcome: "block", reason: `${PREFIX}the strict check failed; the run is refused.` };
  }
}

// before_prompt_build: true when the domain gets no prompt context at all.
export function strictPrompt(setup: StrictSetup, ctx: any): boolean {
  try { return inDomain(setup, ctx); } catch { return true; }
}

// Mappers from the pinned host hook shapes to identity-state.ts inputs. A field the host context does not carry stays
// absent; nothing is filled from tool parameters, prompt text, process state or an earlier run.
export function promptIdentity(ctx: any): Plain {
  const out: Plain = {};
  for (const key of ["agentId", "sessionKey", "sessionId", "runId", "workspaceDir", "channel", "accountId", "chatId", "senderId", "messageProvider", "channelId"]) {
    const value = text(ctx?.[key]); if (value !== undefined) out[key] = value;
  }
  const nativeChat = text(ctx?.channelContext?.chat?.id); if (nativeChat !== undefined) out.nativeChatId = nativeChat;
  const nativeSender = text(ctx?.channelContext?.sender?.id); if (nativeSender !== undefined) out.nativeSenderId = nativeSender;
  return out;
}

export function toolInput(event: any, ctx: any, epoch: string, operation: string, invocationCurrent: boolean): Plain {
  const key: Plain = {};
  for (const field of ["agentId", "sessionKey", "sessionId", "runId"]) { const value = text(ctx?.[field]); if (value !== undefined) key[field] = value; }
  const out: Plain = { epoch, key, operation, invocationCurrent: invocationCurrent === true, aborted: ctx?.abortSignal?.aborted === true };
  const raw = ctx?.requester;
  if (plain(raw)) {
    const requester: Plain = {};
    for (const field of ["channel", "accountId", "senderId"]) { const value = text(raw[field]); if (value !== undefined) requester[field] = value; }
    if (typeof raw.senderIsOwner === "boolean") requester.senderIsOwner = raw.senderIsOwner;
    out.requester = requester;
  }
  const eventRun = text(event?.runId); if (eventRun !== undefined) out.eventRunId = eventRun;
  const channelId = text(ctx?.channelId); if (channelId !== undefined) out.channelId = channelId;
  return out;
}
