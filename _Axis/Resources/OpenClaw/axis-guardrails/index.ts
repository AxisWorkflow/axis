// Axis guardrails for OpenClaw (optional; `^install guardrails`). For each agent listed under a guarded role's config
// key (the generated table below), refuse before it runs: spawning an agent or session, any use of _Axis/Secrets/, and
// any file write that guardrails.py refuses for that role (changing an existing file, or a new file outside the places
// its row allows). Other agents are untouched. If this hook throws or times out, OpenClaw blocks the call; if
// guardrails.py itself fails or times out, the hook lets the call through. It catches file-tool mistakes; it is not a
// security boundary, because shell commands pass.
// Role context (3.18): on every run of a listed agent, append its role's guidance (the prose of _Axis/Roles/{Role}.md
// after the axis-role block, at most 8,000 characters, as the axis launcher caps it) to the system prompt, so it
// survives compaction. A sub-agent run (a session key with :subagent: or :acp:), a run without a session key, an
// unlisted agent and a missing role file get nothing.
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { spawnSync } from "node:child_process";
import { existsSync, readdirSync, readFileSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const SPAWN = /^(agent|task|spawn_agent|sessions_spawn|subagent|subagents)$/i;
const SECRETS = "_Axis/Secrets";
const ROLE_GUIDANCE_LIMIT = 8000;
const SUBAGENT_SESSION = /:(subagent|acp):/;
type PromptContext = { appendSystemContext?: string };

type Guard = { agents: (api: any) => Set<string>; spawn: string | null; secrets: string; args: (tool: string, path: string) => string[] };
// BEGIN GENERATED: role-table
// Compiled from _Axis/Roles/ at release; edit the role files, never this region.
const DESCRIPTION = "Refuses tool calls by Axis Auxiliary Agents, Assistants, Group Agents and Observers that Axis rules forbid.";
const GUARDED: Guard[] = [
  { agents: (api: any) => new Set<string>(((api as any).pluginConfig?.externalAgents as string[]) ?? []), spawn: "Axis guardrail: an Auxiliary Agent never spawns agents or sessions.", secrets: "Axis guardrail: an Auxiliary Agent never uses _Axis/Secrets/.", args: (tool: string, path: string) => ["--external", tool, path] },
  { agents: (api: any) => new Set<string>(((api as any).pluginConfig?.assistantAgents as string[]) ?? []), spawn: null, secrets: "Axis guardrail: an Assistant never uses _Axis/Secrets/.", args: (tool: string, path: string) => ["--role", "assistant", tool, path] },
  { agents: (api: any) => new Set<string>(((api as any).pluginConfig?.groupAgents as string[]) ?? []), spawn: "Axis guardrail: a Group Agent never spawns agents or sessions.", secrets: "Axis guardrail: a Group Agent never uses _Axis/Secrets/.", args: (tool: string, path: string) => ["--role", "groupagent", tool, path] },
  { agents: (api: any) => new Set<string>(((api as any).pluginConfig?.observerAgents as string[]) ?? []), spawn: "Axis guardrail: an Observer never spawns agents or sessions.", secrets: "Axis guardrail: an Observer never uses _Axis/Secrets/.", args: (tool: string, path: string) => ["--role", "observer", tool, path] },
];
// END GENERATED: role-table

function projectRoot(path: string): string | null {
  let dir = dirname(path);
  for (let i = 0; i < 64; i++) {
    if (existsSync(join(dir, "_Axis/Resources/guardrails.py"))) return dir;
    const up = dirname(dir);
    if (up === dir) return null;
    dir = up;
  }
  return null;
}

// The role a guarded entry serves, from its guardrails.py call: `--role {name}`, or the Auxiliary wire flag.
function roleName(g: Guard): string {
  const call = g.args("", "");
  return call[0] === "--role" ? call[1] : "auxiliary";
}

// The plugin's own project: it is installed from {project}/_Axis/Resources/OpenClaw/axis-guardrails/.
function pluginProject(): string | null {
  try { return resolve(dirname(fileURLToPath(import.meta.url)), "../../../.."); } catch { return null; }
}

// The prose of _Axis/Roles/{Role}.md after its axis-role block, cut at the launcher's cap; "" when missing.
export function roleGuidance(root: string, name: string): string {
  try {
    const dir = join(root, "_Axis/Roles");
    const file = readdirSync(dir).find((f) => f.toLowerCase() === name.toLowerCase() + ".md");
    if (!file) return "";
    const text = readFileSync(join(dir, file), "utf8");
    const open = text.indexOf("```");
    const close = open < 0 ? -1 : text.indexOf("```", open + 3);
    if (close < 0) return "";
    return Array.from(text.slice(close + 3).replace(/^\n+/, "")).slice(0, ROLE_GUIDANCE_LIMIT).join("");
  } catch { return ""; }
}

// roleGuidance first caps the role prose at 8,000 characters. The resulting contribution is added whole or omitted.
// When a run reports its context window, omit a contribution longer than a quarter of it (one character per token).
export function roleContext(listed: (agentId: string) => string | null, event: any, ctx: any, root: string | null): PromptContext {
  const name = listed(String(ctx?.agentId ?? ""));
  const key = ctx?.sessionKey;
  if (!name || typeof key !== "string" || !key || SUBAGENT_SESSION.test(key)) return {};
  const workspace = typeof ctx?.workspaceDir === "string" && existsSync(join(ctx.workspaceDir, "_Axis/Roles")) ? ctx.workspaceDir : root;
  const guidance = workspace ? roleGuidance(workspace, name) : "";
  if (!guidance) return {};
  const window = Number(event?.contextWindow ?? ctx?.contextWindow ?? 0);
  const text = `Axis role guidance for this agent, added by the axis-guardrails plugin from _Axis/Roles/ on every run:\n\n${guidance}`;
  if (window > 0 && Array.from(text).length > window / 4) return {};
  return { appendSystemContext: text };
}

function targetPaths(params: any): string[] {
  const out = new Set<string>();
  for (const key of ["file_path", "path", "notebook_path"]) if (typeof params?.[key] === "string") out.add(params[key]);
  const patch = typeof params?.input === "string" ? params.input : typeof params?.patch === "string" ? params.patch : "";
  for (const m of patch.matchAll(/^\*\*\* (?:Add|Update|Delete) File: (.+)$/gm)) out.add(m[1].trim());
  return [...out];
}

export default definePluginEntry({
  id: "axis-guardrails",
  name: "Axis Guardrails",
  description: DESCRIPTION,
  register(api) {
    const guarded = GUARDED.map((g) => ({ ...g, listed: g.agents(api) }));
    api.on("before_tool_call", (event: any, ctx: any) => {
      const role = guarded.find((g) => g.listed.has(ctx?.agentId));
      if (!role) return {};
      const tool = String(event?.toolName ?? "");
      if (role.spawn && SPAWN.test(tool)) return { block: true, blockReason: role.spawn };
      const params = event?.params ?? {};
      if (JSON.stringify(params).includes(SECRETS)) return { block: true, blockReason: role.secrets };
      for (const raw of targetPaths(params)) {
        const path = isAbsolute(raw) ? raw : resolve(process.cwd(), raw);
        const root = projectRoot(path);
        if (!root) continue;
        const r = spawnSync("python3", [join(root, "_Axis/Resources/guardrails.py"), ...role.args(tool, path)], { cwd: root, encoding: "utf8", timeout: 10000 });
        if (r.status === 2) return { block: true, blockReason: (r.stdout || r.stderr || "Axis guardrail refused this call.").trim() };
      }
      return {};
    });
    const root = pluginProject();
    const listed = (agentId: string): string | null => {
      const g = guarded.find((x) => x.listed.has(agentId));
      return g ? roleName(g) : null;
    };
    api.on("before_prompt_build", (event: any, ctx: any): PromptContext => {
      try { return roleContext(listed, event, ctx, root); } catch { return {}; }
    });
  },
});
