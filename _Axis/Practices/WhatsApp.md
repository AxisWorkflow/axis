# WhatsApp
> **Purpose:** Protocols to set up messaging between WhatsApp and an OpenClaw agent. OpenClaw must already be installed and its onboard process completed before you can set up text messaging with WhatsApp.

## Enable WhatsApp
> **Purpose:** Enable the WhatsApp channel in OpenClaw. Run this section ("Enable WhatsApp") just **one time** per machine - if WhatsApp is already enabled, SKIP this section.

**Tell User what is about to happen, before starting.** In your own words: this connects WhatsApp to this computer once, and every project on it reuses the same connection afterwards. They will need a second phone number - the bot's number - with its own WhatsApp account, kept separate from their personal one; that is the number their projects will speak through. Three things need User: getting that number, logging this computer into its WhatsApp account, and sending one message from their own phone so the bot can recognize them as its owner. Everything else is setup you handle. Say roughly how long it will take and that it is one-time, then begin.

- **Check whether this is already done.** Enablement is a fact about the OpenClaw installation on this machine, not durable workflow state, so ask OpenClaw rather than recording a Flag: OpenClaw can be re-linked, unpaired, or reinstalled without Axis ever hearing about it, and a Flag would then assert something false. Run both commands. WhatsApp is already enabled when the channel reports linked and connected AND the Owner list carries a `whatsapp:` entry - if both hold, SKIP to **Harden an already-enabled install** at the end of this section. If only one holds, enablement is half-finished: work through the section, which is safe to re-run.

  `openclaw channels status`

  `openclaw config get commands.ownerAllowFrom`

- Confirm that the OpenClaw installation and onboarding process is complete:

  `openclaw onboard`

- **Skip future bootstraps.**
  OpenClaw will seed six template files into your project folder if it keeps trying to complete the bootstrap process. OpenClaw persona files are not needed and are overridden by Axis, so you can skip bootstrapping with this command:

  `openclaw config set agents.defaults.skipBootstrap true`

- **Link a dedicated WhatsApp account to OpenClaw.**
  Instruct the User to obtain a separate phone number (the "bot number") and establish a WhatsApp account with it for OpenClaw to use. That phone number is separate from the WhatsApp phone number/account used by the User. When User is ready and is running WhatsApp with the bot number, you can add yourself (this OpenClaw "device") to the account by following this command:

  `openclaw channels login --channel whatsapp`

- Confirm OpenClaw is enabled, configured, linked, running, connected:

  `openclaw channels status`

- **Enable tools for outbound messaging.**
  The current session will not see the new tools, so you need to start a new session and then continue (but you do NOT need to restart the OpenClaw gateway).

  `openclaw config set tools.profile full`

- **Do NOT set `plugins.allow`.** OpenClaw prints "plugins.allow is empty; may auto-load" on unrelated commands and invites you to silence it by trusting the plugin. Do not: setting it broke model resolution outright on a measured run, and the damage surfaces later and looks like an unrelated problem. The warning is cosmetic. See **Harden an already-enabled install** below for the evidence.

- **Pair an Owner.**
  From the Owner's phone, send a WhatsApp-message to the bot number. The default `dmPolicy` for OpenClaw is pairing, so you will get a pairing `<CODE>` back on WhatsApp (for example BPHP4LRS). Note that when `commands.ownerAllowFrom` in the OpenClaw config file is empty, the following approval will also make that User (that phone number) the "command **Owner** for WhatsApp" (with owner-level command rights), not merely "allowed to DM." When you receive the pairing code, approve the WhatsApp pairing with the following command:

  `openclaw pairing approve whatsapp <CODE>`

- **Confirm that the Owner is set.**
  Run the following command and it should return a `<channel>:<identifier>` (for example, something like `["whatsapp:+12025550143"]`):

  `openclaw config get commands.ownerAllowFrom`

- Write no Flag. The two confirmations above are exactly the check at the top of this section, so a later session re-derives enablement from OpenClaw itself instead of trusting a stored copy that nothing keeps current.

