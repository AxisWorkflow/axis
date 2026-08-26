# Version Control
> **Purpose:** Define safe, adaptive Git setup, synchronization, checkpoints, encrypted Secrets transport, and rollback.

Git is optional but recommended. A local repository gives the project an undo history; a configured remote also gives `^git`, `^save`, and `^resume` one shared transport. Creating the remote is the User's decision. After User connects one, invoking those Commands is standing authorization for their documented fetch, fast-forward, ordinary push, and encrypted-capsule actions - never for a merge, rebase, reset, force-push, visibility change, or new remote.

## Admission and Repository Boundary

- Main Agent only performs setup, synchronization, or rollback. External Agents and Subagents refuse and route the request to Main.
- Read `host-shell` under [Practices > Flags > Reading Flags]. Git mutation requires valid `yes`; otherwise explain the closest manual action and STOP.
- Resolve the exact project root with `git rev-parse --show-toplevel`. Exact root is eligible. A parent root enters Subproject Repositories below; never initialize or operate on the parent by accident. An inner repository outside an approved Subproject arrangement also stops.
- Refuse while another fresh writer, fresh lock, unresolved Request that affects the same paths, or an unfinished merge, rebase, cherry-pick, revert, bisect, or sequencer operation exists. Never use a new Git operation to cover an incomplete old one.
- Never run raw additional text as a Git CLI tail. Interpret User intent into this Practice's bounded operations.

## Setup

User invoking bare `^git` authorizes local setup when no exact-root repository exists:

1. Check `git --version`. If Git is absent, identify an official installation method for the current platform, present the exact machine change, and offer to perform it. Install only after User approves; failure leaves Axis usable without Git.
2. Before `git init`, inspect the workspace for nested Subprojects (anchor-carrying folders). If any exist, follow Decision Point and Record first: confirm User wants parent version control, select each resulting arrangement, then initialize and apply those choices. If User leaves the parent unversioned, do not initialize or stage it.
3. Check repository identity with `git config --local --get user.name` and `user.email`, then the inherited values. If either is missing, ask User for it and write it repository-locally by default. Never invent an email, copy one from project content, or change global configuration unless User explicitly asks.
4. Run `git init` at the project root. Verify the shipped `.gitignore` and `.gitattributes` exist.
5. Stage with `git add -A`, run the Subproject and staged-content gates under Checkpoints, and commit `axis: initial project state`. A clean initial tree is an error to explain, not permission for an empty commit.
6. Add or update a logical `Git` tool declaration in `_Axis/ENVIRONMENT.md` with `tool:git`, the full-folder transfer fallback, and official public re-establishment guidance. Write its setup Event before the initial commit when possible; otherwise include it in one immediate setup commit.

**Nested projects:** if `git rev-parse --show-toplevel` points to a PARENT folder, the project already sits inside another repository. A valid Subproject may remain parent-tracked, become an independent ignored repository, or become a submodule; do not `git init` until User chooses below.

**Detachment:** a project must never carry the Axis template's history. Projects installed from the release ZIP have none. If User cloned the public Axis template instead, explain that its history is not project history and obtain explicit confirmation before removing that exact `.git` directory and initializing a fresh repository.

## Private Remote Setup

After local setup, or whenever an exact-root repository has no remote, finish the local commit first and offer a private GitHub remote. Declining leaves a complete local repository and is never an error.

1. Check `gh --version`. If absent, offer an official installation exactly as for Git; do not require `gh` for an existing Git remote or a non-GitHub provider.
2. Check `gh auth status`. If authentication is absent, offer `gh auth login` through its browser flow. Never ask User to paste a token into chat, run a show-token option, copy authentication into `_Axis/Secrets/`, or infer login from an installed CLI.
3. Confirm the owner, repository name, and visibility. Default to private. Create an empty repository - no generated README, license, or `.gitignore` that could introduce unrelated history - then add it as `origin`, establish the current branch's upstream, push normally, and verify both upstream and visibility.
4. Add or update a logical `Git Remote Authentication` declaration in `_Axis/ENVIRONMENT.md` with `manual` revalidation, a full-folder transfer fallback, and `Ask User` or public authentication guidance. Record the remote provider and confirmed visibility in one Note and one Event, never a credential-bearing URL or account token.
5. If bounded Secrets discovery reports plaintext credential material, offer Encrypted Secrets Transport below. Do not list or read the entries.

