# Papercuts

Papercuts gives Codex a durable local journal for material engineering friction. During an engineering task, the included skill searches open complaints in the active project, votes for a clear match, or lodges a concise new complaint. It then continues the task without announcing routine logging.

The skill records dead-end tool calls, misleading documentation, missing helpers, repeated recovery work, configuration footguns, unclear repository instructions, and failures that consume meaningful time. It excludes expected validation failures, corrected typing mistakes, and ordinary unsuccessful searches unless an interface made the failure predictably misleading.

## Requirements and privacy

The CLI requires Python 3.11 or later. The local MCP server also requires [uv](https://docs.astral.sh/uv/); on its first run, `uv` may fetch the pinned `mcp==2.1.1` dependency. The core and CLI have no dependency beyond Python.

Papercuts stores data locally. It has no telemetry and makes no network requests, except for `uv` fetching that pinned MCP dependency on first run. Credential redaction is best effort, not a guarantee: never submit secrets, credentials, raw environment dumps, arbitrary attachments, or unbounded evidence.

Context supports a command up to 1,024 characters, an integer exit status, sanitized stderr up to 4,096 UTF-8 bytes, and a note up to 2,048 characters. Evidence files must be regular files no larger than 1 MiB. Tags are limited to ten.

## Storage and scope

By default, Papercuts writes the current project's journal to `<project>/.codex/papercuts.jsonl`. User scope writes a shared journal to `~/.codex/papercuts.jsonl`; lists from it stay scoped to the current project unless `--all-projects` is supplied.

Scope configuration files are `<project>/.codex/papercuts.config.json` and `~/.codex/papercuts.config.json`. Project configuration takes precedence over user configuration. The CLI selects storage in this order: `--file`, `PAPERCUTS_FILE`, project configuration, user configuration, then project scope.

```sh
# Make this project use the user journal.
plugins/papercuts/scripts/papercuts config set-scope user --level project

# Set the default scope in your user configuration.
plugins/papercuts/scripts/papercuts config set-scope user --level user

# Show the active journal and scope.
plugins/papercuts/scripts/papercuts config show
```

Each event is one JSON object per line in the active `papercuts.jsonl` journal. Pruning creates timestamped backups in `<project>/.codex/papercuts.backups/` for project scope or `~/.codex/papercuts.backups/` for user scope. Backups are never removed automatically.

## CLI

All ordinary commands emit one JSON envelope on stdout. Errors emit one structured JSON envelope on stderr. `list --format md` is the only human-readable output mode.

```text
papercuts [--file PATH] lodge TEXT [--severity minor|major|blocker] [--tag TAG] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH] [--evidence NOTE]
papercuts [--file PATH] list [--status open|resolved|all] [--query TEXT] [--tag TAG] [--severity minor|major|blocker] [--min-encounters N] [--recent-days N] [--all-projects] [--limit N] [--format json|md]
papercuts [--file PATH] get ID [--all-projects]
papercuts [--file PATH] vote ID [--note TEXT] [--cmd COMMAND] [--exit STATUS] [--stderr-file PATH]
papercuts [--file PATH] resolve ID [--note TEXT]
papercuts [--file PATH] reopen ID [--note TEXT]
papercuts [--file PATH] doctor [--repair-tail]
papercuts [--file PATH] prune preview [--resolved-older-than-days N] [--open-max-encounters N] [--open-inactive-for-days N] [--projects current|all]
papercuts [--file PATH] prune apply PLAN_ID [--resolved-older-than-days N] [--open-max-encounters N] [--open-inactive-for-days N] [--projects current|all]
papercuts [--file PATH] config show
papercuts [--file PATH] config set-scope project|user --level project|user
```

For example:

```sh
plugins/papercuts/scripts/papercuts lodge "The validator hides the failing manifest path" --severity major --tag tooling
plugins/papercuts/scripts/papercuts list --status open
plugins/papercuts/scripts/papercuts doctor
```

`prune preview` is safe and writes nothing. Before `prune apply PLAN_ID`, inspect the preview and explicitly authorize that exact plan ID. A general request to clean up, authorization for an earlier plan, or a stale plan never authorizes a newly generated plan.

## MCP tools

Codex starts the local stdio MCP server through `scripts/launch-mcp`. Every MCP call requires the active absolute workspace root as `project_root`. The tools are `lodge_complaint`, `list_complaints`, `get_complaint`, `vote_for_complaint`, `resolve_complaint`, `reopen_complaint`, `inspect_storage`, `preview_prune`, and `apply_prune`. MCP cannot set scope or accept an arbitrary journal path.
