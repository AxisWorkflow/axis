# Axis Workflow - Branding (product package)

Version **2.0.1** · 29 September 2026 · Owner: SimAxis

The small brand package that ships with every copy of the Axis Workflow, at `_Axis/Branding/`. It
gives the Dashboard and any local page the Axis look: the stylesheet, fonts, colour tokens, the mark,
the logo and the favicons.

**Do not edit these files.** They are replaced whole by each Axis update. The brand assets are
trademarks and are **not** covered by the Axis Workflow's MIT License; see `LICENSE-ASSETS.md`.

## Contents

| Path | Contents |
| --- | --- |
| `css/axis-brand.css` | Fonts, tokens, base type, components, light and dark themes |
| `tokens/` | `tokens.json` and `tokens.css` - colours, roles, dark theme, type, terminal rule |
| `fonts/` | Inter and IBM Plex Mono as WOFF2, with their SIL Open Font License texts |
| `svg/mark/` | The mark, positive and reversed |
| `svg/logo/` | The horizontal logo, positive and reversed |
| `svg/illustrations/pattern.svg` | The background pattern the stylesheet references |
| `favicon/` | `favicon.svg`, `favicon.ico`, `apple-touch-icon.png`, `icon-192.png`, `icon-512.png` |
| `manifest.json` | Every file with its SHA-256 |

## Use

```html
<link rel="stylesheet" href="_Axis/Branding/css/axis-brand.css">
<link rel="icon" href="_Axis/Branding/favicon/favicon.svg" type="image/svg+xml">
<body class="axis-root">
  <img class="axis-on-light" src="_Axis/Branding/svg/logo/logo.svg" alt="Axis Workflow" height="40">
  <img class="axis-on-dark" src="_Axis/Branding/svg/logo/logo-reversed.svg" alt="Axis Workflow" height="40">
```

Paths inside the package are relative, so it also works at the project root as `Branding/`. Tools
look in `_Axis/Branding/` first, then `Branding/`.

The theme follows the operating system; `<html data-axis-theme="light">` or `"dark"` fixes it. Script
output in a terminal is plain text with bold brand-blue headings only in a real terminal
(`tokens.json` → `terminal`).

The full brand package - every asset, Axel, illustrations, and the brand guidelines - is kept with
the Axis Workflow source and on axisworkflow.ai.
