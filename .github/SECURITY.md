# Security Policy

Axis Workflow is a set of Markdown instructions and small standard-library Python and shell helpers that run inside your own AI host. It has no server, no account and no network service of its own.

## Reporting a problem

Please report a suspected vulnerability privately through GitHub: open the **Security** tab of this repository and choose **Report a vulnerability**. Do not open a public issue for it.

Include what you observed, how to reproduce it, the Axis version (`current-version` in `_Axis/CHANGELOG.md`), your host and operating system, and what an attacker could gain. Remove any secrets or private project content first.

## What to expect

The maintainers read reports as they arrive, confirm or ask follow-up questions in the private advisory, and publish a fix in the next release with credit if you want it. Axis has no bug bounty.

## Scope

In scope: the shipped Axis files (`_Axis/`, the entry files) and how they protect project records, secrets in `_Axis/Secrets/`, updates and releases. Out of scope: the AI hosts and models Axis runs in, and projects built with Axis.

## What is checked

GitHub code scanning and the OpenSSF Scorecard run on this repository; their results are public in the Security tab and on scorecard.dev. These checks describe the repository's practices. They are not an audit, and Axis makes no claim to be secure.

<!-- axis:production-only - lives only on the public Axis repository; Axis removes it from a new project at first startup. -->
