# WhatsApp
> **Purpose:** Protocols to set up messaging between WhatsApp and an OpenClaw agent. OpenClaw must already be installed and its onboard process completed before you can set up text messaging with WhatsApp.

Where these steps describe live configuration writes, the fallback owner, per-account gates, onboarding defaults or the group declaration, they follow OpenClaw's documentation and are untested on an installed OpenClaw.

## Enable WhatsApp
> **Purpose:** Enable the WhatsApp channel in the selected Axis OpenClaw profile. Run this section once per profile - if WhatsApp is already enabled there, SKIP its linking steps.

**Tell User what is about to happen, before starting.** In your own words: this connects WhatsApp to the selected OpenClaw profile, and Axis projects on that profile reuse the connection. They will need a second phone number - the bot's number - with its own WhatsApp account, kept separate from their personal one; that is the number their projects will speak through. Three things need User: deciding whether the Gateway is Axis-only or needs a dedicated `axis` profile, getting that number, and logging the profile into its WhatsApp account plus sending one message from their own phone so the bot can recognize them as its owner. Everything else is setup you handle. Say roughly how long it will take and that linking is one-time per profile, then begin.

- **Select and preserve the Axis profile.** Follow [Practices > OpenClaw > Schema-Adaptive Hardening] before any onboarding or channel change. If the existing Gateway also serves non-Axis agents, propose a dedicated `axis` profile and obtain approval for its separate state, port/service, and channel login. Run every command below against that same selected profile; do not switch profiles mid-procedure or apply Axis hardening to unrelated agents. The examples omit a profile flag for readability: when a named profile is selected, insert `--profile <AXIS_PROFILE>` immediately after `openclaw` in every command and derive any state location from that profile's `openclaw config file` result rather than `~/.openclaw`.

- **Check whether this is already done.** Enablement is a fact about the selected OpenClaw profile, not durable workflow state, so ask OpenClaw rather than recording a Flag: OpenClaw can be re-linked, unpaired, or reinstalled without Axis ever hearing about it, and a Flag would then assert something false. Run both commands against the selected profile. WhatsApp is already enabled when the channel reports linked and connected AND the Owner list carries a `whatsapp:` entry - if both hold, SKIP to **Harden an already-enabled install** at the end of this section. If only one holds, enablement is half-finished: work through the section, which is safe to re-run.

  `openclaw channels status`

  `openclaw config get commands.ownerAllowFrom`

- **Sign a paired bot account in again.** If the channel no longer reports linked and connected while the Owner list still carries its `whatsapp:` entry, User signs in again with the bot number's WhatsApp, and you rerun the check above:

  `openclaw channels login --channel whatsapp`

  Do not repeat the Owner pairing. Whether the Owner entry, the group gates and the bindings survive a logout is untested on an installed OpenClaw: read each back (`commands.ownerAllowFrom`, `channels.whatsapp.groupAllowFrom`, `channels.whatsapp.groups`, `channels.whatsapp.groupPolicy`, `bindings`) and repair only what is missing, by the steps of this Practice. When both checks hold, SKIP to **Harden an already-enabled install**.

- Confirm that the OpenClaw installation and onboarding process is complete. Onboarding sets the full tool profile when none is configured and may set up memory, skills, persona, the Proactive check, and other assistant features; decline those optional layers for the Axis profile, and treat the profile as unsafe until the hardening readback below passes:

  `openclaw onboard`

- **Apply the thin-harness baseline.** Follow [Practices > OpenClaw > Schema-Adaptive Hardening] against the live schema. This preserves `AGENTS.md` while disabling optional bootstrap/persona files, non-Axis bootstrap hooks, memory search and plugins, session-memory capture, the memory flush, dreaming, the Proactive check, standing intents, self-learned and default skills, open cross-agent access, and broad tools. Do not copy a fixed config key from this Practice merely because one release used it.

- **Link a dedicated WhatsApp account to OpenClaw.**
  Instruct the User to obtain a separate phone number (the "bot number") and establish a WhatsApp account with it for OpenClaw to use. That phone number is separate from the WhatsApp phone number/account used by the User. When User is ready and is running WhatsApp with the bot number, you can add yourself (this OpenClaw "device") to the account by following this command:

  `openclaw channels login --channel whatsapp`

