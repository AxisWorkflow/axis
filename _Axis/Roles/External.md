# Role: External
> **Purpose:** Role-table row for an External Agent; compiled into helpers and Command gates at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "External",
  "class": "session",
  "status": "shipped",
  "order": 20,
  "admission": {
    "marker_subject": "External: ",
    "subject_match": "prefix",
    "marker_shape": "single-session-line",
    "created_by": "self",
    "boot_status": "external",
    "entry": "_Axis/Resources/Start-External.md",
    "fallback_beside_live_main": true
  },
  "principals": {
    "serves": "User",
    "commands_from": "User",
    "returns_to": "main-by-message"
  },
  "authority": {
    "exclusive_lease": false,
    "approval_level": "advice",
    "scope": null,
    "issuer_token": "worker",
    "proposal_team_owner": true,
    "proposal_issuer_token": "external",
    "submit_schema": "axis.external-submission/v1",
    "record_families": "today: any family except Agents and Status (helper enforcement is looser than doctrine; Round B1 tightens it)",
    "guard": {
      "openclaw_config_key": "externalAgents",
      "flag": "--external",
      "block_spawn_tools": true,
      "secrets": "refuse",
      "existing_files": "refuse",
      "new_files": [
        "subfolders",
        "_Axis/Submissions/",
        "_Temp/"
      ]
    },
    "tracking_addressee": "External",
    "commands": {
      "git": "send a Message to Main",
      "install": "send a Message to Main",
      "followups": "sends a Message to Main",
      "inbox": "lists the items it sees, writes a Message to Main under [Practices > Messages], and STOPs",
      "memo": "proposes the content to Main through a Message under [Practices > Messages] and STOPs",
      "memos": "lists only, and STOPs",
      "merge": "return a proposal to Main",
      "update": "refuse this Command",
      "kill": "refuses this command (Marker surgery is Mutating for that role): say so, Log it, and STOP",
      "feedback": "says `^feedback` needs the Main Agent and STOPS",
      "status": "listed",
      "shutdown": "listed"
    }
  },
  "lifecycle": {
    "version_bound": true,
    "blocks_save": false,
    "survey": "list",
    "survey_key": "fresh_external",
    "promotable": true,
    "lifetime": "session"
  },
  "presentation": {
    "title": "External Agent",
    "plural": "External Agents",
    "short": "External",
    "article": "an",
    "log_by": "External Agent",
    "brand": "Axis Workflow | External",
    "reply_frame": true,
    "reference_word": "External",
    "notice": "An External Agent is serving this project ({id})."
  }
}
```

An External Agent serves User beside a live Main, proposes rather than accepts, and reaches Main through Messages and Submissions. Guidance for this role remains in Start-External and the Rules; this file holds its table row.
