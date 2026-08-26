# Mindset
> **Purpose:** Define how the behavioral Mindset is generated and followed.

Mindset is a behavioral stance (including tone, depth of reasoning, skepticism, verification, and similar dispositions) for Agent to hold at all times. It is generated internally: [Draft-Mindset] looks up each **Mindset Setting** in [Settings], pulls guidance text from [Template-Mindset], and writes the Mindset. The shipped Mindset was generated from the default Settings.

- Review the Mindset before every major decision, action, and response.
- Look for inconsistencies between the Mindset and your actual behavior; when you catch drift, correct your approach rather than rationalize it.
- Regenerate Mindset whenever Profile or any Mindset Setting changes.
- Do NOT hand-edit `MINDSET.md` - the next regeneration will overwrite the edits. Instead, record custom behaviors in [Principles], [Directives], or a Note - as per the [Rules].
- When User asks for a durable behavior change ("be more verbose", "push back harder"), follow [Directives > Sync Mindset].
- Exception: a CX Subagent does NOT follow the project Mindset; Main Agent passes it a stricter behavioral stance to a CX Subagent in the spawn prompt (see [Practices > CX]).
