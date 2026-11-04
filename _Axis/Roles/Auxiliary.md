# Role: Auxiliary
> **Purpose:** Role-table row for an Auxiliary Agent; compiled into helpers and Command gates at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "Auxiliary",
  "class": "session",
  "status": "shipped",
  "order": 20,
  "admission": {
    "marker_subject": "Auxiliary: ",
    "subject_match": "prefix",
    "marker_shape": "single-session-line",
    "created_by": "self",
    "boot_status": "external",
    "entry": "_Axis/Resources/Start-Auxiliary.md",
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
    "proposal_issuer_token": "auxiliary",
    "submit_schema": "axis.external-submission/v1",
    "record_families": "today: any family except Agents and Status (helper enforcement is looser than doctrine; 3.16 tightens it)",
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
    "tracking_addressee": "Auxiliary",
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
    "survey_key": "fresh_auxiliary",
    "promotable": false,
    "lifetime": "session"
  },
  "presentation": {
    "title": "Auxiliary Agent",
    "plural": "Auxiliary Agents",
    "short": "Auxiliary",
    "article": "an",
    "log_by": "Auxiliary Agent",
    "brand": "Axis Workflow | Auxiliary",
    "reply_frame": true,
    "reference_word": "Auxiliary",
    "notice": "An Auxiliary Agent is serving this project ({id})."
  }
}
```

An Auxiliary Agent serves User beside a live Main, proposes rather than accepts, and reaches Main through Messages and Submissions. It never becomes Main and keeps its booted role for life. The OpenClaw guard keeps its `externalAgents` configuration key and `--external` flag, wire names written into existing installs, until Round B2 migrates each chat. Guidance for this role remains in Start-Auxiliary and the Rules; this file holds its table row.