- Confirm OpenClaw is enabled, configured, linked, running, connected:

  `openclaw channels status`

- **Verify the outbound messaging tool.** Session Start needs the narrow outbound messaging surface to deliver its early loading notice. Confirm that the effective Axis-agent allowlist includes messaging/session-send without broadening it to `tools.profile: full`. A current session may need to restart before it sees the revised surface.

- **Do NOT set `plugins.allow`.** OpenClaw prints "plugins.allow is empty; may auto-load" on unrelated commands and invites you to silence it by trusting the plugin. Do not: setting it broke model resolution outright on a measured run, and the damage surfaces later and looks like an unrelated problem. The warning is cosmetic. See **Harden an already-enabled install** below for the evidence.

- **Pair an Owner.**
  From the Owner's phone, send a WhatsApp-message to the bot number. The default `dmPolicy` for OpenClaw is pairing, so you will get a pairing `<CODE>` back on WhatsApp (for example BPHP4LRS). Note that when `commands.ownerAllowFrom` in the OpenClaw config file is empty, the following approval will also make that User (that phone number) the "command **Owner** for WhatsApp" (with owner-level command rights), not merely "allowed to DM." When you receive the pairing code, approve the WhatsApp pairing with the following command:

  `openclaw pairing approve whatsapp <CODE>`

- **Confirm that the Owner is set.**
  Run the following command and it should return a `<channel>:<identifier>` (for example, something like `["whatsapp:+12025550143"]`):

  `openclaw config get commands.ownerAllowFrom`

- Write no Flag. The two confirmations above are exactly the check at the top of this section, so a later session re-derives enablement from OpenClaw itself instead of trusting a stored copy that nothing keeps current.

### Harden an already-enabled install

Arrive here either by working through the section above or by skipping it. The skip is the point: a profile that enabled WhatsApp before this Practice existed may satisfy the channel check while still carrying persona, memory, a heartbeat or the Proactive check, skills, or unrestricted tools. Run the targeted hardening audit every time, skip or no skip.

- **Plugin trust - do NOT set `plugins.allow`, despite what the warning says.** An empty `plugins.allow` lets discovered plugins auto-load and prints "plugins.allow is empty; may auto-load" on unrelated commands. That warning is cosmetic. Acting on it is not: setting `plugins.allow` to `["whatsapp"]` on OpenClaw 2026.7.1-2 left the model unresolvable (`Unknown model: claude-cli/claude-opus-5 ... no matching models.providers["claude-cli"].models[] entry`) and a freshly registered agent could not run at all, while agents with an established session binding kept working - so the breakage looks partial and arrives later than the change. `openclaw config unset plugins.allow` restored it immediately and the identical probe then booted in full. `plugins.allow` is an allowlist over more than the plugin named in the warning. Leave it unset unless you are prepared to re-run the boot probe for every agent afterwards and revert the moment one fails.

- **Thin-harness audit.** Follow `^audit openclaw` read-only. If it reports `Degraded` or `Unverified`, preview and obtain approval for `^install openclaw` to apply only the resolved semantic controls in [Practices > OpenClaw]. Do not authenticate, mutate, restart, move legacy files, or erase old state merely because the audit found it.

- **Outbound tools.** Session Start delivers the early loading notice to the channel explicitly ([Practices > OpenClaw]); the validated opening rides the final greeting. Confirm the effective tool surface includes the narrow messaging/session-send capability and explicitly does not use `tools.profile: full`. A session already running may not see a changed policy until it restarts.

## Pair a WhatsApp Group
> **Purpose:** Register an OpenClaw Agent to receive/send via a WhatsApp Group. You must first enable WhatsApp (see section above) before you can pair a particular Agent to a WhatsApp group (the purpose of this section).

**Tell User what is about to happen, before starting.** In your own words: this gives one project its own WhatsApp group, so messages there reach that project and nothing else. Three things need User: create the group and add the bot to it, send one short message in it so you can find it, and then ask a real question to confirm the right project answered. In between, you wire the group to the project and lock it down so no other chat can reach it. Warn them the first reply is slow - the Agent runs a full startup before it answers - and that you will ask for those three things one at a time.

