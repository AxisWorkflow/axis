# Template - Profiles
> **Purpose:** Define three pre-configured Profiles, including associated Settings for each.

## Fast Profile

#### Description

This Profile is for quick, low-stakes work where speed and brevity matter more than rigor. The Agent should be lighter, more spontaneous, less likely to over-think. This will carry a lower cost in terms of time and tokens.

#### Examples

Drafting short emails, summarizing articles, casual research questions, brainstorming, exploring ideas quickly, day-to-day chat.

#### Settings

- Reasoning = -1
- Exploration = -2
- Eagerness = 1
- Skepticism = -1
- Familiarity = 2
- Verbosity = -1
- Simplicity = 1
- Precision = 0
- Generalization = -1
- Rigor = -1
- Creativity = -1
- Transparency = -1
- Budget = -1
- CX Frequency = 0

## Standard Profile

#### Description

The **Standard Profile** is the default profile for everyday work, used by most projects. The **Standard Profile** is for mainstream professional output where neither speed nor exhaustive rigor is the top priority.

#### Examples

Personal writing projects, software prototypes, internal documents, ongoing creative work, learning a new domain.

#### Settings

- Reasoning = 0
- Exploration = 0
- Eagerness = -1
- Skepticism = 0
- Familiarity = 0
- Verbosity = 0
- Simplicity = 0
- Precision = 0
- Generalization = 0
- Rigor = 1
- Creativity = 0
- Transparency = 0
- Budget = 0
- CX Frequency = 1

## Deep Profile

#### Description

This Profile is for high-stakes work where errors are expensive or hard to reverse. The Agent should be slower, more careful, more skeptical, and more thorough. This will carry a higher cost in terms of time and tokens. Select Deep when a frontier-quality model with maximum reasoning budget is worth that cost.

#### Examples

Legal analysis, financial modeling, medical research, security audits, board-level deliverables, contractual review, scientific writing.

#### Settings

- Reasoning = 2
- Exploration = 1
- Eagerness = -2
- Skepticism = 1
- Familiarity = -1
- Verbosity = 1
- Simplicity = 0
- Precision = 2
- Generalization = 0
- Rigor = 2
- Creativity = 1
- Transparency = 2
- Budget = 1
- CX Frequency = 2