### Harden an already-enabled install

Arrive here either by working through the section above or by skipping it. The skip is the point: a machine that enabled WhatsApp before this Practice existed satisfies the enablement check on its first line and would otherwise never receive the hardening steps buried in the middle of it. Those steps are cheap, idempotent, and easy to leave undone forever. Run these two checks every time, skip or no skip.

- **Plugin trust - do NOT set `plugins.allow`, despite what the warning says.** An empty `plugins.allow` lets discovered plugins auto-load and prints "plugins.allow is empty; may auto-load" on unrelated commands. That warning is cosmetic. Acting on it is not: setting `plugins.allow` to `["whatsapp"]` on OpenClaw 2026.7.1-2 left the model unresolvable (`Unknown model: claude-cli/claude-opus-5 ... no matching models.providers["claude-cli"].models[] entry`) and a freshly registered agent could not run at all, while agents with an established session binding kept working - so the breakage looks partial and arrives later than the change. `openclaw config unset plugins.allow` restored it immediately and the identical probe then booted in full (measured 2026-08-06, both directions). `plugins.allow` is an allowlist over more than the plugin named in the warning. Leave it unset unless you are prepared to re-run the boot probe for every agent afterwards and revert the moment one fails.

- **Outbound tools.** Session Start delivers the early loading notice to the channel explicitly ([Practices > OpenClaw]); the validated Session ID banner rides the final greeting. The early notice needs the full tool profile. Confirm it, and set it if absent - a session already running will not see new tools until it restarts.

  `openclaw config get tools.profile`

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

- **Shut the probe session down before continuing.** This is not tidiness. A booted probe holds a live `Main: session` Marker, and the group session that boots later will find a fresh foreign Marker less than an hour old and open its first reply with an arbitration notice about a competing session. Send `^shutdown` on the SAME session key so the probe deletes its own Marker and releases its lease:

  `openclaw agent --agent <agent-id> --session-key probe-boot --message "^shutdown" --json --timeout 240`

  Then confirm the field is clear - `<PROJECT_PATH>/_Axis/Agents/` holds no Marker. A probe that boots and is never shut down is worse than no probe at all.

  A passing probe proves this Agent CAN boot the Workflow in this workspace. It does not prove the group session will: sessions are keyed per channel and peer, and each one boots on its own. The end of this Practice checks the group session separately, and the two checks are not interchangeable (observed 2026-08-06: a workspace where the probe boots cleanly and the WhatsApp group session does not boot at all).

- **Have User create the group FIRST, before anything is opened.** Ask User to create a WhatsApp Group, add their own WhatsApp number, add the bot's WhatsApp number, and add any other team members who will communicate with the Agent. Neither OpenClaw nor Axis can create groups on WhatsApp - a User must do it manually. The group can be called anything, but it is helpful to mirror the agent name. **For Example:** Create a WhatsApp group called: "Product Launch - Main". Tell User NOT to send anything in it yet. Wait for User to confirm the group exists.

  Record the numbers of everyone who will message the Agent in this group - each one needs an entry in the sender gate below, and a number that is missing there is dropped in silence.

- **Open the discovery window - and treat everything from here to the Policy gate as one unbroken stretch.** The group's JID can only be read off an inbound message, and an inbound message from an unknown group bounces while `groupPolicy` is `allowlist`. So the policy has to be opened briefly. While it is open, ANY WhatsApp group the bot belongs to can reach the `main` OpenClaw agent, whose workspace is not this project and is not a sandbox.

  Read the current value first and write it down - restoring it is a step you must be able to perform from memory if something fails:

  `openclaw config get channels.whatsapp.groupPolicy`

  `openclaw config set channels.whatsapp.groupPolicy open`

  **If ANY step between here and the Policy gate fails, errors, or is interrupted - restore the policy immediately before doing anything else, including before diagnosing the failure:**

  `openclaw config set channels.whatsapp.groupPolicy allowlist`

  This is not hypothetical. A script under `set -e` that aborts mid-sequence leaves the window open, reports only the original error, and says nothing about the policy (observed 2026-08-06). Nothing in OpenClaw closes it for you, and nothing warns that it is open.

