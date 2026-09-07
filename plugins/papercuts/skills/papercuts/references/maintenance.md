# Inspection and maintenance

For requested reviews or inspection, use `list_complaints` and `get_complaint`. Lists and mutation acknowledgments contain compact summaries; `get_complaint` supplies a record's evidence and history. Use `inspect_storage` to inspect the active journal.

Resolve only when verified evidence shows friction no longer occurs; reopen only when verified evidence shows it returned. Include a concise note naming that evidence.

## Pruning

Never prune automatically. On request:

1. Use `preview_prune` to show candidates and the plan ID without changing the journal.
2. Obtain explicit user authorization of that exact preview plan ID before `apply_prune`.

General cleanup intent, authorization for an earlier plan, or a stale plan does not authorize a newly generated or unseen plan. If another preview is needed, show its new plan ID and obtain explicit authorization for that ID before applying it.
