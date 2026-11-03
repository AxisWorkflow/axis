# Role: Local
> **Purpose:** Role-table row for the Local delegated Subagent; compiled into the envelope check at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "Local",
  "class": "delegated",
  "status": "shipped",
  "order": 130,
  "admission": {
    "session_role": "Subagent",
    "envelope_token": "LOCAL",
    "carries_blocks": false
  },
  "authority": {
    "approval_level": "advice",
    "scope": null,
    "guard": null
  }
}
```

A Local Subagent is a small local model that receives only the boundary lines, never the carried blocks. Its contract is in [Start-Subagent].
