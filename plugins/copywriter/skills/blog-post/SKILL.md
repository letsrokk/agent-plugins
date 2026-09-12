---
name: blog-post
description: Use when transforming supplied drafts, substantive notes, or an author's existing writing into social media posts, X/Twitter threads, LinkedIn posts or articles, or personal blog posts.
---

# Blog post

Read the shared [workflow and source gate](../write/references/workflow.md), [editorial guidance](../write/references/editorial.md), and the relevant format in [writing and handoff](references/formats.md). Read the [research synthesis](references/research.md) when selecting or explaining a practice or checking its evidence limits. This skill transforms the author's substance for a public audience; it does not generate a persona or argument from a topic.

## Source and scope

Require a draft, outline, substantive notes, transcript, or existing author-written piece that supplies the intended point, supporting facts or experience, and takeaway. A short post can have a short source; do not demand an essay to rewrite one complete thought. A topic, keywords, bare link collection, or repository alone is insufficient. Read a supplied article URL when permitted; its actual contents may qualify, but a link is not evidence until inspected. When source is missing, return `needs-source` with one focused request for the author's point and supporting substance, not finished post prose.

Identify who is speaking, to whom, on which platform, and for what purpose. Use supplied writing to preserve voice. Default to curious general-public readers and engaging, conversational language. Explain unfamiliar terms through their everyday consequence. A LinkedIn destination does not automatically imply jargon or a corporate voice.

Preserve attribution, uncertainty, time frames, and the scope of results. Never invent first-person experience, emotions, opinions, quotes, credentials, customers, or numbers. Third-party material supports an attributed summary; it does not become the author's lived experience or endorsement. Research may verify and contextualize supplied substance, but cannot supply a missing personal position. Flag contradictions and propose material additions separately for author input.

## Draft and adapt

Accept `--platform x|linkedin|blog`, `--format post|thread|longform`, `--max-chars N`, `--words N`, and `--variants N` plus shared options. These are prompt options, not executable commands. Infer format from the request; default to one post for a named social platform and longform for a personal blog. Ask for the destination if it materially affects an otherwise ambiguous request. Do not silently turn a requested single post into a thread or article to evade a limit.

Choose one source-backed point and make its relevance apparent at the start. Develop it with the strongest supplied detail, then the author's takeaway or an appropriate next action. This is a useful sequence, not a mandatory template. A question is optional and should invite a specific, worthwhile response. Do not add engagement bait, a sales pitch, or a cliffhanger by default.

Adapt each requested version independently: short form selects and compresses; longform develops the supplied reasoning and qualifications. Preserve the meaning across versions without forcing identical openings. Let source substance determine length. Offer fewer words or request more material when a target would require padding. Variants change emphasis or structure without changing facts.

## Deliver and verify

For posts, deliver each copy-ready body as `post.txt`; use `post-01.txt`, etc. for threads, and separate platform/variant directories when needed. Put labels and counts in private review notes, outside reusable copy. For longform, deliver `post.md` and `post-meta.json` with title, summary, language, and destination; do not invent author identity, publication date, or URL. Preserve shared private brief/claim/review records and `sources.json`; add asset records only when assets exist. An explicit inline-only request overrides the default file handoff.

Check each final body against its actual destination limit, including links, line breaks, hashtags, and thread numbering. Record the counting method and any unverified platform behavior. Review the opening and ending against the source, every factual implication, paragraph flow, and the shared punctuation rules. Keep public attribution beside borrowed claims; private sources alone do not provide reader-facing attribution. Map source passages to each post or longform section in `review.md`.

No scheduling or publication is implied. For LinkedIn, consult the current [AI-assisted content guidance](https://www.linkedin.com/help/linkedin/answer/a1481496) when research is enabled; accurately describe assistance and applicable disclosure recommendations in the handoff. Offline mode records that policy verification is stale. Do not promise reach, authenticity detection results, or acceptance.
