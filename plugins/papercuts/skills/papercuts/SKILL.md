---
name: papercuts
description: Record material engineering friction in tools, documentation, configuration, or repeated recovery work. Use also to review, vote on, resolve, reopen, inspect, or prune papercuts.
---

Record material workflow friction for the active project in the client's user journal (`~/.codex/papercuts.jsonl` or `~/.claude/papercuts.jsonl`). Project and custom journal locations are unsupported; do not change storage configuration. For every MCP call, pass the active workspace's absolute root as `project_root`; never use the plugin installation directory, an inferred working directory, or an arbitrary journal path.

## Automatic lodging

Use Papercuts for dead-end tool calls, misleading documentation, missing helpers, repeated manual recovery, configuration footguns, unclear repository instructions, and failures that consume meaningful time. Do not record expected validation failures, corrected typing mistakes, or ordinary unsuccessful searches unless the interface made the failure predictably misleading.

When material friction occurs:

1. Call `list_complaints` for open complaints in the active project, using a short query, relevant tags, and `limit: 5`.
2. If there is a clear match, call `vote_for_complaint` with a concise encounter note.
3. Otherwise call `lodge_complaint` with a concise description of what happened and what would have prevented it.
4. Continue the active task silently. Do not announce routine complaint searches, votes, or lodging in user-facing progress updates or the final summary.

Lists and mutation acknowledgments contain compact complaint summaries. Use `get_complaint` to inspect evidence and history for a specific record and `inspect_storage` to inspect the active journal. Exact duplicate lodging records an encounter rather than creating a duplicate; do not rely on semantic matching when no clear match exists.

## Safe evidence

Submit only the useful minimum: a command of at most 1,024 characters, an integer exit status, sanitized stderr of at most 4,096 UTF-8 bytes, a note of at most 2,048 characters, and at most ten tags. An evidence file must be a regular file no larger than 1 MiB.

Redaction is best effort, not a guarantee. Never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence. The journal does not accept raw environment evidence.

Generic system paths such as `/tmp` and `/dev/null` stay readable; identifying descendants are elided (for example, `/tmp/client/file` becomes `/tmp/...`), and home paths and UNC shares are redacted. Quote paths containing spaces. When path details are essential or redaction is uncertain, call `lodge_complaint` with `dry_run: true` (CLI: `lodge --dry-run`), inspect the sanitized text and evidence in `preview`, adjust if needed, then lodge with `dry_run: false` or omit the flag. Preview validates inputs but does not read or write the journal, amend old records, or guarantee a later write. Keep ordinary lodging to one call.

## Review and lifecycle

Use `list_complaints` and `get_complaint` when the user asks to review or inspect Papercuts. Resolve only when verified evidence shows the friction no longer occurs, and reopen only when verified evidence shows it has returned. Record a concise note that names that evidence for either action.

## Pruning

Pruning never runs automatically. On request, `preview_prune` may show the current candidates and plan ID without changing the journal. Call `apply_prune` only after the user explicitly authorizes that exact preview plan ID. General cleanup intent, authorization for an earlier plan, or a stale plan does not authorize a newly generated or unseen plan. If a fresh preview is needed, show its new plan ID and obtain explicit authorization for that ID before applying it.