- Restart the OpenClaw gateway so the opened policy takes effect. `config set` only writes the file; every gate change in this Practice needs a restart before it means anything.

  `openclaw gateway restart`

- Have User send ONE message **in** the new group, then read the group's JID from the raw log. Only a message sent AFTER the window opened will appear. Take the JID from this log and nowhere else - the two commands that look like they would list it both mislead, and **Traps** below says how.
    ```
    grep -o '"from":"[0-9]*@g\.us"' ~/.openclaw/tmp/openclaw-*/openclaw-$(date +%F).log | tail -1
    ```
    If more than one group is live on this gateway, `tail -1` can return the wrong one. List the distinct JIDs seen today and confirm which is new:
    ```
    grep -o '"from":"[0-9]*@g\.us"' ~/.openclaw/tmp/openclaw-*/openclaw-$(date +%F).log | sort -u
    ```

- Lock down and bind the sender gate. This takes sender numbers, not group IDs - putting a JID here silently drops every message. Like the two gates below it, this key is gateway-wide and `config set` replaces the whole array, so READ it first:
    ```
    openclaw config get channels.whatsapp.groupAllowFrom
    ```
    Then write back the merged array, carrying over every number the read returned and adding one entry per person who will message the Agent in the group. Drop the `<EXISTING_SENDERS>,` part only when the read came back empty:
    ```
    openclaw config set channels.whatsapp.groupAllowFrom '[<EXISTING_SENDERS>,"<USER_PHONE>"]'
    ```
    Overwriting this gate is the quietest mistake in this Practice: the gateway stays up, the group stays bound, the listener line still reads healthy, and the dropped senders simply go unheard. Check the merged array against the group's member list before moving on.

- Lock down and bind the Group gate. Group JIDs belong here. `requireMention` defaults to true, meaning the agent only wakes on an @-mention, its bot number in the text, a quoted reply, or a name-derived pattern. Set it to false for always-on, or expect silence. This key holds every group on the gateway, across every project, and `config set` replaces the whole value - so READ it first:
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

- Restart the gateway:

   `openclaw gateway restart`

- Confirm that OpenClaw is Listening for WhatsApp inbound messages. The listener line names the gate that is wrong: "blocked by empty groupPolicy allowlist" means the Policy gate is set to `allowlist` while nothing is allowlisted; "sender allowlist configured" means the sender gate holds non-sender values (a JID sitting where a phone number belongs); "all groups" or "no group allowlist configured" means the Group gate is unset; "DM + N configured group(s)" is correct.
  ```
    grep -o '"message":"Listening for WhatsApp[^"]*"' ~/.openclaw/tmp/openclaw-*/openclaw-$(date +%F).log | tail -1
  ```

- **Pre-warm the group's own session before User ever writes to it.** The probe above booted a session; it did not boot THIS one, and each session boots on its own. Boot the group session directly by naming its exact session key - the same key the channel will use - so the Workflow is already running when User's first message lands. Omit `--deliver`: nothing is sent to the group.

  `openclaw agent --agent <agent-id> --session-key "whatsapp:group:<GROUP_JID>" --message "hello" --json --timeout 240`

  Send `hello` and nothing else. A bare greeting has no answer to shortcut to, which is exactly why it boots reliably; a question does not (see the Traps entry on first-message skipping). Again, expect up to 60 seconds of silence - Session Start is running.

  Do NOT `^shutdown` this one. Unlike the probe, this session IS the group's ongoing Main session, and its Marker and lease are supposed to stay live. Confirm the Workflow came up before continuing:
  ```
  ls <PROJECT_PATH>/_Axis/Agents/ && head -1 <PROJECT_PATH>/_Axis/Flags/session-id
  ```

