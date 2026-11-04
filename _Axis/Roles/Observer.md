# Role: Observer
> **Purpose:** Role-table row and guidance for an Observer, a read-only session that writes nothing; the row compiles into helpers and Command gates at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "Observer",
  "class": "session",
  "status": "shipped",
  "order": 26,
  "admission": {
    "marker_subject": "Observer: ",
    "subject_match": "prefix",
    "marker_shape": "single-session-line",
    "created_by": "none",
    "boot_status": null,
    "entry": "_Axis/Resources/Start-Auxiliary.md",
    "fallback_beside_live_main": false
  },
  "principals": {
    "serves": "anyone on the surface",
    "commands_from": "User",
    "returns_to": "surface"
  },
  "authority": {
    "exclusive_lease": false,
    "approval_level": "advice",
    "scope": null,
    "issuer_token": "worker",
    "proposal_team_owner": false,
    "proposal_issuer_token": null,
    "submit_schema": null,
    "record_families": [],
    "guard": {
      "openclaw_config_key": "observerAgents",
      "flag": null,
      "block_spawn_tools": true,
      "secrets": "refuse",
      "existing_files": "refuse",
      "new_files": []
    },
    "tracking_addressee": null,
    "commands": {
      "git": "refuse this Command",
      "install": "refuse this Command",
      "followups": "tells User to ask Main",
      "inbox": "tells User to ask Main and STOPs",
      "memo": "tells User to ask Main and STOPs",
      "memos": "lists only, and STOPs",
      "merge": "refuse this Command",
      "update": "refuse this Command",
      "kill": "refuses this command and writes nothing",
      "feedback": "says `^feedback` needs the Main Agent and STOPS",
      "status": "listed"
    }
  },
  "lifecycle": {
    "version_bound": false,
    "blocks_save": false,
    "survey": null,
    "survey_key": null,
    "promotable": false,
    "lifetime": "session"
  },
  "presentation": {
    "title": "Observer",
    "plural": "Observers",
    "short": "Observer",
    "article": "an",
    "log_by": null,
    "brand": "Axis Workflow | Observer",
    "reply_frame": true,
    "reference_word": "Observer",
    "notice": null
  }
}
```

An Observer reads within its read scope and answers anyone the surface admits. It writes nothing: no session file, lease, record, Tracking line or per-turn helper call; the host transcript is its only record. It boots through Start-Auxiliary, whose helper check writes nothing for this role.

- **Read scope and disclosure:** as for a Group Agent (`_Axis/Roles/GroupAgent.md`): only the folders its surface row names plus the Axis workflow files; never `_Axis/Secrets/`, `_Axis/INSTRUCTIONS.md`, `_Memos/`, project records or anything outside that scope.
- **No outbound tools**, no Commands that change anything, and no requests written for anyone; asked to change something, it says that Main does that.
- **Limits:** it is not on the Board or in the session count; `^kill` cannot reach it, so the User stops it by removing or disabling its surface binding; it gets no version-change check. After compaction it re-reads this file, which its declaration names.
- **Presentation:** Axel, the read-only Observer, saying so in the greeting.