Creating the remote is the authorization boundary. After it is connected, ordinary `^git`, `^save`, and `^resume` may synchronize with that upstream without asking on each operation. Public visibility, a new remote, or a remote/visibility change always requires a fresh explicit decision.

## Shared Synchronization State Machine

`^git`, `^save`, and `^resume` use this one procedure. Fetch before classifying whenever an upstream exists. `git fetch {remote}` updates remote-tracking references but does not merge project files. Suppress credential-bearing output and never place a remote URL in a Log.

### Resolve the upstream

1. Prefer the current branch's configured upstream.
2. With no upstream and exactly one remote, inspect its default/current matching branch. Establish the upstream automatically only when the mapping is unambiguous and linear; otherwise ask User.
3. With multiple candidate remotes or branches, stop and ask which is authoritative.
4. With no remote, use local-only checkpoint behavior and offer Private Remote Setup only from `^git`, not while `^save` or `^resume` is trying to finish.
5. A fetch or authentication failure never destroys a local checkpoint. Report `saved locally; remote not verified` on an outgoing path, or `resumed locally; remote not verified` on an incoming path.

### Classify the graph

After a successful fetch, classify `HEAD...@{upstream}` by commit ancestry, never timestamps, status prose, or version strings:

| Local commits only | Remote commits only | State | Automatic action |
| --- | --- | --- | --- |
| 0 | 0 | equal | None unless local files need a checkpoint |
| positive | 0 | local ahead | ordinary push |
| 0 | positive | remote ahead | fast-forward only when the receiving gate passes |
| positive | positive | diverged | STOP; preserve both sides and propose reconciliation |

Use `git rev-list --left-right --count HEAD...@{upstream}` or an equivalent ancestry check. Never call a state merely ahead or behind from a stale tracking reference.

### Classify local files

- `clean` means no tracked, untracked, deleted, or renamed project change.
- `receive-safe` means the only local differences are verified ignored current-session artifacts and/or untracked session-lifecycle Logs under `_Axis/Logs/{timestamp}.md`. Each eligible Log must be a regular non-link file with a valid unique timestamp name, satisfy [Practices > Logs], and have the exact Subject `Session Starting`, `Session Started`, or `Shutdown by User` with a valid `by: Main Agent` and `session:` line. Its path must be absent from the fetched upstream tree and incoming range. These Logs are append-only operational evidence: hash their bytes before receipt, leave them untracked during the fast-forward, verify the same paths and bytes afterward, and let the next outgoing checkpoint commit them normally. This includes the shutdown tail intentionally written after a handoff save; returning to the original computer must not require discarding that WORM record.
- Everything else is `substantive`. A malformed, modified, colliding, linked, non-lifecycle, or otherwise unverified Log is substantive. Never stash, discard, hide, or auto-merge substantive local work.

### Take one linear action

- **Equal + clean:** no operation.
- **Equal + substantive local changes:** in checkpoint mode, stage, validate, commit, re-fetch, then push only if the result remains local-ahead. In receive mode, stop and ask User to save or discard the local work through an explicit procedure.
- **Local ahead:** push normally. If the push is rejected, re-fetch and reclassify; never force.
- **Remote ahead + clean or receive-safe:** record the old `HEAD` and any receive-safe Log hashes, run `git merge --ff-only @{upstream}`, verify the new `HEAD` equals the fetched upstream and every preserved Log is byte-identical, then run Incoming Change Validation below.
- **Remote ahead + substantive local changes:** checkpoint mode may finish a local safety commit, after which the histories are divergent and must stop. Receive mode does not commit or pull; it reports the local work that prevents receipt.
- **Diverged:** do not merge or rebase automatically even when files appear disjoint. Show the two bounded commit summaries, preserve both histories, and propose a reviewed reconciliation.

Re-fetch immediately before every push. A remote race becomes a rejected push and a preserved local commit, never an automatic integration.

### Incoming Change Validation

After a fast-forward:

1. Compare old and new `HEAD`. Validate the checkout is at the fetched commit, no pre-existing substantive local file was removed or overwritten, and every receive-safe lifecycle Log remains byte-identical and untracked.
2. Run Encrypted Secrets Transport in receive mode when configured. A missing tool/identity or a conflict is a portability finding; never silently overwrite plaintext.
3. If the incoming range changed an entry file, `_Axis/CHANGELOG.md`, or anything under `_Axis/Commands/`, `Practices/`, `Rules/`, `Resources/`, or other loaded Workflow machinery, the current in-memory instructions are stale. Say what changed in User terms, run `^shutdown`, and require a fresh session. Do not continue into `^resume` under old instructions.
4. Otherwise run the complete [Practices > Portability > Always-On Resume Revalidation] before treating the received state as current. Bare `^git` then runs the ordinary `^resume` summary automatically; `^resume` continues its own procedure.

## Command Modes

- **Bare `^git`:** no repository means Setup; a repository with local changes means checkpoint unless those changes are receive-safe and the remote is ahead; a clean or receive-safe remote-ahead repository means receive and resume; local-ahead means push; equal and clean means report current. It may offer Private Remote Setup when none exists.
- **`^save` outgoing:** perform an early fetch. A clean or receive-safe remote-ahead tree may fast-forward before the Snapshot; substantive local work plus remote-ahead is remembered as a local-only/divergent result. After the portability assessment, encrypted-capsule refresh, Snapshot, and Save Event, checkpoint and push whenever the graph remains linear.
- **`^resume` incoming:** fetch before reading the saved checkpoint. Fast-forward only from clean or receive-safe state, receive encrypted Secrets, then revalidate and summarize. Offline/authentication failure continues from local state with remote freshness `Unverified`.
- **Read-only intent:** `status`, `history`, and `diff` inspect bounded Git facts without staging, committing, fetching unless remote freshness was requested, or writing an Axis Event.
- **Local checkpoint intent:** `checkpoint` commits after all gates but does not push. Additional natural-language text is a commit-message hint, never shell syntax.

## Checkpoints

- Commit locally at meaningful moments: during `^save`, from `^git`, at milestones, and before rollback.
- During `^save`, write the Save Event before staging. The Snapshot and its audit Event enter the same commit. A later `^shutdown` Event is post-checkpoint operational evidence and is not promised to a Git clone unless another commit includes it.
- Use `axis: {event}` messages: `axis: initial project state`, `axis: snapshot {timestamp}`, or `axis: checkpoint - {concise semantic summary}`. Draft from the actual diff; never include secret data, local paths, or raw User prose unnecessarily.
- Do not create an empty commit. A clean tree is a successful no-op.
- Before every `git add -A`, run the Subproject gate below. After staging, inspect `git diff --cached` without printing discovered secret values. Block if a staged addition contains a secret-looking value, any `_Axis/Secrets/` path other than `.recipient` or `.capsule.age`, a complete nonce-bound Subagent Prompt Envelope under `_Axis/Logs/`, or a raw embedded source block over 8 KB under `_Axis/Logs/`. Report only file and rule. Move plaintext credentials to `_Axis/Secrets/`; replace prohibited prompt/source copies with the redacted metadata required by [Start-Subagent].
- Session Flags, Markers, Tracking, `_Temp/`, `_Trash/`, plaintext Secrets and `.binding`, and Wiki content stay ignored. When configured, only `_Axis/Secrets/.recipient` and `.capsule.age` are tracked from the Secrets directory. Project Subfolders and parent-tracked Subprojects are committed; exact-path ignored Subprojects are independent; submodules contribute only their gitlink.
- Routine `^git` checkpoint/push/receive uses the Git commit as its audit entry and writes no separate Event after the commit, because that would immediately dirty the synchronized tree. Log setup, remote/visibility changes, Secrets-capsule configuration, rejected safety gates, reconciliation, and rollback as their owning procedures direct; write any Event that belongs in a checkpoint before staging it.
- A failed commit or push is reported exactly. Never claim remote synchronization from a local commit alone.

## Encrypted Secrets Transport

Plaintext `_Axis/Secrets/` remains ignored even in a private repository. The optional capsule tracks only `_Axis/Secrets/.recipient` (public configuration) and `.capsule.age` (one encrypted archive whose interior hides the plaintext filenames). The private identity lives outside the project at `~/.axis/keys/{key-id}.agekey`; it never enters Git, chat, records, a Snapshot, Dashboard, or a Subagent.