- Ask User in the group to send a message asking Agent to return something that confirms access to the project (e.g., a note from, or a fact about, the project). Confirm with User that Agent responded correctly. The reply should come back promptly now - the pre-warm already paid the 30-to-60-second startup cost. Do not coach User on what to write: if a plain question fails to reach a booted Workflow, that is a defect to surface, not to paper over.

- Confirm the **correct** agent handled the message - not merely that a reply went out. Expect a key of the form `agent:<agent-id>:whatsapp:group:<GROUP_JID>`:
  ```
  python3 -c "import json; print(list(json.load(open('$HOME/.openclaw/agents/<agent-id>/sessions/sessions.json')).keys()))"
  ```
  Finding the key under the agent you expected is only half the answer: it proves that agent handled A message, not that no other agent also woke. Check the agents you did NOT bind and confirm none of them holds a session for this JID:
  ```
  for a in $(openclaw agents list | grep -o '^- [a-z0-9-]*' | cut -d' ' -f2); do
    f="$HOME/.openclaw/agents/$a/sessions/sessions.json"
    [ -f "$f" ] && echo "$a: $(python3 -c "import json;print([k for k in json.load(open('$f')) if '<GROUP_JID>' in k])")"
  done
  ```

- **Confirm the Agent actually booted the Workflow - a correct answer does not prove it.** A right reply proves routing and workspace access; it does not prove Session Start ran. An Agent can read a project file and answer from it without ever entering the Workflow (observed 2026-08-06: a correct canary answer, cwd correct, and not one Session Start artifact on disk). Check the workspace for boot evidence:
  ```
  ls <PROJECT_PATH>/_Axis/Agents/ && head -1 <PROJECT_PATH>/_Axis/Flags/session-id
  ```
  A fresh `Main: session` Marker and a `session-id` Flag whose Line 1 matches it mean the Workflow booted. Neither present means the Agent answered from the files without starting a Session: routing is good, but the Agent is not running Axis. Report that to User plainly rather than recording the pairing as fully working, and treat it as a host-side boot problem to investigate separately - it is not a fault in this binding.

- **Before declaring done, confirm the Policy gate is closed.** Run this last, every time, on every path through this Practice - including paths where nothing failed, and especially paths that aborted and were resumed. The one failure mode here that is both silent and remotely reachable is a `groupPolicy` left `open`:
  ```
  openclaw config get channels.whatsapp.groupPolicy
  ```
  Anything other than `allowlist` means the window is still open: set it to `allowlist`, restart the gateway, and re-check before telling User the pairing is complete.

### Traps

This Practice runs rarely, so nothing here should depend on remembering it. Read this section before starting, not after something breaks.

**Config writes**

- `config set` on `groupAllowFrom` / `groups` / `bindings` / `plugins.allow`
  replaces the whole value. Read first and merge, or you silently unbind other
  projects. `groupAllowFrom` is the one that hides: nothing errors and the
  listener still reads healthy, so a clobbered sender list looks exactly like a
  working one until someone asks why the Agent ignores them.

- `config set` only writes the file. Every gate change needs `openclaw gateway
  restart` before it means anything - the command even says so. A test run
  before the restart proves nothing about the configuration you just wrote.

- A rejected write leaves the OLD value in place. Config validation can refuse
  your value (observed 2026-08-06: `must be object`), and the failure is a
  message on stderr, not a rollback. Always read the key back after writing it.

- Never put a group JID in `commands.ownerAllowFrom` or in `groupAllowFrom`.
  Owner and sender keys take phone numbers; a JID in either is accepted and
  then matches nothing.

- Do not act on the "plugins.allow is empty; may auto-load" warning. Setting
  `plugins.allow` to `["whatsapp"]` broke model resolution outright on OpenClaw
  2026.7.1-2 - a newly registered agent could not run (`Unknown model:
  claude-cli/...`) while agents with an established session binding carried on,
  so the damage reads as an isolated new-agent problem rather than as config
  fallout. `config unset plugins.allow` fixed it on the spot (measured
  2026-08-06, reverted and re-broken to confirm). The warning is cosmetic; the
  cure is not. A config change that "applies without restarting the gateway"
  can still change what loads.