- Confirm WhatsApp is enabled by running the same check that opens the **Enable WhatsApp** section above - `openclaw channels status` reports the channel linked and connected, and `openclaw config get commands.ownerAllowFrom` carries a `whatsapp:` entry. If either fails, tell User that WhatsApp is not enabled yet, Log the problem, and STOP.

- **Register an Agent.**
  Register an Agent to a given Workspace (i.e., to an Axis Project). Registration only defines the agent - a workspace plus a session config folder - so nothing runs until a turn is sent to it, which the boot step below does deliberately. Note that Agent ID will be lowercased by OpenClaw.

  `openclaw agents add <PROJECT_NAME> --workspace "<PROJECT_PATH>" --non-interactive --json`

  Always quote the workspace path: project folder names contain spaces far more often than not, and an unquoted path splits into two arguments and registers the agent against the wrong workspace. A tilde does NOT expand inside double quotes, so write `"$HOME/..."` rather than `"~/..."`.

  An agent can be named anything, but it is clearest to name it by Project Name + Purpose. For example: Start a Main Agent for the "Product Launch" Project at `~/Projects/Product Launch/` by running:

  `openclaw agents add product-launch-main --workspace "$HOME/Projects/Product Launch/" --non-interactive --json`

- Confirm agent, workspace, and model:

  `openclaw agents list`

- **Boot the Agent headlessly and confirm it starts the Workflow.** An agent is instantiated on demand, so nothing has run in that workspace yet and nothing has proved it can. Force one turn now, before a group exists and before any policy is opened: a failure here costs nothing, while the same failure discovered at the end costs a group, an open window, and User's time. `--deliver` is deliberately omitted - the reply goes nowhere, so this sends no message to anyone.

  **Tell User to expect up to 60 seconds of silence before this returns.** The Agent is running a full Session Start - reading its context, detecting Capabilities, writing Flags - and it produces no output at all until that finishes. A quiet minute here is the protocol working, not a hang.

  `openclaw agent --agent <agent-id> --session-key probe-boot --message "hello" --json --timeout 240`

- Confirm the probe actually entered the Workflow. Look in the project, not at the reply - a friendly answer proves nothing:
  ```
  ls <PROJECT_PATH>/_Axis/Agents/ && head -1 <PROJECT_PATH>/_Axis/Flags/session-id
  ```
  A PASS is a `Main: session` Marker whose filename matches Line 1 of `session-id`, plus `host-*` Capability Flags and a `Session Started` Log. Anything less means the Agent answered without starting a Session: STOP here, tell User the Agent is not running Axis in this workspace, and do not wire any gates. Nothing below this line will fix it, and a bound group would then be served by an Agent outside the Workflow - no lease, no Logs, no arbitration - while looking perfectly healthy.

  If Main already lives in User's direct chat ([Practices > OpenClaw > Group Chats and the Main Lease]), the probe boots Auxiliary beside it: a PASS is then one new `Auxiliary:` Marker, `host-*` Flags and a `Session Started` Log by the Auxiliary Agent.

- **Shut the probe session down before continuing.** This is not tidiness. A booted probe holds a live `Main: session` Marker, and the group session that boots later will find a fresh foreign Marker less than an hour old and open its first reply with an arbitration notice about a competing session. Send `^shutdown` on the SAME session key so the probe deletes its own Marker and releases its lease:

  `openclaw agent --agent <agent-id> --session-key probe-boot --message "^shutdown" --json --timeout 240`

  Then confirm the probe's own Marker is gone from `<PROJECT_PATH>/_Axis/Agents/`. A probe that boots and is never shut down is worse than no probe at all.

  A passing probe proves this Agent CAN boot the Workflow in this workspace. It does not prove the group session will: sessions are keyed per channel and peer, and each one boots on its own. The end of this Practice checks the group session separately, and the two checks are not interchangeable.

- **Have User create the group FIRST, before anything is opened.** Ask User to create a WhatsApp Group, add their own WhatsApp number, add the bot's WhatsApp number, and add any other team members who will communicate with the Agent. Neither OpenClaw nor Axis can create groups on WhatsApp - a User must do it manually. The group can be called anything, but it is helpful to mirror the agent name. **For Example:** Create a WhatsApp group called: "Product Launch - Main". Tell User NOT to send anything in it yet. Wait for User to confirm the group exists.

  Record the numbers of everyone who will message the Agent in this group - each one needs an entry in the sender gate below, and a number that is missing there is dropped in silence.

