# Deck narrative and generation

| Purpose | Source-led narrative | Required evidence |
| --- | --- | --- |
| Adopter | Problem, current workflow, product, demonstration, fit/limits, first use | Repository behavior, examples, prerequisites |
| Investor | Purpose, problem, solution, why now, market, alternatives, model, progress, team, ask | Human pitch brief, attributable market/business facts, authorized financial material |
| Sales | Buyer problem, workflow, solution, proof, implementation, fit, next step | Product source and approved customer/operational evidence |
| Sponsor | Purpose, users served, demonstrated value, maintenance needs, proposed support, next step | Maintainer notes, real usage, authorized support proposal |

Investor order adapts Sequoia guidance; it is not a fundraising formula. Say concept/pre-revenue when relevant. Missing business data produces supported slides plus a private missing-input list and partial status, never plausible placeholder figures. For live delivery reduce slide detail and put explanation in notes; for send-ahead make the story understandable without speech. Do not silently reuse one visual file for both.

## Packaged renderer

Resolve [render-deck.js](../../../scripts/render-deck.js) relative to this installed reference and execute Node with argument arrays: script path, `slides.json` path, new output directory. Run from the authorized workspace. The output must be a new directory within that workspace with an existing parent; never overwrite another run. Input assets/data must be local relative files contained under the `slides.json` parent, including resolved symlink targets.

Input is a JSON object with `title`, optional installed `fontFace` and `language` locale, `claims: [{id}]`, `assets: [{id,file,alt,source_file?}]`, and `slides`. Every slide has unique `id` and `title`, plain-text `body`, `notes`, `claim_ids`, `asset_ids`, and `layout`. Layouts are `title`, `statement`, `two-column`, `image`, `diagram`, `chart`, `closing`, `sources`, and `appendix`.

- `two-column` additionally has `columns: [{title,body},{title,body}]`.
- `image` and `diagram` reference exactly one asset ID. The renderer embeds PNG/JPEG; preserve original editable `.svg`/`.mmd` as `source_file` for diagrams and render a raster copy first. Retained SVG accepts a restricted static shapes/text subset; scripts, styles, external references, and unsupported attributes are rejected. Keep richer authorized source separately in the private working directory if it cannot pass the renderer's safe subset.
- `chart` additionally has `chart: {file,type,alt}` with type `bar` or `line`. Its local JSON data is `{units,labels,series:[{name,values}],source,method}`. Values must correspond to labels; missing/invalid referenced data is a generation error. Include real units, source, labels, and methodology; preserve derivations and distinguish measured results, forecasts, and hypothetical examples.

Use claim IDs from the private ledger, but export only safe claim identifiers and public citations. Put short citations on factual slides where useful; full public sources and qualifications belong in notes or a sources appendix. All embedded notes are public deck content.

The generator uses the bundled pinned PptxGenJS path and writes editable text/shapes/charts, notes, slide source, asset/data copies, and `render-status.json`. It then reads the generated PPTX with bundled @office-kit/pptx 0.12.0 and renders `previews/slide-N.svg` with @office-kit/pptx-preview 0.9.1. Only their JavaScript SVG path is bundled; it requires no browser, native renderer, or font files. PDF and PNG export are not supported. Font metrics are estimated, so text wrapping and layout can differ from PowerPoint. Unsupported content or preview failures preserve the PPTX and are reported in the status file. Overall status remains partial until preview inspection and applicable content checks are completed; successful SVG generation is not visual review. Host compatibility and exact tested versions are in [compatibility](../../../packaging/compatibility.md).

## Visual and package verification

Start with 16:9, restrained palette, installed readable font, consistent margins, roughly 28–36 pt titles and 20–24 pt body text. These are starting settings; judge actual renders. Split crowded content instead of endlessly shrinking it. Crop/annotate genuine demos to remain legible; move detailed interfaces to an appendix when needed.

Inspect every generated SVG for clipping, overlap, missing images, labels, and chart-data mismatches. Record actual checks and renderer/version in the review. If SVG inspection is unavailable, deliver the files with partial status and record visual review as not checked. Do not install external rendering software; an explicit request for unsupported PDF or PNG output receives the supported files with partial status. SVG previews are approximate and do not establish editor compatibility.

Check expected slide count, unique titles, editable objects, notes, links, and embedded media in the PPTX package. Check final accessibility metadata and meaningful reading order independently from image previews; informative images need alternatives, and charts need textual explanation/data. Use an application's accessibility checker when available. A PNG preview cannot establish reading order/alt metadata; contrast is not full accessibility conformance. Do not claim accessible PDF unless export preserves tagging and reading order.

At runtime report exactly which checks ran; file creation does not establish compatibility with PowerPoint, Keynote, or Google Slides. Only claim editor compatibility when the deck was actually opened and checked in that editor. Finish with editable PPTX, source, notes, data/assets, SVG previews, and review notes listing remaining limits.
