# Role: Subagent
> **Purpose:** Role-table row for an enveloped Subagent session; compiled into helpers and Command gates at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "Subagent",
  "class": "session",
  "status": "shipped",
  "order": 30,
  "admission": {
    "marker_subject": "Subagent: ",
    "subject_match": "prefix",
    "marker_shape": "free",
    "created_by": "spawner",
    "boot_status": null,
    "entry": "_Axis/Resources/Start-Subagent.md",
    "fallback_beside_live_main": false
  },
  "principals": {
    "serves": "spawner",
    "commands_from": "spawner",
    "returns_to": "spawner"
  },
  "authority": {
    "exclusive_lease": false,
    "approval_level": "advice",
    "scope": null,
    "issuer_token": "worker",
    "proposal_team_owner": false,
    "proposal_issuer_token": null,
    "submit_schema": null,
    "record_families": "delegated",
    "guard": null,
    "tracking_addressee": null,
    "commands": {
      "git": "return the request without acting",
      "install": "return the request without acting",
      "followups": "returns a candidate to Main",
      "merge": "return a proposal to Main",
      "update": "refuse this Command",
      "feedback": "says `^feedback` needs the Main Agent and STOPS",
      "shutdown": "listed"
    }
  },
  "lifecycle": {
    "version_bound": false,
    "blocks_save": true,
    "survey": "count",
    "survey_key": "orphan_subagents",
    "promotable": false,
    "lifetime": "task"
  },
  "presentation": {
    "title": "Subagent",
    "plural": "Subagents",
    "short": "Subagent",
    "article": "a",
    "log_by": null,
    "brand": null,
    "reply_frame": false,
    "reference_word": "Subagent",
    "notice": "{count} orphaned Subagent record(s) from a crashed spawn; ^refresh can clear them"
  }
}
```

A Subagent runs one bounded task for the agent that spawned it and returns its result there. Its delegated kind is one of the delegated rows (CX, Wiki, Local, General); this file holds the session row.
