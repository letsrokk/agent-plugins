# Copywriter

Turn verified product material into clear, well-structured taglines, READMEs, landing pages, editable pitch decks, and articles. Copywriter prioritizes the argument, wording, voice, and text formatting, with illustrations, diagrams, charts, and deck graphics to support the message. Articles require your draft, outline, or substantive notes; a topic alone is insufficient.

The default voice is warm, engaging, and accessible to the general public, with marketing language used in moderation. Copywriter explains why the subject matters, keeps promises grounded, and adapts to specialist audiences when the task calls for it.

Ask your agent: “Use Copywriter to create a README for this package.” Other examples:

- “Use Copywriter to rewrite these article notes, preserving the uncertainty, with a lead illustration.”
- “Use Copywriter to make an adopter pitch deck from this repository.”
- “Use Copywriter to draft a landing page with a local HTML preview.”
- “Use Copywriter to build a product brief without channel copy.”

The six skills are `write` (router, brief, research), `tagline`, `readme`, `landing-page`, `pitch-deck`, and `article`. Claude Code documents namespaced invocation such as `/copywriter:readme` and `/copywriter:write brief`. Codex picker syntax has not yet been verified; use natural language. These are agent requests, not shell commands.

## Installation and capabilities

Copywriter checks the active host's available skills and plugins for relevant help. It searches descriptions for capabilities such as frontend design, typography, visual hierarchy, responsive layout, accessibility, and presentation design, then uses a matching skill to improve visual presentation after revising the copy. It preserves source-backed claims, citations, and the requested output format. Optional design plugins are not required: the bundled generators remain available, and Copywriter does not install or enable other plugins. Text-only work stays focused on writing and formatting.

The source uses one shared skill tree with portable, Codex, and Claude manifests. Release directories contain exactly one target manifest. See [compatibility and release checks](packaging/compatibility.md) before treating any host as supported.

Text tasks use the agent's file tools without a runtime dependency. Local HTML and PowerPoint generation require Node.js 24 or later; the PowerPoint dependency is bundled. Browsing, image generation, and image inspection use capabilities supplied by the host. Copywriter does not install or configure integrations. The deck generator produces editable PowerPoint, source, notes, assets, and SVG slide previews using only Node.js. The pinned @office-kit/pptx and @office-kit/pptx-preview JavaScript libraries are bundled; no browser, native renderer, or font files are required. PDF and PNG export are not supported. Preview font measurements are approximate; inspect the SVGs before claiming reviewed layout, and do not treat them as proof of PowerPoint compatibility.

Output defaults to a new `copywriter-output/<run-id>/` in the authorized workspace. Direct requests to edit an existing README authorize that edit. Publishing, deployment, repository metadata changes, and sending artifacts require authorization for those actions. Private briefs, claims, and review notes stay out of public exports.

## Local generators

The skills prepare and verify the inputs. Run these commands from the authorized output workspace, replacing the paths with real files and **new** output directories:

```sh
node /path/to/copywriter/scripts/render-page.js page.json page-output
node /path/to/copywriter/scripts/render-deck.js slides.json deck-output
```

The [landing-page guide](skills/landing-page/SKILL.md) describes the plain-text page model. The [deck guide](skills/pitch-deck/references/decks.md) describes slides, notes, assets, and chart data. Generators never establish claim truth or visual quality by themselves. Review their stage reports and inspect the rendered artifacts.

## Contributor checks and packaging

From this plugin directory in the **source checkout** (contributor files are omitted from installed releases):

```sh
npm ci --ignore-scripts --no-audit --no-fund
node scripts/build.js
node scripts/test.js
node scripts/validate.js
node scripts/package.js /existing/parent/new-release-directory
```

Packaging copies shared files into `copywriter-portable/copywriter`, `copywriter-codex/copywriter`, and `copywriter-claude/copywriter`. No external symlinks or development dependencies are required at runtime. The committed native manifests are the release inputs; keep all three versions synchronized. The portable manifest is validated against the official pinned v1 schema. Native ingestion and behavioral tests are separate checks.

The repository's MIT license applies to this new plugin. Bundled dependencies retain their own notices. The [source bibliography](skills/write/references/sources.md) attributes editorial guidance; it provides no evidence for product or marketing performance claims.
