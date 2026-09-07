---
name: papercuts
description: Record material engineering friction in tools, documentation, configuration, or repeated recovery work. Use also to review, vote on, resolve, reopen, inspect, or prune papercuts.
---

Record material workflow friction in the client's user journal (`~/.codex/papercuts.jsonl` or `~/.claude/papercuts.jsonl`). No project/custom journals or storage configuration changes. Every MCP call must use the active workspace's absolute root as `project_root`, never the plugin directory, inferred working directory, or journal path.

## Automatic lodging

Record dead-end tools, misleading documentation, missing helpers, repeated recovery, configuration footguns, unclear repository instructions, and failures consuming meaningful time. Exclude expected validation failures, corrected typos, and ordinary unsuccessful searches unless the interface made failure predictably misleading.

1. Search open project complaints with `list_complaints`: short query, relevant tags, `limit: 5`.
2. For a clear match, `vote_for_complaint` with a concise encounter note; otherwise `lodge_complaint` describing what happened and what would prevent it. Exact duplicates add encounters, but lodging does not replace searching for semantic matches.
3. Continue the active task silently: no routine search/vote/lodging announcements in updates or final summaries. Ordinary lodging takes one call.

## Safety and references

Submit only useful minimum evidence; integer exit statuses; notes: at most 2,048 characters; tags: at most ten. Redaction is best effort. Never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence; raw environment evidence is unsupported.

Before submitting commands, stderr, evidence files, or path-sensitive details, or whenever redaction is uncertain, read [Evidence](references/evidence.md) for limits, redaction, and preview requirements. Text-only lodging needs no extra read unless path-sensitive or redaction is uncertain.

Before inspection, resolution, reopening, or pruning, read [Maintenance](references/maintenance.md). Resolve only when verified evidence shows friction is gone; reopen only when verified evidence shows it returned. Name that evidence in a concise note. Never prune automatically; `apply_prune` requires explicit user authorization of that exact preview plan ID. General cleanup intent or an earlier/stale approval is insufficient.

Read references only when absent from active context; reuse them while present, including after compaction.
