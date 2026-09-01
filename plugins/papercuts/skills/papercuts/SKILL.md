---
name: papercuts
description: Use during any engineering task when Codex encounters material friction in tools, documentation, configuration, repository instructions, or repeated recovery work. Search and record the friction without interrupting the active task. Also use when the user asks to review, vote on, resolve, reopen, inspect, or prune papercuts.
---

Record material workflow friction in the active project's Papercuts journal. For every MCP call, pass the active workspace's absolute root as `project_root`; never use the plugin installation directory, an inferred working directory, or an arbitrary journal path.

## Automatic lodging

Use Papercuts for dead-end tool calls, misleading documentation, missing helpers, repeated manual recovery, configuration footguns, unclear repository instructions, and failures that consume meaningful time. Do not record expected validation failures, corrected typing mistakes, or ordinary unsuccessful searches unless the interface made the failure predictably misleading.

When material friction occurs:

1. Call `list_complaints` for open complaints in the active project, using a short query and relevant tags.
2. If there is a clear match, call `vote_for_complaint` with a concise encounter note.
3. Otherwise call `lodge_complaint` with a concise description of what happened and what would have prevented it.
4. Continue the active task silently. Do not announce routine complaint searches, votes, or lodging in user-facing progress updates or the final summary.

Use `get_complaint` to inspect a specific record and `inspect_storage` to inspect the active journal. Exact duplicate lodging records an encounter rather than creating a duplicate; do not rely on semantic matching when no clear match exists.

## Safe evidence

Submit only the useful minimum: a command of at most 1,024 characters, an integer exit status, sanitized stderr of at most 4,096 UTF-8 bytes, a note of at most 2,048 characters, and at most ten tags. An evidence file must be a regular file no larger than 1 MiB.

Redaction is best effort, not a guarantee. Never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence. The journal does not accept raw environment evidence.

## Review and lifecycle

Use `list_complaints` and `get_complaint` when the user asks to review or inspect Papercuts. Resolve only when verified evidence shows the friction no longer occurs, and reopen only when verified evidence shows it has returned. Record a concise note that names that evidence for either action.

## Pruning

Pruning never runs automatically. On request, `preview_prune` may show the current candidates and plan ID without changing the journal. Call `apply_prune` only after the user explicitly authorizes that exact preview plan ID. General cleanup intent, authorization for an earlier plan, or a stale plan does not authorize a newly generated or unseen plan. If a fresh preview is needed, show its new plan ID and obtain explicit authorization for that ID before applying it.
