# Role: General
> **Purpose:** Role-table row for the General delegated Subagent; compiled into the envelope check and guardrails at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "General",
  "class": "delegated",
  "status": "shipped",
  "order": 140,
  "admission": {
    "session_role": "Subagent",
    "envelope_token": "GENERAL",
    "carries_blocks": true
  },
  "authority": {
    "approval_level": "advice",
    "scope": null,
    "guard": {
      "agent_type": "axis-general",
      "write_scope": null,
      "deny": [
        "_Axis/Agents/",
        "_Axis/Flags/",
        "_Axis/Secrets/",
        "_Axis/Submissions/",
        "_Axis/Messages/",
        "_Axis/Teams/",
        "_Axis/Jobs/",
        "_Axis/Schedules/",
        "_Axis/Updates/",
        ".git/",
        ".claude/",
        ".codex/",
        ".gemini/"
      ]
    }
  }
}
```

A General Subagent may write anywhere in the project except the control folders its guard denies. Its contract is in [Start-Subagent].