**The discovery window**

- An aborted run leaves `groupPolicy` open. A script under `set -e` that fails
  between opening the window and the Policy gate reports its own error and says
  nothing about the policy (observed 2026-08-06). Nothing in OpenClaw closes it
  for you and nothing warns that it is open. Restore `allowlist` on any failure
  BEFORE diagnosing, and confirm it at the end of every run.

- While the window is open, every group the bot belongs to can reach the `main`
  agent - not this project's agent. `main`'s workspace is its own folder, and a
  workspace is not a sandbox.

- Only a message sent AFTER the window opened appears in the log. Re-reading
  the log for a message User sent earlier will not find the JID.

**Reading the log**

- `openclaw directory groups list` reports "No groups found" even for working
  groups. Don't use it to discover JIDs - use the log.

- `openclaw channels logs --channel whatsapp` hides group traffic. Group inbound
  logs under module web-inbound, not gateway/channels/whatsapp/inbound. Read
  the raw file at `~/.openclaw/tmp/openclaw-*/openclaw-<date>.log`.

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
  payload (observed 2026-08-06; caught only because config validation rejected
  a scalar). Name the variable anything else.

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
  leaving no Marker, no `session-id` Flag, and no Log (observed 2026-08-06).
  Check the workspace for boot artifacts before calling the pairing complete.

- Finding the expected session key proves that agent answered, not that only
  that agent woke. Check the agents you did not bind for a session on the same
  JID.

- A headless probe booting the Workflow does NOT mean the channel session will.
  Measured on one workspace, 2026-08-06: `openclaw agent` runs booted Axis in
  full (Marker, Flags, Logs; ~97k and ~100k cached tokens) under both a plain
  session key and a channel-shaped one, while a real WhatsApp group message on
  the same agent, workspace, and model booted nothing at all (~54k cached
  tokens). Workspace, entry files, agent, model, and session-key shape were all
  ruled out; the difference lives in the host's channel-inbound turn assembly.
  So run BOTH checks - the probe early and the group-session check at the end -
  and never let one stand in for the other.

- A probe that boots and is never shut down leaves a live Marker, and the next
  session to boot opens with an arbitration notice about a competing session.
  Always `^shutdown` the probe on its own session key. The pre-warm of the
  group's own session key is the one exception - that Marker is meant to live.

- A channel session can answer a question correctly WITHOUT starting the
  Workflow. Measured 2026-08-06 on one session: turn 1 asked a question
  answerable from a single project file and got a correct answer with no
  Session Start at all - no Marker, no Flags, no Log; turn 2 on that same
  session said only `hello` and booted in full (166 seconds, cacheRead 54k
  then 109k). The entry file was injected complete and untruncated in both
  turns, so this is not the host withholding doctrine - it is the host's
  channel framing urging a direct reply and winning against a protocol the
  Agent had in front of it. Headless runs boot on either message, so the skip
  needs BOTH the channel framing and something immediately answerable.
  Mitigations: the entry-file Guardrails now name this rationalization
  explicitly, and the pre-warm step above boots the group session before User
  can send anything. Neither is a guarantee - a host that resets sessions on a
  schedule will boot fresh again on whatever arrives next.

- `gateway restart` can report "killing N stale gateway process(es)" (observed
  2026-08-06). A restart is not proof of a healthy listener - read the listener
  line afterwards.

**Standing risks**

- Config-write access is a routing-takeover risk. An agent that can write
  config can re-point any binding, including your DMs. Keep config tools out of
  sandboxed/test agents' profiles.

- The workspace is not a sandbox. It's the default cwd; absolute paths reach
  anywhere on the host unless agents.defaults.sandbox is enabled. Any
  folder-scoping scheme is advisory without it.
