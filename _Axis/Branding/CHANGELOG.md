# Changelog - Axis Workflow Branding package

## 2.0.1 - 29 September 2026

Names only; no asset or rule changed.

- The exports are now named `SimAxis Branding/` (full package) and `_Axis Branding/` (product
  package). Where they go in the development project is unchanged: the full package at the
  repository root as `Branding/`, the product package at `_Axis/Branding/`.

## 2.0.0 - 29 September 2026

New rules the development project must act on, so a major version.

- **Two packages, one version.** The full package (`Branding/`, repository root: website, README,
  docs) and a small product package (`Branding-Product/`, shipped at `_Axis/Branding/` in every
  release): stylesheet, WOFF2 fonts, tokens, mark, logo, favicons. Either may live at the root or at
  `_Axis/Branding/`; tools look in `_Axis/Branding/` first. The product package is a byte-identical
  subset of the full one.
- **Dark theme.** Plain text on navy, plain white headings; colour only on links, buttons, focus and
  the logo. Follows the operating system; `data-axis-theme` fixes it. Components now use role tokens.
- **Terminal rule (GUIDELINES 8A).** Plain text; bold brand-blue headings only in a real terminal,
  with the blue chosen by background and none when the background is unknown.
- **Fonts as WOFF2.** Inter subset (877 KB to 188 KB); IBM Plex Mono repackaged unchanged. The
  stylesheet now loads the WOFF2 files. The full package keeps the TTFs for design tools.

## 1.0.1 - 29 September 2026

Wording only; no asset changed.

- Canonical credit line now includes the license: "Axis Workflow™ is free and open source (MIT
  License), from SimAxis - training and consulting at simaxis.ai." (Ken, 29.09.2026). Update the
  footer and README credit line to match.

## 1.0.0 - 29 September 2026

First export for the development project.

- Identity: the Curved crosshair mark, the two-tone wordmark and Axel, as approved on
  25 September 2026. Colour and type are unchanged from the 21 September identity.
- Assets: every SVG from the approved package, plus reversed Axel for the wave and point poses and
  transparent-background versions of every Axel drawing (both derived mechanically; no new drawing).
- PNGs at standard sizes, favicons (ICO, Apple touch, 192 and 512), and the social preview.
- `css/axis-brand.css` stylesheet and `tokens/` (JSON and CSS variables).
- `GUIDELINES.md` contract, including wording rules: MIT License, `Start Axis`, the canonical
  credit line.
- `LICENSE-ASSETS.md`: brand assets are not covered by the software's MIT License.
