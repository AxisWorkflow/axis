// Axis guardrails for OpenClaw (optional; `^install guardrails`). For each agent listed in `externalAgents`, refuse
// before it runs: spawning an agent or session, any use of _Axis/Secrets/, and any file write that guardrails.py
// refuses for an External Agent (changing an existing file, or a new file outside Project Subfolders,
// _Axis/Requests/ and _Temp/). Other agents are untouched. A hook error lets the call through, so the written
// Axis rules still apply.
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, isAbsolute, join, resolve } from "node:path";

const SPAWN = /^(agent|task|spawn_agent|sessions_spawn|subagent|subagents)$/i;
const SECRETS = "_Axis/Secrets";

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
  description: "Refuses tool calls by Axis External Agents that Axis rules forbid.",
  register(api) {
    const external = new Set<string>(((api as any).pluginConfig?.externalAgents as string[]) ?? []);
    api.on("before_tool_call", (event: any, ctx: any) => {
      if (!external.has(ctx?.agentId)) return {};
      const tool = String(event?.toolName ?? "");
      if (SPAWN.test(tool)) return { block: true, blockReason: "Axis guardrail: an External Agent never spawns agents or sessions." };
      const params = event?.params ?? {};
      if (JSON.stringify(params).includes(SECRETS)) return { block: true, blockReason: "Axis guardrail: an External Agent never uses _Axis/Secrets/." };
      for (const raw of targetPaths(params)) {
        const path = isAbsolute(raw) ? raw : resolve(process.cwd(), raw);
        const root = projectRoot(path);
        if (!root) continue;
        const r = spawnSync("python3", [join(root, "_Axis/Resources/guardrails.py"), "--external", tool, path], { cwd: root, encoding: "utf8", timeout: 10000 });
        if (r.status === 2) return { block: true, blockReason: (r.stdout || r.stderr || "Axis guardrail refused this call.").trim() };
      }
      return {};
    });
  },
});
