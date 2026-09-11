---
name: landing-page
description: Use when transforming product source into persuasive landing-page copy and a responsive local static HTML preview with supported proof and an honest call to action.
---

# Landing page

Read the shared [workflow and source gate](../write/references/workflow.md), [editorial guidance](../write/references/editorial.md), and [visuals](../write/references/visuals.md) when assets are useful.

Accept `--format copy|html|both` (default both), `--cta TEXT`, and `--cta-url URL` plus shared options. Infer an action only when product context supports it; ask for essential missing offer/audience facts after inspection.

Build the argument from reader and action: a hero identifying category/useful outcome/audience; mechanism; actual example/screenshot/result or approved customer proof; prerequisites/limitations/fit/objections; suitable closing action. This is a starting structure, not a required funnel. Do not manufacture anxiety, urgency, guarantees, logos, testimonials, or numbers.

Deliver `landing-page.md` and `preview/index.html` by default, selected actual assets, and private review records. For HTML, prefer authorized existing project styles or the packaged plain static renderer at [render-page.js](../../scripts/render-page.js). Resolve that script relative to this installed skill; invoke Node with argument arrays using `page.json` and a new authorized output directory whose parent exists. Inputs and relative assets stay under the source directory, including resolved symlink targets. The renderer writes both copy and HTML; for a single-format request deliver only the selected finished format. Its input is:

```json
{
  "title": "Source-backed page title",
  "description": "Accurate page summary",
  "audience": "Intended reader",
  "hero": {"heading": "Actual headline", "body": "Actual supporting copy"},
  "cta": {"text": "Try the documented example"},
  "sections": [{"id": "workflow", "heading": "Actual section heading", "body": "Actual copy", "bullets": ["Supported point"]}]
}
```

Replace illustrative copy with supported final content. `cta.url` is optional; each section may have `image: {file, alt, caption}` referencing a local raster asset. Body fields are plain text, not HTML. Use real paths and a verified CTA destination; without one render a clearly non-submitting preview state and record the missing destination privately. Never simulate signup success or collect personal data. Keep implementation limitations out of marketing claims.

The preview needs semantic headings, responsive CSS, visible keyboard focus, 4.5:1 normal-text/3:1 large-text contrast, meaningful links/controls, and no clipping at narrow widths. Use no framework, remote fonts, trackers, backend implication, or unnecessary JavaScript. Inspect desktop and narrow viewport renders; verify actual copy, focus/CTA behavior, links, assets, and no overflow. Report unavailable visual inspection as partial. A preview does not imply deployment or complete WCAG conformance.