### Enable once

1. Require an exact-root repository, valid `host-shell=yes`, Git, `tar`, and the official `age` plus `age-keygen` CLIs. If `age` is absent, explain the optional installation and offer an official platform-appropriate install after User approval. Axis remains usable and plaintext Secrets remain local when declined.
2. Run `bash _Axis/Resources/secrets-capsule.sh init` from the project root. The helper generates one project identity outside the project, writes only public configuration and verified ciphertext into the tracked exceptions, and returns a public key ID - never a secret value or filename.
3. Tell User to copy `~/.axis/keys/{key-id}.agekey` once to the same conventional location on each authorized computer and keep one protected recovery copy. Do not open or print it. Recommend full-disk encryption; anyone who gets both identity and capsule can decrypt every historical capsule.
4. Add or update required Environment declarations for `Secrets Encryption Tool` (`tool:age`) and `Project Secrets Identity` (`manual`). Their fallback is manual Secrets transfer and their re-establishment guidance is public documentation or `Ask User`; no key ID/path enters the declarations.
5. Stage and safety-check only `.recipient` and `.capsule.age`, write one configuration Event before the commit, commit, and push only to the already approved remote. Confirm private visibility once as defense in depth; if it cannot be verified, obtain User confirmation before the first capsule push.

### Send automatically

Before any outgoing `^git` checkpoint or repository-backed `^save`, run `bash _Axis/Resources/secrets-capsule.sh status` when `.recipient` or `.capsule.age` exists.

- `ready` or `local-changes`: run `seal`, verify `sealed`, then stage the two tracked files with the project checkpoint.
- `incoming`, `conflict`, or `unbound`: do not seal over an incoming state; stop the remote push and resolve receipt first.
- missing tool/identity, malformed state, or unsafe tree: preserve plaintext, do not replace the last valid capsule, mark Secrets transfer Degraded/Unverified, and never claim those Secrets were sent.
- `disabled`: plaintext remains ignored; when credential material exists, report that Git omits it without listing names.

The helper permits only ordinary files/directories, rejects links, special files, unsafe archive paths, duplicates, and oversized inventories, writes ciphertext atomically, decrypts it back for verification, and emits status tokens only. Never substitute a home-grown cipher, Base64, ZIP password, or a secret passed through chat.

### Receive automatically

After an incoming fast-forward, or during `^resume` when the capsule is configured, run `bash _Axis/Resources/secrets-capsule.sh receive`.

- `current` means plaintext matches the last verified capsule.
- `received` means incoming ciphertext was verified and installed through a pre-change copy plus exit rollback.
- `local-changes` means no incoming capsule change exists; keep the local plaintext for the next save.
- `error:secret-conflict` means both local plaintext and incoming ciphertext changed from their binding. Preserve both, reveal no names, and ask User which computer is authoritative before any replacement.
- missing identity/tool or malformed/unsafe input leaves plaintext untouched and becomes a named infrastructure restoration item.

The gitignored `.binding` stores only content digests needed to recognize a safe round trip. A full-folder copy carries it; a clone reconstructs it after the first verified receive. The helper uses permission-restricted operating-system temporary storage during verified replacement, makes a complete pre-change plaintext/binding copy before mutation, and restores it on an ordinary error or trapped exit. It removes temporary data on exit and never treats it as a durable backup; an untrappable process or machine failure can still leave recovery material for manual review.

Revoking a repository collaborator does not revoke a copied identity. If the identity is exposed, rotate every credential represented in historical capsules, create a new project identity, and review Git history/repository access. Encryption provides confidentiality for the repository copy, not endpoint isolation or proof that a remote writer was trustworthy.

## Subproject Repositories

Every recognized Subproject uses one explicit arrangement:

