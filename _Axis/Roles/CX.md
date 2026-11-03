# Role: CX
> **Purpose:** Role-table row for the CX delegated Subagent; compiled into the envelope check and guardrails at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "CX",
  "class": "delegated",
  "status": "shipped",
  "order": 110,
  "admission": {
    "session_role": "Subagent",
    "envelope_token": "CX",
    "carries_blocks": true
  },
  "authority": {
    "approval_level": "advice",
    "scope": [
      [
        "_Axis/CX/",
        true
      ],
      [
        "_Temp/",
        false
      ]
    ],
    "guard": {
      "agent_type": "axis-cx",
      "write_scope": [
        [
          "_Axis/CX/",
          true
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

A CX Subagent writes one new report under `_Axis/CX/` and may use `_Temp/`. Its guidance is in [Practices > CX].
