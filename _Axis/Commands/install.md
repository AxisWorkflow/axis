# ^install
> **Purpose:** Install extensions, tools, skills, MCPs, CLIs, functions, etc.

1. Main Agent only. External Agents send a Request to Main; Subagents return the request without acting. Installing changes the current host, not merely the project, so never delegate the trust or approval decision.

2. Resolve the text after the command by intent: `qmd` or local document search GOTO **qmd**; `age`, encrypted Secrets, or Secrets transport GOTO **age**; `ollama`, a supported local model name, or local LLM setup GOTO **Ollama**. If User asks for a different local LLM runtime, say in one line that Axis supports Ollama as its sole local runtime, then GOTO **Ollama**. Anything else, including no target, GOTO **Other**. Never run the text as a shell tail.

3. Every route follows **Installation Contract** before its specific steps. A route may add stricter checks but never skip the shared source, preview, approval, verification, or recording boundary.

## Installation Contract

1. Establish the exact target and purpose before changing anything: official product/package name and publisher; CLI, application, plugin, skill, MCP, service, or model; project-local versus host-wide scope; and the feature that will consume it. If User gave no target, ask what capability they want and mention only the few relevant README Add-ons; do not browse for or install a bundle speculatively.

2. Inspect the current host read-only: operating system/distribution and version, architecture, available package manager or native host installer, `host-shell` when shell work is proposed, existing installation and version, prerequisites, and likely conflicts. Do not infer Windows package management from WSL or vice versa. Do not enumerate unrelated host software, accounts, credentials, or global configuration.

3. Use current first-party installation documentation and the publisher's official package/repository. Prefer an already trusted platform package manager or the host's native extension/connector manager. Never substitute a similarly named package, third-party mirror, issue-comment recipe, unofficial plugin, or moving source checkout. Never pipe a download directly into a shell or execute a downloaded installer script without a separate inspection and approval boundary.

4. Before mutation, tell User in plain language: the exact command or host action; publisher/source; install scope; meaningful download, disk, service, permission, account, network, restart, or model-cache effects; how success will be checked; and the known uninstall/rollback path. Obtain approval for that exact bounded change. A command invocation is not permission for `sudo`, an OS package-manager change, a new account/login, a background service, a browser extension, broad host permissions, or an additional model download unless those effects were explicitly included. Never ask User to paste a password, token, private key, or recovery code into chat; use the native prompt, browser login, keychain, or approved Secrets path.

5. Install one layer at a time. Do not silently change package manager, publisher, version channel, global/project scope, privilege level, or fallback tool after a failure. Preserve the useful error text while redacting credentials and local private paths; diagnose against current first-party documentation, then explain and STOP if the approved path still fails.

6. Verify independently after installation: re-run the product's version/identity check, perform one harmless functional smoke test, read back any configuration the route changed, and confirm the intended Axis capability rather than treating exit code zero as enough. Report the installed version and outcome, not the resolved executable path or host-private details. Do not enable optional integrations, index User files, start persistent services, download models, authenticate accounts, or modify project configuration unless the approved route explicitly includes that phase.

7. For a nontrivial dependency the project will use, read [Practices > Portability] and add or update its logical `_Axis/ENVIRONMENT.md` declaration with purpose/consumer, required or optional status, safe revalidation, fallback, and a non-secret official setup reference. Never record the local install path, account, current-health claim, credential, private key, or secret filename. Log a project behavior/configuration change; a host-wide install with no project use needs no project Log. Refresh the owning Capability Flag when one exists. Report the verified result and the one next configuration step, if any. STOP unless the selected route explicitly continues.

## qmd

**qmd** is a local search engine for markdown files with hybrid BM25/vector search and re-ranking, all on-device. It has both a CLI (so the Agent can shell out to it) and an MCP server (so the Agent can use it as a native tool). qmd is useful for searching across files in the project Wiki, as well as other project files provided by User.

