# Role: Main
> **Purpose:** Role-table row for the Main Agent; compiled into helpers and Command gates at release.

```axis-role
{
  "schema": "axis.role/v1",
  "name": "Main",
  "class": "session",
  "status": "shipped",
  "order": 10,
  "admission": {
    "marker_subject": "Main: session",
    "subject_match": "exact",
    "marker_shape": "exact4",
    "created_by": "claim",
    "boot_status": null,
    "entry": "_Axis/Resources/Start-Session.md",
    "fallback_beside_live_main": false
  },
  "principals": {
    "serves": "User",
    "commands_from": "User",
    "returns_to": "direct"
  },
  "authority": {
    "exclusive_lease": true,
    "approval_level": "project",
    "scope": null,
    "issuer_token": "main",
    "proposal_team_owner": false,
    "proposal_issuer_token": null,
    "submit_schema": null,
    "record_families": "all",
    "guard": null,
    "tracking_addressee": "Main",
    "commands": {
      "status": "listed",
      "shutdown": "listed"
    }
  },
  "lifecycle": {
    "version_bound": true,
    "blocks_save": false,
    "survey": null,
    "survey_key": null,
    "promotable": false,
    "lifetime": "session"
  },
  "presentation": {
    "title": "Main Agent",
    "plural": "Main Agents",
    "short": "Main",
    "article": "the",
    "log_by": "Main Agent",
    "brand": "Axis Workflow | Main",
    "reply_frame": true,
    "reference_word": "Main",
    "notice": null
  }
}
```

The Main Agent holds the single project lease, admits through Claim-Session, and alone accepts project work. Guidance for this role remains in the Rules, Practices and Commands; this file holds its table row.
