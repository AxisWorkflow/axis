# Role: Wiki
> **Purpose:** Role-table row for the Wiki delegated Subagent; compiled into the envelope check and guardrails at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "Wiki",
  "class": "delegated",
  "status": "shipped",
  "order": 120,
  "admission": {
    "session_role": "Subagent",
    "envelope_token": "WIKI",
    "carries_blocks": true
  },
  "authority": {
    "approval_level": "advice",
    "scope": [
      [
        "_Wiki/",
        false
      ],
      [
        "_Axis/Wiki/",
        false
      ],
      [
        "_Temp/",
        false
      ]
    ],
    "guard": {
      "agent_type": "axis-wiki",
      "write_scope": [
        [
          "_Wiki/",
          false
        ],
        [
          "_Axis/Wiki/",
          false
        ],
        [
          "_Temp/",
          false
        ]
      ],
      "deny": null
    }
  }
}
```

A Wiki Subagent maintains the Wiki and its bookkeeping. Its guidance is in [Practices > Wiki].
