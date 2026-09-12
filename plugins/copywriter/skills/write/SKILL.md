---
name: write
description: Use when Copywriter is requested to transform source material into a tagline, README, landing page, pitch deck, article, or social post, or to prepare a product brief or scoped research dossier.
---

# Copywriter

Transform substantive source material into useful local artifacts. Read [workflow](references/workflow.md) for every run, including its source gate, options, evidence records, and completion contract. Read [editorial guidance](references/editorial.md) when drafting.

Route to the requested medium and read its instructions:

| Request | Skill |
| --- | --- |
| Repository tagline or short description | [tagline](../tagline/SKILL.md) |
| README creation or scoped edit | [readme](../readme/SKILL.md) |
| Landing-page copy or static preview | [landing-page](../landing-page/SKILL.md) |
| Editable presentation | [pitch-deck](../pitch-deck/SKILL.md) |
| Transform an author's article source | [article](../article/SKILL.md) |
| Social posts, X/Twitter threads, LinkedIn writing, or personal blog reflections | [blog-post](../blog-post/SKILL.md) |

Use `blog-post` for platform adaptations and personal reflections; use `article` for standalone tutorials, explainers, Medium pieces, and illustrated articles. Follow the explicitly requested skill when named.

For `brief`, inspect the product and deliver `brief.json`, `claims.json`, a short human summary, and `review.md`; do not add channel copy. For `research`, read [research](references/research.md), answer the scoped question in a source dossier, save `sources.json`, and explain supported implications for the brief. Research mode does not authorize an invented article thesis.

Natural-language example: “Use Copywriter to create a README for this package.” Logical requests such as `copywriter brief` are prompt vocabulary, not a shell executable. For host-specific invocation or missing capabilities, read [hosts](references/hosts.md).
