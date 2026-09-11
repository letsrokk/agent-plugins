# Compatibility and release evidence

Implementation target: Copywriter 0.1.0. This record distinguishes package checks from actual host support. Release acceptance remains pending until the unmet checks below are completed.

| Target or capability | Evidence | Status |
| --- | --- | --- |
| Portable v1 | Pinned official schema in `plugin.schema.json`; shared skill paths checked after relocation | Schema and relocation checks pass |
| Codex | CLI 0.154.0 detected on macOS; native manifest declares `./skills/`; local scaffold validator passes | Installation and picker invocation not tested |
| Claude Code | Official 2.1.268 CLI in temporary storage; `plugin validate` exited 0 | Manifest passes with optional-author warning; installed skill invocation not tested |
| Local HTML | Node.js generator and Safari 26.6.2: desktop preview and 390 × 844 responsive hero inspected | Generation/security checks pass; full-page narrow-screen scrolling and keyboard review incomplete |
| Editable PowerPoint | Bundled PptxGenJS 4.0.1; OOXML checks for text, notes, chart values, workbook, media, alt text, ratio, and locale; eight-slide demo opened in LibreOffice Impress 26.2.6.3 with editable text objects | Generation and real-editor opening verified |
| PDF and slide previews | Independent headless LibreOffice 26.2.6.3 export; PDFKit produced eight page PNGs | Every slide and contact sheet inspected; no clipping or unreadable chart values observed; accessibility checker not run |
| Images | Host-generated lead illustration plus original SVG diagram rasterized with resvg 2.6.2 | Actual assets inspected with captions, alternatives and provenance; provider availability remains host-dependent |

The current packaged generator requires only Node.js and produces SVG previews using bundled @office-kit/pptx 0.12.0 and @office-kit/pptx-preview 0.9.1. PDF and PNG export have been removed. The office-rendering results above are historical checks of the initial implementation, not current runtime requirements. SVG generation was checked for all nine layouts, bar and line chart value labels, escaped text, and embedded raster images. Font measurements remain approximate; these checks do not establish PowerPoint layout compatibility.

No desktop application is installed or configured by this plugin. Desktop checks used a temporary LibreOffice disk image, then quit the application and unmounted it. Keynote onboarding required accepting a software license; that action was not taken. Impress supplied the real-editor check instead. Text skills and packaged deck generation require no office software.

The local Codex scaffold validator passes with isolated PyYAML. Codex publisher metadata uses Rokk Club, the existing repository marketplace owner and copyright holder; it does not invent an individual author. Native ingestion remains unverified. The repository validator verifies synchronized identity and skill discovery paths.

Record exact host/model versions and actual results in `tests/evaluation.md` in the source checkout. Evaluation files are deliberately omitted from installed releases; this compatibility record accompanies them.

## Release gates

Run all six skills in each tested host from relocated packages, including offline research and unavailable-image cases. Check that outputs stay outside the installed package. Record absence of browsing for `--research off`; do not infer it from prose. If claiming editor compatibility, open a generated deck in the named editor and inspect every slide; this is separate from Node-only generation checks. Check notes, chart values, titles, alt text, reading order, and sources. Run the application's accessibility checker where available; do not claim tagged PDF accessibility from image previews.

Use the documented Claude development commands only when that CLI is installed: `claude plugin validate /path/to/copywriter` and `claude --plugin-dir /path/to/copywriter`. These commands are documented upstream, not tested here. For Codex, use an isolated test home and marketplace rather than changing a user's normal installation. Never infer picker syntax from the portable specification.

Official references: [portable schema](https://agent-plugins.org/schemas/1.0.0/plugin.schema.json), [Agent Skills](https://agentskills.io/specification), and [Claude plugin reference](https://code.claude.com/docs/en/plugins-reference), checked 2026-09-11. Format conformance does not establish task capabilities or installation behavior.
