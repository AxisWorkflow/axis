# Environment
> **Purpose:** Declare non-portable project infrastructure and portable restoration guidance without recording secrets or host bindings.

## Infrastructure

| Kind | Infrastructure | Purpose / Consumer | Need | Safe Revalidation | Portable Fallback | Re-establish |
| --- | --- | --- | --- | --- | --- | --- |
| - | None declared | - | optional | manual | - | Ask User |

## Contract

The `None declared` row is the exact empty-state placeholder; remove it when adding the first real row. Each real row follows [Practices > Portability > Infrastructure Inventory]. `Kind` is `tool`, `credential`, `authentication`, `service`, `scheduler`, `environment`, `host-integration`, or `other`; `Need` is `required` or `optional`; and `Safe Revalidation` is one fixed non-executable token: `tool:{name}`, `env:{NAME}`, `loopback:{local URL}`, `capability:{boolean host-* Flag}`, or `manual`.

This file is portable project state. Never put commands, install paths, hostnames, usernames, account or channel identifiers, scheduler job IDs, machine timestamps, secret filenames or values, credentials, current-health claims, or an environment-signature ID here. Current host facts belong in Capability Flags; credentials belong only under `_Axis/Secrets/` or an approved host secret store. A scheduler row describes portable intent and points to a non-secret Axis Note; the host job itself never travels.

`^git` adds logical declarations for Git, remote authentication, and optional Secrets encryption when those features are enabled. It records only the portable requirement and restoration guidance; host login state and the private Secrets identity remain outside the project.
