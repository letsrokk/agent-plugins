---
name: pitch-deck
description: Use when transforming repository evidence or supplied pitch notes into an editable PowerPoint deck with speaker notes, sourced charts, and SVG previews.
---

# Pitch deck

Read the shared [workflow and source gate](../write/references/workflow.md), [editorial guidance](../write/references/editorial.md), [deck guide](references/decks.md), and [visuals](../write/references/visuals.md) when assets are used.

Accept `--purpose adopter|investor|sales|sponsor`, `--delivery live|send-ahead`, `--slides N`, and `--minutes N` plus shared options. Default to adopter and send-ahead unless context indicates otherwise; state assumptions. Target roughly 8–12 substantive slides, but let source substance determine count. A slide target never authorizes fabricated commercial facts or padding.

Create an actual editable `pitch-deck.pptx`, `slides.json`, `speaker-notes.md`, actual assets/data, SVG slide previews under `previews/`, and `review.md`. PDF and PNG export are not supported. An outline, a PDF alone, or full-slide raster images do not satisfy the PowerPoint contract.

Prefer a discovered host presentation capability supporting editable export, notes, and SVG previews. Otherwise use the packaged [render-deck.js](../../scripts/render-deck.js) with the schema and verification steps in the deck guide. The packaged generator requires only Node.js 24 or later; its bundled JavaScript renderer produces SVG previews without external tools. Font measurements are approximate; inspect every preview. Never equate successful PPTX generation with reviewed layout or editor compatibility.
