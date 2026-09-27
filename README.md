# Axis Workflow

[![License: FSL-1.1-MIT](https://img.shields.io/badge/License-FSL--1.1--MIT-2ea44f.svg)](/_Axis/LICENSE)
[![Version](https://img.shields.io/badge/Version-1.02-blue.svg)](https://github.com/AxisWorkflow/axis)
[![Works with](https://img.shields.io/badge/Works%20with-Claude%20Cowork%20%7C%20Claude%20Code%20%7C%20ChatGPT%20Work%20%7C%20Codex%20%7C%20Cursor%20%7C%20Gemini%20CLI-6f42c1.svg)](https://github.com/AxisWorkflow/axis)

The [**Axis Workflow™**](https://github.com/AxisWorkflow/axis) is a source-available project developed by [SimAxis](https://simaxis.ai). Current releases use [FSL-1.1-MIT](/_Axis/LICENSE): most use is allowed immediately, Competing Use is prohibited, and each version converts to MIT two years after that version is made available. The license grants no trademark rights. If you like **Axis**, [please buy us a coffee](https://buymeacoffee.com/SimAxis). Please **[star the repo](https://github.com/AxisWorkflow/axis)** - it helps others to find it.

> **How to use Axis:** read the **[User Manual](/_Axis/USERMANUAL.md)**. Technical, security and compliance details are in the **[Specification](/_Axis/SPECIFICATION.md)**.



## Quick Start

1. [Download Axis](https://github.com/AxisWorkflow/axis/releases/latest/download/axis-project.zip) and unzip - now you have a project folder.
2. Open the folder with Cowork, Claude Code, Codex, Cursor, Gemini, etc...
3. Say hello. Your Agent finds the Workflow and helps you get started.

	That's it. **60 seconds** to go time!



## What is the Axis Workflow?

**Axis** is a simple but disciplined way to work with AI Agents. Drop Axis into your project (just a few folders of instructions), open your project folder with your AI (e.g., Claude Code, Codex, Cowork, etc.), and Agents will automatically start to plan, track tasks, keep records, hold memory between sessions, and cross-check everything you do. Best of all, the canonical project files stay in your own project folder.

You do not need to open an account, install an app, or set up a server. Axis is free - simply download the Axis files, drop them in, and go.

![An Axis project folder: your own work sits beside the _Axis control folder, which holds the Plan, Tasks, Notes, Logs, Snapshots, Wiki and Dashboard as plain Markdown files](/_Axis/Resources/axis-folders.svg)

Open the live Dashboard with `^dashboard` to see the whole project at a glance, read directly from those files:

![The Axis Dashboard on the Meridian example project - Configuration, Mindset, Agents, Project, activity queues, Plan, Tasks, and the newest Status Report](/_Axis/Resources/axis-dashboard-meridian.png)

### Features at a Glance

- **Memory between sessions.** The Agent reads your Plan, Tasks, Follow-Ups, Snapshots and Notes at startup, so it knows where you left off without being prompted.
- **Planning and tracking.** A Plan, Tasks with status and history, Follow-Ups for the things only you can do, time-based Reminders, and optional Initiatives that group related Tasks.
- **A permanent record.** Logs, Snapshots, Status Reports and Cross-Examinations are written once and never edited, so the history of your project can be audited.
- **Cross-examination.** A separate Agent can challenge key decisions and deliverables before you rely on them.
- **A knowledge wiki.** The Agent builds and cross-links a Wiki from your sources, readable in Obsidian or any Markdown editor.
- **A live Dashboard.** `^dashboard` shows the Plan, Tasks, queues, activity and reports, read directly from your files.
- **Simple commands.** Type `^help` for the list: save and resume, notes, ideas, status, archive and more.
- **Portability.** Switch AI tools or computers mid-project; optional Git support checkpoints and moves your work.
- **Cost control.** Routine work can go to cheaper or local models while stronger models handle judgment.



## Why use the Axis Workflow?

- **Control your content.**

  **Axis** captures everything about your project and stores it on **your computer:** Plans, Tasks, Follow-Ups, Notes, Ideas, Logs, Snapshots, Wiki content, etc.

- **Avoid lock-in.**

  **Axis** runs from a simple collection of Markdown files. You can switch AI tools without exporting or converting your project; the new host reads the same directory and revalidates its own capabilities at startup.

- **Track changes.**

  **Axis** integrates the **`git`** version-control system for knowledge work (optional - not required). A standard practice in software development, **`git`** lets you track and roll back changes and makes coordinated, single-writer handoffs between computers much easier.

- **Audit your work.**

  **Axis** records core events and material decisions in write-once files, creating a traceable history of your inputs, Logs, Tasks, Plans, Reminders, Follow-Ups, and deliverables.

- **Cross-examine results.**

  **Axis** does not just oversell the first solution - it can spin up a devil's advocate to cross-examine results. When a local model is used (see [Settings > CX Model](/_Axis/SETTINGS.md#cx-model)), that additional critique has no per-token provider charge, so you can use it on routine work as well as final deliverables.

- **Improve security.**

  **Axis** treats external sources as untrusted data and directs your Agent to warn you when it finds instruction-shaped content that may be a prompt-injection attempt.

- **Control Costs.**

  **Axis** implements an internal routing table to route tasks to the least expensive model that is qualified to perform it. Local and lower-cost models can handle routine work; stronger models are responsible for synthesis, judgment, and sensitive decisions. Every handoff is validated, with retry and fallback when the economical route does not meet a rigorous contract.

- **Work how YOU want to work.**

  **Axis** is completely open and transparent. Everything is right there in your own project directory; you can ask your Agent to customize the Workflow, add features that fit your needs, or adapt **Axis** and make it your own.



### Compare Alternatives

| Capability               | Axis | Chat projects  | NotebookLM     | Obsidian <br> + Agent |
| ------------------------ | ---- | -------------- | -------------- | --------------------- |
| Control<br>your content  | Yes  | Tied to vendor | Tied to vendor | Yes                   |
| Switch AI<br>mid-project | Yes  | No             | No             | Only if you are ready |
| Versioning<br>& Rollback | Yes  | No             | No             | Only if you know how  |
| Knowledge<br>Base        | Yes  | Retrieval only | Retrieval only | Only if you build it  |
| Cross Examination        | Yes  | No             | No             | Only if you build it  |



## Who needs the Axis Workflow?

- Knowledge workers with independent projects.
- Entrepreneurs with new products or business plans.
- Attorneys with a large number of case documents and filings.
- Managers with complex reporting across multiple teams.
- Scientists working on technical projects.
- Professors researching new topics.
- Teachers developing new courses.
- Students working on major projects.
- Parents keeping the family-life on track.
- Anyone who is just doing life (filing taxes, managing mail, etc.).

**Axis** is **not** the best solution for:

- Programming - Cursor and Visual Studio are better for building software.
- Complex collaboration - Asana, Trello, and Slack are better for coordinating teams.
- Knowledge sharing - Confluence and Notion are better for enterprise platforms.
- Skim [Limitations](/_Axis/SPECIFICATION.md#limitations) before you commit a large project to the Axis Workflow - we want you to find the right fit for your particular project.



## Learn More

- **[User Manual](/_Axis/USERMANUAL.md)** - how to use Axis day to day: setup, commands, the Dashboard, the Wiki, portability, and working with Agents and models.
- **[Specification](/_Axis/SPECIFICATION.md)** - the technical reference for IT, security and compliance reviews, and for Agents: system design, security model, limitations and every key file.



## Trademarks

"Axis Workflow", "Axis" when used as the name of this project, and their associated logos and lockups are trademarks of Kenneth A. Younge. The "Axis Workflow" trademark was originally registered in Switzerland. "SimAxis" and its associated marks are trademarks of [SimAxis](https://simaxis.ai). Together, these are the "Marks" used in this notice. The [Axis FSL-1.1-MIT License](/_Axis/LICENSE) covers Axis-authored text, templates, and code in current releases. It does not grant rights to the Marks or automatically license the User's project. Copyright and trademark are separate: the future MIT grant changes copyright permissions after two years, but it never grants trademark rights.

#### You may, without asking

- Use the Marks to refer truthfully to this project - for example, "built with the Axis Workflow", "compatible with Axis Workflow", or "a tutorial for Axis Workflow".
- Redistribute unmodified copies of this repository under the project name, with a link to the official source.
- Say that your product, service, or training works with the Axis Workflow, provided no sponsorship or endorsement is implied.

#### Please do not

- Use the Marks, or confusingly similar names, logos, or domains, as the name of a fork, product, service, company, course, or website. Give forks their own name and describe them as "based on the Axis Workflow".
- Imply sponsorship, certification, or endorsement by SimAxis without a written agreement.
- Alter the Marks or combine them with other names or logos.

#### Symbols and attribution

- On first prominent use in a document, write "Axis Workflow™"; after that, plain "Axis Workflow" or "Axis" is fine.
- When an attribution line is appropriate, use: "Axis Workflow™ - source available under FSL-1.1-MIT, from SimAxis."

Questions or permission requests can be sent to [AxisWorkflow](https://axisworkflow.ai).



## License

This release is licensed under the **Functional Source License, Version 1.1, MIT Future License (`FSL-1.1-MIT`)**. The license permits use, study, modification, and redistribution for any Permitted Purpose, but prohibits making Axis available as a competing commercial product or service. An MIT license is then issued two years after this version was first made available. Third-party components retain their own copyright and licenses, including the bundled Mermaid renderer. See the complete [Axis License](/_Axis/LICENSE), [Contributor License Agreement and Copyright Assignment](/_Axis/CLA.md), and [Trademarks](#trademarks).



## Copyright

Copyright 2026 Kenneth A. Younge. All rights reserved except as expressly licensed.

<!-- axis:workflow-readme -->