1. **Parent-tracked.** The Subproject has no inner `.git` file or directory. The parent's repository versions all child files alongside its own. A clone of the parent includes the Subproject.
2. **Independent repository.** The Subproject carries its own `.git` repository and may have its own remote or hosted GitHub repository. Add that child's exact root-relative path to the parent's `.gitignore` (for example, `/Clients/Acme/`). A clone of the parent does not include the child; clone the child separately into the same path. Never write a broad ignore rule that covers many nested projects at once, because that would also hide parent-tracked children and the required `.gitkeep`.
3. **Intentional submodule.** Add the Subproject with `git submodule add`, so the parent records `.gitmodules` and a gitlink to one child commit. A clone must run `git submodule update --init --recursive` (or use a recursive clone) to populate the child.

A nested Git repository is NOT automatically ignored by the parent. If a parent runs `git add` on an unignored embedded repository, Git normally warns and stages the directory as a gitlink (mode `160000`); it does not stage the child repository's ordinary files. That is incomplete unless User intentionally selected a submodule.

### Decision Point and Record

Git stores the arrangement; Axis does not duplicate it as a Setting. The authoritative state is the parent's tracked files, the exact child rule in `.gitignore`, or the `.gitmodules` entry plus gitlink.

Main Agent must STOP and ask User to select one of the three arrangements when User creates/moves a nested Project, a new immediate child is ambiguous, parent version control is enabled around a child, or the staging gate finds an incomplete/conflicting arrangement. Ask before initializing/removing a repository, editing `.gitignore` or `.gitmodules`, adding a remote, or staging the child. Explain what the parent clone includes. Never silently choose parent-tracked merely because a child has no `.git`.

If the parent is not a Git repository, parent-tracked and submodule modes require enabling parent version control. A child may still be independent, but enabling the parent later reopens this decision.

After User chooses:

- **Parent-tracked:** require no inner `.git`, exact ignore rule, or `.gitmodules` entry. Removing existing child history needs separate confirmation.
- **Independent repository:** retain/initialize the child's repository and add only its exact path to the parent ignore rules.
- **Intentional submodule:** require a retrievable child remote and use the normal submodule procedure so `.gitmodules` and gitlink agree.

Apply the choice when `host-shell=yes` and Git is available; otherwise provide and later verify the exact changes. After applying it, verify the exact repository state; never claim or record a completed configuration that was not verified. Write one parent-project Note and one Event with subject `Subproject repository arrangement: {path}` recording the non-secret operational evidence. Git remains the operational source of truth.

Before any parent-level `git add -A`, inspect every KNOWN nested Subproject - recognized Subprojects and incomplete candidates alike. A child with no inner `.git` whose files are not already parent-tracked is unconfigured, not automatically parent-tracked. If any child is new, ambiguous, contradictory, or incomplete, follow this Decision Point and STOP.

## Rollback

- Determine whether User means uncommitted changes, one path, one commit, or the whole project. Show the exact target and affected paths, then confirm before overwriting working content.
- Preserve unrelated current work with a normal safety checkpoint when one can be created. A clean tree needs no pre-undo commit.
- Undo a whole commit with `git revert --no-commit {commit}`, inspect the inverse, write its Event, and commit it as `axis: revert {summary}` so published history stays linear and reversible.
- Restore one file/folder with `git restore --source={commit} -- {path}`, inspect the result, write its Event, then commit it as `axis: restore {summary}`.
- Restore an old whole-tree state into a new recovery commit with its Event; never use `reset --hard` or rewrite shared history.
- Fetch/reclassify before rollback. Remote-ahead or divergent history stops until User chooses a reconciliation.
- Verify the resulting diff/commit, Log the confirmed recovery before its final checkpoint when an Axis Event is needed, and push the recovery commit when the configured upstream remains linear.

## Cautions

- A remote is transport, not a distributed Axis lease. Session Markers are intentionally ignored, so one clone cannot prove another computer stopped. Run `^shutdown` before opening a different writable copy.
- Cloud-synced folders can corrupt repository state and file locks; prefer a plain local folder for Git-backed projects.
- Git clones still omit Wiki content, plaintext Secrets when the encrypted capsule is disabled/unavailable, ignored independent Subprojects, host authentication, installed tools, machine/session Flags, Markers, Tracking, scratch, and Trash. `^save` and `^resume` report those omissions; a full-folder transfer remains the universal fallback.
- GitHub authentication must be established on each computer before it can fetch the encrypted capsule. Never put the bootstrap credential inside that capsule.