1. Follow **Installation Contract** using only the current qmd repository/README (https://github.com/tobi/qmd). Check `qmd --version` first. Verify one supported runtime before proposing installation: current qmd requires Node.js 22+ or Bun 1+; macOS also requires Homebrew SQLite for extension support.
2. Prefer the official published package through an already installed supported runtime: `npm install -g @tobilu/qmd` or `bun install -g @tobilu/qmd`. Do not clone the development repository by default. Preview and obtain approval for the chosen global package install and any missing prerequisite separately.
3. Verify `qmd --version`, then run `qmd doctor` without printing local collection paths in the User-facing response. Explain before any embedding step that qmd downloads and caches several local GGUF models and may use multiple gigabytes. Installing qmd does not authorize indexing the project or downloading those models.
4. If User also asked for setup, propose one narrowly named collection and its exact project-root-relative source, then obtain separate approval before `qmd collection add`, `qmd update`, or `qmd embed`. Never index `_Axis/Secrets/`, `_Temp/`, `_Trash/`, protected `_X` content, or a broader directory than User approved. Complete the Installation Contract recording step. STOP.

## age

**age** is Axis's optional encryption tool for carrying an encrypted `_Axis/Secrets/` capsule through Git. Axis itself and ordinary local-only Secrets do not require it.

1. Follow **Installation Contract** using only age's official repository/installation table (https://github.com/FiloSottile/age#installation). Check both `age --version` and `age-keygen --version`; one missing executable is an incomplete installation.
2. When missing, choose the exact currently documented command for the detected platform. Common official routes are `brew install age` on Homebrew macOS/Linux, `winget install --id FiloSottile.age` on Windows, `apt install age` on Debian 12+/Ubuntu 22.04+, `dnf install age` on Fedora, `pacman -S age` on Arch, `apk add age` on Alpine, and `pkg install age` on FreeBSD. WSL follows its Linux distribution. Do not download a prebuilt binary or build from source when a supported trusted package manager is available; if User chooses either exceptional route, verify its official provenance/signature instructions separately.
3. Preview the exact package-manager change and obtain approval. If elevation is required, disclose it and let the operating system request authorization; never request the password in chat. Run only the approved install command.
4. Verify that both executables report the same installed release. Then perform a privacy-safe smoke test in a permission-restricted temporary directory: generate an ephemeral identity with output suppressed, derive its recipient, encrypt the fixed literal `axis-age-smoke`, decrypt it, and require an exact byte match. Print or Log no identity, recipient, ciphertext, or temporary path; remove the temporary directory afterward.
5. Invoking `^install age` alone installs and verifies the tool but does not create a project identity or enable Secrets transport. If User also asked to enable encrypted Secrets, continue only after the smoke test to [Practices > GIT > Encrypted Secrets Transport > Enable once], which has its own repository, identity-storage, remote-visibility, and commit gates. Complete the Installation Contract recording step. STOP.

## Ollama

1. Check whether Ollama is installed (`ollama --version`).
2. If missing: follow **Installation Contract** against Ollama's current official installation page (https://ollama.com/download), preview the exact platform-native install and service effects, and ask User whether to proceed; if No, STOP. After installation, require `ollama --version` before continuing.
3. Run `ollama list` to see which models User has already pulled.
4. Pick a sensible starting candidate: prefer Qwen3-VL 4B Instruct Q4 (`qwen3-vl:4b-instruct-q4_K_M`) - the benchmark-recommended default on the tested reference machines - with `gemma3:4b` as a small installation fallback, and `qwen3:8b` as a scored but materially slower alternate on machines with more capacity; otherwise choose a small general-purpose instruct model such as `llama3.2:3b`. The accepted Qwen3 8B reference passes extraction, classification, and citation preservation, but every new machine must still earn its own matching aptitude and task-class evidence. The recommendation only chooses what to test - it never grants aptitude. Do not recommend DeepSeek-R1: repeated benchmark campaigns preserved it as high-latency negative evidence for this bounded work. Treat any other reasoning-tuned model or thinking mode as benchmark-first because such models can overthink simple transforms and run long per request; suggest one only when User explicitly asks for it or matching accepted class evidence exists. Confirm the choice with User.
5. If no suitable model is installed: suggest one to pull (e.g., `ollama pull qwen3-vl:4b-instruct-q4_K_M`) and wait for User to confirm before running it.
6. Verify: `ollama run {model} "ping"` should return a non-empty response. If it does not, tell User and STOP.
7. GOTO **Local LLM Models**.

## Local LLM Models

You arrive here from **Ollama** having chosen a model; the base URL is `http://localhost:11434/v1`.

1. Write the chosen model name into [Settings > Local Model] (`### {Setting}` → `**Value:** {model}`). Do NOT touch [Settings > CX Model] yet - the Aptitude Check below decides whether this model is fit to cross-examine.

2. Aptitude Check - sets expectations BEFORE real work is delegated. Build five prompts from [Template-LocalPrompt], send each with a generous response-length cap, strip `<think>...</think>` blocks and leaked `<|...|>` special tokens, extract the text between the LAST complete pair of output markers, and validate mechanically - applying the same one-feedback-retry loop as [Start-Subagent] (a pass on retry counts, noted as such):
	- a. Token echo - INPUT names a single token (`OK-AXIS`); TASK: output it exactly. PASS = the text between the markers is exactly `OK-AXIS`.
	- b. Field extraction - INPUT: five lines naming a person, a date, and a total; TASK: return `name:`, `date:`, and `total:` lines. PASS = all three keys present with the correct values.
	- c. Constrained summary - INPUT: a ~200-word paragraph; TASK: a one-line summary of 25 words or fewer. PASS = exactly one line, 25 words or fewer, between the markers.
	- d. Flaw spotting - INPUT: a five-sentence argument containing exactly one planted flaw (e.g., sales counts that contradict a "best day" claim); TASK: name the flaw in one line. PASS = the flaw is correctly identified. This fixture gates judgment work: on a FAIL, warn User specifically that this model is a poor fit for [Settings > CX Model] (Cross-Examination), even if the clerical fixtures passed.
	- e. Long-input fidelity - INPUT: roughly 6,000 characters of filler prose with a distinctive verification phrase planted in the LAST 200 characters; TASK: report that phrase in one line. PASS = the phrase is reproduced exactly. This fixture measures the EFFECTIVE context window, which no other fixture touches: a prompt longer than the server's window is truncated SILENTLY, and the model then answers confidently from material it never saw. On a FAIL, raise the context window (`num_ctx`) and re-run before delegating any work that embeds a long source.
	Show User a per-fixture PASS / PASS-on-retry / FAIL scorecard, save it in a Note, and Log one Event with the scorecard and the model name (the WORM copy survives Note archiving, so `^audit` can compare later failure rates against it). On any FAIL, warn User: delegation will lean on the validate-retry-fallback loop (see [Start-Subagent]) more often, and a stronger local model may be worth pulling.

3. Point Cross-Examination at the model only if it earned it. If fixture (d) PASSED (on the first try or on the retry): write the model name into [Settings > CX Model] and tell User that Cross-Examination will now run locally. If fixture (d) FAILED: leave [Settings > CX Model] at its current value, and tell User in one line that the model handles clerical work but missed the planted flaw, so critique stays on the host model - they can override by setting it themselves.

4. Record the scorecard where it survives. Write `_Axis/Flags/local-aptitude`: the model name on Line 1, a UTC timestamp on Line 2, and the five fixture results in order on Line 3 as `PASS`, `RETRY`, or `FAIL` (e.g., `PASS RETRY PASS FAIL PASS`). The Note and the Log entry stay as the readable record; this Flag is the structured one, so a later session - or a session on a different AI platform - can see at a glance whether this model was ever vetted, and which fixtures it failed, without mining Logs.

	If User or an organization has also run a repeatable multi-sample benchmark, preserve its report path in the Note. Append its verified fingerprint on Line 4 as `benchmark: transport=ollama quantization={token} context={integer}`, then append only its stable routing decisions as `class-score: {task-class} {PASS|CONDITIONAL|FAIL} {passed}/{total} first={first-pass}/{total}`. Do not infer one class from another, and do not append a score from a different model, quantization, machine, transport, or configured context. [Start-Subagent] consumes these optional rows. The five-fixture installation check remains the required baseline; do not turn routine installation into a full benchmark.

5. Write `yes` into the Flag `_Axis/Flags/host-local-llm`: the value on Line 1, a UTC timestamp on Line 2, and the base URL `http://localhost:11434/v1` on Line 3. [Start-Subagent] reads the URL from there. STOP.

## Other

1. Follow **Installation Contract**. If the target is ambiguous, clarify the capability and exact product before researching or changing anything. The README Add-ons are suggestions, not a bundle or allowlist; mention only options that directly fit User's stated need.
2. For a host skill, plugin, MCP, connector, or extension, use the host's official management surface and current first-party listing. Before approval, name the publisher, requested permissions/data access, scope, authentication, persistence, and removal path. Installation never authorizes connecting an account, granting broad permissions, or sending project data.
3. For a CLI, application, service, or library, use the official package and an already trusted package manager where possible. Keep host-wide tools separate from project-local dependencies; do not create a lockfile, manifest, virtual environment, daemon, login item, or background service unless User approved that exact scope.
4. Run the product-specific version check and one harmless functional probe, then complete the Installation Contract recording step. When done, STOP.
