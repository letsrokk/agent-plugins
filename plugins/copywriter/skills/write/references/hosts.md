# Host capabilities and invocation

The shared skills do not assume browsing, filesystem access, or image generation. Discover actual callable capabilities once per run. Text work needs source access and file writing for file deliverables, but no Node/office dependency. Deck and SVG preview generation need only Node.js 24; PDF and PNG export are not supported. The preview libraries are bundled JavaScript and require no browser, native renderer, or font files. SVG font measurements are approximate; visual verification still needs image inspection. Illustrations need a working image capability; visual verification needs image inspection. Missing capabilities yield the supported files and explicit partial completion. Chat-only copy is appropriate only when its missing file deliverables are identified.

Natural-language invocation is portable: “Use Copywriter to create a README for this package.” Logical requests such as `copywriter article` are semantic prompts, not installed shell commands. Claude Code's plugin namespace uses `/copywriter:readme`, `/copywriter:article`, and `/copywriter:write brief`. Portable v1 defines no slash syntax. For Codex use the entry actually displayed by the installed skill picker; do not promise an unobserved slash command.

See the release [compatibility record](../../../packaging/compatibility.md) for tested host versions, installation/invocation evidence, and limits. Schema validation is not host discovery or behavioral testing. Do not infer support for other Claude products, every portable client, or every office editor. Keep installed package files read-only; all artifacts belong in an authorized user destination.

## Installed skills and design help

Use the active session's skill/plugin catalog first. If it is incomplete and the host exposes a read-only installed-plugin listing or skill search, use that to find relevant helpers. Marketplace listings and files in a cache do not prove a plugin is enabled or callable. If discovery is unavailable, record that limit privately and continue with Copywriter's own guidance; do not scan unrelated user files, install plugins, or change configuration.

Select by the current deliverable and the helper's actual description, not its name alone. Honor an explicitly requested helper. Read only the selected skill's instructions through its advertised location or host mechanism, and follow its applicable workflow within the user's scope. Apply an available matching helper when it improves the requested presentation; merely listing it is not using it.

- Text-only work: use relevant available writing guidance for voice and formatting. A tagline or Markdown-only edit does not need a visual-design workflow.
- Web presentation: a frontend design skill such as Impeccable can refine typography, spacing, hierarchy, responsive layout, and accessibility in a local HTML preview, even when no images are selected.
- Decks: prefer a presentation design skill that supports the requested editable output and previews. Do not assume a frontend-only skill can create PowerPoint files. Use available illustration, diagram, or chart skills for those specific assets.

Give the helper the reader, purpose, revised copy, approved brand/assets, target format, and authorized output location. Keep factual claims, source qualifications, citations, and editable-output requirements intact. Copywriter remains responsible for final wording and verification; review substantive text changes against the source. Helpers do not expand permission to install dependencies, send private material, publish, or redesign unrelated surfaces.

Use the helper through available skill/tool mechanisms; apply its instructions locally when no separate execution mechanism exists. Record the helper actually used, its contribution, and checks in `review.md`. If none fits or it cannot run, use the existing renderer/guidance. Absence of an optional helper alone does not make the result partial; an unmet requested artifact or required check does.
