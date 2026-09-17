# Version control

Use the contract for the requested artifact:

- **Commit:** Use a conventional single-line subject. Apply a required ticket prefix when repository instructions or the branch establish one. Add a body only for context a future maintainer cannot recover from the diff.
- **Pull or merge request title:** State the delivered outcome in the repository's established form. Keep required ticket prefixes exact.
- **Pull or merge request description:** Require Summary and Verification sections with concise bullets unless a repository template specifies otherwise. Include delivered behavior and necessary rationale in Summary; include checks, results, and verification limits in Verification. If no checks ran, say so. Add Risks only for material reviewer concerns; omit other unnecessary sections. Keep the description as short as possible without compromising clarity, precision, or necessary reviewer context.
- **New review finding:** Lead with the finding or requested change and whether it blocks. For findings needing explanation, use concise bullets for evidence, impact, and the requested action rather than several prose paragraphs. Use a plain approval when there is no finding.
- **Discussion reply:** Follow the thread-reply guidance below.

## Thread replies

Treat the parent comment as shared context. Add acknowledgment and only new information, usually in one or two natural sentences. Do not quote or paraphrase the finding merely to confirm it. Repeat only the fragment needed to distinguish multiple findings, correct a misunderstanding, or explain a partial fix.

- **Accepting:** Confirm agreement; add a decision or next action only when established. "Agreed." can be enough.
- **Verifying a finding:** State verification and useful new evidence without repeating the reported mechanism or impact.
- **Confirming a fix:** State what changed; include a supplied commit reference, relevant check result, or limitation when useful.
- **Disagreeing or blocked:** Identify the unresolved point and supporting evidence. Make partial completion explicit.

Keep accepted, verified, fixed, and tested distinct. Use brief prose without mandatory labels, headings, bullets, praise, or sign-offs. Given a committed fix and passing regression test, "Fixed in `<commit>`. The regression test passes." is sufficient; replace the placeholder with the supplied reference. A reply does not authorize posting or resolving the thread.

## Structure

- Use the required sections and bullets for PR/MR descriptions; prefer sections and bullets for new review findings. Keep one point per bullet; avoid turning paragraphs into long bullet items.
- Use tables when comparing alternatives, before/after behavior, or several checks with the same fields. Do not force narrative explanations or a single finding into a table.
- Group multiple findings under descriptive headings. Keep a simple comment or reply to one or two sentences when extra structure would add noise.
- Use brief prose only where connected reasoning makes the point clearer. Do not repeat the same information in prose, bullets, and tables.

Before drafting a pull or merge request description, read the diff. Do not inventory changed files or methods, repeat rationale already documented in code, recount commit history, or assess the work's quality. Include rationale only when it affects review or is not recoverable from the diff.

Describe delivered work. Mention a rejected option only when it explains a material constraint a reviewer would otherwise encounter.

Scope verification claims to their evidence: a focused test proves its covered path, not every related behavior.

Commit subjects and pull or merge request titles may use conventional fragments instead of sentence-form prose.
