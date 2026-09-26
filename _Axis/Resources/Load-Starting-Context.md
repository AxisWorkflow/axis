# Load Starting Context
> **Purpose:** Load the exact governing startup core for Main and External, with a portable source fallback.

## Source table

This table is the sole ordered input list for the compiler and manual fallback. `whole` means the entire source; a section means its exact heading and text through the next heading of equal level or end of file. No independent summary is permitted.

| Source | Selection |
| --- | --- |
| `_Axis/PRACTICES.md` | whole |
| `_Axis/Practices/References.md` | whole |
| `_Axis/Practices/Markers.md` | whole |
| `_Axis/PRINCIPLES.md` | whole |
| `_Axis/RULES.md` | whole |
| `_Axis/Practices/Flags.md` | Reading Flags |

## Load completion

This Resource owns one complete core load in this admitted startup. Do not repeat a completed core read after this Resource returns. Reuse actual full instruction text still available in this context, never a remembered summary or a prior session. A changed source, context loss or reported truncation requires the affected read again. Treat completion only as knowledge of available text, with no disk cache, Flag or receipt, and never as authority to skip fresh state rereads.

Plan the response capacity before retrieval, including aggregate output from grouped calls. Use named file boundaries and split oversized reads before requesting them; sequential bounded file tools are sufficient. A retained end marker does not excuse a reported middle cut. Reading the file again solely to reassure yourself after a complete result adds no evidence.

Main-only required inputs: when called by Main's Start-Session Step 1, also load `_Axis/Practices/Logs.md`, `_Axis/Practices/Tracking.md`, `_Axis/Resources/Detect-Capabilities.md` and `_Axis/SETTINGS.md`. These may share the selected core's bounded batch when the full output fits. External and other callers load only the core. Retrieving instructions never executes their probes or changes their order; Main applies standing User guidance before those actions.

## Steps

1. Compare `mtime` of this loader and every source in the table with `_Axis/Resources/Starting-Context.md`, without reading their bodies yet. Missing bundle or newer input means stale. Missing required source or unreadable freshness metadata means the compiled shortcut is unavailable; GOTO3, which validates actual source availability.
2. Read the complete bundle through terminal `<!-- axis:starting-context:end -->`. Any reported truncation, including a middle cut with a retained tail, is incomplete; GOTO3. Otherwise GOTO5 with the completed core; do not read it again.
3. Read every selection in Source table directly, in order, using bounded file reads where necessary. A bounded batch may retrieve independent sources together while preserving table order and named boundaries; the same complete-read gate applies. Require its full text, intact section boundaries and no reported truncation. A missing required source, missing section or failed complete read stops startup; report the exact path and STOP. Do not substitute memory or a guessed summary.
4. Main queues one concise stale/missing-bundle notice; External loads without that notice. No repair or compile is required during startup. The fallback is equivalent core context and needs no shell, Python or other add-on. GOTO5 with the completed fallback.

5. Main only: for the Start-Session Step 1 caller, load any Main-only required input above whose full current text is not already loaded; after lost or incomplete output, recover only the affected input. Other callers perform no Main-input read. RETURN the complete core and any required Main inputs to the caller, then STOP this Resource.

## First-use closure

The complete PRACTICES and RULES indexes remain always loaded. Their triggers are mandatory before each affected action, including after context loss. Read [Glossary] only for an Axis meaning not defined in loaded context, before relying on that meaning. Read [Manifest] before its startup presence check or a layout change. Read [Practices > IndexDetail] before interpreting or writing an index/detail record, [Practices > Flags] for the registry before creating or changing a Flag whose domain is not fully specified by its owning loaded procedure, and [Practices > Commands] before interpreting or dispatching a literal User Command. Reading Flags above applies to every Flag consumer. The User Manual remains explanatory and outside ordinary startup. A deferred source cannot disappear merely because the first turn has not used it yet.
