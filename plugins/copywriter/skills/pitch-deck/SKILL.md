---
name: pitch-deck
description: Use when transforming repository evidence or supplied pitch notes into an editable PowerPoint deck with speaker notes, sourced charts, and rendered previews.
---

# Pitch deck

Read the shared [workflow and source gate](../write/references/workflow.md), [editorial guidance](../write/references/editorial.md), [deck guide](references/decks.md), and [visuals](../write/references/visuals.md) when assets are used.

Accept `--purpose adopter|investor|sales|sponsor`, `--delivery live|send-ahead`, `--slides N`, and `--minutes N` plus shared options. Default to adopter and send-ahead unless context indicates otherwise; state assumptions. Target roughly 8–12 substantive slides, but let source substance determine count. A slide target never authorizes fabricated commercial facts or padding.

Create an actual editable `pitch-deck.pptx`, `slides.json`, `speaker-notes.md`, actual assets/data, rendered preview PDF and slide images when compatible rendering is available, and `review.md`. An outline, a PDF alone, or full-slide raster images do not satisfy the PowerPoint contract.

Prefer a discovered host presentation capability supporting editable export, notes, and rendering. Otherwise use the packaged [render-deck.js](../../scripts/render-deck.js) with the schema and verification steps in the deck guide. No runtime dependency installation is required for the packaged generator; office rendering is a separately detected capability. Never equate successful PPTX generation with reviewed layout or editor compatibility.