- **Open the discovery window - and treat everything from here to the Policy gate as one unbroken stretch.** The group's JID can only be read off an inbound message, and an inbound message from an unknown group bounces while `groupPolicy` is `allowlist`. So the policy has to be opened briefly. While it is open, ANY WhatsApp group the bot belongs to can reach whichever agent catches unbound group traffic: a group-wildcard, account-wide or channel-wide binding, otherwise the fallback owner (the configured system agent, a retained legacy owner, or the only agent); with several agents and none of these, the message is left undispatched. That agent's workspace is not a sandbox. Before opening the window, confirm this project's agent is none of these; if it is, the discovery message boots a session in this project, which must be retired before the gates are written. Treat the window as open from the moment the write commits. Where a group map without `*` already applies to the bot account, OpenClaw drops unlisted groups before routing whatever `groupPolicy` says; whether the log then still shows the new group's JID is untested.

  Read the current value first and write it down - restoring it is a step you must be able to perform from memory if something fails:

  `openclaw config get channels.whatsapp.groupPolicy`

  `openclaw config set channels.whatsapp.groupPolicy open`

  **If ANY step between here and the Policy gate fails, errors, or is interrupted - restore the policy immediately before doing anything else, including before diagnosing the failure:**

  `openclaw config set channels.whatsapp.groupPolicy allowlist`

  This is not hypothetical. A script under `set -e` that aborts mid-sequence leaves the window open, reports only the original error, and says nothing about the policy. Nothing in OpenClaw closes it for you, and nothing warns that it is open.

- Make sure the opened policy is live. A running Gateway applies the write at once or restarts itself to apply it. Run a restart only when the CLI prints that one is needed (reload mode `off`, or a write made while the Gateway was stopped):

  `openclaw gateway restart`

- Start the selected profile's Gateway log stream with `openclaw logs --follow --json --no-color`, then have User send ONE message **in** the new group. Stop the stream as soon as the new inbound event arrives and take the group JID from that event's `from` field ending `@g.us`. Only a message sent AFTER the window opened will appear. Do not paste or save the raw event in Axis - it may contain phone numbers, message content, and channel identifiers. If several groups are active, compare the distinct new `from` values and use the event's `to` field only to confirm which bot account received it; ask User when still ambiguous. The two commands that look like they would list the group can mislead, and **Traps** below explains them.

- Lock down and bind the sender gate. This takes sender numbers, not group IDs - putting a JID here silently drops every message. Like the Group gate below it, this key is shared by every project on every bot account that inherits it: the value in effect is the bot account's own entry, else `accounts.default`, else the root, so read and write the one in effect. `config set` replaces the whole array, so READ it first:
    ```
    openclaw config get channels.whatsapp.groupAllowFrom
    ```
    Then write back the merged array, carrying over every number the read returned and adding one entry per person who will message the Agent in the group. Drop the `<EXISTING_SENDERS>,` part only when the read came back empty:
    ```
    openclaw config set channels.whatsapp.groupAllowFrom '[<EXISTING_SENDERS>,"<USER_PHONE>"]'
    ```
    Overwriting this gate is the quietest mistake in this Practice: the gateway stays up, the group stays bound, the listener line still reads healthy, and the dropped senders simply go unheard. Check the merged array against the group's member list before moving on.

- **If anyone besides User will write in this group**, apply [Practices > OpenClaw > Group Chats and the Main Lease]: Main lives in User's direct chat, and this group's Group gate entry below carries the Auxiliary declaration as its group prompt, for example `"<GROUP_JID>":{"requireMention":false,"systemPrompt":"Axis role: Auxiliary; surface: <name>"}`. OpenClaw documents the group prompt for inbound group messages only, so skip the pre-warm below for a declared group: User's first message in the group boots the session. If a session for this group already booted (for example from the discovery message), retire it as that section's step 2 says before User writes. This is documented but untested on an installed OpenClaw.

