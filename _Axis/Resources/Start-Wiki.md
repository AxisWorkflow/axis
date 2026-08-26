# Start Wiki
> **Purpose:** Interview User to infer and then draft a schema for the Wiki. Draft and save schema to `_Axis/Wiki/Library-Schema.md`. The file may already exist - if it does, read it now and continue to update and/or extend `_Axis/Wiki/Library-Schema.md` with a Schema. Don't create folders, scripts, or any other artifacts at this stage - only the schema.

## Step 1: Check the skip-wiki Flag

1. Read `_Axis/Flags/skip-wiki` under [Practices > Flags > Reading Flags]. Its only valid set value is a UTC timestamp. Missing, blank, malformed, or `cleared` is absent: GOTO Step 2.
2. If the Flag is set: ask User whether they want to change their mind and proceed with setting up the Wiki now.
	- If Yes: delete `_Axis/Flags/skip-wiki` and continue.
	- If No: tell User that the Wiki remains uncompleted. STOP.

## Step 2: Interview User

Ask one question at a time. Wait for each answer. Push back on vague answers - ask for a concrete example. Skip questions you can infer. Roughly 12-18 questions total, in four rounds.

1. After each round below, summarize what you have learned in 2-3 sentences and confirm before moving on.
2. Round 1 - Purpose:
	- Domain in one sentence (specifically what this wiki is for).
	- Source types User will feed into Wiki (articles, papers, transcripts, own writing, code, photos, etc.).
	- Top three questions User expects to ask the wiki most often.
	- Audience (just the User? a team? publication of Wiki for some purpose? etc.).
	- If User says something broad ("research" / "my business"), push for the narrower thing inside it.
3. Round 2 - Page types (the defaults are: **sources**, **entities**, and **concepts**):
	- Suggest **syntheses** (compiled rollups and maintained summaries) as an optional fourth default - the Query procedure files good answers back into the Wiki, and they need a home.
	- What recurring "things" in User's domain deserve their own pages beyond those three?
	- Anything User wants to track over time on a single page (a position that evolves) versus point-in-time records?
	- Domain-specific types worth their own category? (e.g., decisions, patterns, projects, recipes, gear, papers, clients - whatever fits).
	- Cap at 5-7 page types. Push back if User asks for more.
4. Round 3 - Workflow:
	- How sources arrive (manual drop, web clip, generated, email).
	- What should not enter the wiki.
	- Contradictions between sources: always flag, or auto-resolve? (Default and recommended: always flag.)
	- Any pages User will edit by hand that Agent should then preserve?
5. Round 4 - Conventions:
	- Filename slug style (kebab-case unless User says otherwise).
	- Frontmatter fields User actually wants.
	- Anything domain-specific about formatting (math, code, citation style, image embeds, language).

## Step 3: Confirm the Plan

1. Show User a one-screen plan: page types with one-line descriptions, the ingest / query / lint procedures in outline, and the prohibitions list.
2. Wait for approval. Iterate if User pushes back. Do NOT continue to Step 4 without approval.

## Step 4: Draft the Schema

1. Draft a schema in markdown using these sections, in order:
	- a. **What the wiki is** - one paragraph
	- b. **The three rules** - raw input is immutable, wiki supports User, every claim cites a source
	- c. **Page conventions** - frontmatter fields, filename slugs, wikilink format
	- d. **Page templates** - one per page type, kept short
	- e. **Operations** - ingest, query, lint. Each as a numbered procedure, ≤ 10 steps.
	- f. **Style** - cite at claim level not page level, plain prose, no invented facts, hedge when sources disagree
	- g. **What Agent should not do** - explicit prohibitions (see the constraints below)
	- h. **Evolving this schema** - propose diffs, don't modify without approval
2. Apply these hard constraints while drafting:
	- Model the schema on [v1 Karpathy](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f). Do not use confidence scores, supersession metadata, typed relationships, quality scoring, or auto-resolution.
	- Citation is very strongly encouraged - try to link every claim to a source.
	- Contradictions are flagged under a `## Contradictions` heading, but **not** resolved.
	- Write in second person ("you" addresses the future LLM maintainer).
	- Limit the frontmatter to the fields named in Round 4.
	- Never modify raw sources.
	- Use a direct tone and no hedging.
	- If User proposes something that is off-pattern (auto-resolve contradictions, 12 page types, skip citations), push back once with a good reason before going along with it.
3. Save the above 8 sections into `_Axis/Wiki/Library-Schema.md` (leaving the first header line and the second Purpose line, but replacing all other content). If the file is missing entirely, first create it with the H1 `# Wiki Library Schema` and the Purpose line `> **Purpose:** Define a schema for the Wiki Library.`, then save the 8 sections beneath them.

## Step 5: Create Supporting Files

Create supporting Wiki files when missing (the first Wiki Subagent run will populate them with real content).

1. `_Axis/Wiki/Input-Index.md` - Index of files in `Wiki/Inbox/` that have been ingested.
	- If the file already exists, do NOT overwrite it.
	- If this file is missing, create and initialize it with: the H1 header `# Wiki Input Index`; the Purpose line `> **Purpose:** Index of all inbound raw source documents for the Wiki.`; a blank line; then a placeholder line `{{ no content yet }}`.
2. `_Axis/Wiki/Library-Index.md` - Catalog of every Wiki page with a one-line summary.
	- If the file already exists, do NOT overwrite it.
	- If this file is missing, create and initialize it with: the H1 header `# Wiki Library Index`; the Purpose line `> **Purpose:** Index all pages in the Wiki.`; a blank line; then a placeholder line `{{ no content yet }}`.
3. `_Axis/Wiki/Library-Activity.md` - Append-only log of Wiki ingests, queries, and lint passes.
	- If the file already exists, do NOT overwrite it.
	- If this file is missing, create and initialize it with: the H1 header `# Wiki Library Activity`; the Purpose line `> **Purpose:** Log activity relevant to the administration and updating of the Wiki.`; a blank line; then a placeholder line `{{ no content yet }}`.

4. `_Axis/Wiki/Library-Status.md` - Append-only Library Status record of Wiki Review findings.
	- If the file already exists, do NOT overwrite it.
	- If this file is missing, create and initialize it with: the H1 header `# Wiki Library Status`; the Purpose line `> **Purpose:** Append-only record of Wiki status - one ## section per report, headline by date.`; a blank line; then a placeholder line `{{ no content yet }}`.

## Step 6: Close Out

1. Log an Event to record the setup of the Wiki. STOP.
