# Evidence

Submit only useful minimum evidence: commands at most 1,024 characters, integer exit statuses, sanitized stderr at most 4,096 UTF-8 bytes, notes at most 2,048 characters, and at most ten tags. Evidence files must be regular files no larger than 1 MiB.

Redaction is best effort, not a guarantee. Never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence. Raw environment evidence is unsupported.

Generic system paths such as `/tmp` and `/dev/null` stay readable; identifying descendants are elided (`/tmp/client/file` becomes `/tmp/...`), and home paths and UNC shares are redacted. Quote paths containing spaces.

When path details are essential or redaction is uncertain:

1. Call `lodge_complaint` with `dry_run: true` (CLI: `lodge --dry-run`).
2. Inspect sanitized text and evidence in `preview`; adjust inputs if needed.
3. Lodge with `dry_run: false` or omit the flag.

Preview validates inputs but does not read or write the journal, amend old records, or guarantee a later write. Keep ordinary lodging to one call.