- Lock down and bind the Group gate. Group JIDs belong here. `requireMention` defaults to true, meaning the agent only wakes on an @-mention, its bot number in the text, a quoted reply, or a name-derived pattern. Set it to false for always-on, or expect silence. This key holds every group on every bot account that inherits it, across every project; the map in effect is the bot account's own, else `accounts.default`, else the root, and the first present replaces the others entirely, so the declaration must sit in that map and it must not contain `*`. `config set` replaces the whole value - so READ it first:
    ```
    openclaw config get channels.whatsapp.groups
    ```
    Then write back the merged object, carrying over every entry the read returned. Drop the `<EXISTING_ENTRIES>,` part only when the read came back empty:
    ```
    openclaw config set channels.whatsapp.groups '{<EXISTING_ENTRIES>,"<GROUP_JID>":{"requireMention":false}}'
    ```

- Lock down and bind the Policy gate. This closes the discovery window opened above - do it as soon as the JID is in hand, not at the end of the run.

    `openclaw config set channels.whatsapp.groupPolicy allowlist`

    Then read it back. A write that was rejected by config validation leaves the old value in place and the window still open:

    `openclaw config get channels.whatsapp.groupPolicy`

- Do NOT use the following command because it only does channel-level binding (which would hijack all WhatsApp traffic for that agent):

    `openclaw agents bind`

- Instead, write the peer-level binding. `bindings` is gateway-wide and `config set` replaces the whole array, so read it first here too - a bare write silently unbinds every other project on this gateway:
    ```
    openclaw config get bindings
    ```
    Then write back the merged array. Keep the whole binding on ONE line: a line break inside the JSON string breaks the command. Drop the `<EXISTING_BINDINGS>,` part only when the read came back empty:
    ```
    openclaw config set bindings '[<EXISTING_BINDINGS>,{"type":"route","agentId":"<projectname>","comment":"<ProjectName> group -> agent","match":{"channel":"whatsapp","peer":{"kind":"group","id":"<GROUP_JID>"}}}]'
    ```

- Restart the gateway only if the CLI says one is needed:

   `openclaw gateway restart`

- Confirm that OpenClaw is Listening for WhatsApp inbound messages by reading the selected profile's recent stream with `openclaw logs --json --limit 200 --no-color` and locating the newest WhatsApp listener event without quoting its identifiers. The listener line names the gate that is wrong: "blocked by empty groupPolicy allowlist" means the Policy gate is set to `allowlist` while nothing is allowlisted; "sender allowlist configured" means the sender gate holds non-sender values (a JID sitting where a phone number belongs); "all groups" or "no group allowlist configured" means the Group gate is unset; "DM + N configured group(s)" is correct.

- **Pre-warm the group's own session before User ever writes to it** (skip this for a declared group). The probe above booted a session; it did not boot THIS one, and each session boots on its own. Boot the group session directly by naming its exact session key - the same key the channel will use - so the Workflow is already running when User's first message lands. Omit `--deliver`: nothing is sent to the group.

  `openclaw agent --agent <agent-id> --session-key "whatsapp:group:<GROUP_JID>" --message "hello" --json --timeout 240`

  On a non-default bot account the channel's key ends in `:thread:whatsapp-account-<accountId>`; use that full key, or skip the pre-warm.

  Send `hello` and nothing else. A bare greeting has no answer to shortcut to, which is exactly why it boots reliably; a question does not (see the Traps entry on first-message skipping). Again, expect up to 60 seconds of silence - Session Start is running.

  Do NOT `^shutdown` this one. Unlike the probe, this session IS the group's ongoing Main session, and its Marker and lease are supposed to stay live. Confirm the Workflow came up before continuing:
  ```
  ls <PROJECT_PATH>/_Axis/Agents/ && head -1 <PROJECT_PATH>/_Axis/Flags/session-id
  ```

- Ask User in the group to send a message asking Agent to return something that confirms access to the project (e.g., a note from, or a fact about, the project). Confirm with User that Agent responded correctly. The reply should come back promptly now - the pre-warm already paid the 30-to-60-second startup cost. Do not coach User on what to write: if a plain question fails to reach a booted Workflow, that is a defect to surface, not to paper over.

- Confirm the **correct** agent handled the message - not merely that a reply went out. Resolve the selected profile's private state root from `openclaw config file` without reporting it, then inspect only the session-key names in that profile's per-agent session indexes. Require the exact expected key shape `agent:<agent-id>:whatsapp:group:<GROUP_JID>` under the bound agent. Return only PASS/FAIL to User; do not print the session keys or state path.

  Finding the key under the expected agent is only half the answer: it proves that agent handled a message, not that no other agent also woke. Enumerate the selected profile's registered agent IDs, inspect each other agent's session-key names, and require no match for `<GROUP_JID>`. Do not read transcript bodies. A match under any other agent is a routing failure: close the Policy gate, report the conflicting agent ID only, and fix the binding before continuing.

- **Confirm the Agent actually booted the Workflow - a correct answer does not prove it.** A right reply proves routing and workspace access; it does not prove Session Start ran. An Agent can read a project file and answer from it without ever entering the Workflow. Check the workspace for boot evidence:
  ```
  ls <PROJECT_PATH>/_Axis/Agents/ && head -1 <PROJECT_PATH>/_Axis/Flags/session-id
  ```
  A fresh `Main: session` Marker and a `session-id` Flag whose Line 1 matches it mean the Workflow booted. For a declared group the evidence is instead the group session's own new `Auxiliary:` Marker, and its reply says it is Auxiliary per the standing declaration; the direct-chat Main's Marker and `session-id` prove nothing about the group. If the group session came up as Main, User sends `^shutdown` and then `/new` alone in the group, and the check is repeated. Neither present means the Agent answered from the files without starting a Session: routing is good, but the Agent is not running Axis. Report that to User plainly rather than recording the pairing as fully working, and treat it as a host-side boot problem to investigate separately - it is not a fault in this binding.

- **Before declaring done, confirm the Policy gate is closed.** Run this last, every time, on every path through this Practice - including paths where nothing failed, and especially paths that aborted and were resumed. The one failure mode here that is both silent and remotely reachable is a `groupPolicy` left `open`:
  ```
  openclaw config get channels.whatsapp.groupPolicy
  ```
  Anything other than `allowlist` means the window is still open: set it to `allowlist`, restart the gateway if the CLI says one is needed, and re-check before telling User the pairing is complete.

### Traps

This Practice runs rarely, so nothing here should depend on remembering it. Read this section before starting, not after something breaks.

**Config writes**

- `config set` on `groupAllowFrom` / `groups` / `bindings` / `plugins.allow`
  replaces the whole value. Read first and merge, or you silently unbind other
  projects. `groupAllowFrom` is the one that hides: nothing errors and the
  listener still reads healthy, so a clobbered sender list looks exactly like a
  working one until someone asks why the Agent ignores them.

- Assume every write is live as soon as it commits, so the discovery window
  opens at the write. Only reload mode `off` or a write made while the Gateway
  was stopped waits for `openclaw gateway restart`. Either way, read the key
  back and check the listener line before testing.

- A rejected write leaves the OLD value in place. Config validation can refuse
  your value, and the failure is a
  message on stderr, not a rollback. Always read the key back after writing it.

- Never put a group JID in `commands.ownerAllowFrom` or in `groupAllowFrom`.
  Owner and sender keys take phone numbers; a JID in either is accepted and
  then matches nothing.

- Do not act on the "plugins.allow is empty; may auto-load" warning. Setting
  `plugins.allow` to `["whatsapp"]` broke model resolution outright on OpenClaw
  2026.7.1-2 - a newly registered agent could not run (`Unknown model:
  claude-cli/...`) while agents with an established session binding carried on,
  so the damage reads as an isolated new-agent problem rather than as config
  fallout. `config unset plugins.allow` fixed it on the spot. The warning is cosmetic; the
  cure is not. A config change that "applies without restarting the gateway"
  can still change what loads.

**The discovery window**

- An aborted run leaves `groupPolicy` open. A script under `set -e` that fails
  between opening the window and the Policy gate reports its own error and says
  nothing about the policy. Nothing in OpenClaw closes it
  for you and nothing warns that it is open. Restore `allowlist` on any failure
  BEFORE diagnosing, and confirm it at the end of every run.

- While the window is open, every group the bot belongs to can reach the
  agent that catches unbound traffic - usually not this project's agent; check
  before opening the window. A workspace is not a sandbox.

- Only a message sent AFTER the window opened appears in the log. Re-reading
  the log for a message User sent earlier will not find the JID.

**Reading the log**

- `openclaw directory groups list` reports "No groups found" even for working
  groups. Don't use it to discover JIDs - use the log.

- `openclaw channels logs --channel whatsapp` may hide group traffic. Group inbound
  logs under module web-inbound, not gateway/channels/whatsapp/inbound. Use the
  selected profile's `openclaw logs --follow --json --no-color` stream instead
  of assuming the default profile's raw log path.

- `tail -1` returns the most recent group, not necessarily yours. On a gateway
  with several live groups, list distinct JIDs with `sort -u` and identify the
  new one. The same log line carries a `to` field holding the bot number, which
  confirms which account received the message.

- The three gates have names and keys, not numbers: the sender gate is
  `groupAllowFrom` (phone numbers), the Group gate is `groups` (JIDs), and the
  Policy gate is `groupPolicy`. The listener line tells you which one failed:
  blocked by empty groupPolicy allowlist is the Policy gate set to allowlist
  with nothing allowlisted; sender allowlist configured is the sender gate
  holding non-sender values; all groups, or no group allowlist configured, is
  the Group gate unset; DM + N configured group(s) is correct.

**Shell hazards**

- `GROUPS` is a special variable in Bash - the list of groups the invoking user
  belongs to. Assigning your merged JSON to it appears to work and then expands
  to a numeric GID, so the command silently receives `20` instead of your
  payload. Name the variable anything else.

- Quote every workspace path. Project folder names contain spaces more often
  than not, and an unquoted path splits into two arguments and registers the
  agent against the wrong workspace. A tilde does NOT expand inside double
  quotes, so write `"$HOME/..."`, never `"~/..."`.

- Keep each JSON payload on ONE line. A line break inside the quoted JSON
  breaks the command.

**Agents and bindings**

- --bind on agents add is channel-level only. It cannot express a group JID,
  and writing it hijacks all WhatsApp for that agent.

- Agent IDs are lowercased on creation. Any folder-name convention must account
  for it.

- Moving, renaming, or deleting a project folder strands its binding. The
  binding survives and keeps routing to an agent whose workspace no longer
  exists; nothing revalidates it.

**Verification**

- A correct answer proves workspace access, not that the Workflow booted. An
  Agent can read a project file and answer from it with no Session Start,
  leaving no Marker, no `session-id` Flag, and no Log.
  Check the workspace for boot artifacts before calling the pairing complete.

- Finding the expected session key proves that agent answered, not that only
  that agent woke. Check the agents you did not bind for a session on the same
  JID.

- A headless probe booting the Workflow does NOT mean the channel session will.
  So run BOTH checks - the probe early and the group-session check at the end -
  and never let one stand in for the other.

- A probe that boots and is never shut down leaves a live Marker, and the next
  session to boot opens with an arbitration notice about a competing session.
  Always `^shutdown` the probe on its own session key. The pre-warm of the
  group's own session key is the one exception - that Marker is meant to live.

- A channel session can answer a question correctly WITHOUT starting the
  Workflow. The entry file was injected complete and untruncated in both
  turns, so this is not the host withholding doctrine - it is the host's
  channel framing urging a direct reply and winning against a protocol the
  Agent had in front of it. Headless runs boot on either message, so the skip
  needs BOTH the channel framing and something immediately answerable.
  Mitigations: the entry-file Guardrails now name this rationalization
  explicitly, and the pre-warm step above boots the group session before User
  can send anything. Neither is a guarantee - a host that resets sessions on a
  schedule will boot fresh again on whatever arrives next.

- `gateway restart` can report "killing N stale gateway process(es)". A restart is not proof of a healthy listener - read the listener
  line afterwards.

**Standing risks**

- Config-write access is a routing-takeover risk. An agent that can write
  config can re-point any binding, including your DMs. Keep config tools out of
  sandboxed/test agents' profiles.

- The workspace is not a sandbox. It's the default cwd; absolute paths reach
  anywhere on the host unless agents.defaults.sandbox is enabled. Any
  folder-scoping scheme is advisory without it.
